from datetime import datetime
from unittest import TestCase
from unittest.mock import MagicMock

from iso4217 import Currency
from pydantic import ValidationError

from ua_banktools.banks.monobank import MonobankPersonalClient, MonobankPublicClient
from ua_banktools.banks.monobank.types import (
    MonobankErrorResponse,
    MonobankSyncResponse,
    MonobankClientResponse,
    MonobankCurrencyRate,
    MonobankTransaction,
    MonobankWebhookResponse,
)
from ua_banktools.core import IPN


class MonobankPublicClientTests(TestCase):
    def setUp(self):
        self.client = MonobankPublicClient(base_url="https://egress.example/mono")
        self.session = MagicMock()
        self.client.session = self.session

    def response(self, payload):
        response = MagicMock(is_success=True)
        response.json.return_value = payload
        return response

    def test_base_url_is_normalized(self):
        self.assertEqual(self.client.base_url, "https://egress.example/mono/")
        self.assertEqual(
            MonobankPublicClient().base_url,
            MonobankPublicClient.BASE_URL,
        )

    def test_get_currency_rates(self):
        self.session.get.return_value = self.response(
            [
                {
                    "currencyCodeA": 840,
                    "currencyCodeB": 980,
                    "date": 1552392228,
                    "rateBuy": 27.2,
                    "rateSell": 27,
                }
            ]
        )

        result = self.client.get_currency_rates()

        self.assertIsInstance(result[0], MonobankCurrencyRate)
        self.assertIs(result[0].currency_code_a, Currency.USD)
        self.assertIs(result[0].currency_code_b, Currency.UAH)
        self.session.get.assert_called_once_with(
            "https://egress.example/mono/bank/currency"
        )

    def test_get_currency_rates_survives_withdrawn_iso_codes(self):
        # Monobank still quotes BGN (975), which left ISO 4217 when Bulgaria
        # adopted the euro; one such row must not sink the whole response.
        self.session.get.return_value = self.response(
            [
                {
                    "currencyCodeA": 840,
                    "currencyCodeB": 980,
                    "date": 1,
                    "rateBuy": 41.1,
                },
                {
                    "currencyCodeA": 975,
                    "currencyCodeB": 980,
                    "date": 1,
                    "rateCross": 24.7,
                },
            ]
        )

        result = self.client.get_currency_rates()

        self.assertEqual(len(result), 1)
        self.assertIs(result[0].currency_code_a, Currency.USD)

    def test_get_currency_rates_still_raises_on_other_malformed_rows(self):
        # Only withdrawn currencies are skipped; anything else is API drift.
        self.session.get.return_value = self.response(
            [
                {
                    "currencyCodeA": 840,
                    "currencyCodeB": 980,
                    "date": 1,
                    "rateBuy": 41.1,
                },
                {
                    "currencyCodeA": 978,
                    "currencyCodeB": 980,
                    "rateBuy": 48.0,
                },
            ]
        )

        with self.assertRaises(ValidationError):
            self.client.get_currency_rates()

    def test_rate_limit_error_uses_the_public_error_shape(self):
        response = MagicMock(is_success=False, status_code=429)
        response.json.return_value = {"errCode": "TMR", "errText": "Too many requests"}
        self.session.get.return_value = response

        result = self.client.get_currency_rates()

        self.assertIsInstance(result, MonobankErrorResponse)
        self.assertEqual(result.error_description, "Too many requests")
        self.assertEqual(result.error_code, "TMR")

    def test_get_bank_sync(self):
        self.session.get.return_value = self.response(
            {
                "serverKeyId": "key-id",
                "serverPubKey": "public-key",
                "serverTimeMsec": 1755509467397,
            }
        )

        result = self.client.get_bank_sync()

        self.assertIsInstance(result, MonobankSyncResponse)
        self.session.get.assert_called_once_with(
            "https://egress.example/mono/bank/sync"
        )


class MonobankPersonalClientTests(TestCase):
    def setUp(self):
        self.client = MonobankPersonalClient(
            "secret",
            base_url="https://egress.example/mono",
        )
        self.session = MagicMock()
        self.client.session = self.session

    def response(self, payload):
        response = MagicMock(is_success=True)
        response.json.return_value = payload
        return response

    def test_base_url_is_normalized(self):
        self.assertEqual(self.client.base_url, "https://egress.example/mono/")
        self.assertEqual(
            MonobankPersonalClient("secret").base_url,
            MonobankPersonalClient.BASE_URL,
        )

    def test_public_operations_are_not_exposed(self):
        self.assertFalse(hasattr(self.client, "get_currency_rates"))
        self.assertFalse(hasattr(self.client, "get_bank_sync"))

    def test_get_client_info_supports_jars_and_managed_clients(self):
        self.session.get.return_value = self.response(
            {
                "clientId": "client-id",
                "name": "Test Client",
                "webHookUrl": "",
                "permissions": "psfj",
                "accounts": [],
                "jars": [
                    {
                        "id": "jar-id",
                        "sendId": "send-id",
                        "title": "Jar",
                        "description": "Savings",
                        "currencyCode": 980,
                        "balance": 100,
                        "goal": 1000,
                    }
                ],
                "managedClients": [
                    {
                        "clientId": "managed-id",
                        "tin": "3123456789",
                        "name": "Managed Client",
                        "accounts": [],
                    },
                    {
                        # Fails the IPN checksum, as passport-registered FOPs do.
                        "clientId": "passport-id",
                        "tin": "0123456789",
                        "name": "Passport Client",
                        "accounts": [],
                    },
                ],
            }
        )

        result = self.client.get_client_info()

        self.assertIsInstance(result, MonobankClientResponse)
        self.assertEqual(result.jars[0].send_id, "send-id")
        self.assertIs(result.jars[0].currency_code, Currency.UAH)
        self.assertEqual(result.managed_clients[0].client_id, "managed-id")
        self.assertIsInstance(result.managed_clients[0].tin, IPN)
        self.assertEqual(result.managed_clients[0].tin, "3123456789")
        self.assertEqual(result.managed_clients[1].tin, "0123456789")
        self.assertNotIsInstance(result.managed_clients[1].tin, IPN)

        dumped = result.model_dump(mode="json")
        self.assertEqual(dumped["managed_clients"][0]["tin"], "3123456789")
        restored = MonobankClientResponse.model_validate(dumped)
        self.assertIsInstance(restored.managed_clients[0].tin, IPN)
        self.session.get.assert_called_once_with(
            "https://egress.example/mono/personal/client-info",
            headers={"X-Token": "secret"},
        )

    def test_set_webhook(self):
        self.session.post.return_value = self.response({"status": "ok"})

        result = self.client.set_webhook("https://example.com/webhook")

        self.assertIsInstance(result, MonobankWebhookResponse)
        self.session.post.assert_called_once_with(
            "https://egress.example/mono/personal/webhook",
            headers={"X-Token": "secret"},
            json={"webHookUrl": "https://example.com/webhook"},
        )

    def test_get_statement_supports_optional_to_and_counterparty_fields(self):
        self.session.get.return_value = self.response(
            [
                {
                    "id": "transaction-id",
                    "time": 1554466347,
                    "description": "Payment",
                    "mcc": 7997,
                    "originalMcc": 7997,
                    "hold": False,
                    "amount": -95000,
                    "operationAmount": -95000,
                    "currencyCode": 980,
                    "commissionRate": 0,
                    "cashbackAmount": 0,
                    "balance": 10050000,
                    "invoiceId": "invoice-id",
                    "counterEdrpou": "3096889974",
                    "counterIban": "UA898999980000355639201001404",
                    "counterName": "Counterparty",
                }
            ]
        )
        start = datetime.fromtimestamp(1546304461)

        result = self.client.get_statement("account-id", start)

        self.assertIsInstance(result[0], MonobankTransaction)
        self.assertIs(result[0].currency_code, Currency.UAH)
        self.assertEqual(result[0].invoice_id, "invoice-id")
        self.session.get.assert_called_once_with(
            "https://egress.example/mono/personal/statement/account-id/1546304461",
            headers={"X-Token": "secret"},
        )
