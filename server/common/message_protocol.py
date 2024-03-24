from socket import socket
import logging

MESSAGE_FLAG = {
    'NON_PROTOCOL': '0',
    'NORMAL': '1',
    'BET': '2',
    'FINAL': '3',
    'ERROR': '4'
}

SIZE_DELIMETER = ','
HEADER_DELIMETER = '|'

def send_message(conn:socket, message: str, flag:str) -> None:
    """
    Sends a message to a socket
    """
    conn.sendall(f"|{len(message)},{flag}|{message}".encode())

def read_until(conn:socket, delimeter:str) -> str:
    read = ""
    while True:
        recv = conn.recv(1).decode()
        if recv == delimeter:
            break
        read += recv
    
    return read


def read_header(conn:socket) -> tuple[str, str]:
    """
    Reads the header of a message from a socket
    """
    header = conn.recv(1).decode()
    if header != HEADER_DELIMETER:
        return (header, MESSAGE_FLAG['NON_PROTOCOL'])
    
    size = read_until(conn, SIZE_DELIMETER)
    flag = read_until(conn, HEADER_DELIMETER)
    return (size, flag)

def receive_message(conn:socket) -> tuple[str,str]:
    """
    Receives a message from a socket
    """
    size, flag = read_header(conn)
    if flag == MESSAGE_FLAG['NON_PROTOCOL']:
        return  (size + conn.recv(1024).decode(), flag)

    message = conn.recv(int(size)).decode()
    while len(message) < int(size):
        message += conn.recv(int(size) - len(message)).decode()
    
    return (message, flag) 
