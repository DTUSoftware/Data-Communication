import os
import random
import socket
import ssl
import base64

ADDRESS = os.environ.get("MAILSERVER_ADDRESS", "localhost")
PORT = int(os.environ.get("MAILSERVER_PORT", "2525"))
USE_SSL = True if os.environ.get("USE_SSL", "False").lower() == "true" else False
USERNAME = base64.b64encode(os.environ.get("MAILSERVER_USERNAME", "admin").encode("UTF-8")).decode("UTF-8")
PASSWORD = base64.b64encode(os.environ.get("MAILSERVER_PASSWORD", "password").encode("UTF-8")).decode("UTF-8")
BOUNDARY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'()+_,-./:=?"

print(USERNAME)
print(PASSWORD)


class Connection:
    def __init__(self):
        self.sock = None
        self.ssock = None
        self.ctx = None

        self.open()

    def is_open(self):
        return self.ssock or self.sock

    def open_secure(self):
        global USE_SSL
        if not self.is_open():
            print("You need to open an insecure connection first!")
            return
        elif self.ssock:
            print("Secure connection already open! - Close it?")
            return
        elif not USE_SSL:
            print("SSL not enabled!")
            return

        # initial EHLO/HELO
        command = EHLO(ADDRESS)
        res = command.send(self)
        if res:
            print("EHLO accepted")

            command = STARTTLS()
            res = command.send(self)
            if res:
                print("STARTTLS accepted, wrapping socket")

                self.ctx = ssl.create_default_context()
                self.ctx.options |= (
                        ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
                )
                self.ctx.options |= ssl.OP_NO_COMPRESSION
                try:
                    self.ssock = self.ctx.wrap_socket(self.sock, server_hostname=ADDRESS)
                except ssl.SSLError as e:
                    print("Could not open connection over SSL: " + str(e))
                    self.close()
                    if "WRONG_VERSION_NUMBER" in str(e):
                        print("Turning SSL off and trying again!")
                        USE_SSL = False
                        self.open()

    def open(self):
        if self.is_open():
            print("Close connection first!")
            return

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ADDRESS, PORT))

        # Check connection establishment
        reply_code = self.get_response()
        if reply_code == 421:
            print("Could not establish a connection!")
            self.close()
        elif reply_code == 220:
            if USE_SSL:
                self.open_secure()
        else:
            print("Unknown connection establishment reply!")
            self.close()

    def close(self):
        try:
            if self.is_open():
                command = QUIT()
                success = command.send(self)
                if not success:
                    print("Server did not want to close connection - closing on our end anyway - " + str(command.reply_code))
        except Exception as e:
            print("Error while trying to close connection - closing on our end anyway - " + str(e))

        if self.ssock:
            self.ssock.close()
            self.ssock = None
        if self.sock:
            self.sock.close()
            self.sock = None

    def get_current_socket(self):
        if not self.is_open():
            return None
        current_sock = self.sock
        if self.ssock:
            current_sock = self.ssock
        return current_sock

    def get_response(self):
        res = self.get_current_socket().recv(1024)
        print(f"Response: {res}\n")
        reply_code = int((res.decode("UTF-8"))[:3])
        return reply_code

    def send(self, req: str):
        req = req.encode("UTF-8")
        print(f"Sending: {req}")
        self.get_current_socket().sendall(req)
        return self.get_response()


class Command:
    def __init__(self, command: str, reply_codes: dict, content=None):
        self.command = command
        self.content = content
        self.reply_codes = reply_codes
        self.reply_code = None

    def set_content(self, content=None):
        self.content = content

    def send(self, conn: Connection):
        if self.content:
            self.reply_code = conn.send(" ".join([self.command, self.content]) + "\r\n")
        else:
            self.reply_code = conn.send(self.command + "\r\n")
        if self.success(self.reply_code):
            return True
        return False

    def success(self, reply_code: int):
        return "success" in self.reply_codes and reply_code in self.reply_codes["success"]

    def failure(self, reply_code: int):
        return "failure" in self.reply_codes and reply_code in self.reply_codes["failure"]

    def error(self, reply_code: int):
        return "error" in self.reply_codes and reply_code in self.reply_codes["error"]


class HELO(Command):
    reply_codes = {
        "success": [250],
        "error": [500, 501, 504, 421]
    }

    def __init__(self, domain=None):
        super().__init__("HELO", self.reply_codes)
        super().set_content(domain)


class EHLO(Command):
    reply_codes = {
        "success": [250],
        "error": [500, 501, 504, 421]
    }

    def __init__(self, domain=None):
        super().__init__("EHLO", self.reply_codes)
        super().set_content(domain)


class MAIL(Command):
    reply_codes = {
        "success": [250],
        "failure": [552, 451, 452],
        "error": [500, 501, 421]
    }

    def __init__(self, reverse_path=None):
        super().__init__("MAIL", self.reply_codes)
        super().set_content(f"FROM:<{reverse_path}>")


class RCPT(Command):
    reply_codes = {
        "success": [250, 251],
        "failure": [550, 551, 552, 553, 450, 451, 452],
        "error": [500, 501, 503, 421]
    }

    def __init__(self, forward_path=None):
        super().__init__("RCPT", self.reply_codes)
        super().set_content(f"TO:<{forward_path}>")


class DATA(Command):
    reply_codes = {
        "success": [354],
        "failure": [451, 554],
        "error": [500, 501, 503, 421]
    }
    reply_codes_2 = {
        "success": [250],
        "failure": [552, 554, 451, 452]
    }

    def __init__(self, content=None):
        super().__init__("DATA", self.reply_codes)
        lines = content.split("\n")
        for i in range(len(lines)):
            if lines[i].startswith("."):
                lines[i] = "." + lines[i]  # prevent dot-stuffing
        self.data = "\n".join(lines)

    def send(self, conn: Connection):
        # Send initial start
        if super().send(conn):
            # Send data
            self.command = self.data + "\r\n."
            print(self.command)
            self.reply_codes = self.reply_codes_2
            return super().send(conn)


class QUIT(Command):
    reply_codes = {
        "success": [221],
        "error": [500]
    }

    def __init__(self):
        super().__init__("QUIT", self.reply_codes)


class STARTTLS(Command):
    reply_codes = {
        "success": [220],
        "error": [500]
    }

    def __init__(self):
        super().__init__("STARTTLS", self.reply_codes)


class AUTH(Command):
    reply_codes = {
        "success": [220, 334, 235],
        "error": [500]
    }

    def __init__(self, username, password):
        super().__init__("AUTH LOGIN", self.reply_codes)
        self.username = username
        self.password = password

    def send(self, conn: Connection):
        # Send initial part
        if super().send(conn):
            # Send username
            self.command = self.username
            if super().send(conn):
                # Send password
                self.command = self.password
                return super().send(conn)
        if self.success(self.reply_code):
            return True
        return False


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
        command = EHLO(domain=self.sender.split("@")[1])
        success = command.send(conn)
        if not success:
            if command.reply_code == 500:
                mime_supported = False
                command = HELO(domain=self.sender.split("@")[1])
                success = command.send(conn)
                if not success:
                    return command.reply_code
            else:
                return command.reply_code

        # --- AUTH if Secure (TLS or SSL) --- #
        if USE_SSL:
            command = AUTH(USERNAME, PASSWORD)
            success = command.send(conn)
            if not success:
                return command.reply_code

        # ----- MAIL From ---- #
        command = MAIL(self.sender)
        success = command.send(conn)
        if not success:
            return command.reply_code

        # ----- RCPT To ---- #
        command = RCPT(self.recipient)
        success = command.send(conn)
        if not success:
            return command.reply_code

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
        command = DATA(data)
        success = command.send(conn)
        if not success:
            return command.reply_code

        if close_connection:
            conn.close()

        return 200


def send_mail_raw(sender, recipient, subject, content, file=None):
    conn = Connection()
    mail = Mail(sender, recipient, subject, content, file)
    return mail.send(conn, close_connection=True)
