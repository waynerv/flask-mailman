"""
Backend for test environment.
"""
from flask_mailman.message import sanitize_address
from .base import BaseEmailBackend


class EmailBackend(BaseEmailBackend):
    """
    An email backend for use during test sessions.

    The test connection stores email messages in a dummy outbox,
    rather than sending them out on the wire.

    The dummy outbox is accessible through the outbox instance attribute.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self.mailman, 'outbox'):
            self.mailman.outbox = []

    def send_messages(self, messages):
        """Redirect messages to the dummy outbox"""
        msg_count = 0
        for message in messages:  # .message() triggers header validation
            message.message()
            self.mailman.outbox.append(message)
            msg_count += 1
        return msg_count

    def _send(self, email_message):
        """Redirect a single message to the dummy outbox and sanitize addresses"""
        if not email_message.recipients():
            return False
        encoding = email_message.encoding or 'utf-8'
        from_email = sanitize_address(email_message.from_email, encoding)
        recipients = [sanitize_address(addr, encoding) for addr in email_message.recipients()]
        message = email_message.message()
        self.mailman.outbox.append(email_message)
        return True
