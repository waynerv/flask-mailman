import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from flask_mailman import EmailMessage
from flask_mailman.backends import locmem, smtp
from tests import TestCase


class TestBackend(TestCase):
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
