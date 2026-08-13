from typing import Optional

import httpx

from ua_banktools.banks.base import build_session, parse_error
from ua_banktools.banks.monobank.types import (
    MonobankCurrencyRate,
    MonobankErrorResponse,
    MonobankSyncResponse,
)


class MonobankPublicClient:
    """Client for Monobank endpoints that do not require authentication."""

    BASE_URL = "https://api.monobank.ua/"

    def __init__(
        self,
        base_url: str = BASE_URL,
        session: Optional[httpx.Client] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.session = build_session(session)

    def _url(self, path: str) -> str:
        return self.base_url + path.lstrip("/")

    def get_currency_rates(self):
        """Return Monobank exchange rates, cached upstream for five minutes."""
        r = self.session.get(self._url("bank/currency"))
        if r.is_success:
            return [MonobankCurrencyRate(**item) for item in r.json()]
        return parse_error(r, MonobankErrorResponse)

    def get_bank_sync(self):
        """Return the bank public key metadata and server time."""
        r = self.session.get(self._url("bank/sync"))
        if r.is_success:
            return MonobankSyncResponse(**r.json())
        return parse_error(r, MonobankErrorResponse)
