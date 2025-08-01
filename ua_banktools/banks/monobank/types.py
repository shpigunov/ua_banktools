from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from schwifty import IBAN


class MonobankErrorResponse(BaseModel):

    model_config = ConfigDict(
        populate_by_name=True,
    )

    error_description: str = Field(..., alias="errorDescription")


class Account(BaseModel):

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


class ClientResponse(BaseModel):

    class Config:
        populate_by_name = True

    client_id: str = Field(..., alias="clientId")
    name: str
    web_hook_url: str = Field(..., alias="webHookUrl")
    permissions: str
    accounts: List[Account]


class Transaction(BaseModel):
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

    @field_validator("time", mode="before")
    def _parse_time(cls, v):
        return datetime.fromtimestamp(v)
