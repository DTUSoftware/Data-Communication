from smtp import smtp
import random

BOUNDARY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'()+_,-./:=?"


class MIMEContent:
    def __init__(self, content_type: str = None, content_disposition: str = None, content_transfer_encoding: str = None,
                 data: str = None):
        self.content_type = "text/plain"

        if content_type:
            self.content_type = content_type
        self.content_disposition = content_disposition
        self.content_transfer_encoding = content_transfer_encoding
        self.data = data

    def set_data(self, data: str):
        self.data = data

    def get_output(self):
        output = "Content-Type: " + self.content_type + "\n"

        if self.content_transfer_encoding:
            output = output + "Content-Transfer-Encoding: " + self.content_transfer_encoding + "\n"
        if self.content_disposition:
            output = output + "Content-Disposition: " + self.content_disposition + "\n"
        if self.data:
            output = (output +
                      "\n" +
                      self.data + "\n")

        return output


class MIMEMessage:
    version = "1.0"

    def __init__(self):
        self.boundary = "".join([random.choice(BOUNDARY_CHARS) for x in range(random.randint(40, 60))])
        self.content = []
        self.content.append(MIMEContent(content_type='multipart/mixed; boundary="' + self.boundary + '"'))

    def add_content(self, content: MIMEContent):
        self.content.append(content)

    def add_body(self, text: str):
        body = MIMEContent(data=text)
        self.add_content(body)

    def get_output(self):
        output = "MIME-Version: " + self.version + "\n"

        # parts = ("\n--" + self.boundary + "\n").join([part.get_output() for part in self.content])
        # print(parts)
        # output = output + parts
        for part in self.content:
            output = (output + part.get_output() +
                      "\n" +
                      "--" + self.boundary + "\n")

        return output


class File:
    def __init__(self, input=None):
        if input:
            split = input.split(",")
            metadata = split[0]
            data = ",".join(split[1:])
            self.metadata = metadata
            self.data = data

    def __new__(cls, *args, **kwargs):
        if "input" in kwargs and kwargs["input"]:
            return super().__new__(cls)

    def get_mime_content(self):
        filetype = self.metadata.split(":")[1].split(";")[0]
        fileending = filetype.split("/")[1]
        content_type = "application/octet-stream; name=file." + fileending
        content_transfer_encoding = self.metadata.split(";")[1]
        content_disposition = 'attachment; filename="file.' + fileending + '"'
        return MIMEContent(content_type, content_transfer_encoding=content_transfer_encoding,
                           content_disposition=content_disposition, data=self.data)


class Mail:
    def __init__(self, sender, recipient, subject, content, file=None):
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.content = content
        self.file = File(file)

    def send(self, conn, close_connection: bool = True):
        # ----- Hello and check for MIME support ---- #
        mime_supported = True
        success, reply_code = conn.ehlo(domain=self.sender.split("@")[1])
        if not success:
            if reply_code == 500:
                mime_supported = False
                success = conn.helo(domain=self.sender.split("@")[1])
                if not success:
                    return reply_code
            else:
                return reply_code

        # --- AUTH if Secure (TLS or SSL) --- #
        if smtp.USE_SSL:
            success, reply_code = conn.auth(username, password)
            if not success:
                return reply_code

        # ----- MAIL From ---- #
        success, reply_code = conn.mail(self.sender)
        if not success:
            return reply_code

        # ----- RCPT To ---- #
        success, reply_code = conn.rcpt(self.recipient)
        if not success:
            return reply_code

        # ----- DATA ---- #
        header = str("From: " + self.sender + "\n" +
                     "To: " + self.recipient + "\n" +
                     "Subject: " + self.subject + "\n")
        if mime_supported:
            mime_message = MIMEMessage()
            mime_message.add_body(self.content)

            if self.file:
                mime_message.add_content(self.file.get_mime_content())

            data = header + mime_message.get_output()
        else:
            data = header + "\n" + self.content
        success, reply_code = conn.data(data)
        if not success:
            return reply_code

        if close_connection:
            conn.close()

        return 200


def send_mail_raw(sender, recipient, subject, content, file=None):
    conn = smtp.Connection()
    mail = Mail(sender, recipient, subject, content, file)
    return mail.send(conn, close_connection=True)