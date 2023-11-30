from email.mime.text import MIMEText
from tests import TestCase


class PythonGlobalState(TestCase):
    """
    UTF-8 text parts shouldn't pollute global email Python package charset registry when
    django.mail.message is imported.
    """

    def test_utf8(self):
        txt = MIMEText("UTF-8 encoded body", "plain", "utf-8")
        self.assertIn("Content-Transfer-Encoding: base64", txt.as_string())

    def test_7bit(self):
        txt = MIMEText("Body with only ASCII characters.", "plain", "utf-8")
        self.assertIn("Content-Transfer-Encoding: base64", txt.as_string())

    def test_8bit_latin(self):
        txt = MIMEText("Body with latin characters: àáä.", "plain", "utf-8")
        self.assertIn("Content-Transfer-Encoding: base64", txt.as_string())

    def test_8bit_non_latin(self):
        txt = MIMEText(
            "Body with non latin characters: А Б В Г Д Е Ж Ѕ З И І К Л М Н О П.",
            "plain",
            "utf-8",
        )
        self.assertIn("Content-Transfer-Encoding: base64", txt.as_string())
