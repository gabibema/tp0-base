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
HEADER_CHUNK_SIZE = 16

def send_message(conn: socket, message: str, flag: str):
    """
    Sends a message given a socket connection avoiding short writes
    """
    full_message = f"{HEADER_DELIMETER}{len(message)}{SIZE_DELIMETER}{flag}{HEADER_DELIMETER}{message}".encode()
    total_sent = 0
    while total_sent < len(full_message):
        try: 
            sent = conn.send(full_message[total_sent:])
        except OSError as e:
            logging.error(f"Error while sending message: {e}")
            return None
        total_sent += sent
    
    return total_sent


def read_until(conn:socket, delimeter:str) -> str:
    read = ""
    while True:
        recv = conn.recv(1).decode()
        if recv == delimeter:
            break
        read += recv
    
    return read


def read_header(conn: socket) -> tuple[str, str]:
    """
    Reads both the initial and final header of a message from a socket in 16-byte blocks.
    """
    chunks = []
    header_complete = False
    while not header_complete:
        chunk = conn.recv(HEADER_CHUNK_SIZE)
        
        chunks.append(chunk)
        joined_chunks = b''.join(chunks)
        # Check if we have received the start and end delimiters of the header, if receives more than 2 delimiters, the extra ones are part of the message
        if joined_chunks.count(HEADER_DELIMETER.encode()) >= 2:
            header_complete = True
    
    # Convert the received bytes to a string and split it into the header and the message part (if any)
    header_and_message = joined_chunks.decode()
    header_part, message_part = header_and_message.split(HEADER_DELIMETER, 2)[1:3]
    
    # Extract the size and flag from the header
    try:
        size, flag = header_part.split(SIZE_DELIMETER)
    except ValueError:
        # In case the header does not follow the expected format
        raise ValueError("Header does not follow the expected format")
    
    # Return the size, flag, and the start of the message (if any) for further processing
    return (size, flag, message_part)



def receive_message(conn:socket) -> tuple[str,str]:
    """
    Receives a message from a socket
    """
    try: 
        size, flag, message = read_header(conn)
    except ValueError:
        return ("", MESSAGE_FLAG["ERROR"])

    size = int(size) 
    while len(message) < size:
        message += conn.recv(size - len(message)).decode()
    return (message, flag) 
