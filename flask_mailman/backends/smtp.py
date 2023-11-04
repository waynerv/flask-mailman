"""SMTP email backend class."""
import smtplib
import ssl
import threading

from flask_mailman.backends.base import BaseEmailBackend
from flask_mailman.message import sanitize_address
from flask_mailman.utils import DNS_NAME


class EmailBackend(BaseEmailBackend):
    """
    A wrapper that manages the SMTP network connection.
    """

    def __init__(
        self,
        host=None,
        port=None,
        username=None,
        password=None,
        use_tls=None,
        fail_silently=False,
        use_ssl=None,
        timeout=None,
        ssl_keyfile=None,
        ssl_certfile=None,
        source_address=None,
        source_port=None,
        **kwargs,
    ):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.host = host or self.mailman.server
        self.port = port or self.mailman.port
        self.username = self.mailman.username if username is None else username
        self.password = self.mailman.password if password is None else password
        self.use_tls = self.mailman.use_tls if use_tls is None else use_tls
        self.use_ssl = self.mailman.use_ssl if use_ssl is None else use_ssl
        self.timeout = self.mailman.timeout if timeout is None else timeout
        self.ssl_keyfile = self.mailman.ssl_keyfile if ssl_keyfile is None else ssl_keyfile
        self.ssl_certfile = self.mailman.ssl_certfile if ssl_certfile is None else ssl_certfile
        self.source_address = self.mailman.source_address if source_address is None else source_address
        self.source_port = self.mailman.source_port if source_port is None else source_port
        if self.use_ssl and self.use_tls:
            raise ValueError(
                "EMAIL_USE_TLS/EMAIL_USE_SSL are mutually exclusive, so only set " "one of those settings to True."
            )
        self.connection = None
        self._lock = threading.RLock()

    @property
    def connection_class(self):
        return smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP

    def open(self):
        """
        Ensure an open connection to the email server. Return whether or not a
        new connection was required (True or False) or None if an exception
        passed silently.
        """
        if self.connection:
            # Nothing to do if the connection is already open.
            return False

        # If local_hostname is not specified, socket.getfqdn() gets used.
        # For performance, we use the cached FQDN for local_hostname.
        connection_params = {'local_hostname': DNS_NAME.get_fqdn()}
        if self.timeout is not None:
            connection_params['timeout'] = self.timeout
        if self.use_ssl:
            connection_params.update(
                {
                    'keyfile': self.ssl_keyfile,
                    'certfile': self.ssl_certfile,
                }
            )
        if self.source_address is not None or self.source_port is not None:
            connection_params['source_address'] = ((self.source_address or ''), (self.source_port or 0))
        try:
            self.connection = self.connection_class(self.host, self.port, **connection_params)

            # TLS/SSL are mutually exclusive, so only attempt TLS over
            # non-secure connections.
            if not self.use_ssl and self.use_tls:
                if self.ssl_certfile:
                    context = ssl.SSLContext().load_cert_chain(self.ssl_certfile, keyfile=self.ssl_keyfile)
                else:
                    context = None
                self.connection.starttls(context=context)
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except OSError:
            if not self.fail_silently:
                raise

    def close(self):
        """Close the connection to the email server."""
        if self.connection is None:
            return
        try:
            try:
                self.connection.quit()
            except (ssl.SSLError, smtplib.SMTPServerDisconnected):
                # This happens when calling quit() on a TLS connection
                # sometimes, or when the connection was already disconnected
                # by the server.
                self.connection.close()
            except smtplib.SMTPException:
                if self.fail_silently:
                    return
                raise
        finally:
            self.connection = None

    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number of email
        messages sent.
        """
        if not email_messages:
            return 0
        with self._lock:
            new_conn_created = self.open()
            if not self.connection or new_conn_created is None:
                # We failed silently on open().
                # Trying to send would be pointless.
                return 0
            num_sent = 0
            for message in email_messages:
                sent = self._send(message)
                if sent:
                    num_sent += 1
            if new_conn_created:
                self.close()
        return num_sent

    def _send(self, email_message):
        """A helper method that does the actual sending."""
        if not email_message.recipients():
            return False
        encoding = email_message.encoding or self.mailman.default_charset
        from_email = sanitize_address(email_message.from_email, encoding)
        recipients = [sanitize_address(addr, encoding) for addr in email_message.recipients()]
        message = email_message.message()
        try:
            self.connection.sendmail(from_email, recipients, message.as_bytes(linesep='\r\n'))
        except smtplib.SMTPException:
            if not self.fail_silently:
                raise
            return False
        return True
