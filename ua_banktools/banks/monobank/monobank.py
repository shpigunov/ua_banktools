from datetime import datetime
from typing import List, Optional

import httpx

from ua_banktools.banks.base import BasePersonalClient, build_session, parse_error
from ua_banktools.banks.monobank.types import (
    MonobankClientResponse,
    MonobankErrorResponse,
    MonobankTransaction,
    MonobankWebhookResponse,
)

#: Monobank rejects a statement range wider than 31 days plus one hour.
MAX_STATEMENT_RANGE_SECONDS = 2_682_000


class MonobankPersonalClient(BasePersonalClient):
    """
    Client for individual and PE (FOP) accounts.
    Reference: https://api.monobank.ua/docs/index.html
    """

    BASE_URL = "https://api.monobank.ua/"

    def __init__(
        self,
        token: str,
        base_url: str = BASE_URL,
        session: Optional[httpx.Client] = None,
    ) -> None:
        self.token = token
        self.base_url = base_url.rstrip("/") + "/"
        self.session = build_session(session)

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {"X-Token": self.token}

    def _url(self, path: str) -> str:
        return self.base_url + path.lstrip("/")

    def get_client_info(self):
        r = self.session.get(
            self._url("personal/client-info"),
            headers=self._auth_headers,
        )
        if r.is_success:
            return MonobankClientResponse(**r.json())
        return parse_error(r, MonobankErrorResponse)

    def set_webhook(self, webhook_url: str):
        """Set or remove the statement webhook (pass an empty URL to remove it)."""
        r = self.session.post(
            self._url("personal/webhook"),
            headers=self._auth_headers,
            json={"webHookUrl": webhook_url},
        )
        if r.is_success:
            return MonobankWebhookResponse(**r.json())
        return parse_error(r, MonobankErrorResponse)

    def get_statement(
        self,
        acct_id: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
    ):
        """Return one statement window.

        The range must not exceed :data:`MAX_STATEMENT_RANGE_SECONDS`; use
        :meth:`get_full_statement` for anything longer.
        """
        path = f"personal/statement/{acct_id}/{round(start_date.timestamp())}"
        if end_date is not None:
            path += f"/{round(end_date.timestamp())}"

        r = self.session.get(
            self._url(path),
            headers=self._auth_headers,
        )
        if r.is_success:
            return [MonobankTransaction(**item) for item in r.json()]
        return parse_error(r, MonobankErrorResponse)

    def get_transactions(
        self,
        acct_id: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
    ):
        """Backward-compatible alias for :meth:`get_statement`."""
        return self.get_statement(acct_id, start_date, end_date)

    def get_full_statement(
        self,
        acct_id: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
    ) -> List[MonobankTransaction] | MonobankErrorResponse:
        """Return every transaction in a range, splitting it into legal windows.

        Monobank caps a statement request at 31 days plus one hour, so a longer
        span is fetched as consecutive windows and concatenated.

        This is a separate method rather than the default behaviour of
        :meth:`get_statement` because the cost is not obvious from the call: each
        window is one more request against Monobank's rate limit of one statement
        request per 60 seconds. A year-long range is twelve windows, and behind a
        pacing proxy that is twelve minutes of waiting.

        Raises :class:`~ua_banktools.banks.base.BankTransportError` or returns a
        :class:`MonobankErrorResponse` if any window fails; earlier windows are
        discarded, since a partial statement is more dangerous than none.
        """
        start_ts = round(start_date.timestamp())
        end_ts = round((end_date or datetime.now()).timestamp())
        if end_ts < start_ts:
            raise ValueError("end_date must not be before start_date")

        transactions: List[MonobankTransaction] = []
        window_start = start_ts
        while window_start <= end_ts:
            window_end = min(window_start + MAX_STATEMENT_RANGE_SECONDS, end_ts)
            result = self.get_statement(
                acct_id,
                datetime.fromtimestamp(window_start),
                datetime.fromtimestamp(window_end),
            )
            if isinstance(result, MonobankErrorResponse):
                return result
            transactions.extend(result)
            window_start = window_end + 1

        return transactions
