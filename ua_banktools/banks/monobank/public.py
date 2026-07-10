import httpx

from ua_banktools.banks.monobank.types import (
    MonobankCurrencyRate,
    MonobankErrorResponse,
    MonobankSyncResponse,
)


class MonobankPublicClient:
    """Client for Monobank endpoints that do not require authentication."""

    BASE_URL = "https://api.monobank.ua/"

    def __init__(self, base_url: str = BASE_URL) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.session = httpx.Client(follow_redirects=True, timeout=None)

    def _url(self, path: str) -> str:
        return self.base_url + path.lstrip("/")

    def get_currency_rates(self):
        """Return Monobank exchange rates, cached upstream for five minutes."""
        r = self.session.get(self._url("bank/currency"))
        if r.is_success:
            return [MonobankCurrencyRate(**item) for item in r.json()]
        return MonobankErrorResponse(**r.json())

    def get_bank_sync(self):
        """Return the bank public key metadata and server time."""
        r = self.session.get(self._url("bank/sync"))
        if r.is_success:
            return MonobankSyncResponse(**r.json())
        return MonobankErrorResponse(**r.json())
