from enum import Enum
from typing import List

from pydantic import BaseModel

# Allow arbitrary types like IBAN in requests and responses
class Config:
    arbitrary_types_allowed = True


class Currency(Enum):
    UAH = "UAH"
    USD = "USD"
    EUR = "EUR"


# Data classes for the Privatbank API
class ResponseStatus(Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class BalanceItem(BaseModel):
    acc: str
    currency: Currency
    balanceIn: float
    balanceInEq: float
    balanceOut: float
    balanceOutEq: float
    turnoverDebt: float
    turnoverDebtEq: float
    turnoverCred: float
    turnoverCredEq: float
    bgfIBrnm: str
    brnm: str
    dpd: str  # datetime: `dd.mm.yyyy hh:mm:ss`
    nameACC: str
    state: str
    atp: str
    flmn: str
    date_open_acc_reg: str  # datetime: `dd.mm.yyyy hh:mm:ss`
    date_open_acc_sys: str  # datetime: `dd.mm.yyyy hh:mm:ss`
    date_close_acc: str  # datetime: `dd.mm.yyyy hh:mm:ss`
    is_final_bal: bool


class BalanceResponse(BaseModel):
    status: ResponseStatus
    type: str
    exist_next_page: bool
    balances: List[BalanceItem]


class ErrorResponse(BaseModel):
    status: ResponseStatus
    code: int
    message: str
    requestId: str
