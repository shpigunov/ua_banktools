from datetime import datetime
from unittest import TestCase
from unittest.mock import MagicMock

from ua_banktools.banks.monobank.monobank import MonobankPersonalClient
from ua_banktools.banks.monobank.types import (
    MonobankSyncResponse,
    MonobankClientResponse,
    MonobankCurrencyRate,
    MonobankTransaction,
    MonobankWebhookResponse,
)


class MonobankPersonalClientTests(TestCase):
    def setUp(self):
        self.client = MonobankPersonalClient(
            "secret",
            base_url="https://egress.example/mono",
        )
        self.client.session = MagicMock()

    def response(self, payload):
        response = MagicMock(ok=True)
        response.json.return_value = payload
        context = MagicMock()
        context.__enter__.return_value = response
        context.__exit__.return_value = False
        return context

    def test_base_url_is_normalized(self):
        self.assertEqual(self.client.base_url, "https://egress.example/mono/")
        self.assertEqual(
            MonobankPersonalClient("secret").base_url,
            MonobankPersonalClient.BASE_URL,
        )

    def test_get_currency_rates(self):
        self.client.session.get.return_value = self.response(
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
        self.client.session.get.assert_called_once_with(
            "https://egress.example/mono/bank/currency"
        )

    def test_get_bank_sync(self):
        self.client.session.get.return_value = self.response(
            {
                "serverKeyId": "key-id",
                "serverPubKey": "public-key",
                "serverTimeMsec": 1755509467397,
            }
        )

        result = self.client.get_bank_sync()

        self.assertIsInstance(result, MonobankSyncResponse)
        self.client.session.get.assert_called_once_with(
            "https://egress.example/mono/bank/sync"
        )

    def test_get_client_info_supports_jars_and_managed_clients(self):
        self.client.session.get.return_value = self.response(
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
                        "tin": 1234567890,
                        "name": "Managed Client",
                        "accounts": [],
                    }
                ],
            }
        )

        result = self.client.get_client_info()

        self.assertIsInstance(result, MonobankClientResponse)
        self.assertEqual(result.jars[0].send_id, "send-id")
        self.assertEqual(result.managed_clients[0].client_id, "managed-id")
        self.client.session.get.assert_called_once_with(
            "https://egress.example/mono/personal/client-info",
            headers={"X-Token": "secret"},
        )

    def test_set_webhook(self):
        self.client.session.post.return_value = self.response({"status": "ok"})

        result = self.client.set_webhook("https://example.com/webhook")

        self.assertIsInstance(result, MonobankWebhookResponse)
        self.client.session.post.assert_called_once_with(
            "https://egress.example/mono/personal/webhook",
            headers={"X-Token": "secret"},
            json={"webHookUrl": "https://example.com/webhook"},
        )

    def test_get_statement_supports_optional_to_and_counterparty_fields(self):
        self.client.session.get.return_value = self.response(
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
        self.assertEqual(result[0].invoice_id, "invoice-id")
        self.client.session.get.assert_called_once_with(
            "https://egress.example/mono/personal/statement/account-id/1546304461",
            headers={"X-Token": "secret"},
        )
