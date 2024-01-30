from datetime import date
import requests
from schwifty import IBAN

from ua_banktools.core import IPN
from .base import BaseCorporateClient
from .privatbank_types import (
    BalanceResponse,
    ErrorResponse,
    TransactionsResponse,
    PaymentCreateRequest,
    PaymentCreateSuccessResponse,
)


# Privatbank API Client
class PBCorporateClient(BaseCorporateClient):
    BASE_URL = "https://acp.privatbank.ua/api/"

    def __init__(self, token: str, client_id: str) -> None:
        self.token = token
        self.client_id = client_id
        self.session = requests.session()
        self.session.headers.update(
            {
                "User-Agent": super().USER_AGENT,
                "Content-Type": "application/json;charset=utf-8",
                "id": self.client_id,
                "token": self.token,
            }
        )

    def get_balance(
        self, acct: IBAN, start_date: date, end_date: date
    ) -> BalanceResponse | ErrorResponse:
        with self.session.get(
            self.BASE_URL + "statements/balance",
            params={
                "acc": str(acct),
                "startDate": start_date.strftime("%d-%m-%Y"),
                "endDate": end_date.strftime("%d-%m-%Y"),
            },
        ) as r:
            if r.ok:
                return BalanceResponse(**r.json())
            else:
                return ErrorResponse(**r.json())

    def get_transactions(
        self, acct: IBAN, start_date: date, end_date: date
    ) -> TransactionsResponse | ErrorResponse:
        with self.session.get(
            self.BASE_URL + "statements/transactions",
            params={
                "acc": str(acct),
                "startDate": start_date.strftime("%d-%m-%Y"),
                "endDate": end_date.strftime("%d-%m-%Y"),
            },
        ) as r:
            if r.ok:
                return TransactionsResponse(**r.json())
            else:
                return ErrorResponse(**r.json())

    def create_payment(
        self,
        payer_acct: IBAN,
        recipient_acct: IBAN,
        recipient_nceo: IPN | str,
        payee_name: str,
        amount: float,
        designation: str,
        document_number: str,
    ) -> PaymentCreateSuccessResponse | ErrorResponse:
        with self.session.post(
            self.BASE_URL + "proxy/payment/create",
            json=PaymentCreateRequest(
                document_number=document_number,
                payer_account=str(payer_acct),
                recipient_account=str(recipient_acct),
                recipient_nceo=str(recipient_nceo),
                payment_naming=payee_name,
                payment_amount=round(amount, 2),
                payment_destination=designation,
            ).dict(),
        ) as r:
            if r.ok:
                return PaymentCreateSuccessResponse(**r.json())
            else:
                return ErrorResponse(**r.json())


"""
TODO:
* Parse dates in responses as per template (%d-%m-%Y, etc.);
* Publish to PyPI via Github Actions to be usable as a dependency
"""
