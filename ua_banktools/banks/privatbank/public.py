from datetime import date
from enum import IntEnum

import requests

from ua_banktools.banks.base import BaseCorporateClient

from .types import HistoricalExchangeRatesResponse, PublicExchangeRate


class ExchangeRateType(IntEnum):
    CASH = 5
    NON_CASH = 11


class PBPublicClient:
    """Client for PrivatBank endpoints that do not require authentication."""

    BASE_URL = "https://api.privatbank.ua/"

    def __init__(self, base_url: str = BASE_URL) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.session = requests.session()
        self.session.headers.update({"User-Agent": BaseCorporateClient.USER_AGENT})

    def get_exchange_rates(
        self,
        rate_type: ExchangeRateType = ExchangeRateType.CASH,
    ) -> list[PublicExchangeRate]:
        params: dict[str, str | int] = {
            "exchange": "",
            "coursid": int(rate_type),
        }
        with self.session.get(
            self.base_url + "p24api/pubinfo",
            params=params,
        ) as r:
            r.raise_for_status()
            return [PublicExchangeRate(**item) for item in r.json()]

    def get_historical_exchange_rates(
        self,
        rate_date: date,
    ) -> HistoricalExchangeRatesResponse:
        with self.session.get(
            self.base_url + "p24api/exchange_rates",
            params={"date": rate_date.strftime("%d.%m.%Y")},
        ) as r:
            r.raise_for_status()
            return HistoricalExchangeRatesResponse(**r.json())
