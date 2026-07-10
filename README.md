# ua-banktools

A collection of Python tools and APIs for interacting with Ukrainian banks

## Banks currently supported

- PrivatBank (legal entities only)
- monobank (public and personal)
- National Bank of Ukraine (public exchange rates)

## Features

- Object-oriented as much as possible, with IBANs validated by `schwifty`, timestamps automatically parsed into `datetime` objects, and known categorical values parsed into `enum`s.
- Multiple banks in one package.

## Monobank Open API

```python
from datetime import datetime

from ua_banktools.banks import MonobankPersonalClient, MonobankPublicClient

public_client = MonobankPublicClient()
client = MonobankPersonalClient("your-token")
public_client.get_currency_rates()
public_client.get_bank_sync()
client.get_client_info()
client.set_webhook("https://example.com/monobank-webhook")
client.get_statement("account-id", datetime(2026, 1, 1))
```

The default base URL is `https://api.monobank.ua/`. It can be overridden for an
egress gateway; include any route prefix required by the gateway:

```python
client = MonobankPersonalClient(
    "your-token",
    base_url="https://mono-egress.example.com/mono/",
)
```

### Tests

Run the mocked Monobank tests with `just test mono`, or all available tests with
`just test`. An explicitly opted-in, read-only smoke test is also available:

```bash
# .env (do not commit this file!)
MONO_TOKEN=your-personal-token

just test mono-live
```

The live test makes one client-info request and one statement request for the
most recent hour. It is skipped by normal test runs and never changes webhook
configuration.

## PrivatBank Autoclient API

```python
from datetime import date
from decimal import Decimal

from schwifty import IBAN

from ua_banktools.banks import ExchangeRateType, PBCorporateClient, PBPublicClient

client = PBCorporateClient("your-token")
public_client = PBPublicClient()
account = IBAN("UA943052990000026100050001037")

cash_rates = public_client.get_exchange_rates()
non_cash_rates = public_client.get_exchange_rates(ExchangeRateType.NON_CASH)
historical_rates = public_client.get_historical_exchange_rates(date(2026, 7, 1))
balances = client.get_balance(account, date(2026, 7, 1), limit=100)
transactions = client.get_transactions(
    account,
    date(2026, 7, 1),
    date(2026, 7, 10),
)
payment = client.create_payment(
    payer_acct=account,
    recipient_acct=IBAN("UA323052990000026000000000000"),
    recipient_nceo="14360570",
    payee_name="Counterparty",
    amount=Decimal("1.20"),
    designation="Payment purpose",
    document_number="42",
)

# Delete a created payment while it is still eligible for deletion.
client.delete_payment(payment.payment_ref)
```

Pass `None` as the statement account to request all active accounts. If
`exist_next_page` is true, pass the response's `next_page_id` back as
`follow_id`. The optional `client_id` constructor argument remains available
for legacy integrations.

Run the mocked PrivatBank tests with `just test pb`.

## National Bank of Ukraine Open Data API

```python
from datetime import date

from ua_banktools.banks import NBUPublicClient, NBUSortOrder

client = NBUPublicClient()

current_rates = client.get_exchange_rates()
eur_rate = client.get_exchange_rate("EUR", date(2026, 7, 1))
usd_history = client.get_exchange_rate_history(
    "USD",
    date(2026, 7, 1),
    date(2026, 7, 10),
    order=NBUSortOrder.DESC,
)
```

Currency and investment-metal codes are case-insensitive and normalized to
uppercase. Rates are parsed as `Decimal` values and NBU dates as `date` values.
The API is public and does not require authentication. Run its mocked tests with
`just test nbu`.
