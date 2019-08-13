from unittest import mock

from flask_mailman import Message, BadHeaderError
from tests import TestCase


class TestConnection(TestCase):

    def test_send_message(self):
        with self.mail.get_connection() as conn:
            conn.send_message(subject="testing",
                              recipients=["to@example.com"],
                              body="testing")
            self.assertEqual(len(self.mail.outbox), 1)
            sent_msg = self.mail.outbox[0]
            self.assertEqual(sent_msg.from_email, self.app.extensions['mailman'].default_sender)

    def test_send_single(self):
        with self.mail.get_connection() as conn:
            msg = Message(subject="testing",
                          recipients=["to@example.com"],
                          body="testing")
            conn._send(msg)
            self.assertEqual(len(self.mail.outbox), 1)
            sent_msg = self.mail.outbox[0]
            self.assertEqual(sent_msg.subject, "testing")
            self.assertEqual(sent_msg.to, ["to@example.com"])
            self.assertEqual(sent_msg.body, "testing")
            self.assertEqual(sent_msg.from_email, self.app.extensions['mailman'].default_sender)

    def test_send_many(self):
        with self.mail.get_connection() as conn:
            for i in range(100):
                msg = Message(subject="testing",
                              recipients=["to@example.com"],
                              body="testing")
                conn._send(msg)
            self.assertEqual(len(self.mail.outbox), 100)
            sent_msg = self.mail.outbox[0]
            self.assertEqual(sent_msg.from_email, self.app.extensions['mailman'].default_sender)

    def test_send_without_sender(self):
        self.app.extensions['mailman'].default_sender = None
        msg = Message(subject="testing", recipients=["to@example.com"], body="testing")
        with self.mail.get_connection() as conn:
            self.assertRaises(IndexError, conn._send, msg)

    def test_send_without_recipients(self):
        msg = Message(subject="testing",
                      recipients=[],
                      body="testing")
        with self.mail.get_connection() as conn:
            self.assertEqual(False, conn._send(msg))

    def test_bad_header_subject(self):
        msg = Message(subject="testing\n\r",
                      body="testing",
                      recipients=["to@example.com"])
        with self.mail.get_connection() as conn:
            self.assertRaises(BadHeaderError, conn._send, msg)

    def test_sendmail_with_ascii_recipient(self):
        conn = self.mail.get_connection('smtp')
        with mock.patch.object(conn, 'connection') as connection:
            msg = Message(subject="testing",
                          sender="from@example.com",
                          recipients=["to@example.com"],
                          body="testing",
                          extra_headers={'message-id': 'test_message_id'})
            conn._send(msg)

            connection.sendmail.assert_called_once_with(
                "from@example.com",
                ["to@example.com"],
                msg.message().as_bytes(linesep='\r\n'),
                msg.mail_options,
                msg.rcpt_options
            )

    def test_sendmail_with_non_ascii_recipient(self):
        conn = self.mail.get_connection('smtp')
        with mock.patch.object(conn, 'connection') as connection:
            msg = Message(subject="testing",
                          sender="from@example.com",
                          recipients=[u'ÄÜÖ → ✓ <to@example.com>'],
                          body="testing",
                          extra_headers={'message-id': 'test_message_id'})
            conn._send(msg)

            connection.sendmail.assert_called_once_with(
                "from@example.com",
                ["=?utf-8?b?w4TDnMOWIOKGkiDinJM=?= <to@example.com>"],
                msg.message().as_bytes(linesep='\r\n'),
                msg.mail_options,
                msg.rcpt_options
            )

    def test_sendmail_with_ascii_body(self):
        conn = self.mail.get_connection('smtp')
        with mock.patch.object(conn, 'connection') as connection:
            msg = Message(subject="testing",
                          sender="from@example.com",
                          recipients=["to@example.com"],
                          body="body",
                          extra_headers={'message-id': 'test_message_id'})
            conn._send(msg)

            connection.sendmail.assert_called_once_with(
                "from@example.com",
                ["to@example.com"],
                msg.message().as_bytes(linesep='\r\n'),
                msg.mail_options,
                msg.rcpt_options
            )

    def test_sendmail_with_non_ascii_body(self):
        conn = self.mail.get_connection('smtp')
        with mock.patch.object(conn, 'connection') as connection:
            msg = Message(subject="testing",
                          sender="from@example.com",
                          recipients=["to@example.com"],
                          body=u"Öö",
                          extra_headers={'message-id': 'test_message_id'})

            conn._send(msg)

            connection.sendmail.assert_called_once_with(
                "from@example.com",
                ["to@example.com"],
                msg.message().as_bytes(linesep='\r\n'),
                msg.mail_options,
                msg.rcpt_options
            )
