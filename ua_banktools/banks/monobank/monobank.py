from datetime import datetime

import requests

from ua_banktools.banks.base import BasePersonalClient
from ua_banktools.banks.monobank.types import (
    ClientResponse,
    MonobankErrorResponse,
    Transaction,
)


class MonobankPersonalClient(BasePersonalClient):
    BASE_URL = "https://api.monobank.ua/"

    def __init__(self, token: str) -> None:
        self.token = token
        self.session = requests.session()

    def get_client_info(self):
        with self.session.get(
            self.BASE_URL + "personal/client-info",
            headers={
                "X-Token": self.token,
            },
        ) as r:
            if r.ok:
                return ClientResponse(**r.json())
            else:
                return MonobankErrorResponse(**r.json())

    def get_transactions(self, acct_id: str, start_date: datetime, end_date: datetime):
        """
        https://api.monobank.ua/personal/statement/{account}/{from}/{to}
        """

        with self.session.get(
            f"{self.BASE_URL}personal/statement/{acct_id}/{round(start_date.timestamp())}/{round(end_date.timestamp())}",
            headers={
                "X-Token": self.token,
            },
        ) as r:
            if r.ok:
                # return r.json()
                return [Transaction(**item) for item in r.json()]
            else:
                return MonobankErrorResponse(**r.json())
