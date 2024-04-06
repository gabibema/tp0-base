import socket
import time
import logging
import signal
from configparser import ConfigParser
from typing import Generator
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


    """
    Send bets to the server by chunks, returning False if an error occurs.
    """
    def send_bets(self, bets: Generator[Bet, None, None]) -> bool:
        chunk_size = int(self.config['batch_size'])
        chunk = []

        for bet in bets:
            if not self.keep_running:
                return
            chunk.append(bet)
            if len(chunk) < chunk_size:
                continue

            sent_size = mp.send_message(self.conn, bets_to_string(chunk), mp.MESSAGE_FLAG['BET'])
            if sent_size is None:
                return False
            
            logging.info(f"action: send_bets | result: success | client_id: {self.config['id']} | bets_sent: {len(chunk)} | size: {len(bets_to_string(chunk))}")
            msg, flag = self.get_server_response()
            if flag == mp.MESSAGE_FLAG['ERROR']:
                logging.error(f"action: receive_message | result: error | client_id: {self.config['id']} | error: {msg}")
                return False
            
            chunk = []
        
        if chunk:
            sent_size = mp.send_message(self.conn, bets_to_string(chunk), mp.MESSAGE_FLAG['BET'])
            if sent_size is None:
                return False
            
            logging.info(f"action: send_bets | result: success | client_id: {self.config['id']} | bets_sent: {len(chunk)} | size: {len(bets_to_string(chunk))}")
            msg, flag = self.get_server_response()
            if flag == mp.MESSAGE_FLAG['ERROR']:
                logging.error(f"action: receive_message | result: error | client_id: {self.config['id']} | error: {msg}")
                return False
        
        return True
            

    def start(self, bets: Generator[Bet, None, None]):
        """Sends a bets to the server by chunks"""
        self.create_client_socket()
        if self.conn is None:
            return
        
        if not self.send_bets(bets):
            return
        
        mp.send_message(self.conn, f"{self.config['id']}", mp.MESSAGE_FLAG['FINAL'])
        message,flag = mp.receive_message(self.conn)
        if flag == mp.MESSAGE_FLAG['ERROR']:
            logging.error(f"action: receive_message | result: error | client_id: {self.config['id']} | error: {msg}")
        elif flag == mp.MESSAGE_FLAG['BET']:
            bets = bets_from_string(message)
            logging.info(f"action: receive_message | result: success | client_id: {self.config['id']} | winners_amount: {len(bets)}")
        


    
    def close(self):
        """
        Closes the client
        """
        if self.conn is None:
            return
        logging.info(f"action: client_closed | client_id: {self.config['id']}")
        self.conn.close()
        