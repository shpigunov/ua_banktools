from datetime import date
from decimal import Decimal
from unittest import TestCase
from unittest.mock import MagicMock

from pydantic import ValidationError

from ua_banktools.banks.nbu import NBUPublicClient, NBUSortOrder
from ua_banktools.banks.nbu.types import (
    NBUExchangeRate,
    NBUExchangeRateHistory,
)


class NBUPublicClientTests(TestCase):
    def setUp(self):
        self.client = NBUPublicClient(base_url="https://egress.example/nbu")
        self.client.session = MagicMock()

    def response(self, payload):
        response = MagicMock()
        response.json.return_value = payload
        return response

    def test_base_url_is_normalized(self):
        self.assertEqual(self.client.base_url, "https://egress.example/nbu/")
        self.assertEqual(NBUPublicClient().base_url, NBUPublicClient.BASE_URL)

    def test_get_current_exchange_rates(self):
        self.client.session.get.return_value = self.response(
            [
                {
                    "r030": 840,
                    "txt": "Долар США",
                    "rate": 44.495,
                    "cc": "USD",
                    "exchangedate": "13.07.2026",
                    "special": "N",
                }
            ]
        )

        result = self.client.get_exchange_rates()

        self.assertIsInstance(result[0], NBUExchangeRate)
        self.assertEqual(result[0].rate, Decimal("44.495"))
        self.assertEqual(result[0].exchange_date, date(2026, 7, 13))
        self.assertEqual(result[0].special, "N")
        self.client.session.get.assert_called_once_with(
            "https://egress.example/nbu/NBUStatService/v1/statdirectory/exchange",
            params={"json": ""},
        )

    def test_get_exchange_rate_for_date_normalizes_currency(self):
        self.client.session.get.return_value = self.response(
            [
                {
                    "r030": 978,
                    "txt": "Євро",
                    "rate": 26.9789,
                    "cc": "EUR",
                    "exchangedate": "02.03.2020",
                    "special": None,
                }
            ]
        )

        result = self.client.get_exchange_rate("eur", date(2020, 3, 2))

        self.assertIsInstance(result, NBUExchangeRate)
        self.assertEqual(result.currency, "EUR")
        self.client.session.get.assert_called_once_with(
            "https://egress.example/nbu/NBUStatService/v1/statdirectory/exchange",
            params={"json": "", "date": "20200302", "valcode": "EUR"},
        )

    def test_get_exchange_rate_returns_none_for_an_empty_response(self):
        self.client.session.get.return_value = self.response([])

        self.assertIsNone(self.client.get_exchange_rate("USD"))

    def test_get_exchange_rate_history(self):
        self.client.session.get.return_value = self.response(
            [
                {
                    "exchangedate": "31.01.2022",
                    "r030": 840,
                    "cc": "USD",
                    "txt": "Долар США",
                    "enname": "US Dollar",
                    "rate": 28.7839,
                    "units": 1,
                    "rate_per_unit": 28.7839,
                    "group": "1",
                    "calcdate": "28.01.2022",
                    "special": None,
                }
            ]
        )

        result = self.client.get_exchange_rate_history(
            "usd",
            date(2022, 1, 15),
            date(2022, 1, 31),
            order=NBUSortOrder.DESC,
        )

        self.assertIsInstance(result[0], NBUExchangeRateHistory)
        self.assertEqual(result[0].english_name, "US Dollar")
        self.assertEqual(result[0].calculation_date, date(2022, 1, 28))
        self.assertEqual(result[0].rate_per_unit, Decimal("28.7839"))
        self.client.session.get.assert_called_once_with(
            "https://egress.example/nbu/NBU_Exchange/exchange_site",
            params={
                "json": "",
                "start": "20220115",
                "end": "20220131",
                "valcode": "USD",
                "sort": "exchangedate",
                "order": "desc",
            },
        )

    def test_history_rejects_an_inverted_date_range(self):
        with self.assertRaisesRegex(
            ValidationError,
            "start_date must not be after end_date",
        ):
            self.client.get_exchange_rate_history(
                "USD",
                date(2022, 2, 1),
                date(2022, 1, 31),
            )

        self.client.session.get.assert_not_called()

    def test_http_errors_are_raised(self):
        response = self.response({"error": "unavailable"})
        response.raise_for_status.side_effect = RuntimeError("request failed")
        self.client.session.get.return_value = response

        with self.assertRaisesRegex(RuntimeError, "request failed"):
            self.client.get_exchange_rates()
