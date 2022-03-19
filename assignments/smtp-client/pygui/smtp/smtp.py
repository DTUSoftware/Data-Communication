import os
import socket
import ssl
import base64

ADDRESS = os.environ.get("MAILSERVER_ADDRESS", "localhost")
PORT = int(os.environ.get("MAILSERVER_PORT", "2525"))
USE_SSL = True if os.environ.get("USE_SSL", "False").lower() == "true" else False
USERNAME = base64.b64encode(os.environ.get("MAILSERVER_USERNAME", "admin").encode("UTF-8")).decode("UTF-8")
PASSWORD = base64.b64encode(os.environ.get("MAILSERVER_PASSWORD", "password").encode("UTF-8")).decode("UTF-8")


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
        res = self.ehlo(ADDRESS)
        if res:
            print("EHLO accepted")

            res = self.starttls()
            if res:
                print("STARTTLS accepted, wrapping socket")

                # create a default context, to try and find the highest standard of safety for the socket
                self.ctx = ssl.create_default_context()
                # disable insecure/older versions, we want dat TLS
                self.ctx.options |= (
                        ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
                )
                # no compression
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
                success = self.quit()
                if not success:
                    print("Server did not want to close connection - closing on our end anyway")
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

    def ehlo(self, domain):
        command = EHLO(domain)
        res = command.send(self)
        return res, command.reply_code

    def helo(self, domain):
        command = HELO(domain)
        res = command.send(self)
        return res, command.reply_code

    def mail(self, reverse_path):
        command = MAIL(reverse_path)
        res = command.send(self)
        return res, command.reply_code

    def rcpt(self, forward_path):
        command = RCPT(forward_path)
        res = command.send(self)
        return res, command.reply_code

    def data(self, data):
        command = DATA(data)
        res = command.send(self)
        return res, command.reply_code

    def quit(self):
        command = QUIT()
        res = command.send(self)
        return res, command.reply_code

    def starttls(self):
        command = STARTTLS()
        res = command.send(self)
        return res, command.reply_code

    def auth(self, username, password):
        command = AUTH(username, password)
        res = command.send(self)
        return res, command.reply_code


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

    def __init__(self, reverse_path):
        super().__init__("MAIL", self.reply_codes)
        super().set_content(f"FROM:<{reverse_path}>")


class RCPT(Command):
    reply_codes = {
        "success": [250, 251],
        "failure": [550, 551, 552, 553, 450, 451, 452],
        "error": [500, 501, 503, 421]
    }

    def __init__(self, forward_path):
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
