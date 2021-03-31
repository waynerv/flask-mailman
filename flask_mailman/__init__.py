"""
Tools for sending email.
"""
from flask import current_app

from flask_mailman.backends.console import EmailBackend as ConsoleEmailBackend
from flask_mailman.backends.dummy import EmailBackend as DummyEmailBackend
from flask_mailman.backends.filebased import EmailBackend as FileEmailBackend
from flask_mailman.backends.locmem import EmailBackend as MemoryEmailBackend
from flask_mailman.backends.smtp import EmailBackend as SMTPEmailBackend

from .message import (
    DEFAULT_ATTACHMENT_MIME_TYPE, BadHeaderError, EmailMessage,
    EmailMultiAlternatives, SafeMIMEMultipart, SafeMIMEText,
    forbid_multi_line_headers, make_msgid,
)
from flask_mailman.utils import DNS_NAME, CachedDnsName

__all__ = [
    'CachedDnsName', 'DNS_NAME', 'EmailMessage', 'EmailMultiAlternatives',
    'SafeMIMEText', 'SafeMIMEMultipart', 'DEFAULT_ATTACHMENT_MIME_TYPE',
    'make_msgid', 'BadHeaderError', 'forbid_multi_line_headers',
    'Mail',
]

MAIL_BACKENDS = {
    'console': ConsoleEmailBackend,
    'dummy': DummyEmailBackend,
    'file': FileEmailBackend,
    'locmem': MemoryEmailBackend,
    'smtp': SMTPEmailBackend
}


class _MailMixin(object):

    def get_connection(self, backend=None, fail_silently=False, **kwds):
        """Load an email backend and return an instance of it.

        If backend is None (default), use app.config.MAIL_BACKEND.

        Both fail_silently and other keyword arguments are used in the
        constructor of the backend.
        """
        app = getattr(self, "app", None) or current_app
        try:
            mailman = app.extensions['mailman']
        except KeyError:
            raise RuntimeError("The current application was not configured with Flask-Mailman")

        try:
            if backend is None:
                klass = MAIL_BACKENDS[mailman.backend]
            elif isinstance(backend, str):
                klass = MAIL_BACKENDS[backend]
            else:
                klass = backend
        except KeyError:
            raise RuntimeError("The available built-in mail backends are: {}".format(', '.join(MAIL_BACKENDS.keys())))

        return klass(mailman=mailman, fail_silently=fail_silently, **kwds)

    def send_mail(self, subject, message, from_email=None, recipient_list=None,
                  fail_silently=False, auth_user=None, auth_password=None,
                  connection=None, html_message=None):
        """
        Easy wrapper for sending a single message to a recipient list. All members
        of the recipient list will see the other recipients in the 'To' field.

        If auth_user is None, use the MAIL_USERNAME setting.
        If auth_password is None, use the MAIL_PASSWORD setting.
        """
        connection = connection or self.get_connection(
            username=auth_user,
            password=auth_password,
            fail_silently=fail_silently,
        )
        mail = EmailMultiAlternatives(subject, message, from_email, recipient_list, connection=connection)
        if html_message:
            mail.attach_alternative(html_message, 'text/html')

        return mail.send()

    def send_mass_mail(self, datatuple, fail_silently=False, auth_user=None,
                       auth_password=None, connection=None):
        """
        Given a datatuple of (subject, message, from_email, recipient_list), send
        each message to each recipient list. Return the number of emails sent.

        If from_email is None, use the MAIL_DEFAULT_SENDER setting.
        If auth_user and auth_password are set, use them to log in.
        If auth_user is None, use the MAIL_USERNAME setting.
        If auth_password is None, use the MAIL_PASSWORD setting.

        Note: The API for this method is frozen. New code wanting to extend the
        functionality should use the EmailMessage class directly.
        """
        connection = connection or self.get_connection(
            username=auth_user,
            password=auth_password,
            fail_silently=fail_silently,
        )
        messages = [
            EmailMessage(subject, message, sender, recipient, connection=connection)
            for subject, message, sender, recipient in datatuple
        ]
        return connection.send_messages(messages)


class _Mail(_MailMixin):
    """Initialize a state instance with all configs and methods"""

    def __init__(self, server, port, username, password, use_tls, use_ssl, default_sender, timeout, ssl_keyfile,
                 ssl_certfile, use_localtime, file_path, default_charset, backend):
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.default_sender = default_sender
        self.timeout = timeout
        self.ssl_keyfile = ssl_keyfile
        self.ssl_certfile = ssl_certfile
        self.use_localtime = use_localtime
        self.file_path = file_path
        self.default_charset = default_charset
        self.backend = backend


class Mail(_MailMixin):
    """Manages email messaging

    :param app: Flask instance
    """

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.state = self.init_app(app)
        else:
            self.state = None

    @staticmethod
    def init_mail(config, testing=False):
        # Set default mail backend in different environment
        mail_backend = config.get('MAIL_BACKEND')
        if mail_backend is None or mail_backend not in MAIL_BACKENDS.keys():
            mail_backend = 'locmem' if testing else 'smtp'

        return _Mail(
            config.get('MAIL_SERVER', 'localhost'),
            config.get('MAIL_PORT', 25),
            config.get('MAIL_USERNAME'),
            config.get('MAIL_PASSWORD'),
            config.get('MAIL_USE_TLS', False),
            config.get('MAIL_USE_SSL', False),
            config.get('MAIL_DEFAULT_SENDER'),
            config.get('MAIL_TIMEOUT'),
            config.get('MAIL_SSL_KEYFILE'),
            config.get('MAIL_SSL_CERTFILE'),
            config.get('MAIL_USE_LOCALTIME', False),
            config.get('MAIL_FILE_PATH'),
            config.get('MAIL_DEFAULT_CHARSET', 'utf-8'),
            mail_backend,
        )

    def init_app(self, app):
        """Initializes your mail settings from the application settings.

        You can use this if you want to set up your Mail instance
        at configuration time.

        :param app: Flask application instance
        """
        state = self.init_mail(app.config, app.testing)

        # register extension with app
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['mailman'] = state
        return state

    def __getattr__(self, name):
        return getattr(self.state, name, None)
