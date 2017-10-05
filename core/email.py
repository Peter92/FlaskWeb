from __future__ import absolute_import
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from email.MIMEBase import MIMEBase
from email import encoders
from ssl import SSLError
import smtplib

from extensions.html2text import html2text

def form_message(sender, receivers, subject, body, attachments=[]):

    msg = MIMEMultipart('alternative')
    msg['To'] = ', '.join(receivers)
    msg['From'] = sender
    msg['Subject'] = 'subject'

    if '<' in body and '>' in body:
        msg.attach(MIMEText(html2text(body), 'plain'))
        msg.attach(MIMEText(body, 'html'))
    else:
        msg.attach(MIMEText(body, 'plain'))

    for attachment in attachments:
        try:
            with open(attachment, 'rb') as f:
                filename = attachment.replace('\\', '/').split('/')[-1]
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', "attachment; filename={}".format(filename))
                msg.attach(part)
        except IOError:
            print 'Failed to attach {}.'.format(attachment)

    return msg.as_string()


class Mail(object):
    def __init__(self, subject, body, attachments=None):            
        self.subject = subject
        self.body = body
        self.attachments = []
        self.replacements = {}
        self.recipients = []

    def _body_replacement(self):
        """Apply any replacements to the body of the message."""
        body = self.body
        for k, v in self.replacements.iteritems():
            body.replace(k, v)
        return body

    def add_recipient(self, email, name=None):
        if name is not None:
            self.recipients.append('{} <{}>'.format(name, email))
        else:
            self.recipients.append(email)

    def attach(self, filename):
        self.attachments.append(filename)

    def replace(self, value, replacement):
        self.replacements[value] = replacement

    def send_with_papercut(self):
                 
        sender = 'Papercut@Papercut.com'
        recipients = ['Papercut@user.com']

        body = self._body_replacement()
        msg = form_message(sender, recipients, self.subject, body, self.attachments)
        try:
            server = smtplib.SMTP('localhost')
            server.sendmail(sender, recipients, msg)
            return True
            
        except smtplib.SMTPException as e:
            print 'Error: {}'.format(e)
            
        return False
        
    def send_with_gmail(self, username, password):
        
        body = self._body_replacement()
        msg = form_message(username, self.recipients, self.subject, body, self.attachments)
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(username, password)
            server.sendmail(username, self.recipients, msg)
            return True
            
        except smtplib.SMTPAuthenticationError:
            print 'Error: Username and password not accepted.'
            
        except SSLError:
            print 'Error: Unable to establish a secure connection.'
            
        except smtplib.SMTPException as e:
            print 'Error: {}'.format(e)
            
        return False
