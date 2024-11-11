"""Sample API Client."""

from __future__ import annotations

import socket
import urllib
import urllib.parse
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date, datetime

import aiohttp
import async_timeout
from bs4 import BeautifulSoup, PageElement, Tag
from homeassistant.exceptions import HomeAssistantError

from .const import _LOGGER, Selector, Url


@dataclass
class TritiusBorrowing:
    """Tritius borrowing information informations."""

    author: str
    title: str
    id: int
    expiration: date


@dataclass
class TritiusUser:
    """Tritius user informations."""

    url: str
    id: str
    name: str
    surname: str
    registration_expiration: date | None


class TritiusApiClientError(Exception):
    """Exception to indicate a general API error."""


class TritiusApiClientCommunicationError(
    TritiusApiClientError,
):
    """Exception to indicate a communication error."""


class TritiusUnknownStructureError(TritiusApiClientError):
    """Exception to indicate unknown structure of html."""


class TritiusApiClientAuthenticationError(
    TritiusApiClientError,
):
    """Exception to indicate an authentication error."""


class TritiusApplicationError(TritiusApiClientError):
    """Exception error in appication."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in {401, 403}:
        msg = "Invalid credentials"
        raise TritiusApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


def _get_form_inputs(tag: Tag) -> dict[str, str]:
    """Get form data for tag."""
    inputs = tag.select("input")
    return (
        {
            x.attrs["name"]: x.attrs["value"]
            for x in inputs
            if x.attrs is not None and "name" in x.attrs and "value" in x.attrs
        }
        if inputs is not None
        else {}
    )


def _format(tag: PageElement) -> str:
    """Format page element to string."""
    return tag.text.removeprefix("\n").removesuffix("\n")


def _formatdate(tag: PageElement) -> date:
    """Format page element to date."""
    return datetime.strptime(_format(tag), "%d.%m.%Y").date()


def _select_one(tag: Tag, selector: str) -> Tag:
    """Select one element from page, when not found throw exception."""
    s = tag.select_one(selector)
    if s is None:
        raise TritiusUnknownStructureError(f"Tag searched by '{selector}' not found")
    return s


class TritiusAuthenticatedContext:
    """Context for telling that we are authenticated."""

    def __init__(self):
        """Initialize class."""

    def __enter__(self):
        """Enter resource usage."""
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Exit resource usage."""


class TritiusApiConnection:
    """Api connection for basic operation."""

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Tritius scraper Client."""
        parsed = urllib.parse.urlsplit(url)
        formatted_url = "https://" if parsed.scheme == "" else parsed.scheme + "://"
        if parsed.netloc != "":
            formatted_url += parsed.netloc
        formatted_url += parsed.path
        formatted_url += "" if parsed.path.endswith("/") else "/"

        self.url = formatted_url
        self.username = username
        self.password = password
        self._session = session
        self._cx = None

    async def get(self, url: str = "", data: dict | None = None) -> BeautifulSoup:
        """Get operation."""
        page = await self._api_wrapper("get", url, data)

        soup = BeautifulSoup(await page.text(), "html.parser")

        if self._cx is not None:
            _LOGGER.debug("Running in authorization context, omit login checking")
        else:
            _LOGGER.debug("Ensures logged in")
            form = soup.select_one(Selector.LOGIN_FORM)
            if form is not None:
                _LOGGER.debug("Login form found try to login")
                inputs = _get_form_inputs(form)
                inputs["username"] = self.username
                inputs["password"] = self.password
                form = await self.post(Url.LOGIN, data=inputs, omitErrorParsing=True)

                _LOGGER.debug("Retrieve page again")
                page = await self._api_wrapper("get", url, data)
                soup = BeautifulSoup(await page.text(), "html.parser")
                form = soup.select_one(Selector.LOGIN_FORM)
                if form is not None:
                    _LOGGER.debug("Login page found raising error")
                    raise TritiusApiClientAuthenticationError

        return soup

    async def post(
        self, url: str, data: dict | None = None, omitErrorParsing=False
    ) -> BeautifulSoup | None:
        """Post operation."""
        page = await self._api_wrapper("post", url, data)
        soap = BeautifulSoup(await page.text(), "html.parser")
        if not omitErrorParsing:
            alert = soap.select_one("div.flash-messages div.alert-danger span")
            if alert is not None:
                raise TritiusApplicationError(alert.text)

        return soap

    @asynccontextmanager
    async def authorized(self):
        """Enforce authorization for all next calls."""
        try:
            await self.get()
            self._cx = TritiusAuthenticatedContext()
            yield self._cx
        finally:
            self._cx = None

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> aiohttp.ClientResponse:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                _LOGGER.debug("Calling %s %s data=%s", method, self.url + url, data)
                response = await self._session.request(
                    method=method, url=self.url + url, headers=headers, data=data
                )
                _verify_response_or_raise(response)
                return response

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise TritiusApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise TritiusApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise TritiusApiClientError(
                msg,
            ) from exception


class TritiusApiClient:
    """Tritius scraper Client."""

    _connection: TritiusApiConnection

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Tritius scraper Client."""
        self._connection = TritiusApiConnection(url, username, password, session)

    @asynccontextmanager
    async def authorized(self):
        """Run client in authorized context."""
        async with self._connection.authorized():
            yield

    async def async_get_user_data(self) -> TritiusUser:
        """Parse user data from profile page."""
        html = await self._connection.get(Url.PERSONAL_DATA)
        pers_data = _select_one(html, Selector.PORTLET_PERSONAL_DATA)

        registration_expiration = _formatdate(
            _select_one(html, Selector.REGISTRATION_EXPIRATION)
        )

        input_data = _get_form_inputs(pers_data)

        return TritiusUser(
            self._connection.url,
            input_data.get("values[readerNumber]", ""),
            input_data.get("values[firstname]", ""),
            input_data.get("values[lastname]", ""),
            registration_expiration,
        )

    async def async_get_borrowings(self) -> list[TritiusBorrowing] | None:
        """Get list of borrowings."""

        borrowings_page = await self.async_get_borrowings_page()

        items = borrowings_page.select(
            Selector.PORTLET_BORROWINGS + " " + Selector.PORTLET_BORROWINGS_DATA
        )

        borrowings: list[TritiusBorrowing] = []
        for item in items:
            tds = item.select("td")
            form = _select_one(tds[7], "form")
            id_tag = _select_one(form, "input[name='id']")
            borrowing_id = int(id_tag.attrs["value"])
            expiration = _formatdate(tds[2])
            borrowings.append(
                TritiusBorrowing(
                    author=_format(tds[5]),
                    title=_format(_select_one(tds[4], "a")),
                    id=borrowing_id,
                    expiration=expiration,
                )
            )
        borrowings.sort(key=lambda x: (x.expiration, x.title))
        return borrowings

    async def async_renew_all(self) -> bool:
        """Renew all borrowings."""
        borrowings_page = await self.async_get_borrowings_page()
        form = borrowings_page.select_one(Selector.RENEW_ALL_FORM)
        if form is None:
            _LOGGER.debug("Nothing to renew")
            return False
        try:
            await self._connection.post(Url.RENEW_ALL, data=_get_form_inputs(form))
        except Exception as e:
            raise HomeAssistantError(e) from e

        return True

    async def async_get_borrowings_page(self) -> BeautifulSoup:
        """Get convenience borrowing page."""
        return await self._connection.get(Url.BORROWINGS)
