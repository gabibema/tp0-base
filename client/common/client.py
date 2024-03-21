import socket
import time
import logging
from configparser import ConfigParser

class Client:
    def __init__(self, config):
        self.config = config
        self.conn = None


    def create_client_socket(self):
        
        try:
            host, port_str = self.config['server_address'].split(':')
            port = int(port_str)

            self.conn = socket.create_connection((host, port))
        except Exception as e:
            logging.fatal(f"action: connect | result: fail | client_id: {self.config['id']} | error: {e}")
            exit(1)

    def start_client_loop(self):
        msg_id = 1
        end_time = time.time() + self.config['loop_lapse']
        
        while time.time() < end_time:
            self.create_client_socket()
            
            try:
                message = f"[CLIENT {self.config['id']}] Message N°{msg_id}\n"
                self.conn.sendall(message.encode())
                
                response = self.conn.recv(1024).decode()
                logging.info(f"action: receive_message | result: success | client_id: {self.config['id']} | msg: {response.strip()}")
            except Exception as e:
                logging.error(f"action: receive_message | result: fail | client_id: {self.config['id']} | error: {e}")
                return
            finally:
                self.conn.close()

            msg_id += 1
            time.sleep(self.config['loop_period'])
        
        logging.info(f"action: loop_finished | result: success | client_id: {self.config['id']}")
