from datetime import date
from decimal import Decimal
from typing import Optional

import httpx
from schwifty import IBAN

from ua_banktools.core import IPN
from ua_banktools.banks.base import BaseCorporateClient, build_session, parse_error
from .types import (
    BalanceResponse,
    PrivatbankErrorResponse,
    TransactionsResponse,
    PaymentCreateRequest,
    PaymentCreateSuccessResponse,
    StatementParams,
)


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
