import email
import re
import time
from email.header import Header

from speaklater import make_lazy_string

from flask_mailman import Message
from flask_mailman.message import sanitize_address, BadHeaderError, forbid_multi_line_headers
from tests import TestCase


class TestMessage(TestCase):

    def test_initialize(self):
        msg = Message(subject="subject",
                      recipients=["to@example.com"])
        self.assertEqual(msg.from_email, self.app.extensions['mailman'].default_sender)
        self.assertEqual(msg.to, ["to@example.com"])

    def test_recipients_properly_initialized(self):
        msg = Message(subject="subject")
        self.assertEqual(msg.to, [])
        msg2 = Message(subject="subject")
        msg2.add_recipient("somebody@here.com")
        self.assertEqual(len(msg2.to), 1)

    def test_esmtp_options_properly_initialized(self):
        msg = Message(subject="subject")
        self.assertEqual(msg.mail_options, [])
        self.assertEqual(msg.rcpt_options, [])

        msg = Message(subject="subject", mail_options=['BODY=8BITMIME'])
        self.assertEqual(msg.mail_options, ['BODY=8BITMIME'])

        msg2 = Message(subject="subject", rcpt_options=['NOTIFY=SUCCESS'])
        self.assertEqual(msg2.rcpt_options, ['NOTIFY=SUCCESS'])

    def test_sendto_properly_set(self):
        msg = Message(subject="subject", recipients=["somebody@here.com"],
                      cc=["cc@example.com"], bcc=["bcc@example.com"])
        self.assertEqual(len(msg.recipients()), 3)
        msg.add_recipient("cc@example.com")
        self.assertEqual(len(set(msg.recipients())), 3)

    def test_add_recipient(self):
        msg = Message("testing")
        msg.add_recipient("to@example.com")
        self.assertEqual(msg.to, ["to@example.com"])

    def test_sender_as_tuple(self):
        msg = Message(subject="testing",
                      sender=("tester", "tester@example.com"))
        self.assertEqual('tester <tester@example.com>', msg.from_email)

    def test_default_sender_as_tuple(self):
        self.app.extensions['mailman'].default_sender = ('tester', 'tester@example.com')
        msg = Message(subject="testing")
        self.assertEqual('tester <tester@example.com>', msg.from_email)

    def test_reply_to(self):
        msg = Message(subject="testing",
                      recipients=["to@example.com"],
                      sender="spammer <spammer@example.com>",
                      reply_to="somebody <somebody@example.com>",
                      body="testing")
        response = msg.message().as_string()

        h = Header(
            "Reply-To: %s" % forbid_multi_line_headers('reply-to', 'somebody <somebody@example.com>', 'utf-8')[1])
        self.assertIn(h.encode(), str(response))

    def test_send_without_sender(self):
        self.app.extensions['mailman'].default_sender = None
        msg = Message(subject="-testing", recipients=["to@example.com"], body="testing")
        self.assertEqual(1, self.mail.send(msg))

    def test_send_without_recipients(self):
        msg = Message(subject="testing",
                      recipients=[],
                      body="testing")
        self.assertEqual(False, self.mail.send(msg))

    def test_bcc(self):
        msg = Message(sender="from@example.com",
                      subject="testing",
                      recipients=["to@example.com"],
                      body="testing",
                      bcc=["tosomeoneelse@example.com"])
        response = msg.message().as_string()
        self.assertNotIn("tosomeoneelse@example.com", str(response))

    def test_cc(self):
        msg = Message(sender="from@example.com",
                      subject="testing",
                      recipients=["to@example.com"],
                      body="testing",
                      cc=["tosomeoneelse@example.com"])
        response = msg.message().as_string()
        self.assertIn("Cc: tosomeoneelse@example.com", str(response))

    def test_attach(self):
        msg = Message(subject="testing",
                      recipients=["to@example.com"],
                      body="testing")
        msg.attach(content="this is a test",
                   mimetype="text/plain")
        a = msg.attachments[0]
        self.assertIsNone(a[0])
        self.assertEqual(a[1], "this is a test")
        self.assertEqual(a[2], "text/plain")
        # self.assertIsNone(a.filename)
        # self.assertEqual(a.disposition, 'attachment')
        # self.assertEqual(a.content_type, "text/plain")
        # self.assertEqual(a.data, b"this is a test")

    def test_bad_header_subject(self):
        msg = Message(subject="testing\r\n",
                      sender="from@example.com",
                      body="testing",
                      recipients=["to@example.com"])
        self.assertRaises(BadHeaderError, self.mail.send, msg)

    def test_multiline_subject(self):
        msg = Message(subject="testing\r\n testing\r\n testing \r\n \ttesting",
                      sender="from@example.com",
                      body="testing",
                      recipients=["to@example.com"])
        self.assertRaises(BadHeaderError, self.mail.send, msg)
        # self.mail.send(msg)
        # response = msg.message().as_string()
        # self.assertIn("From: from@example.com", str(response))
        # self.assertIn("testing\r\n testing\r\n testing \r\n \ttesting", str(response))

    def test_bad_multiline_subject(self):
        msg = Message(subject="testing\r\n testing\r\n ",
                      sender="from@example.com",
                      body="testing",
                      recipients=["to@example.com"])
        self.assertRaises(BadHeaderError, self.mail.send, msg)

        msg = Message(subject="testing\r\n testing\r\n\t",
                      sender="from@example.com",
                      body="testing",
                      recipients=["to@example.com"])
        self.assertRaises(BadHeaderError, self.mail.send, msg)

        msg = Message(subject="testing\r\n testing\r\n\n",
                      sender="from@example.com",
                      body="testing",
                      recipients=["to@example.com"])
        self.assertRaises(BadHeaderError, self.mail.send, msg)

    def test_bad_header_sender(self):
        msg = Message(subject="testing",
                      sender="from@example.com\r\n",
                      recipients=["to@example.com"],
                      body="testing")

        self.assertRaises(BadHeaderError, self.mail.send, msg)
        # self.assertIn('From: from@example.com', msg.message().as_string())

    def test_bad_header_reply_to(self):
        msg = Message(subject="testing",
                      sender="from@example.com",
                      reply_to="evil@example.com\r",
                      recipients=["to@example.com"],
                      body="testing")

        self.assertRaises(BadHeaderError, self.mail.send, msg)
        # self.assertIn('From: from@example.com', msg.message().as_string())
        # self.assertIn('To: to@example.com', msg.message().as_string())
        # self.assertIn('Reply-To: evil@example.com', msg.message().as_string())

    def test_bad_header_recipient(self):
        msg = Message(subject="testing",
                      sender="from@example.com",
                      recipients=[
                          "to@example.com",
                          "to\r\n@example.com"],
                      body="testing")

        self.assertRaises(BadHeaderError, self.mail.send, msg)
        # self.assertIn('To: to@example.com', msg.message().as_string())

    def test_emails_are_sanitized(self):
        msg = Message(subject="testing",
                      sender="sender\r\n@example.com",
                      reply_to="reply_to\r\n@example.com",
                      recipients=["recipient\r\n@example.com"])
        self.assertRaises(BadHeaderError, self.mail.send, msg)
        # self.assertIn('sender@example.com', msg.message().as_string())
        # self.assertIn('reply_to@example.com', msg.message().as_string())
        # self.assertIn('recipient@example.com', msg.message().as_string())

    def test_plain_message(self):
        plain_text = "Hello Joe,\nHow are you?"
        msg = Message(sender="from@example.com",
                      subject="subject",
                      recipients=["to@example.com"],
                      body=plain_text)
        self.assertEqual(plain_text, msg.body)
        self.assertIn('Content-Type: text/plain', msg.message().as_string())

    def test_message_str(self):
        msg = Message(sender="from@example.com",
                      subject="subject",
                      recipients=["to@example.com"],
                      body="some plain text")
        # Skip the tail part, the Message-ID is certainly different.
        self.assertEqual(msg.message().as_string()[:200], str(msg)[:200])

    def test_plain_message_with_attachments(self):
        msg = Message(sender="from@example.com",
                      subject="subject",
                      recipients=["to@example.com"],
                      body="hello")

        msg.attach(content=b"this is a test",
                   mimetype="text/plain")

        self.assertIn('Content-Type: multipart/mixed', msg.message().as_string())

    def test_plain_message_with_ascii_attachment(self):
        msg = Message(subject="subject",
                      recipients=["to@example.com"],
                      body="hello")

        msg.attach(content=b"this is a test",
                   mimetype="text/plain",
                   filename='test doc.txt')

        self.assertIn('Content-Disposition: attachment; filename="test doc.txt"', msg.message().as_string())

    def test_plain_message_with_unicode_attachment(self):
        msg = Message(subject="subject",
                      recipients=["to@example.com"],
                      body="hello")

        msg.attach(content=b"this is a test",
                   mimetype="text/plain",
                   filename=u'ünicöde ←→ ✓.txt')

        parsed = email.message_from_string(msg.message().as_string())

        self.assertIn(re.sub(r'\s+', ' ', parsed.get_payload()[1].get('Content-Disposition')), [
            'attachment; filename*="utf-8\'\'%C3%BCnic%C3%B6de%20%E2%86%90%E2%86%92%20%E2%9C%93.txt"',
            'attachment; filename*=utf-8\'\'%C3%BCnic%C3%B6de%20%E2%86%90%E2%86%92%20%E2%9C%93.txt'
        ])

    # def test_plain_message_with_ascii_converted_attachment(self):
    #     with self.mail_config(ascii_attachments=True):
    #         msg = Message(subject="subject",
    #                       recipients=["to@example.com"],
    #                       body="hello")
    #
    #         msg.attach(data=b"this is a test",
    #                    content_type="text/plain",
    #                    filename=u'ünicödeß ←.→ ✓.txt')
    #
    #         parsed = email.message_from_string(msg.message().as_string())
    #         self.assertIn(
    #             'Content-Disposition: attachment; filename="unicode . .txt"',
    #             msg.message().as_string())

    def test_html_message(self):
        html_text = "<p>Hello World</p>"
        msg = Message(sender="from@example.com",
                      subject="subject",
                      recipients=["to@example.com"],
                      html=html_text)

        self.assertEqual(html_text, msg.html)
        self.assertIn('Content-Type: multipart/alternative', msg.message().as_string())

    def test_json_message(self):
        json_text = '{"msg": "Hello World!}'
        msg = Message(sender="from@example.com",
                      subject="subject",
                      recipients=["to@example.com"],
                      alts={'text/json': json_text})

        self.assertIn('Content-Type: multipart/alternative', msg.message().as_string())
        self.assertEqual(json_text, msg.alternatives.pop()[0])
        self.assertNotIn('Content-Type: multipart/alternative', msg.message().as_string())

    def test_html_message_with_attachments(self):
        html_text = "<p>Hello World</p>"
        plain_text = 'Hello World'
        msg = Message(sender="from@example.com",
                      subject="subject",
                      recipients=["to@example.com"],
                      body=plain_text,
                      html=html_text)
        msg.attach(content=b"this is a test",
                   mimetype="text/plain")

        self.assertEqual(html_text, msg.html)
        self.assertIn('Content-Type: multipart/alternative', msg.message().as_string())

        parsed = email.message_from_string(msg.message().as_string())
        self.assertEqual(len(parsed.get_payload()), 2)

        body, attachment = parsed.get_payload()
        self.assertEqual(len(body.get_payload()), 2)

        plain, html = body.get_payload()
        self.assertEqual(plain.get_payload(), plain_text)
        self.assertEqual(html.get_payload(), html_text)

        self.assertEqual(attachment.get_payload(), 'this is a test')
        # self.assertEqual(base64.b64decode(attachment.get_payload()), b'this is a test')

    def test_date_header(self):
        before = time.time()
        msg = Message(sender="from@example.com",
                      subject="subject",
                      recipients=["to@example.com"],
                      body="hello",
                      date=time.time())
        after = time.time()

        self.assertTrue(before <= msg.date <= after)
        date_formatted = email.utils.formatdate(msg.date, localtime=True)
        self.assertIn('Date: ' + date_formatted, msg.message().as_string())

    def test_msgid_header(self):
        msg = Message(sender="from@example.com",
                      subject="subject",
                      recipients=["to@example.com"],
                      body="hello")

        # see RFC 5322 section 3.6.4. for the exact format specification
        r = re.compile(r"<\S+@\S+>").match(msg.message()['Message-ID'])
        self.assertIsNotNone(r)
        self.assertIn('Message-ID: ', msg.message().as_string())
        self.assertIn(msg.message()['Message-ID'][-28:], msg.message().as_string())

    def test_unicode_sender_tuple(self):
        msg = Message(subject="subject",
                      sender=("ÄÜÖ → ✓", 'from@example.com'),
                      recipients=["to@example.com"])

        self.assertIn('From: =?utf-8?b?w4TDnMOWIOKGkiDinJM=?= <from@example.com>', msg.message().as_string())

    def test_unicode_sender(self):
        msg = Message(subject="subject",
                      sender='ÄÜÖ → ✓ <from@example.com>',
                      recipients=["to@example.com"])

        self.assertIn('From: =?utf-8?b?w4TDnMOWIOKGkiDinJM=?= <from@example.com>', msg.message().as_string())

    def test_unicode_headers(self):
        msg = Message(subject="subject",
                      sender=u'ÄÜÖ → ✓ <from@example.com>',
                      recipients=[u"Ä <t1@example.com>", u"Ü <t2@example.com>"],
                      cc=[u"Ö <cc@example.com>"])

        response = msg.message().as_string()
        a1 = sanitize_address(u"Ä <t1@example.com>", 'utf-8')
        a2 = sanitize_address(u"Ü <t2@example.com>", 'utf-8')
        h1_a = Header("To: %s, %s" % (a1, a2))
        h1_b = Header("To: %s, %s" % (a2, a1))
        h2 = Header("From: %s" % sanitize_address(u"ÄÜÖ → ✓ <from@example.com>", 'utf-8'))
        h3 = Header("Cc: %s" % sanitize_address(u"Ö <cc@example.com>", 'utf-8'))

        # Ugly, but there's no guaranteed order of the recipieints in the header
        try:
            self.assertIn(h1_a.encode(), response)
        except AssertionError:
            self.assertIn(h1_b.encode(), response)

        self.assertIn(h2.encode(), response)
        self.assertIn(h3.encode(), response)

    def test_unicode_subject(self):
        msg = Message(subject=make_lazy_string(lambda a: a, u"sübject"),
                      sender='from@example.com',
                      recipients=["to@example.com"])
        self.assertIn('=?utf-8?q?s=C3=BCbject?=', msg.message().as_string())

    def test_extra_headers(self):
        msg = Message(sender="from@example.com",
                      subject="subject",
                      recipients=["to@example.com"],
                      body="hello",
                      extra_headers={'X-Extra-Header': 'Yes'})
        self.assertIn('X-Extra-Header: Yes', msg.message().as_string())

    def test_message_charset(self):
        msg = Message(sender="from@example.com",
                      subject="subject",
                      recipients=["foo@bar.com"],
                      charset='us-ascii')

        # ascii body
        msg.body = "normal ascii text"
        self.assertIn('Content-Type: text/plain; charset="us-ascii"', msg.message().as_string())

        # ascii html
        msg = Message(sender="from@example.com",
                      subject="subject",
                      recipients=["foo@bar.com"],
                      charset='us-ascii')
        msg.body = None
        msg.html = "<html><h1>hello</h1></html>"
        self.assertIn('Content-Type: text/html; charset="us-ascii"', msg.message().as_string())

        # unicode body
        msg = Message(sender="from@example.com",
                      subject="subject",
                      recipients=["foo@bar.com"])
        msg.body = u"ünicöde ←→ ✓"
        self.assertIn('Content-Type: text/plain; charset="utf-8"', msg.message().as_string())

        # unicode body and unicode html
        msg = Message(sender="from@example.com",
                      subject="subject",
                      recipients=["foo@bar.com"])
        msg.html = u"ünicöde ←→ ✓"
        self.assertIn('Content-Type: multipart/alternative;', msg.message().as_string())
        self.assertIn('Content-Type: text/html; charset="utf-8"', msg.message().as_string())

        # unicode body and attachments
        msg = Message(sender="from@example.com",
                      subject="subject",
                      recipients=["foo@bar.com"])
        msg.html = None
        msg.attach(content=b"foobar", mimetype='text/csv')
        self.assertIn('Content-Type: multipart/mixed;', msg.message().as_string())
        self.assertIn('Content-Type: text/csv; charset="utf-8"', msg.message().as_string())

        # unicode sender as tuple
        msg = Message(sender=(u"送信者", "from@example.com"),
                      subject=u"表題",
                      recipients=["foo@bar.com"],
                      reply_to=u"返信先 <somebody@example.com>",
                      charset='shift_jis')  # japanese
        msg.body = u'内容'
        self.assertIn('From: =?iso-2022-jp?', msg.message().as_string())
        self.assertNotIn('From: =?utf-8?', msg.message().as_string())
        self.assertIn('Subject: =?iso-2022-jp?', msg.message().as_string())
        self.assertNotIn('Subject: =?utf-8?', msg.message().as_string())
        self.assertIn('Reply-To: =?iso-2022-jp?', msg.message().as_string())
        self.assertNotIn('Reply-To: =?utf-8?', msg.message().as_string())
        self.assertIn('Content-Type: text/plain; charset="iso-2022-jp"', msg.message().as_string())

        # unicode subject sjis
        msg = Message(sender="from@example.com",
                      subject=u"表題",
                      recipients=["foo@bar.com"],
                      charset='shift_jis')  # japanese
        msg.body = u'内容'
        self.assertIn('Subject: =?iso-2022-jp?', msg.message().as_string())
        self.assertIn('Content-Type: text/plain; charset="iso-2022-jp"', msg.message().as_string())

        # unicode subject utf-8
        msg = Message(sender="from@example.com",
                      subject="subject",
                      recipients=["foo@bar.com"],
                      charset='utf-8')
        msg.body = u'内容'
        self.assertIn('Subject: subject', msg.message().as_string())
        self.assertIn('Content-Type: text/plain; charset="utf-8"', msg.message().as_string())

        # ascii subject
        msg = Message(sender="from@example.com",
                      subject="subject",
                      recipients=["foo@bar.com"],
                      charset='us-ascii')
        msg.body = "normal ascii text"
        self.assertNotIn('Subject: =?us-ascii?', msg.message().as_string())
        self.assertIn('Content-Type: text/plain; charset="us-ascii"', msg.message().as_string())

        # default charset
        msg = Message(sender="from@example.com",
                      subject="subject",
                      recipients=["foo@bar.com"])
        msg.body = "normal ascii text"
        self.assertNotIn('Subject: =?', msg.message().as_string())
        self.assertIn('Content-Type: text/plain; charset="utf-8"', msg.message().as_string())

    def test_empty_subject_header(self):
        msg = Message(sender="from@example.com",
                      recipients=["foo@bar.com"])
        msg.body = "normal ascii text"
        self.mail.send(msg)
        self.assertIn('Subject:', msg.message().as_string())
