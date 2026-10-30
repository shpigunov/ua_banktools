
import httpx
from pydantic import ValidationError

from ua_banktools.banks.base import build_session, parse_error
from ua_banktools.banks.monobank.types import (
    MonobankCurrencyRate,
    MonobankErrorResponse,
    MonobankSyncResponse,
)

#: Numeric codes ISO 4217 has withdrawn but Monobank still quotes:
#: BGN (975), HRK (191) and SLL (694).
WITHDRAWN_CURRENCY_CODES = {975, 191, 694}


class MonobankPublicClient:
    """Client for Monobank endpoints that do not require authentication."""

    BASE_URL = "https://api.monobank.ua/"

    def __init__(
        self,
        base_url: str = BASE_URL,
        session: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.session = build_session(session)

    def _url(self, path: str) -> str:
        return self.base_url + path.lstrip("/")

    def get_currency_rates(self):
        """Return Monobank exchange rates, cached upstream for five minutes."""
        r = self.session.get(self._url("bank/currency"))
        if r.is_success:
            return _parse_currency_rates(r.json())
        return parse_error(r, MonobankErrorResponse)

    def get_bank_sync(self):
        """Return the bank public key metadata and server time."""
        r = self.session.get(self._url("bank/sync"))
        if r.is_success:
            return MonobankSyncResponse(**r.json())
        return parse_error(r, MonobankErrorResponse)


def _parse_currency_rates(items: list[dict]) -> list[MonobankCurrencyRate]:
    """Parse the ``bank/currency`` rows into models.

    Monobank still quotes currencies that ISO 4217 has since withdrawn -- BGN
    (975, euro since 2026), HRK (191, euro since 2023), SLL (694, redenominated
    to SLE) -- and ``iso4217`` only knows the current table, so those rows fail
    validation with a ``ValueError`` naming the unknown code. Every other row in
    the response is still good.

    Those rows are skipped rather than mapped to a successor: a lev, kuna or old
    leone is not worth one euro or one new leone, so the rate would be wrong.
    Any other validation failure still raises -- that is real API drift.
    """
    rates = []
    for item in items:
        try:
            rates.append(MonobankCurrencyRate(**item))
        except ValidationError:
            if (
                item.get("currencyCodeA") in WITHDRAWN_CURRENCY_CODES
                or item.get("currencyCodeB") in WITHDRAWN_CURRENCY_CODES
            ):
                continue
            raise

    return rates
