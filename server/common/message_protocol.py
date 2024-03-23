from socket import socket

def send_message(conn:socket, message: str) -> None:
    """
    Sends a message to a socket
    """
    conn.sendall(f"|{len(message)},{message}".encode())

def receive_message(conn:socket) -> str:
    """
    Receives a message from a socket
    """
    message = conn.recv(1).decode()
    if message != '|':
        return  message + conn.recv(1024).decode()

    size = conn.recv(4).decode()
    delimeter = size.find('|')
    if delimeter != -1:
        size = size[:delimeter]
        message = size[delimeter:]
        message += conn.recv(int(size)-delimeter+1).decode()
    
    else:
        message = conn.recv(int(size)).decode()
    
    return message[1:]