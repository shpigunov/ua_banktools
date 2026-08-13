from datetime import date
from typing import Optional, Type, TypeVar

import httpx
from pydantic import BaseModel, ValidationError
from schwifty import IBAN

from ua_banktools.core import IPN

#: Bounded default so a hung upstream cannot block a caller indefinitely.
#: Override by passing your own ``session`` if you need a different budget --
#: routing through a throttling proxy, for instance, can legitimately take
#: longer than a direct call to the bank.
DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)

ErrorModel = TypeVar("ErrorModel", bound=BaseModel)


class BankTransportError(RuntimeError):
    """An HTTP error response that is not one of the bank's own error payloads.

    Monobank and the PrivatBank corporate API describe their failures with
    documented JSON bodies, and the clients return those as values so callers
    can branch on them. Anything else -- a proxy rejecting the request, an HTML
    error page, a gateway timeout -- carries no such body, and parsing it as one
    would surface as a confusing ``ValidationError`` far from the cause. Those
    cases raise this instead.
    """

    def __init__(self, status_code: int, body: str, url: str = "") -> None:
        self.status_code = status_code
        self.body = body
        self.url = url
        excerpt = body[:200] + "…" if len(body) > 200 else body
        location = f" from {url}" if url else ""
        super().__init__(
            f"HTTP {status_code}{location} was not a recognisable bank error "
            f"response: {excerpt!r}"
        )


def build_session(session: Optional[httpx.Client] = None) -> httpx.Client:
    """Return the caller's session, or a default one with a bounded timeout."""
    if session is not None:
        return session
    return httpx.Client(follow_redirects=True, timeout=DEFAULT_TIMEOUT)


def parse_error(response: httpx.Response, model: Type[ErrorModel]) -> ErrorModel:
    """Parse an error response as the bank's own error model.

    Raises :class:`BankTransportError` when the body is not JSON or does not
    match ``model`` -- see that class for why this is worth distinguishing.
    """
    try:
        payload = response.json()
    except ValueError as exc:
        raise BankTransportError(
            response.status_code, response.text, str(response.request.url)
        ) from exc

    try:
        return model(**payload)
    except (ValidationError, TypeError) as exc:
        raise BankTransportError(
            response.status_code, response.text, str(response.request.url)
        ) from exc


class BasePersonalClient:
    def __init__(self):
        pass


class BaseCorporateClient:
    """This class serves as a blueprint for creating new clients for corporate
    banking APIs. It includes methods usually expected from such a client."""

    USER_AGENT = "ua_banktools API Client"
    BASE_URL = ""

    def __init__(
        self,
        token: str,
        client_id: str = "",
        session: Optional[httpx.Client] = None,
    ) -> None:
        self.token = token
        self.client_id = client_id
        self.session = build_session(session)

    def get_balance(self, acct: IBAN, start_date: date, end_date: date):
        pass

    def get_transactions(self, acct: IBAN, start_date: date, end_date: date):
        pass

    def create_payment(
        self,
        payer_acct: IBAN,
        recipient_acct: IBAN,
        recipient_nceo: IPN | str,
        payee_name: str,
        amount: float,
        designation: str,
        document_number: str,
    ):
        pass
