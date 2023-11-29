from unittest import mock
from flask_mailman.message import EmailMessage
from flask_mailman.utils import DNS_NAME
from tests import TestCase


class TestMail(TestCase):
    def test_send_mail(self):
        self.mail.send_mail(
            subject="testing",
            message="test",
            from_email=self.MAIL_DEFAULT_SENDER,
            recipient_list=["tester@example.com"],
        )
        self.assertEqual(len(self.mail.outbox), 1)
        sent_msg = self.mail.outbox[0]
        self.assertEqual(sent_msg.from_email, self.MAIL_DEFAULT_SENDER)

    def test_send_mail_with_tuple_from_email(self):
        self.mail.send_mail(
            subject="testing",
            message="test",
            from_email=("Name", "support@mysite.com"),
            recipient_list=["tester@example.com"],
        )
        self.assertEqual(len(self.mail.outbox), 1)
        sent_msg = self.mail.outbox[0]
        self.assertEqual(sent_msg.from_email, "Name <support@mysite.com>")

    def test_send_mass_mail(self):
        message1 = (
            'Subject here',
            'Here is the message',
            'from@example.com',
            ['first@example.com', 'other@example.com'],
        )
        message2 = ('Another Subject', 'Here is another message', ('Name', 'from@example.com'), ['second@test.com'])
        self.mail.send_mass_mail((message1, message2), fail_silently=False)
        self.assertEqual(len(self.mail.outbox), 2)
        msg1 = self.mail.outbox[0]
        self.assertEqual(msg1.subject, "Subject here")
        self.assertEqual(msg1.to, ['first@example.com', 'other@example.com'])
        self.assertEqual(msg1.body, "Here is the message")
        self.assertEqual(msg1.from_email, "from@example.com")
        msg2 = self.mail.outbox[1]
        self.assertEqual(msg2.subject, "Another Subject")
        self.assertEqual(msg2.from_email, "Name <from@example.com>")

    @mock.patch("socket.getfqdn", return_value="漢字")
    def test_non_ascii_dns_non_unicode_email(self, mocked_getfqdn):
        delattr(DNS_NAME, "_fqdn")
        email = EmailMessage("subject", "content", "from@example.com", ["to@example.com"])
        email.encoding = "iso-8859-1"
        self.assertIn("@xn--p8s937b>", email.message()["Message-ID"])
