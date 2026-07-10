from datetime import datetime
from typing import Optional

import httpx

from ua_banktools.banks.base import BasePersonalClient
from ua_banktools.banks.monobank.types import (
    MonobankClientResponse,
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
        self.session = httpx.Client(follow_redirects=True, timeout=None)

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {"X-Token": self.token}

    def _url(self, path: str) -> str:
        return self.base_url + path.lstrip("/")

    def get_client_info(self):
        r = self.session.get(
            self._url("personal/client-info"),
            headers=self._auth_headers,
        )
        if r.is_success:
            return MonobankClientResponse(**r.json())
        return MonobankErrorResponse(**r.json())

    def set_webhook(self, webhook_url: str):
        """Set or remove the statement webhook (pass an empty URL to remove it)."""
        r = self.session.post(
            self._url("personal/webhook"),
            headers=self._auth_headers,
            json={"webHookUrl": webhook_url},
        )
        if r.is_success:
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

        r = self.session.get(
            self._url(path),
            headers=self._auth_headers,
        )
        if r.is_success:
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
