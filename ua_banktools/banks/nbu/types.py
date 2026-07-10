from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal, Optional, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class NBUSortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class NBUExchangeRatesRequest(BaseModel):
    """Query parameters for the NBU exchange-rate directory endpoint."""

    rate_date: Optional[date] = None
    currency: Optional[str] = Field(default=None, pattern=r"^[A-Z]{3}$")

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: object) -> object:
        if isinstance(value, str):
            return value.upper()
        return value

    def to_query_params(self) -> dict[str, str]:
        params = {"json": ""}
        if self.rate_date is not None:
            params["date"] = self.rate_date.strftime("%Y%m%d")
        if self.currency is not None:
            params["valcode"] = self.currency
        return params


class NBUExchangeRateHistoryRequest(BaseModel):
    """Query parameters for a currency or metal exchange-rate history."""

    currency: str = Field(pattern=r"^[A-Z]{3}$")
    start_date: date
    end_date: date
    sort: Literal["exchangedate"] = "exchangedate"
    order: NBUSortOrder = NBUSortOrder.ASC

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: object) -> object:
        if isinstance(value, str):
            return value.upper()
        return value

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.start_date > self.end_date:
            raise ValueError("start_date must not be after end_date")
        return self

    def to_query_params(self) -> dict[str, str]:
        return cast(
            dict[str, str],
            {
                "json": "",
                "start": self.start_date.strftime("%Y%m%d"),
                "end": self.end_date.strftime("%Y%m%d"),
                "valcode": self.currency,
                "sort": self.sort,
                "order": self.order.value,
            },
        )


class NBUExchangeRate(BaseModel):
    """An official hryvnia exchange rate or investment-metal price."""

    model_config = ConfigDict(populate_by_name=True)

    numeric_code: int = Field(alias="r030")
    name: str = Field(alias="txt")
    rate: Decimal
    currency: str = Field(alias="cc")
    exchange_date: date = Field(alias="exchangedate")
    special: Optional[Literal["Y", "N"]] = None

    @field_validator("exchange_date", mode="before")
    @classmethod
    def parse_exchange_date(cls, value: object) -> object:
        if isinstance(value, str):
            return datetime.strptime(value, "%d.%m.%Y").date()
        return value


class NBUExchangeRateHistory(NBUExchangeRate):
    """A detailed exchange-rate entry returned by the history endpoint."""

    english_name: str = Field(alias="enname")
    units: int
    rate_per_unit: Decimal
    group: str
    calculation_date: date = Field(alias="calcdate")

    @field_validator("calculation_date", mode="before")
    @classmethod
    def parse_calculation_date(cls, value: object) -> object:
        if isinstance(value, str):
            return datetime.strptime(value, "%d.%m.%Y").date()
        return value
