from datetime import datetime
from typing import Optional

import requests

from ua_banktools.banks.base import BasePersonalClient
from ua_banktools.banks.monobank.types import (
    MonobankSyncResponse,
    MonobankClientResponse,
    MonobankCurrencyRate,
    MonobankErrorResponse,
    MonobankTransaction,
    MonobankWebhookResponse,
)


class MonobankPersonalClient(BasePersonalClient):
    """
    Client for individual and PE (FOP) accounts.
    Reference: https://api.monobank.ua/docs/index.html
    """

    BASE_URL = "https://api.monobank.ua/"

    def __init__(self, token: str, base_url: str = BASE_URL) -> None:
        self.token = token
        self.base_url = base_url.rstrip("/") + "/"
        self.session = requests.session()

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {"X-Token": self.token}

    def _url(self, path: str) -> str:
        return self.base_url + path.lstrip("/")

    def get_currency_rates(self):
        """Return Monobank exchange rates, cached upstream for five minutes."""
        with self.session.get(self._url("bank/currency")) as r:
            if r.ok:
                return [MonobankCurrencyRate(**item) for item in r.json()]
            return MonobankErrorResponse(**r.json())

    def get_bank_sync(self):
        """Return the bank public key metadata and server time."""
        with self.session.get(self._url("bank/sync")) as r:
            if r.ok:
                return MonobankSyncResponse(**r.json())
            return MonobankErrorResponse(**r.json())

    def get_client_info(self):
        with self.session.get(
            self._url("personal/client-info"),
            headers=self._auth_headers,
        ) as r:
            if r.ok:
                return MonobankClientResponse(**r.json())
            return MonobankErrorResponse(**r.json())

    def set_webhook(self, webhook_url: str):
        """Set or remove the statement webhook (pass an empty URL to remove it)."""
        with self.session.post(
            self._url("personal/webhook"),
            headers=self._auth_headers,
            json={"webHookUrl": webhook_url},
        ) as r:
            if r.ok:
                return MonobankWebhookResponse(**r.json())
            return MonobankErrorResponse(**r.json())

    def get_statement(
        self,
        acct_id: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
    ):
        path = f"personal/statement/{acct_id}/{round(start_date.timestamp())}"
        if end_date is not None:
            path += f"/{round(end_date.timestamp())}"

        with self.session.get(
            self._url(path),
            headers=self._auth_headers,
        ) as r:
            if r.ok:
                return [MonobankTransaction(**item) for item in r.json()]
            return MonobankErrorResponse(**r.json())

    def get_transactions(
        self,
        acct_id: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
    ):
        """Backward-compatible alias for :meth:`get_statement`."""
        return self.get_statement(acct_id, start_date, end_date)
