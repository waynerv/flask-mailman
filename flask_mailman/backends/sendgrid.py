from .smtp import EmailBackend as _EmailBackend

"""
This is useful if you are about send emails using sendgrid.
here is the example to configure sendgris with flask-mailman.

app.config['MAIL_BACKEND'] = 'sendgrid'
app.config['SENDGRID_API_KEY'] = 'your_sendgrid_api_Key'
app.config['MAIL_DEFAULT_SENDER'] = 'sendgrid_verfied_sender_id'
"""

__all__ = ('EmailBackend')


class EmailBackend(_EmailBackend):
    """
    default backend for sending emails using sendgrid.
    """