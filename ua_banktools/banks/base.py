from datetime import date
from schwifty import IBAN
import requests

from ua_banktools.core import IPN


class BasePersonalClient:
    def __init__(self):
        pass


class BaseCorporateClient:
    """This class serves as a blueprint for creating new clients for corporate
    banking APIs. It includes methods usually expected from such a client."""

    USER_AGENT = "ua_banktools API Client"
    BASE_URL = ""

    def __init__(self, token: str, client_id: str = "") -> None:
        self.token = token
        self.client_id = client_id
        self.session = requests.session()

    def get_balance(self, acct: IBAN, start_date: date, end_date: date):
        pass

    def get_transactions(self, acct: IBAN, start_date: date, end_date: date):
        pass

    def create_payment(
        self,
        payer_acct: IBAN,
        recipient_acct: IBAN,
        recipient_nceo: IPN | str,
        payee_name: str,
        amount: float,
        designation: str,
        document_number: str,
    ):
        pass
