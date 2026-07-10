from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, cast

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from schwifty import IBAN


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


class ResponseType(str, Enum):
    Balances = "balances"
    Transactions = "transactions"


class TransactionType(str, Enum):
    Debit = "D"
    Credit = "C"


class TransactionReality(str, Enum):
    REAL = "r"
    INTERNAL = "i"


class TransactionStatus(str, Enum):
    PENDING = "p"
    REVERSED = "t"
    COMPLETED = "r"
    REJECTED = "n"


class PaymentStatus(str, Enum):
    DONE = "DONE"
    IN_PROGRESS = "IN_PROGRESS"


# Data classes for the Privatbank API
class StatementParams(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    acct: Optional[IBAN] = Field(None, serialization_alias="acc")
    start_date: date = Field(serialization_alias="startDate")
    end_date: Optional[date] = Field(None, serialization_alias="endDate")
    follow_id: Optional[str] = Field(None, serialization_alias="followId")
    limit: Optional[int] = Field(None, ge=1, le=500)

    @field_serializer("acct")
    def serialize_account(self, value: Optional[IBAN]) -> Optional[str]:
        return str(value) if value is not None else None

    @field_serializer("start_date", "end_date")
    def serialize_date(self, value: Optional[date]) -> Optional[str]:
        return value.strftime("%d-%m-%Y") if value is not None else None

    def to_query_params(self) -> dict[str, str | int]:
        return cast(
            dict[str, str | int],
            self.model_dump(by_alias=True, exclude_none=True),
        )


class PublicExchangeRate(BaseModel):
    currency: str = Field(alias="ccy")
    base_currency: str = Field(alias="base_ccy")
    buy: Decimal
    sale: Decimal


class HistoricalExchangeRate(BaseModel):
    base_currency: str = Field(alias="baseCurrency")
    currency: str
    sale_rate_nbu: Decimal = Field(alias="saleRateNB")
    purchase_rate_nbu: Decimal = Field(alias="purchaseRateNB")
    sale_rate: Optional[Decimal] = Field(None, alias="saleRate")
    purchase_rate: Optional[Decimal] = Field(None, alias="purchaseRate")


class HistoricalExchangeRatesResponse(BaseModel):
    date: date
    bank: str
    base_currency: int = Field(alias="baseCurrency")
    base_currency_code: str = Field(alias="baseCurrencyLit")
    exchange_rates: List[HistoricalExchangeRate] = Field(alias="exchangeRate")

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, value: object) -> object:
        if isinstance(value, str):
            return datetime.strptime(value, "%d.%m.%Y").date()
        return value


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
    date_open_acc_reg: str  # datetime: `dd.mm.yyyy`
    date_open_acc_sys: str  # datetime: `dd.mm.yyyy`
    date_close_acc: str  # datetime: `dd.mm.yyyy`
    is_final_bal: bool


class BalanceResponse(BaseModel):
    status: ResponseStatus
    type: ResponseType
    exist_next_page: bool
    next_page_id: Optional[str] = None
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
    FL_REAL: TransactionReality
    PR_PR: TransactionStatus
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
    DLR: Optional[str] = None  # 3rd party transaction identifier
    TECHNICAL_TRANSACTION_ID: str
    UETR: Optional[str] = None
    ULTMT: Optional[str] = None
    PAYER_ULTMT_NCEO: Optional[str] = None
    PAYER_ULTMT_DOCUMENT: Optional[str] = None
    PAYER_ULTMT_NAME: Optional[str] = None
    PAYER_ULTMT_COUNTRY_CODE: Optional[str] = None
    RECIPIENT_ULTMT_NCEO: Optional[str] = None
    RECIPIENT_ULTMT_DOCUMENT: Optional[str] = None
    RECIPIENT_ULTMT_NAME: Optional[str] = None
    RECIPIENT_ULTMT_COUNTRY_CODE: Optional[str] = None
    STRUCT_CODE: Optional[str] = None
    STRUCT_TYPE: Optional[str] = None


class TransactionsResponse(BaseModel):
    status: ResponseStatus
    type: ResponseType
    exist_next_page: bool
    next_page_id: Optional[str] = None
    transactions: List[TransactionItem]


class TransactionSignLevel(BaseModel):
    class Config:
        validate_by_name = True

    first_sign_level: Optional[bool] = Field(None, alias="1_sign_level")
    second_sign_level: Optional[bool] = Field(None, alias="2_sign_level")


class PaymentCreateRequest(BaseModel):
    document_number: str
    payer_account: str
    recipient_account: str
    recipient_nceo: str
    payment_naming: str
    payment_amount: str
    payment_destination: str


class PaymentData(BaseModel):
    can_edit: str
    can_copy: Optional[str]
    document_number: str
    document_type: str
    id: str
    internal_type: str
    level_sign: TransactionSignLevel
    payer_account: str
    payer_bank_name: str
    payer_name: str
    payer_nceo: str
    payment_amount: float
    payment_ccy: Currency
    payment_date_unix: str  # Unix Timestamp
    payment_destination: str
    payment_naming: str
    payment_status: str  # Enum?
    payment_status_short: str
    recipient_account: str
    recipient_ifi_text: str
    recipient_nceo: str
    service_update_utime: str
    source: str
    tabs: List[str]
    user_id: str


class PaymentCreateSuccessResponse(BaseModel):
    payment_pack_ref: str
    payment_ref: str


class PrivatbankErrorResponse(BaseModel):
    status: ResponseStatus
    code: str
    message: str
    requestId: str
    serviceCode: Optional[str] = None
