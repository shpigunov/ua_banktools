from datetime import date
from typing import Optional

import httpx
from iso4217 import Currency

from ua_banktools.banks.base import BaseCorporateClient, build_session
from ua_banktools.core import currency_from_numeric_code

from .types import (
    NBUExchangeRate,
    NBUExchangeRateHistory,
    NBUExchangeRateHistoryRequest,
    NBUExchangeRatesRequest,
    NBUSortOrder,
)


class NBUPublicClient:
    """Client for the National Bank of Ukraine public exchange-rate API."""

    BASE_URL = "https://bank.gov.ua/"

    def __init__(
        self,
        base_url: str = BASE_URL,
        session: Optional[httpx.Client] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.session = build_session(session)

    @property
    def _headers(self) -> dict[str, str]:
        return {"User-Agent": BaseCorporateClient.USER_AGENT}

    def get_exchange_rates(
        self,
        rate_date: Optional[date] = None,
        *,
        currency: Optional[Currency | str] = None,
    ) -> list[NBUExchangeRate]:
        """Return official rates for the current day or a specified date.

        Pass a three-letter currency or metal code to limit the response to it.
        """
        params = NBUExchangeRatesRequest(
            rate_date=rate_date,
            # Normalize here rather than in the model, so the public API can keep
            # accepting a plain "EUR" while the request stays strictly typed.
            currency=None if currency is None else currency_from_numeric_code(currency),
        ).to_query_params()
        response = self.session.get(
            self.base_url + "NBUStatService/v1/statdirectory/exchange",
            params=params,
            headers=self._headers,
        )
        response.raise_for_status()
        return [NBUExchangeRate(**item) for item in response.json()]

    def get_exchange_rate(
        self,
        currency: Currency | str,
        rate_date: Optional[date] = None,
    ) -> Optional[NBUExchangeRate]:
        """Return one official currency/metal rate, or ``None`` if unavailable."""
        rates = self.get_exchange_rates(rate_date, currency=currency)
        return rates[0] if rates else None

    def get_exchange_rate_history(
        self,
        currency: Currency | str,
        start_date: date,
        end_date: date,
        *,
        order: NBUSortOrder = NBUSortOrder.ASC,
    ) -> list[NBUExchangeRateHistory]:
        """Return official rates for one currency or metal over a date range."""
        params = NBUExchangeRateHistoryRequest(
            currency=currency_from_numeric_code(currency),
            start_date=start_date,
            end_date=end_date,
            order=order,
        ).to_query_params()
        response = self.session.get(
            self.base_url + "NBU_Exchange/exchange_site",
            params=params,
            headers=self._headers,
        )
        response.raise_for_status()
        return [NBUExchangeRateHistory(**item) for item in response.json()]
