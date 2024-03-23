import configparser
import os
import logging
from common.utils import Bet
from common.client import Client

def init_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    try:
        env_config = {
            'id': os.getenv('CLI_ID', default=config['DEFAULT'].get('ID')),
            'server_address': os.getenv('CLI_SERVER_ADDRESS', default=config['DEFAULT'].get('SERVER_ADDRESS')),
            'loop_lapse': float(os.getenv('CLI_LOOP_LAPSE', default=config['DEFAULT'].get('LOOP_LAPSE'))),
            'loop_period': float(os.getenv('CLI_LOOP_PERIOD', default=config['DEFAULT'].get('LOOP_PERIOD'))),
            'log_level': os.getenv('CLI_LOG_LEVEL', default=config['DEFAULT'].get('LOG_LEVEL')).upper(),
            'agency': os.getenv('AGENCIA', default=config['DEFAULT'].get('AGENCIA')),
            'first_name': os.getenv('NOMBRE', default=config['DEFAULT'].get('NOMBRE')),
            'last_name': os.getenv('APELLIDO', default=config['DEFAULT'].get('APELLIDO')),
            'document': os.getenv('DOCUMENTO', default=config['DEFAULT'].get('DOCUMENTO')),
            'birthdate': os.getenv('NACIMIENTO', default=config['DEFAULT'].get('NACIMIENTO')),
            'number': os.getenv('NUMERO', default=config['DEFAULT'].get('NUMERO'))
        }


    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting client".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting client".format(e))

    return env_config

def init_logger(log_level):
    level = getattr(logging, log_level, logging.INFO)
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def main():
    config = init_config()
    log_level = config['log_level'] 
    init_logger(log_level)

    logging.info(f"action: config | result: success | client_id: {config['id']} | server_address: {config['server_address']} | loop_lapse: {config['loop_lapse']} | loop_period: {config['loop_period']} | log_level: {config['log_level']}")

    
    client = Client(config)
    bet = Bet(config['agency'], config['first_name'], config['last_name'], config['document'], config['birthdate'], config['number'])
    client.start(bet)

if __name__ == "__main__":
    main()
