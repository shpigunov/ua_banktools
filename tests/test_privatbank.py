from datetime import date
from decimal import Decimal
from unittest import TestCase
from unittest.mock import MagicMock

from schwifty import IBAN
from pydantic import ValidationError

from ua_banktools.banks.privatbank.privatbank import PBCorporateClient
from ua_banktools.banks.privatbank.public import ExchangeRateType, PBPublicClient
from ua_banktools.banks.privatbank.types import (
    BalanceResponse,
    HistoricalExchangeRatesResponse,
    PaymentCreateSuccessResponse,
    PrivatbankErrorResponse,
    PublicExchangeRate,
    TransactionsResponse,
)


class PBCorporateClientTests(TestCase):
    def setUp(self):
        self.client = PBCorporateClient(
            "secret",
            base_url="https://egress.example/privat",
        )
        self.client.session = MagicMock()
        self.account = IBAN("UA943052990000026100050001037")

    def response(self, payload):
        response = MagicMock(ok=True)
        response.json.return_value = payload
        context = MagicMock()
        context.__enter__.return_value = response
        context.__exit__.return_value = False
        return context

    def test_authentication_uses_token_without_requiring_legacy_client_id(self):
        client = PBCorporateClient("secret")

        self.assertEqual(client.session.headers["token"], "secret")
        self.assertNotIn("id", client.session.headers)

    def test_get_balance_supports_optional_filters_and_pagination(self):
        self.client.session.get.return_value = self.response(
            {
                "status": "SUCCESS",
                "type": "balances",
                "exist_next_page": True,
                "next_page_id": "next-balance-page",
                "balances": [],
            }
        )

        result = self.client.get_balance(
            self.account,
            date(2026, 7, 1),
            follow_id="current-page",
            limit=100,
        )

        self.assertIsInstance(result, BalanceResponse)
        self.assertEqual(result.next_page_id, "next-balance-page")
        self.client.session.get.assert_called_once_with(
            "https://egress.example/privat/statements/balance",
            params={
                "acc": str(self.account),
                "startDate": "01-07-2026",
                "followId": "current-page",
                "limit": 100,
            },
        )

    def test_get_transactions_allows_all_accounts_and_new_fields(self):
        self.client.session.get.return_value = self.response(
            {
                "status": "SUCCESS",
                "type": "transactions",
                "exist_next_page": False,
                "transactions": [
                    {
                        "AUT_MY_CRF": "31451288",
                        "AUT_MY_MFO": "305299",
                        "AUT_MY_ACC": str(self.account),
                        "AUT_MY_NAM": "Test company",
                        "AUT_MY_MFO_NAME": "PrivatBank",
                        "AUT_MY_MFO_CITY": "Kyiv",
                        "AUT_CNTR_CRF": "14360570",
                        "AUT_CNTR_MFO": "305299",
                        "AUT_CNTR_ACC": str(self.account),
                        "AUT_CNTR_NAM": "Counterparty",
                        "AUT_CNTR_MFO_NAME": "PrivatBank",
                        "AUT_CNTR_MFO_CITY": "Kyiv",
                        "CCY": "UAH",
                        "FL_REAL": "r",
                        "PR_PR": "r",
                        "DOC_TYP": "m",
                        "NUM_DOC": "1",
                        "DAT_KL": "01.07.2026",
                        "DAT_OD": "01.07.2026",
                        "OSND": "Test payment",
                        "SUM": "1.00",
                        "SUM_E": "1.00",
                        "REF": "REF",
                        "REFN": "1",
                        "TIM_P": "12:00",
                        "DATE_TIME_DAT_OD_TIM_P": "01.07.2026 12:00:00",
                        "ID": "transaction-id",
                        "TRANTYPE": "C",
                        "TECHNICAL_TRANSACTION_ID": "technical-id",
                        "UETR": "b23aeadc-1ab7-4c34-a005-0f005a059948",
                        "STRUCT_CODE": "101",
                        "STRUCT_TYPE": "22080000",
                    }
                ],
            }
        )

        result = self.client.get_transactions(None, date(2026, 7, 1))

        self.assertIsInstance(result, TransactionsResponse)
        self.assertEqual(result.transactions[0].STRUCT_CODE, "101")
        self.assertIsNone(result.transactions[0].DLR)
        self.client.session.get.assert_called_once_with(
            "https://egress.example/privat/statements/transactions",
            params={"startDate": "01-07-2026"},
        )

    def test_statement_limit_is_validated_by_request_model(self):
        with self.assertRaisesRegex(ValidationError, "less than or equal to 500"):
            self.client.get_balance(self.account, date(2026, 7, 1), limit=501)

    def test_create_payment_uses_string_amount_and_current_response_schema(self):
        self.client.session.post.return_value = self.response(
            {
                "payment_ref": "payment-ref",
                "payment_pack_ref": "payment-pack-ref",
            }
        )

        result = self.client.create_payment(
            payer_acct=self.account,
            recipient_acct=self.account,
            recipient_nceo="14360570",
            payee_name="Counterparty",
            amount=Decimal("1.20"),
            designation="Test payment",
            document_number="42",
        )

        self.assertIsInstance(result, PaymentCreateSuccessResponse)
        self.client.session.post.assert_called_once_with(
            "https://egress.example/privat/proxy/payment/create",
            json={
                "document_number": "42",
                "payer_account": str(self.account),
                "recipient_account": str(self.account),
                "recipient_nceo": "14360570",
                "payment_naming": "Counterparty",
                "payment_amount": "1.20",
                "payment_destination": "Test payment",
            },
        )

    def test_delete_payment_posts_reference_without_a_body(self):
        self.client.session.post.return_value = self.response(None)

        result = self.client.delete_payment("payment-ref")

        self.assertIsNone(result)
        self.client.session.post.assert_called_once_with(
            "https://egress.example/privat/proxy/payment/delete",
            params={"ref": "payment-ref"},
        )

    def test_delete_payment_parses_error_response(self):
        response = MagicMock(ok=False)
        response.json.return_value = {
            "status": "ERROR",
            "code": "400",
            "message": "Payment cannot be deleted",
            "requestId": "request-id",
            "serviceCode": "PMTMDL004",
        }
        context = MagicMock()
        context.__enter__.return_value = response
        context.__exit__.return_value = False
        self.client.session.post.return_value = context

        result = self.client.delete_payment("payment-ref")

        self.assertIsInstance(result, PrivatbankErrorResponse)
        self.assertEqual(result.serviceCode, "PMTMDL004")


class PBPublicClientTests(TestCase):
    def setUp(self):
        self.client = PBPublicClient(base_url="https://egress.example/public")
        self.client.session = MagicMock()

    def response(self, payload):
        response = MagicMock(ok=True)
        response.json.return_value = payload
        context = MagicMock()
        context.__enter__.return_value = response
        context.__exit__.return_value = False
        return context

    def test_does_not_require_authentication(self):
        client = PBPublicClient()

        self.assertNotIn("token", client.session.headers)
        self.assertNotIn("id", client.session.headers)

    def test_get_exchange_rates_supports_cash_and_non_cash_rates(self):
        self.client.session.get.return_value = self.response(
            [
                {
                    "ccy": "USD",
                    "base_ccy": "UAH",
                    "buy": "41.10000",
                    "sale": "41.70000",
                }
            ]
        )

        result = self.client.get_exchange_rates(ExchangeRateType.NON_CASH)

        self.assertIsInstance(result[0], PublicExchangeRate)
        self.assertEqual(result[0].currency, "USD")
        self.assertEqual(result[0].buy, Decimal("41.10000"))
        self.client.session.get.assert_called_once_with(
            "https://egress.example/public/p24api/pubinfo",
            params={"exchange": "", "coursid": 11},
        )

    def test_get_historical_exchange_rates(self):
        self.client.session.get.return_value = self.response(
            {
                "date": "01.07.2026",
                "bank": "PB",
                "baseCurrency": 980,
                "baseCurrencyLit": "UAH",
                "exchangeRate": [
                    {
                        "baseCurrency": "UAH",
                        "currency": "USD",
                        "saleRateNB": 41.1634,
                        "purchaseRateNB": 41.1634,
                        "saleRate": 41.7,
                        "purchaseRate": 41.1,
                    },
                    {
                        "baseCurrency": "UAH",
                        "currency": "UAH",
                        "saleRateNB": 1,
                        "purchaseRateNB": 1,
                    },
                ],
            }
        )

        result = self.client.get_historical_exchange_rates(date(2026, 7, 1))

        self.assertIsInstance(result, HistoricalExchangeRatesResponse)
        self.assertEqual(result.date, date(2026, 7, 1))
        self.assertEqual(result.exchange_rates[0].sale_rate, Decimal("41.7"))
        self.assertIsNone(result.exchange_rates[1].sale_rate)
        self.client.session.get.assert_called_once_with(
            "https://egress.example/public/p24api/exchange_rates",
            params={"date": "01.07.2026"},
        )
