import mimetypes
import os
from flask_mailman.utils import DNS_NAME
from email import charset, message_from_bytes
from email.mime.text import MIMEText
from unittest import mock
from flask_mailman.message import EmailMessage, EmailMultiAlternatives, sanitize_address
from tests import MailmanCustomizedTestCase


class TestMail(MailmanCustomizedTestCase):
    def test_send_mail(self):
        self.mail.send_mail(
            subject="testing",
            message="test",
            from_email=self.MAIL_DEFAULT_SENDER,
            recipient_list=["tester@example.com"],
        )
        self.assertEqual(len(self.mail.outbox), 1)
        sent_msg = self.mail.outbox[0]
        self.assertEqual(sent_msg.from_email, second=self.MAIL_DEFAULT_SENDER)

    def test_send_mail_with_tuple_from_email(self):
        self.mail.send_mail(
            subject="testing",
            message="test",
            from_email=("Name", "support@mysite.com"),
            recipient_list=["tester@example.com"],
        )
        self.assertEqual(len(self.mail.outbox), 1)
        sent_msg = self.mail.outbox[0]
        self.assertEqual(sent_msg.from_email, "Name <support@mysite.com>")

    def test_send_mass_mail(self):
        message1 = (
            'Subject here',
            'Here is the message',
            'from@example.com',
            ['first@example.com', 'other@example.com'],
        )
        message2 = ('Another Subject', 'Here is another message', ('Name', 'from@example.com'), ['second@test.com'])
        self.mail.send_mass_mail((message1, message2), fail_silently=False)
        self.assertEqual(len(self.mail.outbox), 2)
        msg1 = self.mail.outbox[0]
        self.assertEqual(msg1.subject, "Subject here")
        self.assertEqual(msg1.to, ['first@example.com', 'other@example.com'])
        self.assertEqual(msg1.body, "Here is the message")
        self.assertEqual(msg1.from_email, "from@example.com")
        msg2 = self.mail.outbox[1]
        self.assertEqual(msg2.subject, "Another Subject")
        self.assertEqual(msg2.from_email, "Name <from@example.com>")

    @mock.patch("socket.getfqdn", return_value="漢字")
    def test_non_ascii_dns_non_unicode_email(self, mocked_getfqdn):
        delattr(DNS_NAME, "_fqdn")
        email = EmailMessage("subject", "content", "from@example.com", ["to@example.com"])
        email.encoding = "iso-8859-1"
        self.assertIn("@xn--p8s937b>", email.message()["Message-ID"])

    # Following test cases are originally from:
    #   https://github.com/django/django/tree/main/tests/mail/tests.py

    def test_header_omitted_for_no_to_recipients(self):
        message = EmailMessage("Subject", "Content", "from@example.com", cc=["cc@example.com"]).message()
        self.assertNotIn("To", message)

    def test_recipients_with_empty_strings(self):
        """
        Empty strings in various recipient arguments are always stripped
        off the final recipient list.
        """
        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ["to@example.com", ""],
            cc=["cc@example.com", ""],
            bcc=["", "bcc@example.com"],
            reply_to=["", None],
        )
        self.assertEqual(email.recipients(), ["to@example.com", "cc@example.com", "bcc@example.com"])

    def test_cc(self):
        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ["to@example.com"],
            cc=["cc@example.com"],
        )
        message = email.message()
        self.assertEqual(message["Cc"], "cc@example.com")
        self.assertEqual(email.recipients(), ["to@example.com", "cc@example.com"])

        # Test multiple CC with multiple To
        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ["to@example.com", "other@example.com"],
            cc=["cc@example.com", "cc.other@example.com"],
        )
        message = email.message()
        self.assertEqual(message["Cc"], "cc@example.com, cc.other@example.com")
        self.assertEqual(
            email.recipients(),
            [
                "to@example.com",
                "other@example.com",
                "cc@example.com",
                "cc.other@example.com",
            ],
        )

        # Testing with Bcc
        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ["to@example.com", "other@example.com"],
            cc=["cc@example.com", "cc.other@example.com"],
            bcc=["bcc@example.com"],
        )
        message = email.message()
        self.assertEqual(message["Cc"], "cc@example.com, cc.other@example.com")
        self.assertEqual(
            email.recipients(),
            [
                "to@example.com",
                "other@example.com",
                "cc@example.com",
                "cc.other@example.com",
                "bcc@example.com",
            ],
        )

    def test_cc_headers(self):
        message = EmailMessage(
            "Subject",
            "Content",
            "bounce@example.com",
            ["to@example.com"],
            cc=["foo@example.com"],
            headers={"Cc": "override@example.com"},
        ).message()
        self.assertEqual(message["Cc"], "override@example.com")

    def test_cc_in_headers_only(self):
        message = EmailMessage(
            "Subject",
            "Content",
            "bounce@example.com",
            ["to@example.com"],
            headers={"Cc": "foo@example.com"},
        ).message()
        self.assertEqual(message["Cc"], "foo@example.com")

    def test_reply_to(self):
        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ["to@example.com"],
            reply_to=["reply_to@example.com"],
        )
        message = email.message()
        self.assertEqual(message["Reply-To"], "reply_to@example.com")

        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ["to@example.com"],
            reply_to=["reply_to1@example.com", "reply_to2@example.com"],
        )
        message = email.message()
        self.assertEqual(message["Reply-To"], "reply_to1@example.com, reply_to2@example.com")

    def test_recipients_as_tuple(self):
        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ("to@example.com", "other@example.com"),
            cc=("cc@example.com", "cc.other@example.com"),
            bcc=("bcc@example.com",),
        )
        message = email.message()
        self.assertEqual(message["Cc"], "cc@example.com, cc.other@example.com")
        self.assertEqual(
            email.recipients(),
            [
                "to@example.com",
                "other@example.com",
                "cc@example.com",
                "cc.other@example.com",
                "bcc@example.com",
            ],
        )

    def test_recipients_as_string(self):
        with self.assertRaises(TypeError, msg='"to" argument must be a list or tuple'):
            EmailMessage(to="foo@example.com")
        with self.assertRaises(TypeError, msg='"cc" argument must be a list or tuple'):
            EmailMessage(cc="foo@example.com")
        with self.assertRaises(TypeError, msg='"bcc" argument must be a list or tuple'):
            EmailMessage(bcc="foo@example.com")
        with self.assertRaises(TypeError, msg='"reply_to" argument must be a list or tuple'):
            EmailMessage(reply_to="reply_to@example.com")

    def test_space_continuation(self):
        """
        Test for space continuation character in long (ASCII) subject headers
        """
        email = EmailMessage(
            "Long subject lines that get wrapped should contain a space continuation "
            "character to get expected behavior in Outlook and Thunderbird",
            "Content",
            "from@example.com",
            ["to@example.com"],
        )
        message = email.message()
        self.assertEqual(
            message["Subject"].encode(),
            b"Long subject lines that get wrapped should contain a space continuation\n"
            b" character to get expected behavior in Outlook and Thunderbird",
        )

    def test_message_header_overrides(self):
        """
        Specifying dates or message-ids in the extra headers overrides the
        default values
        """
        headers = {"date": "Fri, 09 Nov 2001 01:08:47 -0000", "Message-ID": "foo"}
        email = EmailMessage(
            "subject",
            "content",
            "from@example.com",
            ["to@example.com"],
            headers=headers,
        )

        self.assertMessageHasHeaders(
            email.message(),
            {
                ("Content-Transfer-Encoding", "7bit"),
                ("Content-Type", 'text/plain; charset="utf-8"'),
                ("From", "from@example.com"),
                ("MIME-Version", "1.0"),
                ("Message-ID", "foo"),
                ("Subject", "subject"),
                ("To", "to@example.com"),
                ("date", "Fri, 09 Nov 2001 01:08:47 -0000"),
            },
        )

    def test_from_header(self):
        """
        Make sure we can manually set the From header
        """
        email = EmailMessage(
            "Subject",
            "Content",
            "bounce@example.com",
            ["to@example.com"],
            headers={"From": "from@example.com"},
        )
        message = email.message()
        self.assertEqual(message["From"], "from@example.com")

    def test_to_header(self):
        """
        Make sure we can manually set the To header (#17444)
        """
        email = EmailMessage(
            "Subject",
            "Content",
            "bounce@example.com",
            ["list-subscriber@example.com", "list-subscriber2@example.com"],
            headers={"To": "mailing-list@example.com"},
        )
        message = email.message()
        self.assertEqual(message["To"], "mailing-list@example.com")
        self.assertEqual(email.to, ["list-subscriber@example.com", "list-subscriber2@example.com"])

        # If we don't set the To header manually, it should default to the `to`
        # argument to the constructor.
        email = EmailMessage(
            "Subject",
            "Content",
            "bounce@example.com",
            ["list-subscriber@example.com", "list-subscriber2@example.com"],
        )
        message = email.message()
        self.assertEqual(message["To"], "list-subscriber@example.com, list-subscriber2@example.com")
        self.assertEqual(email.to, ["list-subscriber@example.com", "list-subscriber2@example.com"])

    def test_to_in_headers_only(self):
        message = EmailMessage(
            "Subject",
            "Content",
            "bounce@example.com",
            headers={"To": "to@example.com"},
        ).message()
        self.assertEqual(message["To"], "to@example.com")

    def test_reply_to_header(self):
        """
        Specifying 'Reply-To' in headers should override reply_to.
        """
        email = EmailMessage(
            "Subject",
            "Content",
            "bounce@example.com",
            ["to@example.com"],
            reply_to=["foo@example.com"],
            headers={"Reply-To": "override@example.com"},
        )
        message = email.message()
        self.assertEqual(message["Reply-To"], "override@example.com")

    def test_reply_to_in_headers_only(self):
        message = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ["to@example.com"],
            headers={"Reply-To": "reply_to@example.com"},
        ).message()
        self.assertEqual(message["Reply-To"], "reply_to@example.com")

    def test_multiple_message_call(self):
        """
        Regression for #13259 - Make sure that headers are not changed when
        calling EmailMessage.message()
        """
        email = EmailMessage(
            "Subject",
            "Content",
            "bounce@example.com",
            ["to@example.com"],
            headers={"From": "from@example.com"},
        )
        message = email.message()
        self.assertEqual(message["From"], "from@example.com")
        message = email.message()
        self.assertEqual(message["From"], "from@example.com")

    def test_unicode_address_header(self):
        """
        Regression for #11144 - When a to/from/cc header contains Unicode,
        make sure the email addresses are parsed correctly (especially with
        regards to commas)
        """
        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ['"Firstname Sürname" <to@example.com>', "other@example.com"],
        )
        self.assertEqual(
            email.message()["To"],
            "=?utf-8?q?Firstname_S=C3=BCrname?= <to@example.com>, other@example.com",
        )
        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ['"Sürname, Firstname" <to@example.com>', "other@example.com"],
        )
        self.assertEqual(
            email.message()["To"],
            "=?utf-8?q?S=C3=BCrname=2C_Firstname?= <to@example.com>, other@example.com",
        )

    def test_unicode_headers(self):
        email = EmailMessage(
            "Gżegżółka",
            "Content",
            "from@example.com",
            ["to@example.com"],
            headers={
                "Sender": '"Firstname Sürname" <sender@example.com>',
                "Comments": "My Sürname is non-ASCII",
            },
        )
        message = email.message()
        self.assertEqual(message["Subject"], "=?utf-8?b?R8W8ZWfFvMOzxYJrYQ==?=")
        self.assertEqual(message["Sender"], "=?utf-8?q?Firstname_S=C3=BCrname?= <sender@example.com>")
        self.assertEqual(message["Comments"], "=?utf-8?q?My_S=C3=BCrname_is_non-ASCII?=")

    def test_safe_mime_multipart(self):
        """
        Make sure headers can be set with a different encoding than utf-8 in
        SafeMIMEMultipart as well
        """
        headers = {"Date": "Fri, 09 Nov 2001 01:08:47 -0000", "Message-ID": "foo"}
        from_email, to = "from@example.com", '"Sürname, Firstname" <to@example.com>'
        text_content = "This is an important message."
        html_content = "<p>This is an <strong>important</strong> message.</p>"
        msg = EmailMultiAlternatives(
            "Message from Firstname Sürname",
            text_content,
            from_email,
            [to],
            headers=headers,
        )
        msg.attach_alternative(html_content, "text/html")
        msg.encoding = "iso-8859-1"
        self.assertEqual(
            msg.message()["To"],
            "=?iso-8859-1?q?S=FCrname=2C_Firstname?= <to@example.com>",
        )
        self.assertEqual(
            msg.message()["Subject"],
            "=?iso-8859-1?q?Message_from_Firstname_S=FCrname?=",
        )

    def test_safe_mime_multipart_with_attachments(self):
        """
        EmailMultiAlternatives includes alternatives if the body is empty and
        it has attachments.
        """
        msg = EmailMultiAlternatives(body="")
        html_content = "<p>This is <strong>html</strong></p>"
        msg.attach_alternative(html_content, "text/html")
        msg.attach("example.txt", "Text file content", "text/plain")
        self.assertIn(html_content, msg.message().as_string())

    def test_none_body(self):
        msg = EmailMessage("subject", None, "from@example.com", ["to@example.com"])
        self.assertEqual(msg.body, "")
        self.assertEqual(msg.message().get_payload(), "")

    def test_encoding(self):
        """
        Regression for #12791 - Encode body correctly with other encodings
        than utf-8
        """
        email = EmailMessage(
            "Subject",
            "Firstname Sürname is a great guy.",
            "from@example.com",
            ["other@example.com"],
        )
        email.encoding = "iso-8859-1"
        message = email.message()
        self.assertMessageHasHeaders(
            message,
            {
                ("MIME-Version", "1.0"),
                ("Content-Type", 'text/plain; charset="iso-8859-1"'),
                ("Content-Transfer-Encoding", "quoted-printable"),
                ("Subject", "Subject"),
                ("From", "from@example.com"),
                ("To", "other@example.com"),
            },
        )
        self.assertEqual(message.get_payload(), "Firstname S=FCrname is a great guy.")

        # MIME attachments works correctly with other encodings than utf-8.
        text_content = "Firstname Sürname is a great guy."
        html_content = "<p>Firstname Sürname is a <strong>great</strong> guy.</p>"
        msg = EmailMultiAlternatives("Subject", text_content, "from@example.com", ["to@example.com"])
        msg.encoding = "iso-8859-1"
        msg.attach_alternative(html_content, "text/html")
        payload0 = msg.message().get_payload(0)
        self.assertMessageHasHeaders(
            payload0,
            {
                ("MIME-Version", "1.0"),
                ("Content-Type", 'text/plain; charset="iso-8859-1"'),
                ("Content-Transfer-Encoding", "quoted-printable"),
            },
        )
        self.assertTrue(payload0.as_bytes().endswith(b"\n\nFirstname S=FCrname is a great guy."))
        payload1 = msg.message().get_payload(1)
        self.assertMessageHasHeaders(
            payload1,
            {
                ("MIME-Version", "1.0"),
                ("Content-Type", 'text/html; charset="iso-8859-1"'),
                ("Content-Transfer-Encoding", "quoted-printable"),
            },
        )
        self.assertTrue(
            payload1.as_bytes().endswith(b"\n\n<p>Firstname S=FCrname is a <strong>great</strong> guy.</p>")
        )

    def test_attachments(self):
        headers = {"Date": "Fri, 09 Nov 2001 01:08:47 -0000", "Message-ID": "foo"}
        subject, from_email, to = "hello", "from@example.com", "to@example.com"
        text_content = "This is an important message."
        html_content = "<p>This is an <strong>important</strong> message.</p>"
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to], headers=headers)
        msg.attach_alternative(html_content, "text/html")
        msg.attach("an attachment.pdf", b"%PDF-1.4.%...", mimetype="application/pdf")
        msg_bytes = msg.message().as_bytes()
        message = message_from_bytes(msg_bytes)
        self.assertTrue(message.is_multipart())
        self.assertEqual(message.get_content_type(), "multipart/mixed")
        self.assertEqual(message.get_default_type(), "text/plain")
        payload = message.get_payload()
        self.assertEqual(payload[0].get_content_type(), "multipart/alternative")
        self.assertEqual(payload[1].get_content_type(), "application/pdf")

    def test_attachments_two_tuple(self):
        msg = EmailMessage(attachments=[("filename1", "content1")])
        filename, content, mimetype = self.get_decoded_attachments(msg)[0]
        self.assertEqual(filename, "filename1")
        self.assertEqual(content, b"content1")
        self.assertEqual(mimetype, "application/octet-stream")

    def test_attachments_MIMEText(self):
        txt = MIMEText("content1")
        msg = EmailMessage(attachments=[txt])
        payload = msg.message().get_payload()
        self.assertEqual(payload[0], txt)

    def test_non_ascii_attachment_filename(self):
        headers = {"Date": "Fri, 09 Nov 2001 01:08:47 -0000", "Message-ID": "foo"}
        subject, from_email, to = "hello", "from@example.com", "to@example.com"
        content = "This is the message."
        msg = EmailMessage(subject, content, from_email, [to], headers=headers)
        # Unicode in file name
        msg.attach("une pièce jointe.pdf", b"%PDF-1.4.%...", mimetype="application/pdf")
        msg_bytes = msg.message().as_bytes()
        message = message_from_bytes(msg_bytes)
        payload = message.get_payload()
        self.assertEqual(payload[1].get_filename(), "une pièce jointe.pdf")

    def test_attach_file(self):
        """
        Test attaching a file against different mimetypes and make sure that
        a file will be attached and sent properly even if an invalid mimetype
        is specified.
        """
        files = (
            # filename, actual mimetype
            ("file.txt", "text/plain"),
            ("file.png", "image/png"),
            ("file_txt", None),
            ("file_png", None),
            ("file_txt.png", "image/png"),
            ("file_png.txt", "text/plain"),
            ("file.eml", "message/rfc822"),
        )
        test_mimetypes = ["text/plain", "image/png", None]

        for basename, real_mimetype in files:
            for mimetype in test_mimetypes:
                email = EmailMessage("subject", "body", "from@example.com", ["to@example.com"])
                self.assertEqual(mimetypes.guess_type(basename)[0], real_mimetype)
                self.assertEqual(email.attachments, [])
                file_path = os.path.join(os.path.dirname(__file__), "attachments", basename)
                email.attach_file(file_path, mimetype=mimetype)
                self.assertEqual(len(email.attachments), 1)
                self.assertIn(basename, email.attachments[0])
                msgs_sent_num = email.send()
                self.assertEqual(msgs_sent_num, 1)

    def test_attach_text_as_bytes(self):
        msg = EmailMessage("subject", "body", "from@example.com", ["to@example.com"])
        msg.attach("file.txt", b"file content")
        sent_num = msg.send()
        self.assertEqual(sent_num, 1)
        filename, content, mimetype = self.get_decoded_attachments(msg)[0]
        self.assertEqual(filename, "file.txt")
        self.assertEqual(content, b"file content")
        self.assertEqual(mimetype, "text/plain")

    def test_attach_utf8_text_as_bytes(self):
        """
        Non-ASCII characters encoded as valid UTF-8 are correctly transported
        and decoded.
        """
        msg = EmailMessage("subject", "body", "from@example.com", ["to@example.com"])
        msg.attach("file.txt", b"\xc3\xa4")  # UTF-8 encoded a umlaut.
        filename, content, mimetype = self.get_decoded_attachments(msg)[0]
        self.assertEqual(filename, "file.txt")
        self.assertEqual(content, b"\xc3\xa4")
        self.assertEqual(mimetype, "text/plain")

    def test_attach_non_utf8_text_as_bytes(self):
        """
        Binary data that can't be decoded as UTF-8 overrides the MIME type
        instead of decoding the data.
        """
        msg = EmailMessage("subject", "body", "from@example.com", ["to@example.com"])
        msg.attach("file.txt", b"\xff")  # Invalid UTF-8.
        filename, content, mimetype = self.get_decoded_attachments(msg)[0]
        self.assertEqual(filename, "file.txt")
        # Content should be passed through unmodified.
        self.assertEqual(content, b"\xff")
        self.assertEqual(mimetype, "application/octet-stream")

    def test_attach_mimetext_content_mimetype(self):
        email_msg = EmailMessage()
        txt = MIMEText("content")
        msg = "content and mimetype must not be given when a MIMEBase instance " "is provided."
        with self.assertRaises(ValueError, msg=msg):
            email_msg.attach(txt, content="content")
        with self.assertRaises(ValueError, msg=msg):
            email_msg.attach(txt, mimetype="text/plain")

    def test_attach_content_none(self):
        email_msg = EmailMessage()
        msg = "content must be provided."
        with self.assertRaises(ValueError, msg=msg):
            email_msg.attach("file.txt", mimetype="application/pdf")

    def test_dont_mangle_from_in_body(self):
        """
        Make sure that EmailMessage doesn't mangle
        'From ' in message body.
        """
        email = EmailMessage(
            "Subject",
            "From the future",
            "bounce@example.com",
            ["to@example.com"],
            headers={"From": "from@example.com"},
        )
        self.assertNotIn(b">From the future", email.message().as_bytes())

    def test_dont_base64_encode(self):
        """Shouldn't use Base64 encoding at all"""
        msg = EmailMessage(
            "Subject",
            "UTF-8 encoded body",
            "bounce@example.com",
            ["to@example.com"],
            headers={"From": "from@example.com"},
        )
        self.assertIn(b"Content-Transfer-Encoding: 7bit", msg.message().as_bytes())

        # Shouldn't use quoted printable, should detect it can represent
        # content with 7 bit data.
        msg = EmailMessage(
            "Subject",
            "Body with only ASCII characters.",
            "bounce@example.com",
            ["to@example.com"],
            headers={"From": "from@example.com"},
        )
        s = msg.message().as_bytes()
        self.assertIn(b"Content-Transfer-Encoding: 7bit", s)

        # Shouldn't use quoted printable, should detect it can represent
        # content with 8 bit data.
        msg = EmailMessage(
            "Subject",
            "Body with latin characters: àáä.",
            "bounce@example.com",
            ["to@example.com"],
            headers={"From": "from@example.com"},
        )
        s = msg.message().as_bytes()
        self.assertIn(b"Content-Transfer-Encoding: 8bit", s)
        s = msg.message().as_string()
        self.assertIn("Content-Transfer-Encoding: 8bit", s)

        msg = EmailMessage(
            "Subject",
            "Body with non latin characters: А Б В Г Д Е Ж Ѕ З И І К Л М Н О П.",
            "bounce@example.com",
            ["to@example.com"],
            headers={"From": "from@example.com"},
        )
        s = msg.message().as_bytes()
        self.assertIn(b"Content-Transfer-Encoding: 8bit", s)
        s = msg.message().as_string()
        self.assertIn("Content-Transfer-Encoding: 8bit", s)

    def test_dont_base64_encode_message_rfc822(self):
        """Shouldn't use base64 encoding for a child EmailMessage attachment."""
        # Create a child message first
        child_msg = EmailMessage(
            "Child Subject",
            "Some body of child message",
            "bounce@example.com",
            ["to@example.com"],
            headers={"From": "from@example.com"},
        )
        child_s = child_msg.message().as_string()

        # Now create a parent
        parent_msg = EmailMessage(
            "Parent Subject",
            "Some parent body",
            "bounce@example.com",
            ["to@example.com"],
            headers={"From": "from@example.com"},
        )

        # Attach to parent as a string
        parent_msg.attach(content=child_s, mimetype="message/rfc822")
        parent_s = parent_msg.message().as_string()

        # The child message header is not base64 encoded
        self.assertIn("Child Subject", parent_s)

        # Feature test: try attaching email.Message object directly to the mail.
        parent_msg = EmailMessage(
            "Parent Subject",
            "Some parent body",
            "bounce@example.com",
            ["to@example.com"],
            headers={"From": "from@example.com"},
        )
        parent_msg.attach(content=child_msg.message(), mimetype="message/rfc822")
        parent_s = parent_msg.message().as_string()

        # The child message header is not base64 encoded
        self.assertIn("Child Subject", parent_s)

        # Feature test: try attaching EmailMessage object directly to the mail.
        parent_msg = EmailMessage(
            "Parent Subject",
            "Some parent body",
            "bounce@example.com",
            ["to@example.com"],
            headers={"From": "from@example.com"},
        )
        parent_msg.attach(content=child_msg, mimetype="message/rfc822")
        parent_s = parent_msg.message().as_string()

        # The child message header is not base64 encoded
        self.assertIn("Child Subject", parent_s)

    def test_custom_utf8_encoding(self):
        """A UTF-8 charset with a custom body encoding is respected."""
        body = "Body with latin characters: àáä."
        msg = EmailMessage("Subject", body, "bounce@example.com", ["to@example.com"])
        encoding = charset.Charset("utf-8")
        encoding.body_encoding = charset.QP
        msg.encoding = encoding
        message = msg.message()
        self.assertMessageHasHeaders(
            message,
            {
                ("MIME-Version", "1.0"),
                ("Content-Type", 'text/plain; charset="utf-8"'),
                ("Content-Transfer-Encoding", "quoted-printable"),
            },
        )
        self.assertEqual(message.get_payload(), encoding.body_encode(body))

    def test_sanitize_address(self):
        """Email addresses are properly sanitized."""
        for email_address, encoding, expected_result in (
            # ASCII addresses.
            ("to@example.com", "ascii", "to@example.com"),
            ("to@example.com", "utf-8", "to@example.com"),
            (("A name", "to@example.com"), "ascii", "A name <to@example.com>"),
            (
                ("A name", "to@example.com"),
                "utf-8",
                "A name <to@example.com>",
            ),
            ("localpartonly", "ascii", "localpartonly"),
            # ASCII addresses with display names.
            ("A name <to@example.com>", "ascii", "A name <to@example.com>"),
            ("A name <to@example.com>", "utf-8", "A name <to@example.com>"),
            ('"A name" <to@example.com>', "ascii", "A name <to@example.com>"),
            ('"A name" <to@example.com>', "utf-8", "A name <to@example.com>"),
            # Unicode addresses (supported per RFC-6532).
            ("tó@example.com", "utf-8", "=?utf-8?b?dMOz?=@example.com"),
            ("to@éxample.com", "utf-8", "to@xn--xample-9ua.com"),
            (
                ("Tó Example", "tó@example.com"),
                "utf-8",
                "=?utf-8?q?T=C3=B3_Example?= <=?utf-8?b?dMOz?=@example.com>",
            ),
            # Unicode addresses with display names.
            (
                "Tó Example <tó@example.com>",
                "utf-8",
                "=?utf-8?q?T=C3=B3_Example?= <=?utf-8?b?dMOz?=@example.com>",
            ),
            (
                "To Example <to@éxample.com>",
                "ascii",
                "To Example <to@xn--xample-9ua.com>",
            ),
            (
                "To Example <to@éxample.com>",
                "utf-8",
                "To Example <to@xn--xample-9ua.com>",
            ),
            # Addresses with two @ signs.
            ('"to@other.com"@example.com', "utf-8", r'"to@other.com"@example.com'),
            (
                '"to@other.com" <to@example.com>',
                "utf-8",
                '"to@other.com" <to@example.com>',
            ),
            (
                ("To Example", "to@other.com@example.com"),
                "utf-8",
                'To Example <"to@other.com"@example.com>',
            ),
            # Addresses with long unicode display names.
            (
                "Tó Example very long" * 4 + " <to@example.com>",
                "utf-8",
                "=?utf-8?q?T=C3=B3_Example_very_longT=C3=B3_Example_very_longT"
                "=C3=B3_Example_?=\n"
                " =?utf-8?q?very_longT=C3=B3_Example_very_long?= "
                "<to@example.com>",
            ),
            (
                ("Tó Example very long" * 4, "to@example.com"),
                "utf-8",
                "=?utf-8?q?T=C3=B3_Example_very_longT=C3=B3_Example_very_longT"
                "=C3=B3_Example_?=\n"
                " =?utf-8?q?very_longT=C3=B3_Example_very_long?= "
                "<to@example.com>",
            ),
            # Address with long display name and unicode domain.
            (
                ("To Example very long" * 4, "to@exampl€.com"),
                "utf-8",
                "To Example very longTo Example very longTo Example very longT"
                "o Example very\n"
                " long <to@xn--exampl-nc1c.com>",
            ),
        ):
            with self.subTest(email_address=email_address, encoding=encoding):
                self.assertEqual(sanitize_address(email_address, encoding), expected_result)

    def test_sanitize_address_invalid(self):
        for email_address in (
            # Invalid address with two @ signs.
            "to@other.com@example.com",
            # Invalid address without the quotes.
            "to@other.com <to@example.com>",
            # Other invalid addresses.
            "@",
            "to@",
            "@example.com",
            ("", ""),
        ):
            with self.subTest(email_address=email_address):
                with self.assertRaises(ValueError, msg="Invalid address"):
                    sanitize_address(email_address, encoding="utf-8")

    def test_sanitize_address_header_injection(self):
        msg = "Invalid address; address parts cannot contain newlines."
        tests = [
            "Name\nInjection <to@example.com>",
            ("Name\nInjection", "to@xample.com"),
            "Name <to\ninjection@example.com>",
            ("Name", "to\ninjection@example.com"),
        ]
        for email_address in tests:
            with self.subTest(email_address=email_address):
                with self.assertRaises(ValueError, msg=msg):
                    sanitize_address(email_address, encoding="utf-8")

    def test_email_multi_alternatives_content_mimetype_none(self):
        email_msg = EmailMultiAlternatives()
        msg = "Both content and mimetype must be provided."
        with self.assertRaises(ValueError, msg=msg):
            email_msg.attach_alternative(None, "text/html")
        with self.assertRaises(ValueError, msg=msg):
            email_msg.attach_alternative("<p>content</p>", None)

    def test_send_unicode(self):
        email = EmailMessage("Chère maman", "Je t'aime très fort", "from@example.com", ["to@example.com"])
        num_sent = email.send()
        self.assertEqual(num_sent, 1)
        sent_msg = self.get_message()
        self.assertEqual(sent_msg['subject'], "=?utf-8?q?Ch=C3=A8re_maman?=")
        self.assertEqual(sent_msg.get_payload(decode=True).decode(), "Je t'aime très fort")

    def test_send_long_lines(self):
        """
        Email line length is limited to 998 chars by the RFC 5322 Section
        2.1.1.
        Message body containing longer lines are converted to Quoted-Printable
        to avoid having to insert newlines, which could be hairy to do properly.
        """
        # Unencoded body length is < 998 (840) but > 998 when utf-8 encoded.
        email = EmailMessage("Subject", "В южных морях " * 60, "from@example.com", ["to@example.com"])
        email.send()
        message = self.get_message()
        self.assertMessageHasHeaders(
            message,
            {
                ("MIME-Version", "1.0"),
                ("Content-Type", 'text/plain; charset="utf-8"'),
                ("Content-Transfer-Encoding", "quoted-printable"),
            },
        )

    def test_send_verbose_name(self):
        email = EmailMessage(
            "Subject",
            "Content",
            '"Firstname Sürname" <from@example.com>',
            ["to@example.com"],
        )
        email.send()
        message = self.get_message()
        self.assertEqual(message["subject"], "Subject")
        self.assertEqual(message.get_payload(), "Content")
        self.assertEqual(message["from"], "=?utf-8?q?Firstname_S=C3=BCrname?= <from@example.com>")

    def test_plaintext_send_mail(self):
        """
        Test send_mail without the html_message
        regression test for adding html_message parameter to send_mail()
        """
        self.mail.send_mail("Subject", "Content", "sender@example.com", ["nobody@example.com"])
        message = self.get_message()

        self.assertEqual(message.get("subject"), "Subject")
        self.assertEqual(message.get_all("to"), ["nobody@example.com"])
        self.assertFalse(message.is_multipart())
        self.assertEqual(message.get_payload(), "Content")
        self.assertEqual(message.get_content_type(), "text/plain")

    def test_html_send_mail(self):
        """Test html_message argument to send_mail"""
        self.mail.send_mail(
            "Subject",
            "Content",
            "sender@example.com",
            ["nobody@example.com"],
            html_message="HTML Content",
        )
        message = self.get_message()

        self.assertEqual(message.get("subject"), "Subject")
        self.assertEqual(message.get_all("to"), ["nobody@example.com"])
        self.assertTrue(message.is_multipart())
        self.assertEqual(len(message.get_payload()), 2)
        self.assertEqual(message.get_payload(0).get_payload(), "Content")
        self.assertEqual(message.get_payload(0).get_content_type(), "text/plain")
        self.assertEqual(message.get_payload(1).get_payload(), "HTML Content")
        self.assertEqual(message.get_payload(1).get_content_type(), "text/html")

    def test_message_cc_header(self):
        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ["to@example.com"],
            cc=["cc@example.com"],
        )
        self.mail.get_connection().send_messages([email])
        message = self.get_message()
        self.assertMessageHasHeaders(
            message,
            {
                ("MIME-Version", "1.0"),
                ("Content-Type", 'text/plain; charset="utf-8"'),
                ("Content-Transfer-Encoding", "7bit"),
                ("Subject", "Subject"),
                ("From", "from@example.com"),
                ("To", "to@example.com"),
                ("Cc", "cc@example.com"),
            },
        )
        self.assertIn("\nDate: ", message.as_string())

    def test_idn_send(self):
        self.assertTrue(self.mail.send_mail("Subject", "Content", "from@öäü.com", ["to@öäü.com"]))
        message = self.get_message()
        self.assertEqual(message.get("subject"), "Subject")
        self.assertEqual(message.get("from"), "from@xn--4ca9at.com")
        self.assertEqual(message.get("to"), "to@xn--4ca9at.com")

        self.flush_mailbox()

        m = EmailMessage("Subject", "Content", "from@öäü.com", ["to@öäü.com"], cc=["cc@öäü.com"])
        m.send()
        message = self.get_message()
        self.assertEqual(message.get("subject"), "Subject")
        self.assertEqual(message.get("from"), "from@xn--4ca9at.com")
        self.assertEqual(message.get("to"), "to@xn--4ca9at.com")
        self.assertEqual(message.get("cc"), "cc@xn--4ca9at.com")

    def test_recipient_without_domain(self):
        """
        Regression test for #15042
        """
        self.assertTrue(self.mail.send_mail("Subject", "Content", "tester", ["little bird"]))
        message = self.get_message()
        self.assertEqual(message.get("subject"), "Subject")
        self.assertEqual(message.get("from"), "tester")
        self.assertEqual(message.get("to"), "little bird")
