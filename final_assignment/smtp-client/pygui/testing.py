from socket import *
import ssl

mailserver = 'smtp.gmail.com'
port = 587
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((mailserver, port))
recv = clientSocket.recv(1024)
print(recv)
if "220" in str(recv):
    print('220 reply not received from server.')

# Send HELO command and print server response
heloCommand = 'EHLO\r\n'
clientSocket.send(heloCommand.encode("UTF-8"))
recv1 = clientSocket.recv(1024)
print(recv1)
if recv1[:3] != '250':
    print('250 reply not received from server.')

# Send MAIL FROM command and print server response.
command = "STARTTLS\r\n"
clientSocket.send(command)
clientSocket = ssl.wrap_socket(clientSocket)
recvdiscard = clientSocket.recv(1024)
print(recvdiscard)
clientSocket.send("MAIL From: email\r\n")
recv2 = clientSocket.recv(1024)
print(recv2)
if recv2[:3] != '250':
    print('250 reply not received from server.')
