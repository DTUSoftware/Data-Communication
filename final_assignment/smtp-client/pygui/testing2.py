import base64
from socket import *
import ssl

# mailserver and port
mailserver = 'smtp.gmail.com'
port = 587



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
    ctx = ssl.create_default_context()
    wrappedClientSocket = ctx.wrap_socket(clientSocket, server_hostname=mailserver)
    send_smtp_command("ehlo google", wrappedClientSocket)
    print_response(wrappedClientSocket)
    send_smtp_command("auth login", wrappedClientSocket)
    print_response(wrappedClientSocket)
    wrappedClientSocket.send(b"Userbane\r\n")
    print_response(wrappedClientSocket)
    wrappedClientSocket.send(b"Password\r\n")
    print_response(wrappedClientSocket)

# print(base64.b64encode(bytes(username, "utf-8")))
# print(base64.b64encode(bytes(password, "utf-8")))
# PROTOCOL_SSLv23
