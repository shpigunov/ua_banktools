from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

# Allow arbitrary types like IBAN in requests and responses
class Config:
    arbitrary_types_allowed = True


# Enums for the Privatbank Commercial API
class Currency(Enum):
    UAH = "UAH"
    USD = "USD"
    EUR = "EUR"


class ResponseStatus(Enum):
    Success = "SUCCESS"
    Error = "ERROR"


class ResponseType(Enum):
    Balances = "balances"
    Transactions = "transactions"


class TransactionType(Enum):
    Debit = "D"
    Credit = "C"


# Data classes for the Privatbank API
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
    type: ResponseType
    exist_next_page: bool
    balances: List[BalanceItem]


class TransactionItem(BaseModel):
    AUT_MY_CRF: str  # My Company Code/ITIN
    AUT_MY_MFO: str  # My Bank Code
    AUT_MY_ACC: str  # My Acct. IBAN
    AUT_MY_NAM: str  # My Name
    AUT_MY_MFO_NAME: str  # My Bank
    AUT_MY_MFO_CITY: str  # My Bank City
    AUT_CNTR_CRF: str  # Counterpart's Company Code/ITIN
    AUT_CNTR_MFO: str  # Conterpart Bank Code
    AUT_CNTR_ACC: str  # Counterpart's Acct. IBAN
    AUT_CNTR_NAM: str  # Counterpart Name
    AUT_CNTR_MFO_NAME: str  # Counterpart's Bank
    AUT_CNTR_MFO_CITY: str  # Counterpart's Bank City
    CCY: Currency  # Transaction Currency
    FL_REAL: str  # "Reality" of the transaction - {r, i}
    PR_PR: str  # Transaction status - p-проводиться, t-сторнирована, r-проведена, n-забракована
    DOC_TYP: str  # Document type, e.g. "m"
    NUM_DOC: str  # Document number
    DAT_KL: str  # Client Date
    DAT_OD: str  # Remittance Date
    OSND: str  # Payment Description
    SUM: float  # Transaction Amount
    SUM_E: float  # Transaction Amount
    REF: str  # Transaction Reference
    REFN: str  # Reference number inside transaction e.g. No.1
    TIM_P: str  # Tranaction Time (most likely Ukraine time)
    DATE_TIME_DAT_OD_TIM_P: str  # Transaction DateTime
    ID: str  # Transaction ID
    TRANTYPE: TransactionType  # Transaction Type {D|C} - debit/credit
    DLR: Optional[str]  # 3rd party transaction identifier
    TECHNICAL_TRANSACTION_ID: str


class TransactionsResponse(BaseModel):
    status: ResponseStatus
    type: ResponseType
    exist_next_page: bool
    transactions: List[TransactionItem]


class ErrorResponse(BaseModel):
    status: ResponseStatus
    code: int
    message: str
    requestId: str
