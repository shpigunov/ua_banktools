# ua-banktools

A collection of Python tools and APIs for interacting with Ukrainian banks

## Banks currently supported

- PrivatBank (legal entities only)
- monobank (public and personal)
- National Bank of Ukraine (public exchange rates)

## Features

- Object-oriented as much as possible, with IBANs validated by `schwifty`, timestamps automatically parsed into `datetime` objects, and known categorical values parsed into `enum`s.
- Multiple banks in one package.
- Every response model survives `model_dump_json()`, so results can be cached or forwarded without re-flattening.
- Statement assembly is built in: PrivatBank pagination and Monobank's 31-day window limit are handled for you.

## Shared client behaviour

Every client accepts an optional `session`. Pass your own `httpx.Client` to set a
different timeout, add headers, install event hooks, or route through a proxy:

```python
import httpx

from ua_banktools.banks import MonobankPersonalClient

session = httpx.Client(
    headers={"Authorization": "Bearer proxy-secret"},
    timeout=httpx.Timeout(90.0),
)
client = MonobankPersonalClient("your-token", base_url="https://gateway.example/mono/", session=session)
```

Credentials are sent per request rather than written into the session, so one
session can safely be shared between clients for different banks.

Without a `session` the default is `httpx.Timeout(30.0, connect=10.0)`. It is
bounded on purpose — an unbounded timeout lets a hung upstream block the caller
indefinitely, which in an async consumer means a stalled event loop.

Monobank and the PrivatBank corporate API describe their failures with documented
JSON bodies, and those are returned as values (`MonobankErrorResponse`,
`PrivatbankErrorResponse`) for the caller to branch on. An HTTP error carrying
anything else — a proxy rejecting the request, an HTML error page, a gateway
timeout — raises `BankTransportError` instead of failing as a confusing
`ValidationError`:

```python
from ua_banktools.banks import BankTransportError
```

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

# Ranges longer than 31 days need to be split; get_full_statement does it for you.
client.get_full_statement("account-id", datetime(2026, 1, 1), datetime(2026, 6, 30))
```

`get_statement` sends exactly one request and so is capped by Monobank at 31 days
plus one hour. `get_full_statement` splits a longer span into consecutive windows
and concatenates them.

The split is a separate method rather than the default because the cost is not
visible at the call site: each window is another request against Monobank's limit
of one statement request per 60 seconds, so a year-long range is twelve windows —
and behind a pacing proxy, twelve minutes of waiting. If any window fails, the
error is returned and earlier windows are discarded; a partial statement mistaken
for a complete one is worse than none.

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

Pass `None` as the statement account to request all active accounts. The optional
`client_id` constructor argument remains available for legacy integrations.

`get_balance` and `get_transactions` return one page each. If `exist_next_page`
is true, pass the response's `next_page_id` back as `follow_id` to fetch the
next. To walk a whole statement instead, use the `get_all_*` variants:

```python
all_transactions = client.get_all_transactions(account, date(2026, 7, 1), date(2026, 7, 31))
all_balances = client.get_all_balances(account, date(2026, 7, 1))
```

These follow pagination to the end and return a flat list. They refuse to loop on
a repeated `next_page_id`, reject a malformed one before echoing it upstream, and
stop at `max_pages` (100 by default).

Run the mocked PrivatBank tests with `just test pb`.

## National Bank of Ukraine Open Data API

```python
from datetime import date

from iso4217 import Currency

from ua_banktools.banks import NBUPublicClient, NBUSortOrder

client = NBUPublicClient()

current_rates = client.get_exchange_rates()
eur_rate = client.get_exchange_rate(Currency.EUR, date(2026, 7, 1))
usd_history = client.get_exchange_rate_history(
    "USD",
    date(2026, 7, 1),
    date(2026, 7, 10),
    order=NBUSortOrder.DESC,
)
```

Currency and investment-metal codes are case-insensitive and normalized to
`iso4217.Currency` objects. Plain strings such as `"EUR"` are also accepted by
client methods. Rates are parsed as `Decimal` values and NBU dates as `date` values.
The API is public and does not require authentication. Run its mocked tests with
`just test nbu`.
