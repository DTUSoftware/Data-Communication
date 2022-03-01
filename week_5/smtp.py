import socket as _socket

ADDRESS = "smtp2.bhsi.xyz"
PORT = 2525

MAILS = [
    {
        "sender": "fuckdig@fuckdig.dk",
        "recipient": "fuckmig@fuckmig.dk",
        "subject": "hello :)",
        "content": "you are so\n"
                   "cute :)"
    },
    {
        "sender": "mads@fuckdig.dk",
        "recipient": "taiwan@fuckmig.dk",
        "subject": "ily",
        "content": "...take care bby, make sure that China doesn't catch u\n"
                   "\n"
                   ".\n"
                   ".\n"
                   "much love,\n"
                   "Mads"
    }
]


class Mail:
    def __init__(self, sender, recipient, subject, content):
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.content = content

    def send(self, socket: _socket.socket = None, close_socket: bool = True, expect_220: bool = True):
        send_mail(self, socket, close_socket, expect_220)


def send_mail(mail: Mail, socket: _socket.socket = None, close_socket: bool = True, expect_220: bool = True):
    if not socket:
        socket = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        socket.connect((ADDRESS, PORT))
    check_res = expect_220
    while True:
        res = b''
        if check_res:
            res = socket.recv(1024)
            # print(f"{res!r}")
            res = res.decode("UTF-8")
        else:
            check_res = True
            res = "250"
        print(res)
        req = None
        if res.startswith("220"):
            req = "HELO " + mail.sender.split("@")[1]
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
                         "Subject: " + mail.subject)
            data = mail.content
            lines = data.split("\n")
            for i in range(len(lines)):
                if lines[i].startswith("."):
                    lines[i] = "." + lines[i]  # prevent dot-stuffing
            data = "\n".join(lines)

            socket.send((header+"\n\n"+data+"\n.\n").encode("UTF-8"))
        elif res.startswith("500"):
            print("Command unrecognized.")
            break
        elif res.startswith("503"):
            print("An error occured.")
            break
        elif res.startswith("221"):
            print("Connection ended.")
            raise ConnectionAbortedError("connection ended")

        if req:
            req = req + "\n"
            print(f"Sending: {req.encode('UTF-8')}")
            socket.sendall(req.encode("UTF-8"))

    if close_socket:
        socket.close()


if __name__ == "__main__":
    with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as socket:
        socket.connect((ADDRESS, PORT))
        initial = True
        for mail_raw in MAILS:
            mail = Mail(mail_raw["sender"], mail_raw["recipient"], mail_raw["subject"], mail_raw["content"])
            if initial:
                mail.send(socket, close_socket=False)
                initial = False
            else:
                mail.send(socket, close_socket=False, expect_220=False)
        socket.sendall("QUIT\n".encode("UTF-8"))
