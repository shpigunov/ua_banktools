# ua-banktools

A collection of Python tools and APIs for interacting with Ukrainian banks

## Banks currently supported

- PrivatBank (legal entities only)
- monobank (personal only)

## Features

- Object-oriented as much as possible, with IBANs validated by `schwifty`, timestamps automatically parsed into `datetime` objects, and known categorical values parsed into `enum`s.
- Multiple banks in one package.

## Monobank Open API

```python
from datetime import datetime

from ua_banktools.banks import MonobankPersonalClient

client = MonobankPersonalClient("your-token")
client.get_currency_rates()
client.get_bank_sync()
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
