from datetime import date
from enum import IntEnum
from typing import Optional

import httpx

from ua_banktools.banks.base import BaseCorporateClient, build_session

from .types import HistoricalExchangeRatesResponse, PublicExchangeRate


class ExchangeRateType(IntEnum):
    CASH = 5
    NON_CASH = 11


class PBPublicClient:
    """Client for PrivatBank endpoints that do not require authentication."""

    BASE_URL = "https://api.privatbank.ua/"

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
        rate_type: ExchangeRateType = ExchangeRateType.CASH,
    ) -> list[PublicExchangeRate]:
        params: dict[str, str | int] = {
            "exchange": "",
            "coursid": int(rate_type),
        }
        r = self.session.get(
            self.base_url + "p24api/pubinfo",
            params=params,
            headers=self._headers,
        )
        r.raise_for_status()
        return [PublicExchangeRate(**item) for item in r.json()]

    def get_historical_exchange_rates(
        self,
        rate_date: date,
    ) -> HistoricalExchangeRatesResponse:
        r = self.session.get(
            self.base_url + "p24api/exchange_rates",
            params={"date": rate_date.strftime("%d.%m.%Y")},
            headers=self._headers,
        )
        r.raise_for_status()
        return HistoricalExchangeRatesResponse(**r.json())
