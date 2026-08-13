# Stub for `iso4217`, overriding the one shipped upstream.
#
# The upstream stub declares `class Currency(enum.Enum)` with its methods and
# properties but no members: the enum is built at runtime from table.xml via the
# functional Enum API, so a type checker -- which reads source, not runtime state
# -- sees every `Currency.USD` as an unknown attribute.
#
# A local stub shadows the installed one entirely, so everything below the member
# list is copied verbatim from upstream and must stay complete.
#
# Generated from iso4217 1.16.20260101. Do not edit by hand; run `just stubs`.

import datetime
import enum
from typing import (
    AbstractSet,
    Any,
    Callable,
    Generator,
    Mapping,
    Optional,
    Tuple,
    Union,
)
from xml.etree import ElementTree as etree


__published__: datetime.date = ...
__version__: str = ...
__version_info__: Tuple[int, int, int] = ...

raw_xml: etree.Element
raw_table: Mapping[str, Mapping[str, Union[AbstractSet[str], str, int]]] = ...


class Currency(enum.Enum):
    AFN: Currency
    EUR: Currency
    ALL: Currency
    DZD: Currency
    USD: Currency
    AOA: Currency
    XCD: Currency
    XAD: Currency
    ARS: Currency
    AMD: Currency
    AWG: Currency
    AUD: Currency
    AZN: Currency
    BSD: Currency
    BHD: Currency
    BDT: Currency
    BBD: Currency
    BYN: Currency
    BZD: Currency
    XOF: Currency
    BMD: Currency
    INR: Currency
    BTN: Currency
    BOB: Currency
    BOV: Currency
    BAM: Currency
    BWP: Currency
    NOK: Currency
    BRL: Currency
    BND: Currency
    BIF: Currency
    CVE: Currency
    KHR: Currency
    XAF: Currency
    CAD: Currency
    KYD: Currency
    CLP: Currency
    CLF: Currency
    CNY: Currency
    COP: Currency
    COU: Currency
    KMF: Currency
    CDF: Currency
    NZD: Currency
    CRC: Currency
    CUP: Currency
    XCG: Currency
    CZK: Currency
    DKK: Currency
    DJF: Currency
    DOP: Currency
    EGP: Currency
    SVC: Currency
    ERN: Currency
    SZL: Currency
    ETB: Currency
    FKP: Currency
    FJD: Currency
    XPF: Currency
    GMD: Currency
    GEL: Currency
    GHS: Currency
    GIP: Currency
    GTQ: Currency
    GBP: Currency
    GNF: Currency
    GYD: Currency
    HTG: Currency
    HNL: Currency
    HKD: Currency
    HUF: Currency
    ISK: Currency
    IDR: Currency
    XDR: Currency
    IRR: Currency
    IQD: Currency
    ILS: Currency
    JMD: Currency
    JPY: Currency
    JOD: Currency
    KZT: Currency
    KES: Currency
    KPW: Currency
    KRW: Currency
    KWD: Currency
    KGS: Currency
    LAK: Currency
    LBP: Currency
    LSL: Currency
    ZAR: Currency
    LRD: Currency
    LYD: Currency
    CHF: Currency
    MOP: Currency
    MKD: Currency
    MGA: Currency
    MWK: Currency
    MYR: Currency
    MVR: Currency
    MRU: Currency
    MUR: Currency
    XUA: Currency
    MXN: Currency
    MXV: Currency
    MDL: Currency
    MNT: Currency
    MAD: Currency
    MZN: Currency
    MMK: Currency
    NAD: Currency
    NPR: Currency
    NIO: Currency
    NGN: Currency
    OMR: Currency
    PKR: Currency
    PAB: Currency
    PGK: Currency
    PYG: Currency
    PEN: Currency
    PHP: Currency
    PLN: Currency
    QAR: Currency
    RON: Currency
    RUB: Currency
    RWF: Currency
    SHP: Currency
    WST: Currency
    STN: Currency
    SAR: Currency
    RSD: Currency
    SCR: Currency
    SLE: Currency
    SGD: Currency
    XSU: Currency
    SBD: Currency
    SOS: Currency
    SSP: Currency
    LKR: Currency
    SDG: Currency
    SRD: Currency
    SEK: Currency
    CHE: Currency
    CHW: Currency
    SYP: Currency
    TWD: Currency
    TJS: Currency
    TZS: Currency
    THB: Currency
    TOP: Currency
    TTD: Currency
    TND: Currency
    TRY: Currency
    TMT: Currency
    UGX: Currency
    UAH: Currency
    AED: Currency
    USN: Currency
    UYU: Currency
    UYI: Currency
    UYW: Currency
    UZS: Currency
    VUV: Currency
    VES: Currency
    VED: Currency
    VND: Currency
    YER: Currency
    ZMW: Currency
    ZWG: Currency
    XBA: Currency
    XBB: Currency
    XBC: Currency
    XBD: Currency
    XTS: Currency
    XXX: Currency
    XAU: Currency
    XPD: Currency
    XPT: Currency
    XAG: Currency

    @classmethod
    def _validate(cls, value: Any) -> "Currency": ...

    # Pydantic v1 support
    @classmethod
    def __get_validators__(cls) -> Generator[Callable[..., Any], None, None]: ...

    # Pydantic v2 support
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> Any: ...

    @property
    def code(self) -> str: ...

    @property
    def number(self) -> int: ...

    @property
    def currency_name(self) -> str: ...

    @property
    def country_names(self) -> AbstractSet[str]: ...

    @property
    def exponent(self) -> Optional[int]: ...
