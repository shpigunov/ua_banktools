from datetime import date
from typing import Optional

import httpx
from iso4217 import Currency

from ua_banktools.banks.base import BaseCorporateClient

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

    def __init__(self, base_url: str = BASE_URL) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.session = httpx.Client(
            headers={"User-Agent": BaseCorporateClient.USER_AGENT},
            follow_redirects=True,
            timeout=None,
        )

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
            currency=currency,
        ).to_query_params()
        response = self.session.get(
            self.base_url + "NBUStatService/v1/statdirectory/exchange",
            params=params,
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
            currency=currency,
            start_date=start_date,
            end_date=end_date,
            order=order,
        ).to_query_params()
        response = self.session.get(
            self.base_url + "NBU_Exchange/exchange_site",
            params=params,
        )
        response.raise_for_status()
        return [NBUExchangeRateHistory(**item) for item in response.json()]
