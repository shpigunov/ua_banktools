from iso4217 import Currency


_CURRENCIES_BY_NUMBER = {currency.number: currency for currency in Currency}
_CURRENCIES_BY_CODE = {currency.code: currency for currency in Currency}


def currency_from_numeric_code(value: object) -> Currency:
    """Return an ISO 4217 currency for a code from a bank API.

    Banks send the numeric code, which is the point of this function. Alpha-3 is
    also accepted so that a model dumped to JSON -- where currencies serialize as
    ``"UAH"`` -- validates back into the same model.
    """
    if isinstance(value, Currency):
        return value

    if isinstance(value, str):
        code = value.strip().upper()
        if code in _CURRENCIES_BY_CODE:
            return _CURRENCIES_BY_CODE[code]

    if isinstance(value, (int, float, str)):
        try:
            return _CURRENCIES_BY_NUMBER[int(value)]
        except (KeyError, ValueError) as error:
            raise ValueError(f"Unknown ISO 4217 currency code: {value}") from error

    raise ValueError(f"Unknown ISO 4217 currency code: {value}")
