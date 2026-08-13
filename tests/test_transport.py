"""Session injection, timeouts, error decoding, and model serialization.

These behaviours are shared by every client, so they are tested here rather than
repeated per bank.
"""

from datetime import date, datetime
from unittest import TestCase
from unittest.mock import MagicMock

import httpx

from ua_banktools.banks import BankTransportError, DEFAULT_TIMEOUT
from ua_banktools.banks.monobank import MonobankPersonalClient, MonobankPublicClient
from ua_banktools.banks.monobank.types import (
    Jar,
    MonobankAccount,
    MonobankCurrencyRate,
    MonobankManagedAccount,
    MonobankTransaction,
)
from ua_banktools.banks.nbu import NBUPublicClient
from ua_banktools.banks.nbu.types import NBUExchangeRate, NBUExchangeRateHistory
from ua_banktools.banks.privatbank.privatbank import PBCorporateClient
from ua_banktools.banks.privatbank.public import PBPublicClient

ALL_CLIENTS = [
    lambda session=None: MonobankPersonalClient("token", session=session),
    lambda session=None: MonobankPublicClient(session=session),
    lambda session=None: PBCorporateClient("token", session=session),
    lambda session=None: PBPublicClient(session=session),
    lambda session=None: NBUPublicClient(session=session),
]


class SessionInjectionTests(TestCase):
    def test_every_client_accepts_an_injected_session(self):
        session = httpx.Client()
        for build in ALL_CLIENTS:
            client = build(session)
            self.assertIs(client.session, session, f"{type(client).__name__}")

    def test_default_session_has_a_bounded_timeout(self):
        # An unbounded timeout lets a hung upstream block the caller forever,
        # which for an async consumer means a stalled event loop.
        for build in ALL_CLIENTS:
            client = build()
            self.assertEqual(
                client.session.timeout,
                DEFAULT_TIMEOUT,
                f"{type(client).__name__} should default to a bounded timeout",
            )
            self.assertIsNotNone(client.session.timeout.read)

    def test_injected_session_keeps_the_callers_timeout(self):
        session = httpx.Client(timeout=httpx.Timeout(90.0))
        client = MonobankPersonalClient("token", session=session)
        self.assertEqual(client.session.timeout.read, 90.0)

    def test_auth_travels_per_request_not_on_the_session(self):
        # The session belongs to the caller, so credentials must not be written
        # into it -- otherwise a shared session leaks one bank's token to another.
        session = httpx.Client()
        MonobankPersonalClient("mono-token", session=session)
        PBCorporateClient("pb-token", client_id="pb-id", session=session)

        self.assertNotIn("X-Token", session.headers)
        self.assertNotIn("token", session.headers)
        self.assertNotIn("id", session.headers)

    def test_privatbank_omits_the_legacy_id_header_unless_given(self):
        self.assertNotIn("id", PBCorporateClient("token")._auth_headers)
        self.assertEqual(
            PBCorporateClient("token", client_id="42")._auth_headers["id"],
            "42",
        )


class TransportErrorTests(TestCase):
    """Non-bank error bodies must not surface as ValidationError."""

    def error_response(self, payload=None, text="", status=502):
        response = MagicMock(is_success=False, status_code=status, text=text)
        if payload is None:
            response.json.side_effect = ValueError("not json")
        else:
            response.json.return_value = payload
        response.request.url = "https://egress.example/mono/personal/client-info"
        return response

    def test_bank_shaped_error_is_returned_as_a_value(self):
        client = MonobankPersonalClient("token")
        client.session = MagicMock()
        client.session.get.return_value = self.error_response(
            {"errorDescription": "Unknown account"}, status=400
        )

        result = client.get_client_info()
        self.assertEqual(result.error_description, "Unknown account")

    def test_non_json_body_raises_transport_error(self):
        client = MonobankPersonalClient("token")
        client.session = MagicMock()
        client.session.get.return_value = self.error_response(
            text="<html>502 Bad Gateway</html>"
        )

        with self.assertRaises(BankTransportError) as ctx:
            client.get_client_info()
        self.assertEqual(ctx.exception.status_code, 502)

    def test_gateway_shaped_json_body_raises_transport_error(self):
        # A proxy rejecting the bearer returns JSON, but not the bank's schema.
        client = MonobankPersonalClient("token")
        client.session = MagicMock()
        client.session.get.return_value = self.error_response(
            {"error": "unauthorized"}, text='{"error": "unauthorized"}', status=401
        )

        with self.assertRaises(BankTransportError) as ctx:
            client.get_client_info()
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("401", str(ctx.exception))

    def test_privatbank_transport_error_carries_the_status(self):
        client = PBCorporateClient("token")
        client.session = MagicMock()
        client.session.get.return_value = self.error_response(
            text="Too Many Requests", status=429
        )

        with self.assertRaises(BankTransportError) as ctx:
            client.get_transactions(None, date(2026, 7, 1))
        self.assertEqual(ctx.exception.status_code, 429)

    def test_long_bodies_are_truncated_in_the_message(self):
        client = MonobankPersonalClient("token")
        client.session = MagicMock()
        client.session.get.return_value = self.error_response(text="x" * 5000)

        with self.assertRaises(BankTransportError) as ctx:
            client.get_client_info()
        self.assertLess(len(str(ctx.exception)), 400)


class ModelSerializationTests(TestCase):
    """Every model must survive ``model_dump_json()``.

    ``schwifty.IBAN`` and ``iso4217.Currency`` are not JSON types, so without
    explicit serializers a consumer handing these models to an API or a cache
    fails at the boundary rather than here.
    """

    def models(self):
        """Build from raw API payloads, as the clients do.

        Passing ``currencyCode=980`` as a keyword type-checks against the
        declared ``Currency`` field even though the before-validator coerces it
        at runtime. Validating a dict keeps the payloads honest -- these are the
        shapes the banks actually send.
        """
        iban = "UA393052990000026008025014463"
        return {
            "MonobankAccount": MonobankAccount.model_validate(
                {
                    "id": "a",
                    "sendId": "s",
                    "currencyCode": 980,
                    "balance": 1,
                    "creditLimit": 0,
                    "maskedPan": ["1"],
                    "type": "black",
                    "iban": iban,
                }
            ),
            "MonobankManagedAccount": MonobankManagedAccount.model_validate(
                {
                    "id": "m",
                    "balance": 1,
                    "creditLimit": 0,
                    "type": "fop",
                    "currencyCode": 980,
                    "iban": iban,
                }
            ),
            "MonobankTransaction": MonobankTransaction.model_validate(
                {
                    "id": "t",
                    "time": 1712016000,
                    "description": "d",
                    "mcc": 1,
                    "originalMcc": 1,
                    "amount": -500,
                    "operationAmount": -500,
                    "currencyCode": 980,
                    "commissionRate": 0,
                    "cashbackAmount": 0,
                    "balance": 10,
                    "hold": False,
                }
            ),
            "MonobankCurrencyRate": MonobankCurrencyRate.model_validate(
                {
                    "currencyCodeA": 840,
                    "currencyCodeB": 980,
                    "date": 1712016000,
                    "rateBuy": 41.0,
                }
            ),
            "Jar": Jar.model_validate(
                {
                    "id": "j",
                    "sendId": "s",
                    "title": "t",
                    "description": "d",
                    "currencyCode": 980,
                    "balance": 5,
                }
            ),
            "NBUExchangeRate": NBUExchangeRate.model_validate(
                {
                    "r030": 840,
                    "txt": "Долар США",
                    "rate": "41.5",
                    "cc": "USD",
                    "exchangedate": "02.04.2024",
                }
            ),
            "NBUExchangeRateHistory": NBUExchangeRateHistory.model_validate(
                {
                    "r030": 840,
                    "txt": "Долар США",
                    "rate": "41.5",
                    "cc": "USD",
                    "exchangedate": "02.04.2024",
                    "enname": "US Dollar",
                    "units": 1,
                    "rate_per_unit": "41.5",
                    "group": "1",
                    "calcdate": "02.04.2024",
                }
            ),
        }

    def test_every_model_dumps_to_json(self):
        for name, model in self.models().items():
            with self.subTest(model=name):
                model.model_dump_json()

    def test_currency_dumps_as_alpha_3(self):
        payload = self.models()["MonobankTransaction"].model_dump(mode="json")
        self.assertEqual(payload["currency_code"], "UAH")

    def test_iban_dumps_as_a_string(self):
        payload = self.models()["MonobankAccount"].model_dump(mode="json")
        self.assertEqual(payload["iban"], "UA393052990000026008025014463")

    def test_paired_currency_fields_both_dump(self):
        payload = self.models()["MonobankCurrencyRate"].model_dump(mode="json")
        self.assertEqual(payload["currency_code_a"], "USD")
        self.assertEqual(payload["currency_code_b"], "UAH")

    def test_dumped_models_round_trip_back_into_the_model(self):
        original = self.models()["MonobankAccount"]
        restored = MonobankAccount.model_validate(original.model_dump(mode="json"))
        self.assertEqual(str(restored.iban), str(original.iban))
        self.assertEqual(restored.currency_code, original.currency_code)

    def test_datetimes_dump_as_iso_strings(self):
        payload = self.models()["MonobankTransaction"].model_dump(mode="json")
        self.assertEqual(
            payload["time"], datetime.fromtimestamp(1712016000).isoformat()
        )
