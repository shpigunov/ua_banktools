from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from schwifty import IBAN


class MonobankErrorResponse(BaseModel):

    model_config = ConfigDict(
        populate_by_name=True,
    )

    error_description: str = Field(..., alias="errorDescription")


class MonobankCurrencyRate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    currency_code_a: int = Field(..., alias="currencyCodeA")
    currency_code_b: int = Field(..., alias="currencyCodeB")
    date: datetime
    rate_sell: Optional[float] = Field(None, alias="rateSell")
    rate_buy: Optional[float] = Field(None, alias="rateBuy")
    rate_cross: Optional[float] = Field(None, alias="rateCross")

    @field_validator("date", mode="before")
    @classmethod
    def _parse_date(cls, value):
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        return value


class MonobankSyncResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    server_key_id: str = Field(..., alias="serverKeyId")
    server_pub_key: str = Field(..., alias="serverPubKey")
    server_time_msec: int = Field(..., alias="serverTimeMsec")


class MonobankWebhookResponse(BaseModel):
    status: str


class MonobankAccount(BaseModel):

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
    )

    id: str
    send_id: str = Field(..., alias="sendId")
    currency_code: int = Field(..., alias="currencyCode")
    cashback_type: Optional[str] = Field(None, alias="cashbackType")
    balance: int
    credit_limit: int = Field(..., alias="creditLimit")
    masked_pan: List[str] = Field(default_factory=list, alias="maskedPan")
    type: str
    iban: IBAN

    @field_validator("iban", mode="before")
    def _parse_iban(cls, v):
        # if we got a string, turn it into an IBAN object
        if isinstance(v, str):
            return IBAN(v)  # raises if invalid
        return v  # already an IBAN


class Jar(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    send_id: str = Field(..., alias="sendId")
    title: str
    description: str
    currency_code: int = Field(..., alias="currencyCode")
    balance: int
    goal: Optional[int] = None


class MonobankManagedAccount(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
    )

    id: str
    balance: int
    credit_limit: int = Field(..., alias="creditLimit")
    type: str
    currency_code: int = Field(..., alias="currencyCode")
    iban: IBAN

    @field_validator("iban", mode="before")
    @classmethod
    def _parse_iban(cls, value):
        if isinstance(value, str):
            return IBAN(value)
        return value


class MonobankManagedClient(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    client_id: str = Field(..., alias="clientId")
    tin: int
    name: str
    accounts: List[MonobankManagedAccount]


class MonobankClientResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    client_id: str = Field(..., alias="clientId")
    name: str
    web_hook_url: str = Field(..., alias="webHookUrl")
    permissions: str
    accounts: List[MonobankAccount]
    jars: List[Jar] = Field(default_factory=list)
    managed_clients: List[MonobankManagedClient] = Field(
        default_factory=list,
        alias="managedClients",
    )


class MonobankTransaction(BaseModel):
    # allow aliases (camelCase) → attributes (snake_case)
    model_config = ConfigDict(populate_by_name=True)

    id: str
    time: datetime
    description: str
    comment: Optional[str] = None
    mcc: int
    original_mcc: int = Field(..., alias="originalMcc")
    amount: int
    operation_amount: int = Field(..., alias="operationAmount")
    currency_code: int = Field(..., alias="currencyCode")
    commission_rate: int = Field(..., alias="commissionRate")
    cashback_amount: int = Field(..., alias="cashbackAmount")
    balance: int
    hold: bool
    receipt_id: Optional[str] = Field(None, alias="receiptId")
    invoice_id: Optional[str] = Field(None, alias="invoiceId")
    counter_edrpou: Optional[str] = Field(None, alias="counterEdrpou")
    counter_iban: Optional[str] = Field(None, alias="counterIban")
    counter_name: Optional[str] = Field(None, alias="counterName")

    @field_validator("time", mode="before")
    @classmethod
    def _parse_time(cls, value):
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        return value
