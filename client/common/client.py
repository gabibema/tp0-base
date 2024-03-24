import socket
import time
import logging
import signal
from configparser import ConfigParser
from common.utils import Bet, bets_to_string, bets_from_string
import common.message_protocol as mp

class Client:
    def __init__(self, config):
        self.config = config
        self.conn = None
        self.keep_running = True  # This variable will be used to control the main loop
        signal.signal(signal.SIGTERM, self.handle_sigterm)

    def handle_sigterm(self, signum, frame):
        """Handler for the SIGTERM signal. It will be called when the process receives the signal."""
        logging.info(f"action: sigterm_received | result: initiating_shutdown | client_id: {self.config['id']}")
        self.keep_running = False  # Changes the value of the variable to False, so the client will stop.

    
    def make_bet(self, bet: Bet):
        """Sends a bet to the server."""
        mp.send_message(self.conn, bet.to_string(), mp.MESSAGE_FLAG['BET'])
        logging.info(f"action: send_bet | result: success | client_id: {self.config['id']} | bet: {bet.to_string()}")

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
        
        while time.time() < end_time and self.keep_running:
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
        self.conn.close()

    def get_server_response(self):
        """
        Receives the server response
        """
        try:
            response, flag = mp.receive_message(self.conn)
            logging.info(f"action: receive_message | result: success | client_id: {self.config['id']} | server_bets_received: {response.strip()}")
        except Exception as e:
            logging.error(f"action: receive_message | result: fail | client_id: {self.config['id']} | error: {e}")
            return None, None
        return response, flag


    def start(self, bets: list[Bet]):

        """Sends a bets to the server by chunks"""
        bets = list(bets)
        bets_split = [bets[i:i + self.config['batch_size']] for i in range(0, len(bets), self.config['batch_size'])]
        self.create_client_socket()
        for chunk in bets_split:
            if not self.keep_running:
                return
                
            mp.send_message(self.conn, bets_to_string(chunk), mp.MESSAGE_FLAG['BET'])
            logging.info(f"action: send_bets | result: success | client_id: {self.config['id']} | bets_sent: {len(chunk)} | size: {len(bets_to_string(chunk))}")
            msg, flag = self.get_server_response()
            if flag == mp.MESSAGE_FLAG['ERROR']:
                logging.error(f"action: receive_message | result: connection_timeout | client_id: {self.config['id']} | error: {msg}")
                return
        
        mp.send_message(self.conn, f"{self.config['id']}", mp.MESSAGE_FLAG['FINAL'])
        message,flag = mp.receive_message(self.conn)
        if flag == mp.MESSAGE_FLAG['ERROR']:
            logging.error(f"action: receive_message | result: connection_timeout | client_id: {self.config['id']} | error: {msg}")
        elif flag == mp.MESSAGE_FLAG['BET']:
            bets = bets_from_string(message)
            logging.info(f"action: receive_message | result: success | client_id: {self.config['id']} | winners_amount: {len(bets)}")
        


    
    def close(self):
        """
        Closes the client
        """
        logging.info(f"action: client_closed | client_id: {self.config['id']}")
        self.conn.close()
        