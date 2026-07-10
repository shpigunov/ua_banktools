from iso4217 import Currency


_CURRENCIES_BY_NUMBER = {currency.number: currency for currency in Currency}


def currency_from_numeric_code(value: object) -> Currency:
    """Return an ISO 4217 currency for a numeric code from a bank API."""
    if isinstance(value, Currency):
        return value

    try:
        numeric_code = int(value)  # type: ignore[arg-type]
        return _CURRENCIES_BY_NUMBER[numeric_code]
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Unknown ISO 4217 numeric currency code: {value}") from error
