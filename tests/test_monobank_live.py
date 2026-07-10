import os
from datetime import datetime, timedelta
from unittest import TestCase, skipUnless

from ua_banktools.banks.monobank.monobank import MonobankPersonalClient
from ua_banktools.banks.monobank.types import (
    MonobankClientResponse,
    MonobankErrorResponse,
    MonobankTransaction,
)


@skipUnless(
    os.getenv("MONOBANK_LIVE_TESTS") == "1",
    "live Monobank tests require MONOBANK_LIVE_TESTS=1",
)
class MonobankPersonalClientLiveTests(TestCase):
    """Opt-in, read-only smoke tests against a real Monobank account."""

    @classmethod
    def setUpClass(cls):
        token = os.getenv("MONO_TOKEN")
        if not token:
            raise RuntimeError("MONO_TOKEN is required for live Monobank tests")
        cls.client = MonobankPersonalClient(token)

    @classmethod
    def tearDownClass(cls):
        cls.client.session.close()

    def _call_redacted(self, operation, callback):
        try:
            return callback()
        except Exception as error:
            raise AssertionError(
                f"{operation} raised {type(error).__name__}; response data redacted"
            ) from None

    def test_client_info_and_recent_statement(self):
        client_info = self._call_redacted(
            "get_client_info",
            self.client.get_client_info,
        )
        if isinstance(client_info, MonobankErrorResponse):
            raise AssertionError(
                f"get_client_info was rejected: {client_info.error_description}"
            ) from None
        if not isinstance(client_info, MonobankClientResponse):
            raise AssertionError(
                f"get_client_info returned unexpected {type(client_info).__name__}"
            ) from None
        if not client_info.accounts:
            self.skipTest("the Monobank account has no statement-capable accounts")

        end_date = datetime.now()
        start_date = end_date - timedelta(hours=1)
        statement = self._call_redacted(
            "get_statement",
            lambda: self.client.get_statement(
                client_info.accounts[0].id,
                start_date,
                end_date,
            ),
        )
        if isinstance(statement, MonobankErrorResponse):
            raise AssertionError(
                f"get_statement was rejected: {statement.error_description}"
            ) from None
        if not isinstance(statement, list):
            raise AssertionError(
                f"get_statement returned unexpected {type(statement).__name__}"
            ) from None
        if not all(isinstance(item, MonobankTransaction) for item in statement):
            raise AssertionError("get_statement returned an unexpected item type")
