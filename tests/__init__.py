import unittest
from contextlib import contextmanager

import pytest
from flask import Flask

from flask_mailman import Mail


class TestCase(unittest.TestCase):
    TESTING = True
    MAIL_DEFAULT_SENDER = "support@mysite.com"

    def setUp(self):
        self.app = Flask(__name__)
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
