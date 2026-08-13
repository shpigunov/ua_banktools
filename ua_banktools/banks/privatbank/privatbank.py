import re
from datetime import date
from decimal import Decimal
from typing import List, Optional

import httpx
from schwifty import IBAN

from ua_banktools.core import IPN
from ua_banktools.banks.base import BaseCorporateClient, build_session, parse_error
from .types import (
    BalanceItem,
    BalanceResponse,
    PrivatbankErrorResponse,
    TransactionItem,
    TransactionsResponse,
    PaymentCreateRequest,
    PaymentCreateSuccessResponse,
    StatementParams,
)

#: Page size used when walking a statement. The API caps ``limit`` at 500, but a
#: smaller page keeps each request (and each cache entry behind a proxy) modest.
DEFAULT_PAGE_SIZE = 100

#: Refuse to walk forever if the API keeps advertising another page.
MAX_PAGES = 100

_FOLLOW_ID_RE = re.compile(r"^[A-Za-z0-9_=:-]{1,128}$")


# Privatbank API Client
class PBCorporateClient(BaseCorporateClient):
    BASE_URL = "https://acp.privatbank.ua/api/"

    def __init__(
        self,
        token: str,
        client_id: Optional[str] = None,
        base_url: str = BASE_URL,
        session: Optional[httpx.Client] = None,
    ) -> None:
        self.token = token
        self.client_id = client_id or ""
        self.base_url = base_url.rstrip("/") + "/"
        self._send_client_id = client_id is not None
        self.session = build_session(session)

    @property
    def _auth_headers(self) -> dict[str, str]:
        """Auth sent per request, so an injected session stays the caller's."""
        headers = {
            "User-Agent": BaseCorporateClient.USER_AGENT,
            "Content-Type": "application/json;charset=utf-8",
            "token": self.token,
        }
        if self._send_client_id:
            headers["id"] = self.client_id
        return headers

    def get_balance(
        self,
        acct: Optional[IBAN],
        start_date: date,
        end_date: Optional[date] = None,
        *,
        follow_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> BalanceResponse | PrivatbankErrorResponse:
        params = StatementParams(
            acct=acct,
            start_date=start_date,
            end_date=end_date,
            follow_id=follow_id,
            limit=limit,
        ).to_query_params()
        r = self.session.get(
            self.base_url + "statements/balance",
            params=params,
            headers=self._auth_headers,
        )
        if r.is_success:
            return BalanceResponse(**r.json())
        return parse_error(r, PrivatbankErrorResponse)

    def get_transactions(
        self,
        acct: Optional[IBAN],
        start_date: date,
        end_date: Optional[date] = None,
        *,
        follow_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> TransactionsResponse | PrivatbankErrorResponse:
        params = StatementParams(
            acct=acct,
            start_date=start_date,
            end_date=end_date,
            follow_id=follow_id,
            limit=limit,
        ).to_query_params()
        r = self.session.get(
            self.base_url + "statements/transactions",
            params=params,
            headers=self._auth_headers,
        )
        if r.is_success:
            return TransactionsResponse(**r.json())
        return parse_error(r, PrivatbankErrorResponse)

    def get_all_transactions(
        self,
        acct: Optional[IBAN],
        start_date: date,
        end_date: Optional[date] = None,
        *,
        limit: int = DEFAULT_PAGE_SIZE,
        max_pages: int = MAX_PAGES,
    ) -> List[TransactionItem] | PrivatbankErrorResponse:
        """Return every transaction in a range, following pagination to the end.

        :meth:`get_transactions` returns one page and leaves ``follow_id`` to the
        caller; this walks the whole statement.
        """
        pages = self._walk_pages(
            self.get_transactions,
            acct,
            start_date,
            end_date,
            limit=limit,
            max_pages=max_pages,
        )
        if isinstance(pages, PrivatbankErrorResponse):
            return pages
        return [item for page in pages for item in page.transactions]

    def get_all_balances(
        self,
        acct: Optional[IBAN],
        start_date: date,
        end_date: Optional[date] = None,
        *,
        limit: int = DEFAULT_PAGE_SIZE,
        max_pages: int = MAX_PAGES,
    ) -> List[BalanceItem] | PrivatbankErrorResponse:
        """Return every balance row in a range, following pagination to the end."""
        pages = self._walk_pages(
            self.get_balance,
            acct,
            start_date,
            end_date,
            limit=limit,
            max_pages=max_pages,
        )
        if isinstance(pages, PrivatbankErrorResponse):
            return pages
        return [item for page in pages for item in page.balances]

    def _walk_pages(
        self,
        fetch,
        acct: Optional[IBAN],
        start_date: date,
        end_date: Optional[date],
        *,
        limit: int,
        max_pages: int,
    ):
        """Follow ``next_page_id`` until the API stops advertising another page.

        The guards matter because ``follow_id`` comes back from the API and drives
        the next request: a repeated or malformed id would otherwise loop forever
        or forward junk upstream.
        """
        pages = []
        seen_follow_ids: set[str] = set()
        follow_id: Optional[str] = None

        for _ in range(max_pages):
            page = fetch(
                acct,
                start_date,
                end_date,
                follow_id=follow_id,
                limit=limit,
            )
            if isinstance(page, PrivatbankErrorResponse):
                return page
            pages.append(page)

            if not page.exist_next_page:
                return pages

            next_page_id = (page.next_page_id or "").strip()
            if not next_page_id:
                raise ValueError(
                    "PrivatBank advertised another page without a next_page_id"
                )
            if not _FOLLOW_ID_RE.match(next_page_id):
                raise ValueError("PrivatBank returned a malformed next_page_id")
            if next_page_id in seen_follow_ids:
                raise ValueError("PrivatBank repeated a next_page_id")
            seen_follow_ids.add(next_page_id)
            follow_id = next_page_id

        raise ValueError(f"PrivatBank statement exceeded {max_pages} pages")

    def create_payment(
        self,
        payer_acct: IBAN,
        recipient_acct: IBAN,
        recipient_nceo: IPN | str,
        payee_name: str,
        amount: Decimal | float,
        designation: str,
        document_number: str,
    ) -> PaymentCreateSuccessResponse | PrivatbankErrorResponse:
        r = self.session.post(
            self.base_url + "proxy/payment/create",
            headers=self._auth_headers,
            json=PaymentCreateRequest(
                document_number=document_number,
                payer_account=str(payer_acct),
                recipient_account=str(recipient_acct),
                recipient_nceo=str(recipient_nceo),
                payment_naming=payee_name,
                payment_amount=f"{Decimal(str(amount)):.2f}",
                payment_destination=designation,
            ).model_dump(),
        )
        if r.is_success:
            return PaymentCreateSuccessResponse(**r.json())
        return parse_error(r, PrivatbankErrorResponse)

    def delete_payment(self, payment_ref: str) -> PrivatbankErrorResponse | None:
        r = self.session.post(
            self.base_url + "proxy/payment/delete",
            headers=self._auth_headers,
            params={"ref": payment_ref},
        )
        if r.is_success:
            return None
        return parse_error(r, PrivatbankErrorResponse)


"""
TODO:
* Parse dates in responses as per template (%d-%m-%Y, etc.);
"""
