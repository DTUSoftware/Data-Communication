import os
import random
import socket as _socket

ADDRESS = os.environ.get("MAILSERVER_ADDRESS", "localhost")
PORT = int(os.environ.get("MAILSERVER_PORT", "2525"))
BOUNDARY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'()+_,-./:=?"


class MIMEContent:
    def __init__(self, content_type: str = None, content_disposition: str = None, content_transfer_encoding: str = None, data: str = None):
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
        self.boundary = "".join([random.choice(BOUNDARY_CHARS) for x in range(random.randint(40,60))])
        self.content = []
        self.content.append(MIMEContent(content_type='multipart/mixed; boundary="' + self.boundary + '"'))

    def add_content(self, content: MIMEContent):
        self.content.append(content)

    def add_body(self, text: str):
        body = MIMEContent(data=text)
        self.add_content(body)

    def get_output(self):
        output = "MIME-Version: " + self.version + "\n"

        for part in self.content:
            output = (output + part.get_output() +
                      "\n" +
                      "--" + self.boundary + "\n")

        return output


class File:
    def __init__(self, input):
        split = input.split(",")
        metadata = split[0]
        data = ",".join(split[1:])
        self.metadata = metadata
        self.data = data

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

    def send(self, socket: _socket.socket = None, close_socket: bool = True):
        send_mail(self, socket, close_socket)


def send_mail(mail: Mail, socket: _socket.socket = None, close_socket: bool = True):
    if not socket:
        socket = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        socket.connect((ADDRESS, PORT))
    while True:
        res = b''
        res = socket.recv(1024)
        # print(f"{res!r}")
        res = res.decode("UTF-8")
        print(res)
        req = None
        if res.startswith("220"):
            req = "EHLO " + mail.sender.split("@")[1]
        elif res.startswith("250"):
            if any(x in res.lower() for x in ["sender", "new message"]):
                req = "RCPT TO: <" + mail.recipient + ">"
            elif any(x in res.lower() for x in ["recipient"]):
                req = "DATA"
            elif any(x in res.lower() for x in ["accepted for delivery", "mail accepted"]):
                if close_socket:
                    req = "QUIT"
                else:
                    break
            else:
                req = "MAIL FROM: <" + mail.sender + ">"
        elif res.startswith("354"):
            header = str("From: " + mail.sender + "\n" +
                         "To: " + mail.recipient + "\n" +
                         "Subject: " + mail.subject + "\n")
            mime_message = MIMEMessage()
            data = mail.content
            lines = data.split("\n")
            for i in range(len(lines)):
                if lines[i].startswith("."):
                    lines[i] = "." + lines[i]  # prevent dot-stuffing
            data = "\n".join(lines)
            mime_message.add_body(data)

            mime_message.add_content(mail.file.get_mime_content())

            req = header+mime_message.get_output()+"."
        elif res.startswith("500"):
            print("Command unrecognized.")
            break
        elif res.startswith("503"):
            print("An error occured.")
            break
        elif res.startswith("221"):
            print("Connection ended.")
            if not close_socket:
                raise ConnectionAbortedError("connection ended")
            break

        if req:
            req = req + "\n"
            print(f"Sending: {(req[:200] + '...') if len(req) > 200 else req}")
            socket.sendall(req.encode("UTF-8"))

    if close_socket:
        socket.close()


def send_mail_raw(sender, recipient, subject, content, file=None):
    with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as socket:
        socket.connect((ADDRESS, PORT))
        mail = Mail(sender, recipient, subject, content, file)
        mail.send(socket)
        return 200
