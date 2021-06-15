from tests import TestCase


class TestInitialization(TestCase):
    def test_init_mail(self):
        mail = self.mail.init_mail(self.app.config, self.app.testing)

        self.assertEqual(self.mail.state.__dict__, mail.__dict__)
