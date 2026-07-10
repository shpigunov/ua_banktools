from datetime import date
from decimal import Decimal
from typing import Optional

import requests
from schwifty import IBAN

from ua_banktools.core import IPN
from ua_banktools.banks.base import BaseCorporateClient
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
    ) -> None:
        self.token = token
        self.client_id = client_id or ""
        self.base_url = base_url.rstrip("/") + "/"
        self.session = requests.session()
        headers = {
            "User-Agent": super().USER_AGENT,
            "Content-Type": "application/json;charset=utf-8",
            "token": self.token,
        }
        if client_id is not None:
            headers["id"] = client_id
        self.session.headers.update(headers)

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
        with self.session.get(
            self.base_url + "statements/balance",
            params=params,
        ) as r:
            if r.ok:
                return BalanceResponse(**r.json())
            return PrivatbankErrorResponse(**r.json())

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
        with self.session.get(
            self.base_url + "statements/transactions",
            params=params,
        ) as r:
            if r.ok:
                return TransactionsResponse(**r.json())
            return PrivatbankErrorResponse(**r.json())

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
        with self.session.post(
            self.base_url + "proxy/payment/create",
            json=PaymentCreateRequest(
                document_number=document_number,
                payer_account=str(payer_acct),
                recipient_account=str(recipient_acct),
                recipient_nceo=str(recipient_nceo),
                payment_naming=payee_name,
                payment_amount=f"{Decimal(str(amount)):.2f}",
                payment_destination=designation,
            ).model_dump(),
        ) as r:
            if r.ok:
                return PaymentCreateSuccessResponse(**r.json())
            return PrivatbankErrorResponse(**r.json())

    def delete_payment(self, payment_ref: str) -> PrivatbankErrorResponse | None:
        with self.session.post(
            self.base_url + "proxy/payment/delete",
            params={"ref": payment_ref},
        ) as r:
            if r.ok:
                return None
            return PrivatbankErrorResponse(**r.json())


"""
TODO:
* Parse dates in responses as per template (%d-%m-%Y, etc.);
"""
