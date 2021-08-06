from tests import TestCase

class UnitTest(TestCase):
    # MAIL_BACKEND = 'flask_mailman.backends.locmem.EmailBackend'
    # MAIL_BACKEND = 'flask_mailman.backends.locmem'

    MAIL_BACKEND = 'locmem12'
    # MAIL_BACKEND = ''

class TestImportBackend(UnitTest):
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