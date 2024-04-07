import multiprocessing
import socket
import logging
import signal
from datetime import datetime, timedelta
from common.utils import Bet, store_bets, bets_from_string, load_bets, has_won, bets_to_string
import common.message_protocol as mp

AGENCY_RAFFLE = 5

class Server:
    def __init__(self, port, listen_backlog):
        self._pending_agencies = multiprocessing.Manager().dict()
        self._client_sockets = multiprocessing.Manager().list()
        self._lock_file = multiprocessing.Lock()

        self.raffle_pending_event = multiprocessing.Event()
        self.raffle_pending_event.set()

        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

        self._processes = []  
        signal.signal(signal.SIGTERM, self.handle_sigterm)

    def handle_sigterm(self, signum, frame):
        raise SystemExit


    def run(self):
        try: 
            self.__handle_connections()
            self.raffle_pending_event.wait()
            self.__join_processes()
            self.__raffle()

        except SystemError:
            logging.error('action: run | result: error | message: system error')

        except SystemExit:
            logging.info('action: run | result: success | message: received SIGTERM signal')

        finally:
            self.__cleanup()
            logging.info('action: run | result: success | message: server closed')


    def __handle_connections(self):
        while len(self._processes) < AGENCY_RAFFLE :
            client_sock = self.__accept_new_connection()
            if client_sock:
                client_process = multiprocessing.Process(target=self.__handle_client_connection, args=(client_sock,))
                client_process.start()
                self._processes.append(client_process)  


    def __raffle(self):
        """
        Raffle agencies

        Function raffles agencies that are pending to be raffled
        """
        bets = load_bets()
        winners = {agency: [] for agency in self._pending_agencies.keys()}
        logging.info(f'action: raffle | result: success | agencies: {len(self._pending_agencies)}')

        for bet in bets:
            if has_won(bet):
                winners[str(bet.agency)].append(bet)

        for agency in winners.keys():
            logging.info(f'action: raffle | result: success | agency: {agency} | winners: {len(winners[agency])}')
            client_sock = self._pending_agencies[agency]

            send = mp.send_message(client_sock, bets_to_string(winners[agency]), mp.MESSAGE_FLAG['BET'])
            if send is None:
                logging.error(f'action: raffle | result: error | agency: {agency} | error: sending message')
                continue

    def __join_processes(self):
        """
        Close processes

        Function closes all processes
        """
        for process in self._processes:
            process.join()

    def __cleanup(self):
        """
        Cleanup function

        Function closes the server socket and all client sockets
        """
        self._server_socket.close()
        for client_sock in self._client_sockets:
            client_sock.close()

        for process in self._processes:
            if process.is_alive():
                process.join()

    def __handle_client_connection(self, client_sock):
        try:
            msg, flag = mp.receive_message(client_sock)
            addr = client_sock.getpeername()
            if flag == mp.MESSAGE_FLAG['BET']:
                self.__handle_raffle_connection(client_sock, msg)
            else:
                logging.error(f'action: receive_message | result: error | ip: {addr[0]} | error: invalid message flag')
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")



    def __handle_raffle_connection(self, client_sock, msg):
        addr = client_sock.getpeername()
        flag = mp.MESSAGE_FLAG['BET']

        self._client_sockets.append(client_sock)

        while flag == mp.MESSAGE_FLAG['BET']:
            bets = bets_from_string(msg)
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | bets_received: {len(bets)}')

            with self._lock_file:
                store_bets(bets)
                
            sent = mp.send_message(client_sock, f"{len(bets)}", mp.MESSAGE_FLAG['NORMAL'])
            if sent is None:
                raise SystemError
            
            msg, flag = mp.receive_message(client_sock) #if flag is ERROR, SystemError is raised after the loop

        if flag == mp.MESSAGE_FLAG['ERROR']:
            logging.error(f'action: receive_message | result: error | ip: {addr[0]} | error: {msg}')
            raise SystemError
        elif flag == mp.MESSAGE_FLAG['FINAL']:
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | agency_waiting_raffle: {msg}')
            self.__add_pending_agency(msg, client_sock)


    def __add_pending_agency(self, agency, client_sock):
        self._pending_agencies[agency] = client_sock
        logging.info(f'action: add_pending_agency | result: success | agency: {agency}')
        
        self.__check_raffles()

    def __check_raffles(self):
        if len(self._pending_agencies.keys()) != AGENCY_RAFFLE:
            return

        logging.info('action: raffle_pending | result: success | all agencies are ready to raffle')
        self.raffle_pending_event.clear()


    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """
        try:
            logging.info('action: accept_connections | result: in_progress')
            c, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            return c
        except OSError as e:
            logging.info('action: accept_connections | result: failed | error: {}'.format(e))
            return None
