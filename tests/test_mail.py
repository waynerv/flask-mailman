from flask_mailman import Message
from tests import TestCase


class TestMail(TestCase):

    def test_send(self):
        with self.mail.get_connection() as conn:
            msg = Message(subject="testing",
                          recipients=["tester@example.com"],
                          body="test",
                          connection=conn)
            self.mail.send(msg)
            self.assertIsNotNone(msg.message()['Date'])
            self.assertEqual(len(self.mail.outbox), 1)
            sent_msg = self.mail.outbox[0]
            self.assertEqual(msg.from_email, self.app.extensions['mailman'].default_sender)

    def test_send_message(self):
        with self.mail.get_connection() as conn:
            conn.send_message(subject="testing",
                              recipients=["tester@example.com"],
                              body="test", )
            self.assertEqual(len(self.mail.outbox), 1)
            msg = self.mail.outbox[0]
            self.assertEqual(msg.subject, "testing")
            self.assertEqual(msg.to, ["tester@example.com"])
            self.assertEqual(msg.body, "test")
            self.assertEqual(msg.from_email, self.app.extensions['mailman'].default_sender)
