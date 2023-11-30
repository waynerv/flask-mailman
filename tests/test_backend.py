from email.header import Header
from email.utils import parseaddr
import os
import socket
from ssl import SSLError
import tempfile
import pytest

from pathlib import Path
from unittest.mock import Mock, patch
from smtplib import SMTP, SMTPException
from email import message_from_binary_file, message_from_bytes
from io import StringIO
from flask_mailman import EmailMessage
from flask_mailman.backends import locmem, smtp
from tests import MailmanCustomizedTestCase
from aiosmtpd.controller import Controller


class SMTPHandler:
    def __init__(self, *args, **kwargs):
        self.mailbox = []

    async def handle_DATA(self, server, session, envelope):
        data = envelope.content
        mail_from = envelope.mail_from

        message = message_from_bytes(data.rstrip())
        message_addr = parseaddr(message.get("from"))[1]
        if mail_from != message_addr:
            # According to the spec, mail_from does not necessarily match the
            # From header - this is the case where the local part isn't
            # encoded, so try to correct that.
            lp, domain = mail_from.split("@", 1)
            lp = Header(lp, "utf-8").encode()
            mail_from = "@".join([lp, domain])

        if mail_from != message_addr:
            return f"553 '{mail_from}' != '{message_addr}'"
        self.mailbox.append(message)
        return "250 OK"

    def flush_mailbox(self):
        self.mailbox[:] = []


class SmtpdContext:
    def __init__(self, mailman):
        self.mailman = mailman

    def __enter__(self):
        # Find a free port.
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        self.smtp_handler = SMTPHandler()
        self.smtp_controller = Controller(
            self.smtp_handler,
            hostname="127.0.0.1",
            port=port,
        )
        self.mailman.port = port
        self.smtp_controller.start()

    def __exit__(self, *args):
        self.smtp_controller.stop()


class TestBackend(MailmanCustomizedTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def stop_smtp(cls):
        cls.smtp_controller.stop()

    def test_console_backend(self):
        self.app.extensions['mailman'].backend = 'console'
        msg = EmailMessage(
            subject="testing",
            to=["to@example.com"],
            body="testing",
        )
        msg.send()

        captured = self.capsys.readouterr()
        assert "testing" in captured.out
        assert "To: to@example.com" in captured.out

    def test_console_stream_kwarg(self):
        """
        The console backend can be pointed at an arbitrary stream.
        """
        self.app.extensions['mailman'].backend = 'console'
        s = StringIO()
        connection = self.mail.get_connection(stream=s)
        self.mail.send_mail(
            "Subject",
            "Content",
            "from@example.com",
            ["to@example.com"],
            connection=connection,
        )
        message = s.getvalue().split("\n" + ("-" * 79) + "\n")[0].encode()
        self.assertMessageHasHeaders(
            message,
            {
                ("MIME-Version", "1.0"),
                ("Content-Type", 'text/plain; charset="utf-8"'),
                ("Content-Transfer-Encoding", "7bit"),
                ("Subject", "Subject"),
                ("From", "from@example.com"),
                ("To", "to@example.com"),
            },
        )
        self.assertIn(b"\nDate: ", message)

    def test_dummy_backend(self):
        self.app.extensions['mailman'].backend = 'dummy'
        msg = EmailMessage(
            subject="testing",
            to=["to@example.com"],
            body="testing",
        )
        assert msg.send() == 1

    def test_file_backend(self):
        with tempfile.TemporaryDirectory() as tempdir:
            self.app.extensions['mailman'].backend = 'file'
            self.app.extensions['mailman'].file_path = tempdir
            with self.mail.get_connection() as conn:
                msg = EmailMessage(
                    subject="testing",
                    to=["to@example.com"],
                    body="testing",
                    connection=conn,
                )
                msg.send()

            wrote_file = Path(conn._fname)
            assert wrote_file.is_file()
            assert "To: to@example.com" in wrote_file.read_text()

    def test_file_sessions(self):
        """Make sure opening a connection creates a new file"""
        with tempfile.TemporaryDirectory() as tempdir:
            self.app.extensions['mailman'].backend = 'file'
            self.app.extensions['mailman'].file_path = tempdir
            msg = EmailMessage(
                "Subject",
                "Content",
                "bounce@example.com",
                ["to@example.com"],
                headers={"From": "from@example.com"},
            )
            connection = self.mail.get_connection()
            connection.send_messages([msg])

            self.assertEqual(len(os.listdir(tempdir)), 1)
            with open(os.path.join(tempdir, os.listdir(tempdir)[0]), "rb") as fp:
                message = message_from_binary_file(fp)
            self.assertEqual(message.get_content_type(), "text/plain")
            self.assertEqual(message.get("subject"), "Subject")
            self.assertEqual(message.get("from"), "from@example.com")
            self.assertEqual(message.get("to"), "to@example.com")

            connection2 = self.mail.get_connection()
            connection2.send_messages([msg])
            self.assertEqual(len(os.listdir(tempdir)), 2)

            connection.send_messages([msg])
            self.assertEqual(len(os.listdir(tempdir)), 2)

            msg.connection = self.mail.get_connection()
            self.assertTrue(connection.open())
            msg.send()
            self.assertEqual(len(os.listdir(tempdir)), 3)
            msg.send()
            self.assertEqual(len(os.listdir(tempdir)), 3)

            connection.close()

    def test_locmem_backend(self):
        self.app.extensions['mailman'].backend = 'locmem'
        msg = EmailMessage(
            subject="testing",
            to=["to@example.com"],
            body="testing",
        )
        msg.send()

        self.assertEqual(len(self.mail.outbox), 1)
        sent_msg = self.mail.outbox[0]
        self.assertEqual(sent_msg.subject, "testing")
        self.assertEqual(sent_msg.to, ["to@example.com"])
        self.assertEqual(sent_msg.body, "testing")
        self.assertEqual(sent_msg.from_email, self.app.extensions["mailman"].default_sender)

    def test_locmem_shared_messages(self):
        """
        Make sure that the locmen backend populates the outbox.
        """
        self.app.extensions['mailman'].backend = 'locmem'
        connection = locmem.EmailBackend()
        connection2 = locmem.EmailBackend()
        email = EmailMessage(
            "Subject",
            "Content",
            "bounce@example.com",
            ["to@example.com"],
            headers={"From": "from@example.com"},
        )
        connection.send_messages([email])
        connection2.send_messages([email])
        self.assertEqual(len(self.mail.outbox), 2)

    def test_smtp_backend(self):
        self.app.extensions['mailman'].backend = 'smtp'
        msg = EmailMessage(
            subject="testing",
            to=["to@example.com"],
            body="testing",
        )

        with patch.object(smtp.EmailBackend, 'send_messages') as mock_send_fn:
            mock_send_fn.return_value = 66
            assert msg.send() == 66

    def test_email_authentication_use_settings(self):
        mailman = self.app.extensions['mailman']
        mailman.username = 'not empty username'
        mailman.password = 'not empty password'

        backend = smtp.EmailBackend()
        self.assertEqual(backend.username, "not empty username")
        self.assertEqual(backend.password, "not empty password")

    def test_email_disabled_authentication(self):
        mailman = self.app.extensions['mailman']
        mailman.username = 'not empty username'
        mailman.password = 'not empty password'

        backend = smtp.EmailBackend(username="", password="")
        self.assertEqual(backend.username, "")
        self.assertEqual(backend.password, "")

    def test_auth_attempted(self):
        """
        Opening the backend with non empty username/password tries
        to authenticate against the SMTP server.
        """
        with SmtpdContext(self.app.extensions['mailman']):
            with self.assertRaises(SMTPException, msg="SMTP AUTH extension not supported by server."):
                with smtp.EmailBackend(username="not empty username", password="not empty password"):
                    pass

    def test_server_open(self):
        """
        open() returns whether it opened a connection.
        """
        with SmtpdContext(self.app.extensions['mailman']):
            backend = smtp.EmailBackend(username="", password="")
            self.assertIsNone(backend.connection)
            opened = backend.open()
            backend.close()
            self.assertIs(opened, True)

    def test_reopen_connection(self):
        backend = smtp.EmailBackend()
        # Simulate an already open connection.
        backend.connection = Mock(spec=object())
        self.assertIs(backend.open(), False)

    def test_email_tls_use_settings(self):
        self.app.extensions['mailman'].use_tls = True
        backend = smtp.EmailBackend()
        self.assertTrue(backend.use_tls)

    def test_email_tls_override_settings(self):
        self.app.extensions['mailman'].use_tls = True
        backend = smtp.EmailBackend(use_tls=False)
        self.assertFalse(backend.use_tls)

    def test_email_tls_default_disabled(self):
        backend = smtp.EmailBackend()
        self.assertFalse(backend.use_tls)

    def test_ssl_tls_mutually_exclusive(self):
        msg = "USE_TLS/USE_SSL are mutually exclusive, so only set " "one of those settings to True."
        with self.assertRaises(ValueError, msg=msg):
            smtp.EmailBackend(use_ssl=True, use_tls=True)

    def test_email_ssl_use_settings(self):
        self.app.extensions['mailman'].use_ssl = True
        backend = smtp.EmailBackend()
        self.assertTrue(backend.use_ssl)

    def test_email_ssl_override_settings(self):
        self.app.extensions['mailman'].use_ssl = True
        backend = smtp.EmailBackend(use_ssl=False)
        self.assertFalse(backend.use_ssl)

    def test_email_ssl_default_disabled(self):
        backend = smtp.EmailBackend()
        self.assertFalse(backend.use_ssl)

    def test_email_ssl_certfile_use_settings(self):
        self.app.extensions['mailman'].ssl_certfile = "foo"
        backend = smtp.EmailBackend()
        self.assertEqual(backend.ssl_certfile, "foo")

    def test_email_ssl_certfile_override_settings(self):
        self.app.extensions['mailman'].ssl_certfile = "foo"
        backend = smtp.EmailBackend(ssl_certfile="bar")
        self.assertEqual(backend.ssl_certfile, "bar")

    def test_email_ssl_certfile_default_disabled(self):
        backend = smtp.EmailBackend()
        self.assertIsNone(backend.ssl_certfile)

    def test_email_ssl_keyfile_use_settings(self):
        self.app.extensions['mailman'].ssl_keyfile = "foo"
        backend = smtp.EmailBackend()
        self.assertEqual(backend.ssl_keyfile, "foo")

    def test_email_ssl_keyfile_override_settings(self):
        self.app.extensions['mailman'].ssl_keyfile = "foo"
        backend = smtp.EmailBackend(ssl_keyfile="bar")
        self.assertEqual(backend.ssl_keyfile, "bar")

    def test_email_ssl_keyfile_default_disabled(self):
        backend = smtp.EmailBackend()
        self.assertIsNone(backend.ssl_keyfile)

    def test_email_tls_attempts_starttls(self):
        with SmtpdContext(self.app.extensions['mailman']):
            self.app.extensions['mailman'].use_tls = True
            backend = smtp.EmailBackend()
            self.assertTrue(backend.use_tls)
            with self.assertRaises(SMTPException, msg="STARTTLS extension not supported by server."):
                with backend:
                    pass

    def test_email_ssl_attempts_ssl_connection(self):
        with SmtpdContext(self.app.extensions['mailman']):
            _, tmpKey = tempfile.mkstemp()
            _, tmpCert = tempfile.mkstemp()
            self.app.extensions['mailman'].use_ssl = True
            self.app.extensions['mailman'].ssl_keyfile = tmpKey
            self.app.extensions['mailman'].ssl_certfile = tmpCert

            backend = smtp.EmailBackend()
            self.assertTrue(backend.use_ssl)
            with self.assertRaises(SSLError):
                with backend:
                    pass

            Path(tmpKey).unlink()
            Path(tmpCert).unlink()

    def test_connection_timeout_default(self):
        """The connection's timeout value is None by default."""
        self.app.extensions['mailman'].backend = "smtp"
        connection = self.mail.get_connection()
        self.assertIsNone(connection.timeout)

    def test_connection_timeout_custom(self):
        """The timeout parameter can be customized."""
        with SmtpdContext(self.app.extensions['mailman']):

            class MyEmailBackend(smtp.EmailBackend):
                def __init__(self, *args, **kwargs):
                    kwargs.setdefault("timeout", 42)
                    super().__init__(*args, **kwargs)

            myemailbackend = MyEmailBackend()
            myemailbackend.open()
            self.assertEqual(myemailbackend.timeout, 42)
            self.assertEqual(myemailbackend.connection.timeout, 42)
            myemailbackend.close()

    def test_email_timeout_override_settings(self):
        self.app.extensions['mailman'].timeout = 10
        backend = smtp.EmailBackend()
        self.assertEqual(backend.timeout, 10)

    def test_email_msg_uses_crlf(self):
        """Compliant messages are sent over SMTP."""
        with SmtpdContext(self.app.extensions['mailman']):
            send = SMTP.send
            try:
                smtp_messages = []

                def mock_send(self, s):
                    smtp_messages.append(s)
                    return send(self, s)

                SMTP.send = mock_send

                email = EmailMessage("Subject", "Content", "from@example.com", ["to@example.com"])
                self.mail.get_connection(backend='smtp').send_messages([email])

                # Find the actual message
                msg = None
                for i, m in enumerate(smtp_messages):
                    if m[:4] == "data":
                        msg = smtp_messages[i + 1]
                        break

                self.assertTrue(msg)

                msg = msg.decode()
                # The message only contains CRLF and not combinations of CRLF, LF, and CR.
                msg = msg.replace("\r\n", "")
                self.assertNotIn("\r", msg)
                self.assertNotIn("\n", msg)

            finally:
                SMTP.send = send

    def test_send_messages_after_open_failed(self):
        """
        send_messages() shouldn't try to send messages if open() raises an
        exception after initializing the connection.
        """
        backend = smtp.EmailBackend()
        # Simulate connection initialization success and a subsequent
        # connection exception.
        backend.connection = Mock(spec=object())
        backend.open = lambda: None
        email = EmailMessage("Subject", "Content", "from@example.com", ["to@example.com"])
        self.assertEqual(backend.send_messages([email]), 0)

    def test_send_messages_empty_list(self):
        backend = smtp.EmailBackend()
        backend.connection = Mock(spec=object())
        self.assertEqual(backend.send_messages([]), 0)

    def test_send_messages_zero_sent(self):
        """A message isn't sent if it doesn't have any recipients."""
        backend = smtp.EmailBackend()
        backend.connection = Mock(spec=object())
        email = EmailMessage("Subject", "Content", "from@example.com", to=[])
        sent = backend.send_messages([email])
        self.assertEqual(sent, 0)

    def test_server_stopped(self):
        """
        Closing the backend while the SMTP server is stopped doesn't raise an
        exception.
        """
        with SmtpdContext(self.app.extensions['mailman']):
            self.mail.get_connection('smtp').close()

    def test_fail_silently_on_connection_error(self):
        """
        A socket connection error is silenced with fail_silently=True.
        """
        backend = self.mail.get_connection('smtp')
        with self.assertRaises(ConnectionError):
            backend.open()
        backend.fail_silently = True
        backend.open()

    def test_invalid_backend(self):
        self.app.extensions['mailman'].backend = 'unknown'
        msg = EmailMessage(
            subject="testing",
            to=["to@example.com"],
            body="testing",
        )

        with pytest.raises(RuntimeError) as exc:
            msg.send()
        assert "The available built-in mail backends" in str(exc)

    def test_override_custom_backend(self):
        self.app.extensions['mailman'].backend = 'console'
        with self.mail.get_connection(backend=locmem.EmailBackend) as conn:
            msg = EmailMessage(subject="testing", to=["to@example.com"], body="testing", connection=conn)
            msg.send()

        self.assertEqual(len(self.mail.outbox), 1)
        sent_msg = self.mail.outbox[0]
        self.assertEqual(sent_msg.subject, "testing")

    def test_import_path_locmem_backend(self):
        for i, backend_path in enumerate(
            ["flask_mailman.backends.locmem", "flask_mailman.backends.locmem.EmailBackend"]
        ):
            with self.subTest():
                self.app.extensions['mailman'].backend = backend_path
                msg = EmailMessage(
                    subject="testing",
                    to=["to@example.com"],
                    body="testing",
                )
                msg.send()

                self.assertEqual(len(self.mail.outbox), i + 1)
                sent_msg = self.mail.outbox[0]
                self.assertEqual(sent_msg.subject, "testing")
