import pytest

from flask_mailman import BadHeaderError, EmailMessage
from tests import TestCase


class TestConnection(TestCase):
    def test_send_message(self):
        msg = EmailMessage(
            subject="testing",
            to=["to@example.com"],
            body="testing",
        )
        msg.send()
        self.assertEqual(len(self.mail.outbox), 1)
        sent_msg = self.mail.outbox[0]
        self.assertEqual(sent_msg.from_email, self.app.extensions["mailman"].default_sender)

    def test_send_message_using_connection(self):
        with self.mail.get_connection() as conn:
            msg = EmailMessage(
                subject="testing",
                to=["to@example.com"],
                body="testing",
                connection=conn,
            )
            msg.send()
            self.assertEqual(len(self.mail.outbox), 1)
            sent_msg = self.mail.outbox[0]
            self.assertEqual(sent_msg.from_email, self.app.extensions["mailman"].default_sender)

            conn.send_messages([msg])
            self.assertEqual(len(self.mail.outbox), 2)

    def test_send_single(self):
        with self.mail.get_connection() as conn:
            msg = EmailMessage(
                subject="testing",
                to=["to@example.com"],
                body="testing",
                connection=conn,
            )
            msg.send()
            self.assertEqual(len(self.mail.outbox), 1)
            sent_msg = self.mail.outbox[0]
            self.assertEqual(sent_msg.subject, "testing")
            self.assertEqual(sent_msg.to, ["to@example.com"])
            self.assertEqual(sent_msg.body, "testing")
            self.assertEqual(sent_msg.from_email, self.app.extensions["mailman"].default_sender)

    def test_send_many(self):
        with self.mail.get_connection() as conn:
            msgs = []
            for i in range(10):
                msg = EmailMessage(subject="testing", to=["to@example.com"], body="testing")
                msgs.append(msg)
            conn.send_messages(msgs)
            self.assertEqual(len(self.mail.outbox), 10)
            sent_msg = self.mail.outbox[0]
            self.assertEqual(sent_msg.from_email, self.app.extensions["mailman"].default_sender)

    def test_send_without_sender(self):
        self.app.extensions['mailman'].default_sender = None
        msg = EmailMessage(subject="testing", to=["to@example.com"], body="testing")
        msg.send()
        self.assertEqual(len(self.mail.outbox), 1)
        sent_msg = self.mail.outbox[0]
        self.assertEqual(sent_msg.from_email, None)

    def test_send_without_to(self):
        msg = EmailMessage(subject="testing", to=[], body="testing")
        assert msg.send() == 0

    def test_bad_header_subject(self):
        msg = EmailMessage(subject="testing\n\r", body="testing", to=["to@example.com"])
        with pytest.raises(BadHeaderError):
            msg.send()
