from email import message_from_bytes
import unittest
from contextlib import contextmanager

import pytest
from flask import Flask

from flask_mailman import Mail


class TestCase(unittest.TestCase):
    TESTING = True
    MAIL_DEFAULT_SENDER = "support@mysite.com"

    def setUp(self):
        self.app = Flask(import_name=__name__)
        self.app.config.from_object(self)
        self.assertTrue(self.app.testing)
        self.mail = Mail(self.app)
        self.ctx = self.app.test_request_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    @contextmanager
    def mail_config(self, **settings):
        """
        Context manager to alter mail config during a test and restore it after,
        even in case of a failure.
        """
        original = {}
        state = self.mail.state
        for key in settings:
            assert hasattr(state, key)
            original[key] = getattr(state, key)
            setattr(state, key, settings[key])

        yield
        # restore
        for k, v in original.items():
            setattr(state, k, v)

    def assertIn(self, member, container, msg=None):
        if hasattr(unittest.TestCase, 'assertIn'):
            return unittest.TestCase.assertIn(self, member, container, msg)
        return self.assertTrue(member in container)

    def assertNotIn(self, member, container, msg=None):
        if hasattr(unittest.TestCase, 'assertNotIn'):
            return unittest.TestCase.assertNotIn(self, member, container, msg)
        return self.assertFalse(member in container)

    def assertIsNone(self, obj, msg=None):
        if hasattr(unittest.TestCase, 'assertIsNone'):
            return unittest.TestCase.assertIsNone(self, obj, msg)
        return self.assertTrue(obj is None)

    def assertIsNotNone(self, obj, msg=None):
        if hasattr(unittest.TestCase, 'assertIsNotNone'):
            return unittest.TestCase.assertIsNotNone(self, obj, msg)
        return self.assertTrue(obj is not None)

    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys


class MailmanCustomizedTestCase(TestCase):
    def assertMessageHasHeaders(self, message, headers):
        """
        Asserts that the `message` has all `headers`.

        message: can be an instance of an email.Message subclass or a string
                with the contents of an email message.
        headers: should be a set of (header-name, header-value) tuples.
        """
        if isinstance(message, bytes):
            message = message_from_bytes(message)
        msg_headers = set(message.items())
        self.assertTrue(
            headers.issubset(msg_headers),
            msg="Message is missing " "the following headers: %s" % (headers - msg_headers),
        )

    def get_decoded_attachments(self, message):
        """
        Encode the specified EmailMessage, then decode
        it using Python's email.parser module and, for each attachment of the
        message, return a list of tuples with (filename, content, mimetype).
        """
        msg_bytes = message.message().as_bytes()
        email_message = message_from_bytes(msg_bytes)

        def iter_attachments():
            for i in email_message.walk():
                if i.get_content_disposition() == "attachment":
                    filename = i.get_filename()
                    content = i.get_payload(decode=True)
                    mimetype = i.get_content_type()
                    yield filename, content, mimetype

        return list(iter_attachments())

    def get_message(self):
        return self.mail.outbox[0].message()

    def flush_mailbox(self):
        self.mail.outbox.clear()
