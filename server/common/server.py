import multiprocessing
import socket
import logging
import signal
from datetime import datetime, timedelta
from common.utils import Bet, store_bets, bets_from_string, load_bets, has_won, bets_to_string
import common.message_protocol as mp

AGENCY_RAFFLE = 5

class Server:
    def __init__(self, port, listen_backlog, time_limit):
        self._pending_agencies = multiprocessing.Manager().dict()
        self._client_sockets = multiprocessing.Manager().list()
        self.keep_running = multiprocessing.Value('i', 1)
        self._lock_file = multiprocessing.Lock()
        self._lock_agencies = multiprocessing.Lock()
    
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

        self._processes = []  
        signal.signal(signal.SIGTERM, self.handle_sigterm)

    def handle_sigterm(self, signum, frame):
        logging.info("action: sigterm_received | result: initiating_shutdown")
        with self.keep_running.get_lock():
            self.keep_running.value = 0
            self._server_socket.close()

            for client_sock in self._client_sockets:
                logging.info(f'action: send_error | result: success | ip: {client_sock.getpeername()[0]}')
                mp.send_message(client_sock, "Server shutdown", mp.MESSAGE_FLAG['ERROR'])
                client_sock.close()
            for p in self._processes:
                p.join()  


    def run(self) -> bool:
        failed = False

        while self.keep_running.value and len(self._processes) < AGENCY_RAFFLE :
            client_sock = self.__accept_new_connection()
            if client_sock:
                client_process = multiprocessing.Process(target=self.__handle_client_connection, args=(client_sock,))
                client_process.start()
                self._processes.append(client_process)  

       
        while self.raffle_pending():
            pass

        for p in self._processes:
            p.join()

        return failed

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
        close_connection = True
        try:
            msg, flag = mp.receive_message(client_sock)
            addr = client_sock.getpeername()
            if flag == mp.MESSAGE_FLAG['BET']:
                close_connection = self.__handle_raffle_connection(client_sock, msg)
            elif flag == mp.MESSAGE_FLAG['ERROR']:
                logging.error(f'action: receive_message | result: error | ip: {addr[0]} | error: {msg}')
            else:
                logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')
                client_sock.send("{}\n".format(msg).encode('utf-8'), )
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            if close_connection:
                client_sock.close()
        return close_connection

    def __handle_raffle_connection(self, client_sock, msg):
        addr = client_sock.getpeername()
        flag = mp.MESSAGE_FLAG['BET']
        error = True

        with self._lock_agencies:
            self._client_sockets.append(client_sock)

        while flag == mp.MESSAGE_FLAG['BET'] and self.keep_running.value :
            bets = bets_from_string(msg)
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | bets_received: {len(bets)}')

            with self._lock_file:
                store_bets(bets)
                
            sent = mp.send_message(client_sock, f"{len(bets)}", mp.MESSAGE_FLAG['NORMAL'])
            if sent is None:
                return error
            
            msg, flag = mp.receive_message(client_sock)

        if flag == mp.MESSAGE_FLAG['ERROR']:
            logging.error(f'action: receive_message | result: error | ip: {addr[0]} | error: {msg}')
            return error
        elif flag == mp.MESSAGE_FLAG['FINAL'] and self.keep_running.value:
                logging.info(f'action: receive_message | result: success | ip: {addr[0]} | agency_waiting_raffle: {msg}')
                with self._lock_agencies:
                    self._pending_agencies[msg] = client_sock

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """
        with self.keep_running.get_lock():
            if not self.keep_running.value:
                return None
            try:
                logging.info('action: accept_connections | result: in_progress')
                c, addr = self._server_socket.accept()
                logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
                return c
            except OSError as e:
                logging.info('action: accept_connections | result: failed | error: {}'.format(e) + ' | server_keep_running: {}'.format(self.keep_running))
                return None
