import datetime
import csv

""" Bets storage location. """
STORAGE_FILEPATH = "./bets.csv"

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


"""
Loads the information all the bets in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""
def load_bets(agency:str) -> list[Bet]:
    with open(STORAGE_FILEPATH, 'r') as file:
        reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            yield Bet(agency,row[0], row[1], row[2], row[3], row[4])


"""
Converts a list of bets to a string representation.
"""
def bets_to_string(bets: list[Bet]) -> str:
    return "".join([f"{bet.to_string()}\n" for bet in bets])