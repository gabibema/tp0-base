import csv
import datetime
import logging
from typing import Generator

""" Bets storage location. """
STORAGE_FILEPATH = "./bets.csv"
""" Simulated winner number in the lottery contest. """
LOTTERY_WINNER_NUMBER = 7574


""" A lottery bet registry. """
class Bet:
    def __init__(self, agency: str, first_name: str, last_name: str, document: str, birthdate: str, number: str):
        """
        agency must be passed with integer format.
        birthdate must be passed with format: 'YYYY-MM-DD'.
        number must be passed with integer format.
        """
        self.agency = int(agency)
        self.first_name = first_name
        self.last_name = last_name
        self.document = document
        self.birthdate = datetime.date.fromisoformat(birthdate)
        self.number = int(number)
    
    def to_string(self):
        return f"{self.agency},{self.first_name},{self.last_name},{self.document},{self.birthdate},{self.number}"
    
    
    @staticmethod
    def from_string(bet_str: str):
        agency, first_name, last_name, document, birthdate, number = bet_str.split(',')
        return Bet(agency, first_name, last_name, document, birthdate, number)


""" Checks whether a bet won the prize or not. """
def has_won(bet: Bet) -> bool:
    return bet.number == LOTTERY_WINNER_NUMBER


"""
Persist the information of each bet in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""
def store_bets(bets: list[Bet]) -> None:
    with open(STORAGE_FILEPATH, 'a+') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
        for bet in bets:
            writer.writerow([bet.agency, bet.first_name, bet.last_name,
                             bet.document, bet.birthdate, bet.number])


"""
Loads the information all the bets in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""
def load_bets() -> Generator[Bet, None, None]:
    with open(STORAGE_FILEPATH, 'r') as file:
        reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            yield Bet(row[0], row[1], row[2], row[3], row[4], row[5])


def bets_from_string(bets_str: str) -> list[Bet]:
    return [Bet.from_string(bet_str) for bet_str in bets_str.split('\n') if bet_str]


def winners_to_string(winners: list[str]) -> str:
    """
    Creates a string including the document of each winner in the list with a separator ','.
    """
    if not len(winners):
        return '-'
    return ', '.join(winners)
    