"""Statement assembly: PrivatBank pagination and Monobank window splitting.

Both banks make the caller do the walking -- PrivatBank hands back a
``next_page_id``, and Monobank refuses a range wider than 31 days plus an hour.
These helpers exist so every consumer does not reimplement the loop.
"""

from datetime import date, datetime
from unittest import TestCase
from unittest.mock import MagicMock

from ua_banktools.banks.monobank import MonobankPersonalClient
from ua_banktools.banks.monobank.monobank import MAX_STATEMENT_RANGE_SECONDS
from ua_banktools.banks.monobank.types import MonobankErrorResponse
from ua_banktools.banks.privatbank.privatbank import PBCorporateClient
from ua_banktools.banks.privatbank.types import PrivatbankErrorResponse


def transaction(ref: str) -> dict:
    """A minimal but complete TransactionItem payload."""
    return {
        "AUT_MY_CRF": "1",
        "AUT_MY_MFO": "305299",
        "AUT_MY_ACC": "UA943052990000026100050001037",
        "AUT_MY_NAM": "Me",
        "AUT_MY_MFO_NAME": "PB",
        "AUT_MY_MFO_CITY": "Kyiv",
        "AUT_CNTR_CRF": "2",
        "AUT_CNTR_MFO": "305299",
        "AUT_CNTR_ACC": "UA943052990000026100050001037",
        "AUT_CNTR_NAM": "Them",
        "AUT_CNTR_MFO_NAME": "PB",
        "AUT_CNTR_MFO_CITY": "Kyiv",
        "CCY": "UAH",
        "FL_REAL": "r",
        "PR_PR": "r",
        "DOC_TYP": "m",
        "NUM_DOC": "1",
        "DAT_KL": "01.07.2026",
        "DAT_OD": "01.07.2026",
        "OSND": "Payment",
        "SUM": 100.0,
        "SUM_E": 100.0,
        "REF": ref,
        "REFN": "1",
        "TIM_P": "12:00:00",
        "DATE_TIME_DAT_OD_TIM_P": "01.07.2026 12:00:00",
        "ID": ref,
        "TRANTYPE": "C",
        "TECHNICAL_TRANSACTION_ID": ref,
    }


def page(refs, *, next_page_id=None):
    return {
        "status": "SUCCESS",
        "type": "transactions",
        "exist_next_page": next_page_id is not None,
        "next_page_id": next_page_id,
        "transactions": [transaction(ref) for ref in refs],
    }


class PrivatbankPaginationTests(TestCase):
    def setUp(self):
        self.client = PBCorporateClient(
            "secret",
            base_url="https://egress.example/privat",
        )
        self.session = MagicMock()
        self.client.session = self.session
        self.start = date(2026, 7, 1)

    def responses(self, *payloads):
        out = []
        for payload in payloads:
            response = MagicMock(is_success=True)
            response.json.return_value = payload
            out.append(response)
        self.session.get.side_effect = out

    def follow_ids(self):
        return [
            call.kwargs["params"].get("followId")
            for call in self.session.get.call_args_list
        ]

    def test_single_page_returns_directly(self):
        self.responses(page(["a", "b"]))

        result = self.client.get_all_transactions(None, self.start)

        assert isinstance(result, list)
        self.assertEqual([t.ID for t in result], ["a", "b"])
        self.assertEqual(self.session.get.call_count, 1)
        self.assertIsNone(self.follow_ids()[0])

    def test_pages_are_concatenated_in_order(self):
        self.responses(
            page(["a"], next_page_id="p2"),
            page(["b"], next_page_id="p3"),
            page(["c"]),
        )

        result = self.client.get_all_transactions(None, self.start)

        assert isinstance(result, list)
        self.assertEqual([t.ID for t in result], ["a", "b", "c"])
        self.assertEqual(self.follow_ids(), [None, "p2", "p3"])

    def test_default_page_size_is_sent(self):
        self.responses(page(["a"]))

        self.client.get_all_transactions(None, self.start)

        self.assertEqual(self.session.get.call_args.kwargs["params"]["limit"], 100)

    def test_repeated_next_page_id_is_refused(self):
        # Without this guard the same page is fetched forever.
        self.responses(
            page(["a"], next_page_id="loop"),
            page(["b"], next_page_id="loop"),
        )

        with self.assertRaisesRegex(ValueError, "repeated"):
            self.client.get_all_transactions(None, self.start)

    def test_malformed_next_page_id_is_refused(self):
        # follow_id is echoed straight back upstream, so it is validated first.
        self.responses(page(["a"], next_page_id="../../etc/passwd"))

        with self.assertRaisesRegex(ValueError, "malformed"):
            self.client.get_all_transactions(None, self.start)

    def test_missing_next_page_id_is_refused(self):
        payload = page(["a"])
        payload["exist_next_page"] = True
        payload["next_page_id"] = None
        self.responses(payload)

        with self.assertRaisesRegex(ValueError, "without a next_page_id"):
            self.client.get_all_transactions(None, self.start)

    def test_page_ceiling_stops_a_runaway_statement(self):
        self.responses(
            *[page([str(i)], next_page_id=f"p{i}") for i in range(10)],
        )

        with self.assertRaisesRegex(ValueError, "exceeded 3 pages"):
            self.client.get_all_transactions(None, self.start, max_pages=3)
        self.assertEqual(self.session.get.call_count, 3)

    def test_error_on_a_later_page_is_returned_not_raised(self):
        error = MagicMock(is_success=False, status_code=400)
        error.json.return_value = {
            "status": "ERROR",
            "code": "1",
            "message": "boom",
            "requestId": "r",
        }
        first = MagicMock(is_success=True)
        first.json.return_value = page(["a"], next_page_id="p2")
        self.session.get.side_effect = [first, error]

        result = self.client.get_all_transactions(None, self.start)

        # assertIsInstance reports a good failure message; the plain assert is
        # what narrows the union for the type checker. Both fail on a bad value.
        self.assertIsInstance(result, PrivatbankErrorResponse)
        assert isinstance(result, PrivatbankErrorResponse)
        self.assertEqual(result.message, "boom")

    def test_balances_paginate_through_the_same_walker(self):
        def balance_page(next_page_id=None):
            return {
                "status": "SUCCESS",
                "type": "balances",
                "exist_next_page": next_page_id is not None,
                "next_page_id": next_page_id,
                "balances": [],
            }

        self.responses(balance_page("b2"), balance_page())

        result = self.client.get_all_balances(None, self.start)

        self.assertEqual(result, [])
        self.assertEqual(self.follow_ids(), [None, "b2"])


class MonobankWindowSplittingTests(TestCase):
    def setUp(self):
        self.client = MonobankPersonalClient(
            "token",
            base_url="https://egress.example/mono",
        )
        self.session = MagicMock()
        self.client.session = self.session

    def empty_statements(self, count):
        out = []
        for _ in range(count):
            response = MagicMock(is_success=True)
            response.json.return_value = []
            out.append(response)
        self.session.get.side_effect = out

    def requested_windows(self):
        """Return the (from, to) timestamp pairs actually requested."""
        windows = []
        for call in self.session.get.call_args_list:
            parts = call.args[0].rsplit("/", 2)
            windows.append((int(parts[-2]), int(parts[-1])))
        return windows

    def test_short_range_is_a_single_window(self):
        self.empty_statements(1)

        self.client.get_full_statement(
            "acct",
            datetime.fromtimestamp(1_000_000),
            datetime.fromtimestamp(1_000_500),
        )

        self.assertEqual(self.requested_windows(), [(1_000_000, 1_000_500)])

    def test_exact_maximum_range_is_not_split(self):
        self.empty_statements(1)

        self.client.get_full_statement(
            "acct",
            datetime.fromtimestamp(0),
            datetime.fromtimestamp(MAX_STATEMENT_RANGE_SECONDS),
        )

        self.assertEqual(
            self.requested_windows(),
            [(0, MAX_STATEMENT_RANGE_SECONDS)],
        )

    def test_long_range_splits_into_contiguous_windows(self):
        end = 2 * MAX_STATEMENT_RANGE_SECONDS + 100
        self.empty_statements(3)

        self.client.get_full_statement(
            "acct",
            datetime.fromtimestamp(0),
            datetime.fromtimestamp(end),
        )

        windows = self.requested_windows()
        self.assertEqual(
            windows,
            [
                (0, MAX_STATEMENT_RANGE_SECONDS),
                (MAX_STATEMENT_RANGE_SECONDS + 1, 2 * MAX_STATEMENT_RANGE_SECONDS + 1),
                (2 * MAX_STATEMENT_RANGE_SECONDS + 2, end),
            ],
        )
        # Windows must not overlap or leave gaps, or transactions are lost.
        for (_, prev_end), (next_start, _) in zip(windows, windows[1:]):
            self.assertEqual(next_start, prev_end + 1)
        for start, stop in windows:
            self.assertLessEqual(stop - start, MAX_STATEMENT_RANGE_SECONDS)

    def test_transactions_from_every_window_are_concatenated(self):
        def statement(tx_id):
            response = MagicMock(is_success=True)
            response.json.return_value = [
                {
                    "id": tx_id,
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
            ]
            return response

        self.session.get.side_effect = [statement("w1"), statement("w2")]

        result = self.client.get_full_statement(
            "acct",
            datetime.fromtimestamp(0),
            datetime.fromtimestamp(MAX_STATEMENT_RANGE_SECONDS + 10),
        )

        assert isinstance(result, list)
        self.assertEqual([t.id for t in result], ["w1", "w2"])

    def test_error_in_a_window_is_returned_without_partial_results(self):
        # A partial statement read as complete is worse than no statement.
        ok = MagicMock(is_success=True)
        ok.json.return_value = []
        error = MagicMock(is_success=False, status_code=429)
        error.json.return_value = {"errorDescription": "Too many requests"}
        self.session.get.side_effect = [ok, error]

        result = self.client.get_full_statement(
            "acct",
            datetime.fromtimestamp(0),
            datetime.fromtimestamp(MAX_STATEMENT_RANGE_SECONDS + 10),
        )

        self.assertIsInstance(result, MonobankErrorResponse)

    def test_inverted_range_is_refused_before_any_request(self):
        self.session.get.side_effect = AssertionError("should not be called")

        with self.assertRaisesRegex(ValueError, "must not be before"):
            self.client.get_full_statement(
                "acct",
                datetime.fromtimestamp(2_000),
                datetime.fromtimestamp(1_000),
            )

    def test_get_statement_still_sends_one_unsplit_request(self):
        # The single-window primitive must stay cheap and predictable.
        self.empty_statements(1)

        self.client.get_statement(
            "acct",
            datetime.fromtimestamp(0),
            datetime.fromtimestamp(10 * MAX_STATEMENT_RANGE_SECONDS),
        )

        self.assertEqual(self.session.get.call_count, 1)
