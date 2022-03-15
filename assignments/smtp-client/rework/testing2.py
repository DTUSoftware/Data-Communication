import base64
from socket import *
import ssl

# mailserver and port
mailserver = 'smtp.gmail.com'
port = 587
username = "smtptestsoftware69@gmail.com"
password = "PleaseWork69"
base64username = "c210cHRlc3Rzb2Z0d2FyZTY5QGdtYWlsLmNvbQ=="
base64password = "UGxlYXNlV29yazY5"


def send_smtp_command(command: str, socket: socket):
    command = command + "\r\n"
    socket.send(command.encode("UTF-8"))


def response(socket: socket):
    response = socket.recv(1024)
    return str(response)


def print_response(socket: socket):
    print(response(socket))


with socket(AF_INET, SOCK_STREAM) as clientSocket:
    clientSocket.connect((mailserver, port))
    print_response(clientSocket)

    send_smtp_command("ehlo google", clientSocket)
    print_response(clientSocket)

    send_smtp_command("starttls", clientSocket)
    print_response(clientSocket)
    # wrappedClientSocket = socket
    wrappedClientSocket = ssl.wrap_socket(clientSocket, ssl_version=ssl.PROTOCOL_SSLv23)
    send_smtp_command("ehlo google", wrappedClientSocket)
    print_response(wrappedClientSocket)
    send_smtp_command("auth login", wrappedClientSocket)
    print_response(wrappedClientSocket)
    wrappedClientSocket.send(b"c210cHRlc3Rzb2Z0d2FyZTY5QGdtYWlsLmNvbQ==\r\n")
    wrappedClientSocket.send(b"UGxlYXNlV29yazY5\r\n")
    print_response(wrappedClientSocket)

# print(base64.b64encode(bytes(username, "utf-8")))
# print(base64.b64encode(bytes(password, "utf-8")))
# PROTOCOL_SSLv23
