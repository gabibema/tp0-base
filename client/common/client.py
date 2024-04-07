import socket
import logging
import signal
from configparser import ConfigParser
from typing import Generator
from common.utils import Bet, bets_to_string
import common.message_protocol as mp

class Client:
    def __init__(self, config):
        self.config = config
        self.conn = None
        signal.signal(signal.SIGTERM, self.handle_sigterm)

    def handle_sigterm(self, signum, frame):
        """Handler for the SIGTERM signal. It will be called when the process receives the signal."""
        logging.info(f"action: sigterm_received | result: initiating_shutdown | client_id: {self.config['id']}")
        raise SystemExit

    
    def make_bet(self, bet: Bet):
        """Sends a bet to the server."""
        sent = mp.send_message(self.conn, bet.to_string(), mp.MESSAGE_FLAG['BET'])
        if sent is None:
            raise SystemError
        
        logging.info(f"action: send_bet | result: success | client_id: {self.config['id']} | bet: {bet.to_string()}")

    def create_client_socket(self):
        
        try:
            host, port_str = self.config['server_address'].split(':')
            port = int(port_str)
            self.conn = socket.create_connection((host, port))
            
        except Exception as e:
            logging.fatal(f"action: connect | result: fail | client_id: {self.config['id']} | error: {e}")
            raise SystemError


    def send_final_message(self):
        """
        Sends the final message to the server
        """
        mp.send_message(self.conn, f"{self.config['id']}", mp.MESSAGE_FLAG['FINAL'])
        message, flag = mp.receive_message(self.conn)
        if flag == mp.MESSAGE_FLAG['ERROR']:
            logging.error(f"action: receive_message | result: error | client_id: {self.config['id']} | error: {message}")
            raise SystemError
        
        elif flag == mp.MESSAGE_FLAG['NORMAL']:
            logging.info(f"action: receive_message | result: success | client_id: {self.config['id']} | winners: {message}")

    def send_chunk(self, chunk: list[Bet]):
        """
        Sends a chunk of bets to the server
        """
        sent_size = mp.send_message(self.conn, bets_to_string(chunk), mp.MESSAGE_FLAG['BET'])
        if sent_size is None:
            raise SystemError
        
        logging.info(f"action: send_bets | result: success | client_id: {self.config['id']} | bets_sent: {len(chunk)} | size: {len(bets_to_string(chunk))}")
        msg, flag = mp.receive_message(self.conn)
        if flag == mp.MESSAGE_FLAG['ERROR']:
            logging.error(f"action: receive_message | result: error | client_id: {self.config['id']} | error: {msg}")
            raise SystemError
        else:
            logging.info(f"action: receive_message | result: success | client_id: {self.config['id']} | bets_received: {msg}")

    """
    Send bets to the server by chunks, returning False if an error occurs.
    """
    def send_bets(self, bets: Generator[Bet, None, None]) -> bool:
        chunk_size = int(self.config['batch_size'])
        chunk = []

        for bet in bets:
            chunk.append(bet)
            if len(chunk) < chunk_size:
                continue

            self.send_chunk(chunk)
            chunk = []
        
        if chunk:
            self.send_chunk(chunk)
            

    def start(self, bets: Generator[Bet, None, None]):
        """Sends a bets to the server by chunks"""
        
        try: 
            self.create_client_socket()
            if self.conn is None:
                raise SystemError
            
            self.send_bets(bets)
            self.send_final_message()

        except SystemError:
            logging.fatal(f"action: client_error | client_id: {self.config['id']}")
        
        except SystemExit:
            logging.info(f"action: client_shutdown | client_id: {self.config['id']}")
        
        finally:
            self.close()


    
    def close(self):
        """
        Closes the client
        """
        logging.info(f"action: client_closed | client_id: {self.config['id']}")
        if self.conn is None:
            return
        self.conn.close()
        