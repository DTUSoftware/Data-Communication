import os
import socket as _socket

ADDRESS = os.environ.get("MAILSERVER_ADDRESS", "localhost")
PORT = int(os.environ.get("MAILSERVER_PORT", "2525"))


class MIMEContent:
    content_type = "text/plain"
    content_disposition = None
    data = None

    def __init__(self, content_type: str = None, content_disposition: str = None, data: str = None):
        if content_type:
            self.content_type = content_type
        if content_disposition:
            self.content_disposition = content_disposition
        if data:
            self.data = data

    def set_data(self, data: str):
        self.data = data

    def get_output(self):
        output = "Content-Type: " + self.content_type + "\n"

        if self.content_disposition:
            output = output + "Content-Disposition: " + self.content_disposition + "\n"
        if self.data:
            output = (output +
                      "\n" +
                      self.data + "\n")

        return output


class MIMEMessage:
    version = "1.0"
    boundary = "WhyDoesThisEvenExistHereIDKAskTomOrJerryPart5"
    content = []

    def __init__(self):
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


class Mail:
    def __init__(self, sender, recipient, subject, content):
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.content = content

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
            print(f"Sending: {req.encode('UTF-8')}")
            socket.sendall(req.encode("UTF-8"))

    if close_socket:
        socket.close()


def send_mail_raw(sender, recipient, subject, content):
    with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as socket:
        socket.connect((ADDRESS, PORT))
        mail = Mail(sender, recipient, subject, content)
        mail.send(socket)
        return 200

