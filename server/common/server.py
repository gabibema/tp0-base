import socket
import logging
import signal
from common.utils import Bet, store_bets, bets_from_string, load_bets, has_won, bets_to_string
import common.message_protocol as mp

AGENCY_RAFFLE = 5

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._pending_agencies = {}
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.keep_running = True
        
        signal.signal(signal.SIGTERM, self.handle_sigterm)


    def handle_sigterm(self, signum, frame):
        """
        Handler for the SIGTERM signal. It will be called when the process receives the signal.
        """
        logging.info(f"action: sigterm_received | result: initiating_shutdown")
        self.keep_running = False  
        self._server_socket.close()


    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        while self.keep_running and self.raffle_pending():
            client_sock = self.__accept_new_connection()
            if client_sock:
                self.__handle_client_connection(client_sock)

    def raffle(self):
        """
        Raffle agencies

        Function raffles agencies that are pending to be raffled
        """
        bets = load_bets()
        winners = {agency: [] for agency in self._pending_agencies.keys()}
        for bet in bets:
            if has_won(bet):
                winners[str(bet.agency)].append(bet)

        for agency, client_sock in self._pending_agencies.items():
            logging.info(f'action: raffle | result: success | agency: {agency} | winners: {len(winners[agency])}')
            if winners[agency]:
                mp.send_message(client_sock, bets_to_string(winners[agency]), mp.MESSAGE_FLAG['BET'])
            client_sock.close()

    def raffle_pending(self):
        """
        Check if there are pending agencies to raffle

        Function returns True if there are pending agencies to raffle
        and False otherwise
        """
        return len(self._pending_agencies) < AGENCY_RAFFLE
    
    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and optionally closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed unless it's a 'FINAL' message, 
        in which case it is added to the pending list.
        """
        close_socket = True
        try:
            msg, flag = mp.receive_message(client_sock)
            addr = client_sock.getpeername()
            if flag == mp.MESSAGE_FLAG['BET']:
                bets = bets_from_string(msg)
                logging.info(f'action: receive_message | result: success | ip: {addr[0]} | bets_received: {len(bets)}')
                mp.send_message(client_sock, f"{len(bets)}", mp.MESSAGE_FLAG['NORMAL'])
                store_bets(bets)

            elif flag == mp.MESSAGE_FLAG['FINAL']:
                logging.info(f'action: receive_message | result: success | ip: {addr[0]} | agency_waiting_raffle: {msg}')
                self._pending_agencies[msg] = client_sock
                close_socket = False
                
            else: 
                logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')
                client_sock.send("{}\n".format(msg).encode('utf-8'), )
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            if close_socket:
                client_sock.close()


    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """
        if not self.keep_running:
            return None

        try:
            logging.info('action: accept_connections | result: in_progress')
            c, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            return c
        except OSError as e:
            logging.info('action: accept_connections | result: failed | error: {}'.format(e) + ' | server_keep_running: {}'.format(self.keep_running))
            return None
