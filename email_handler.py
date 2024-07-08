import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup
import re


class EmailHandler:
    def __init__(self, imap_server, port, email_address=None, password=None):
        self.imap_server = imap_server
        self.port = port
        self.email_address = email_address
        self.password = password

    def get_emails(self, limit=5):
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.port)
            if self.email_address and self.password:
                mail.login(self.email_address, self.password)
            else:
                raise ValueError("Не указаны адрес электронной почты или пароль.")

            mail.select('inbox')

            _, search_data = mail.search(None, 'ALL')
            email_messages = []

            for num in reversed(search_data[0].split()[-limit:]):
                _, msg_data = mail.fetch(num, '(RFC822)')
                email_message = email.message_from_bytes(msg_data[0][1])

                subject, _ = decode_header(email_message['Subject'])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode()

                from_ = email_message['From']

                body = self.get_email_body(email_message)

                compact_body = re.sub(r'\s+', ' ', body).strip()
                email_messages.append(f"{from_}\n{subject}\n{compact_body[:300]}...")

            mail.logout()
            return email_messages
        except Exception as e:
            raise Exception(f"Ошибка при получении писем: {str(e)}")

    def get_email_body(self, email_message):
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    return part.get_payload(decode=True).decode()
                elif content_type == "text/html":
                    return self.html_to_plain_text(part.get_payload(decode=True).decode())
        else:
            return email_message.get_payload(decode=True).decode()

    def html_to_plain_text(self, html):
        soup = BeautifulSoup(html, features="html.parser")
        return soup.get_text()
