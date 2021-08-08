# Welcome to Flask-Mailman

The core part of this extension's source code comes directly from Django's mail module, but with a few interface [differences](#differences-with-django).

And following documentation also draws heavily from Django's.

## Installation

Install with `pip`:
```bash
pip install Flask-Mailman
```

## Configuration

Flask-Mailman is configured through the standard Flask config API. A list of configuration keys currently understood by the extension:

- **MAIL_SERVER**: The host to use for sending email.

    default ‘localhost’.

- **MAIL_PORT**: Port to use for the SMTP server.

    default 25.

- **MAIL_USERNAME**: Username to use for the SMTP server. If empty, Flask-Mailman won’t attempt authentication.

    default None.

- **MAIL_PASSWORD**: Password to use for the SMTP server defined in MAIL_HOST. This setting is used in conjunction with MAIL_USERNAME when authenticating to the SMTP server. If either of these configs is empty, Flask-Mailman won’t attempt authentication.

    default None.

- **MAIL_USE_TLS**: Whether to use a TLS (secure) connection when talking to the SMTP server. This is used for explicit TLS connections, generally on port 587.

    default False.

- **MAIL_USE_SSL**: Whether to use an implicit TLS (secure) connection when talking to the SMTP server. In most email documentation this type of TLS connection is referred to as SSL. It is generally used on port 465.

    default False

- **MAIL_TIMEOUT**: Specifies a timeout in seconds for blocking operations like the connection attempt.

    default None.

- **MAIL_SSL_KEYFILE**: If MAIL_USE_SSL or MAIL_USE_TLS is True, you can optionally specify the path to a PEM-formatted certificate chain file to use for the SSL connection.

    default None.

- **MAIL_SSL_CERTFILE**: If MAIL_USE_SSL or MAIL_USE_TLS is True, you can optionally specify the path to a PEM-formatted private key file to use for the SSL connection.

    Note that setting MAIL_SSL_CERTFILE and MAIL_SSL_KEYFILE doesn’t result in any certificate checking. They’re passed to the underlying SSL connection. Please refer to the documentation of Python’s `ssl.wrap_socket()` function for details on how the certificate chain file and private key file are handled.

    default None.

- **MAIL_DEFAULT_SENDER**: Default email address to use for various automated correspondence from the site manager(s).

    default None.

- **MAIL_BACKEND**: The backend to use for sending emails.

    Default: 'smtp'. In addition the standard Flask TESTING configuration option is used for testing. When `TESTING=True` and `MAIL_BACKEND` is not provided, default will be set to 'locmem'.

- **MAIL_FILE_PATH**: The directory used by the file email backend to store output files.

    Default: Not defined.

- **MAIL_USE_LOCALTIME**: Whether to send the SMTP **Date** header of email messages in the local time zone (True) or in UTC (False).

    Default: False.

Emails are managed through a *Mail* instance:
```python
from flask import Flask
from flask_mailman import Mail

app = Flask(__name__)
mail = Mail(app)
```
In this case all emails are sent using the configuration values of the application that was passed to the *Mail* class constructor.

Alternatively you can set up your *Mail* instance later at configuration time, using the `init_app` method:
```python
from flask import Flask
from flask_mailman import Mail

mail = Mail()

app = Flask(__name__)
mail.init_app(app)
```
In this case emails will be sent using the configuration values from Flask’s `current_app` context global. This is useful if you have multiple applications running in the same process but with different configuration options.

## Sending messages

To send a message first create a `EmailMessage` instance:
```python hl_lines="3-11"
from flask_mailman import EmailMessage

msg = EmailMessage(
    'Hello',
    'Body goes here',
    'from@example.com',
    ['to1@example.com', 'to2@example.com'],
    ['bcc@example.com'],
    reply_to=['another@example.com'],
    headers={'Message-ID': 'foo'},
)
msg.send()
```
Then send the message using `send()` method:
```python hl_lines="12 13"
from flask_mailman import EmailMessage

msg = EmailMessage(
    'Hello',
    'Body goes here',
    'from@example.com',
    ['to1@example.com', 'to2@example.com'],
    ['bcc@example.com'],
    reply_to=['another@example.com'],
    headers={'Message-ID': 'foo'},
)
msg.send()
```

The `EmailMessage` class is initialized with the following parameters (in the given order, if positional arguments are used).
All parameters are optional and can be set at any time prior to calling the `send()` method.

- **subject**: The subject line of the email.
- **body**: The body text. This should be a plain text message.
- **from_email**: The sender’s address. Both `fred@example.com` or `"Fred" <fred@example.com>` forms are legal. If omitted, the MAIL_DEFAULT_SENDER config is used.
- **to**: A list or tuple of recipient addresses.
- **bcc**: A list or tuple of addresses used in the “Bcc” header when sending the email.
- **connection**: An email backend instance. Use this parameter if you want to use the same connection for multiple messages. If omitted, a new connection is created when `send()` is called.
- **attachments**: A list of attachments to put on the message. These can be either MIMEBase instances, or (filename, content, mimetype) triples.
- **headers**: A dictionary of extra headers to put on the message. The keys are the header name, values are the header values. It’s up to the caller to ensure header names and values are in the correct format for an email message. The corresponding attribute is `extra_headers`.
- **cc**: A list or tuple of recipient addresses used in the “Cc” header when sending the email.
- **reply_to**: A list or tuple of recipient addresses used in the “Reply-To” header when sending the email.

`EmailMessage.send(fail_silently=False)` sends the message.

If a connection was specified when the email was constructed, that connection will be used. Otherwise, an instance of the default backend will be instantiated and used.

If the keyword argument `fail_silently` is True, exceptions raised while sending the message will be quashed. An empty list of recipients will not raise an exception.

### Sending html content

By default, the **MIME** type of the body parameter in an `EmailMessage` is "text/plain". It is good practice to leave this alone, because it guarantees that any recipient will be able to read the email, regardless of their mail client. However, if you are confident that your recipients can handle an alternative content type, you can use the `content_subtype` attribute on the `EmailMessage` class to change the main content type. The major type will always be "text", but you can change the subtype. For example:

```python
from flask_mailman import EmailMessage

subject, from_email, to = 'hello', 'from@example.com', 'to@example.com'
html_content = '<p>This is an <strong>important</strong> message.</p>'

msg = EmailMessage(subject, html_content, from_email, [to])
msg.content_subtype = "html"  # Main content is now text/html
msg.send()
```

### Sending multiple emails

Establishing and closing an SMTP connection (or any other network connection, for that matter) is an expensive process. If you have a lot of emails to send, it makes sense to reuse an SMTP connection, rather than creating and destroying a connection every time you want to send an email.

There are two ways you tell an email backend to reuse a connection.

Firstly, you can use the `send_messages()` method. `send_messages()` takes a list of `EmailMessage` instances (or subclasses), and sends them all using a single connection.

For example, if you have a function called `get_notification_email()` that returns a list of `EmailMessage` objects representing some periodic email you wish to send out, you could send these emails using a single call to `send_messages`:

```python
from flask import Flask
from flask_mailman import Mail

app = Flask(__name__)
mail = Mail(app)

connection = mail.get_connection()   # Use default email connection
messages = get_notification_email()
connection.send_messages(messages)
```

In this example, the call to `send_messages()` opens a connection on the backend, sends the list of messages, and then closes the connection again.

The second approach is to use the `open()` and `close()` methods on the email backend to manually control the connection. `send_messages()` will not manually open or close the connection if it is already open, so if you manually open the connection, you can control when it is closed. For example:

```python
from flask import Flask
from flask_mailman import Mail, EmailMessage

app = Flask(__name__)
mail = Mail(app)

connection = mail.get_connection()

# Manually open the connection
connection.open()

# Construct an email message that uses the connection
email1 = EmailMessage(
    'Hello',
    'Body goes here',
    'from@example.com',
    ['to1@example.com'],
    connection=connection,
)
email1.send() # Send the email

# Construct two more messages
email2 = EmailMessage(
    'Hello',
    'Body goes here',
    'from@example.com',
    ['to2@example.com'],
)
email3 = EmailMessage(
    'Hello',
    'Body goes here',
    'from@example.com',
    ['to3@example.com'],
)

# Send the two emails in a single call -
connection.send_messages([email2, email3])
# The connection was already open so send_messages() doesn't close it.
# We need to manually close the connection.
connection.close()
```

Of course there is always a short writing using `with`:

```python
from flask import Flask
from flask_mailman import Mail, EmailMessage

app = Flask(__name__)
mail = Mail(app)

with mail.get_connection() as conn:
    email1 = EmailMessage(
    'Hello',
    'Body goes here',
    'from@example.com',
    ['to1@example.com'],
    connection=conn,
    )
    email1.send()

    email2 = EmailMessage(
        'Hello',
        'Body goes here',
        'from@example.com',
        ['to2@example.com'],
    )
    email3 = EmailMessage(
        'Hello',
        'Body goes here',
        'from@example.com',
        ['to3@example.com'],
    )
    conn.send_messages([email2, email3])
```

## Attachments

You can use the following two methods to adding attachments:

- `EmailMessage.attach()` creates a new file attachment and adds it to the message. There are two ways to call `attach()`:

    - You can pass it a single argument that is a **MIMEBase** instance. This will be inserted directly into the resulting message.

    - Alternatively, you can pass `attach()` three arguments: **filename**, **content** and **mimetype**. filename is the name of the file attachment as it will appear in the email, content is the data that will be contained inside the attachment and mimetype is the optional MIME type for the attachment. If you omit mimetype, the MIME content type will be guessed from the filename of the attachment.

        For example:

        ```
        message.attach('design.png', img_data, 'image/png')
        ```

        If you specify a mimetype of message/rfc822, it will also accept `flask_mailman.EmailMessage` and `email.message.Message`.

        For a mimetype starting with text/, content is expected to be a string. Binary data will be decoded using UTF-8, and if that fails, the MIME type will be changed to application/octet-stream and the data will be attached unchanged.

        In addition, message/rfc822 attachments will no longer be base64-encoded in violation of RFC 2046#section-5.2.1, which can cause issues with displaying the attachments in Evolution and Thunderbird.

- `EmailMessage.attach_file()` creates a new attachment using a file from your filesystem. Call it with the path of the file to attach and, optionally, the **MIME** type to use for the attachment. If the **MIME** type is omitted, it will be guessed from the filename. You can use it like this:

    ```
    message.attach_file('/images/weather_map.png')
    ```

    For **MIME** types starting with text/, binary data is handled as in `attach()`.

## Preventing header injection

Header injection is a security exploit in which an attacker inserts extra email headers to control the “To:” and “From:” in email messages that your scripts generate.

The Flask-Mailman email methods outlined above all protect against header injection by forbidding newlines in header values. If any `subject`, `from_email` or `recipient_list` contains a newline (in either Unix, Windows or Mac style), the email method (e.g. `send_mail()`) will raise `flask_mailman.BadHeaderError` (a subclass of `ValueError`) and, hence, will not send the email. It’s your responsibility to validate all data before passing it to the email functions.

If a message contains headers at the start of the string, the headers will be printed as the first bit of the email message.

## Sending alternative content types

It can be useful to include multiple versions of the content in an email; the classic example is to send both text and HTML versions of a message. With this library, you can do this using the `EmailMultiAlternatives` class. This subclass of `EmailMessage` has an `attach_alternative()` method for including extra versions of the message body in the email. All the other methods (including the class initialization) are inherited directly from `EmailMessage`.

To send a text and HTML combination, you could write:

```python
from flask_mailman import EmailMultiAlternatives

subject, from_email, to = 'hello', 'from@example.com', 'to@example.com'
text_content = 'This is an important message.'
html_content = '<p>This is an <strong>important</strong> message.</p>'
msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
msg.attach_alternative(html_content, "text/html")
msg.send()
```

## Email backends

The actual sending of an email is handled by the email backend.

The email backend class has the following methods:

- `open()` instantiates a long-lived email-sending connection.
- `close()` closes the current email-sending connection.

`send_messages(email_messages)` sends a list of `EmailMessage` objects. If the connection is not open, this call will implicitly open the connection, and close the connection afterwards. If the connection is already open, it will be left open after mail has been sent.
It can also be used as a context manager, which will automatically call `open()` and `close()` as needed:

```python
from flask import Flask
from flask_mailman import Mail

app = Flask(__name__)
mail = Mail(app)

with mail.get_connection() as connection:
    mail.EmailMessage(
        subject1, body1, from1, [to1],
        connection=connection,
    ).send()
    mail.EmailMessage(
        subject2, body2, from2, [to2],
        connection=connection,
    ).send()
```

### Obtaining an instance of an email backend

The `get_connection()` method of **Mail** instance returns an instance of the email backend that you can use.

```python
Mail.get_connection(backend=None, fail_silently=False, *args, **kwargs)
```
By default, a call to `get_connection()` will return an instance of the email backend specified in MAIL_BACKEND configuration. If you specify the backend argument, an instance of that backend will be instantiated.

The `fail_silently` argument controls how the backend should handle errors. If `fail_silently` is True, exceptions during the email sending process will be silently ignored.

All other arguments are passed directly to the constructor of the email backend.

Flask-Mailman ships with several email sending backends. With the exception of the SMTP backend (which is the default), these backends are only useful during testing and development. If you have special email sending requirements, you can write your own email backend.

### SMTP backend

```python
class backends.smtp.EmailBackend(
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
    **kwargs
)
```
This is the default backend. Email will be sent through a SMTP server.

The value for each argument is retrieved from the matching configuration if the argument is None:

- host: MAIL_HOST
- port: MAIL_PORT
- username: MAIL_USERNAME
- password: MAIL_PASSWORD
- use_tls: MAIL_USE_TLS
- use_ssl: MAIL_USE_SSL
- timeout: MAIL_TIMEOUT
- ssl_keyfile: MAIL_SSL_KEYFILE
- ssl_certfile: MAIL_SSL_CERTFILE

The SMTP backend is the default configuration inherited by Flask-Mailman. If you want to specify it explicitly, put the following in your configurations:

```
MAIL_BACKEND = 'smtp'
```
If unspecified, the default timeout will be the one provided by `socket.getdefaulttimeout()`, which defaults to None (no timeout).

### Console backend

Instead of sending out real emails the console backend just writes the emails that would be sent to the standard output. By default, the console backend writes to stdout. You can use a different stream-like object by providing the stream keyword argument when constructing the connection.

To specify this backend, put the following in your settings:

```
MAIL_BACKEND = 'console'
```
This backend is not intended for use in production – it is provided as a convenience that can be used during development.

### File backend

The file backend writes emails to a file. A new file is created for each new session that is opened on this backend. The directory to which the files are written is either taken from the MAIL_FILE_PATH configuration or from the `file_path` keyword when creating a connection with `Mail.get_connection()`.

To specify this backend, put the following in your configurations:

```
MAIL_BACKEND = 'file'
MAIL_FILE_PATH = '/tmp/app-messages' # change this to a proper location
```
This backend is not intended for use in production – it is provided as a convenience that can be used during development.

Support for `pathlib.Path` was added.

### In-memory backend

The 'locmem' backend stores messages in a special attribute of the **Mail** instance. The `outbox` attribute is created when the first message is sent. It’s a list with an `EmailMessage` instance for each message that would be sent.

To specify this backend, put the following in your configurations:

```
MAIL_BACKEND = 'locmem'
```

This backend is not intended for use in production – it is provided as a convenience that can be used during development and testing.

When `TESTING=True` and `MAIL_BACKEND` is not provided, this backend will be used for testing.

### Dummy backend

As the name suggests the dummy backend does nothing with your messages. To specify this backend, put the following in your configurations:

```
MAIL_BACKEND = 'dummy'
```

This backend is not intended for use in production – it is provided as a convenience that can be used during development.

### Defining a custom email backend

If you need to change how emails are sent you can write your own email backend.
The `MAIL_BACKEND` configuration in your settings file is then the Python import path for your backend class. for example:

```
MAIL_BACKEND = 'flask_mailman.backens.custom'
```

A more direct way is to import your custom backend class, and pass it to `flask_mailman.get_connection` function:

```python
from flask import Flask
from flask_mailman import Mail

from your_custom_backend import CustomBackend

app = Flask(__name__)
mail = Mail(app)

connection = mail.get_connection(backend=CustomBackend)
connection.send_messages(messages)
```

Custom email backends should subclass `BaseEmailBackend` that is located in the `flask_mailman.backends.base` module.
A custom email backend must implement the `send_messages(email_messages)` method.
This method receives a list of `EmailMessage` instances and returns the number of successfully delivered messages.
If your backend has any concept of a persistent session or connection, you should also implement the `open()` and `close()` methods.

Refer to `flask_mailman.backends.smtp.EmailBackend` for a reference implementation.

## Convenient functions

### send_mail()
*send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None, connection=None, html_message=None)*

In most cases, you can send email using `Mail.send_mail()`.

The subject, message, from_email and recipient_list parameters are required.

- **subject**: A string.
- **message**: A string.
- **from_email**: A string. If None, Flask-Mailman will use the value of the MAIL_DEFAULT_SENDER configuration.
- **recipient_list**: A list of strings, each an email address. Each member of `recipient_list` will see the other recipients in the “To:” field of the email message.
- **fail_silently**: A boolean. When it’s False, `send_mail()` will raise an `smtplib.SMTPException` if an error occurs. See the smtplib docs for a list of possible exceptions, all of which are subclasses of `SMTPException`.
- **auth_user**: The optional username to use to authenticate to the SMTP server. If this isn’t provided, Flask-Mailman will use the value of the MAIL_USERNAME configuration.
- **auth_password**: The optional password to use to authenticate to the SMTP server. If this isn’t provided, Flask-Mailman will use the value of the MAIL_PASSWORD configuration.
- **connection**: The optional email backend to use to send the mail. If unspecified, an instance of the default backend will be used. See the documentation on Email backends for more details.
- **html_message**: If `html_message` is provided, the resulting email will be a multipart/alternative email with message as the text/plain content type and html_message as the text/html content type.

The return value will be the number of successfully delivered messages (which can be 0 or 1 since it can only send one message).

### send_mass_mail()

*send_mass_mail(datatuple, fail_silently=False, auth_user=None, auth_password=None, connection=None)*

`Mail.send_mass_mail()` is intended to handle mass emailing.

datatuple is a tuple in which each element is in this format:

```
(subject, message, from_email, recipient_list)
```
`fail_silently`, `auth_user` and `auth_password` have the same functions as in `send_mail()`.

Each separate element of datatuple results in a separate email message. As in `send_mail()`, recipients in the same `recipient_list` will all see the other addresses in the email messages’ “To:” field.

For example, the following code would send two different messages to two different sets of recipients; however, only one connection to the mail server would be opened:

```python
from flask import Flask
from flask_mailman import Mail

app = Flask(__name__)
mail = Mail(app)

message1 = ('Subject here', 'Here is the message', 'from@example.com', ['first@example.com', 'other@example.com'])
message2 = ('Another Subject', 'Here is another message', 'from@example.com', ['second@test.com'])
mail.send_mass_mail((message1, message2), fail_silently=False)
# The return value will be the number of successfully delivered messages.
```

### send_mass_mail() vs. send_mail()

The main difference between `send_mass_mail()` and `send_mail()` is that `send_mail()` opens a connection to the mail server each time it’s executed, while `send_mass_mail()` uses a single connection for all of its messages. This makes `send_mass_mail()` slightly more efficient.

## Differences with Django

The name of configuration keys is different here, but you can easily resolve it.

`mail_admins()` and `mail_managers()` methods were removed, you can write an alternative one in a minute if you need.
