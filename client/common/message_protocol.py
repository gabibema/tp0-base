from socket import socket

def send_message(conn:socket, message: str) -> None:
    """
    Sends a message to a socket
    """
    conn.sendall(f"|{len(message)}|{message}".encode())

def receive_message(conn:socket) -> str:
    """
    Receives a message from a socket
    """
    message = conn.recv(1).decode()
    is_protocol_message = False
    if message != '|':
        return  (message + conn.recv(1024).decode(), is_protocol_message)

    is_protocol_message = True
    size = conn.recv(4).decode()
    delimeter = size.find('|')
    if delimeter != -1:
        message = size[delimeter:]
        size = size[:delimeter]
        message += conn.recv(int(size)-delimeter+1).decode()
    
    else:
        message = conn.recv(int(size)).decode()
    
    return (message[1:], is_protocol_message) 