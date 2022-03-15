import socket
from socket import *


def start_socket():
    return socket.socket(AF_INET, SOCK_STREAM)


def connect(socket: socket, mailserver: str, port: int):
    socket.connect()


def send_smtp_command(command: str, socket: socket):
    command = command + "\r\n"
    socket.send(command.encode("UTF-8"))


def response(socket: socket):
    response = socket.recv(1024)
    return str(response)


def print_response(socket: socket):
    print(response(socket))
