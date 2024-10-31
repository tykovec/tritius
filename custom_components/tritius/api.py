"""Sample API Client."""

from __future__ import annotations

import socket
import urllib
import urllib.parse
from datetime import date, datetime
from typing import Any

import aiohttp
import async_timeout
from bs4 import BeautifulSoup, PageElement, Tag

from .const import LOGGER
from .data import TritiusBorrowing, TritiusUser


class TritiusApiClientError(Exception):
    """Exception to indicate a general API error."""


class TritiusApiClientCommunicationError(
    TritiusApiClientError,
):
    """Exception to indicate a communication error."""


class TritiusApiClientAuthenticationError(
    TritiusApiClientError,
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in {401, 403}:
        msg = "Invalid credentials"
        raise TritiusApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


class Soup:
    """Convenience html parsing class."""

    @staticmethod
    async def html(response: aiohttp.ClientResponse) -> BeautifulSoup:
        """Create html soup parser."""
        return BeautifulSoup(await response.text(), "html.parser")

    @staticmethod
    async def html_one(response: aiohttp.ClientResponse, selector: str) -> Tag | None:
        """Create html soup parser."""
        bs = BeautifulSoup(await response.text(), "html.parser")
        return bs.select_one(selector)

    @staticmethod
    def tag_one_attr(tag: Tag | None, selector: str, attr: str) -> str:
        """Create html soup parser."""
        if tag is None:
            return ""
        tag = tag.select_one(selector)
        if tag is None:
            return ""
        if attr not in tag.attrs:
            return ""

        return tag.attrs[attr]


class TritiusApiClient:
    """Tritius scraper Client."""

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

        self._url = formatted_url
        self._username = username
        self._password = password
        self._session = session

    async def login(self) -> TritiusUser:
        """Ensure if user is logger in."""
        user = await self._async_parse_user_data()
        if user is TritiusUser:
            return user
        if user is None:
            raise TritiusApiClientAuthenticationError

        LOGGER.debug("Try to log in")

        await self._api_wrapper(
            "post",
            "process-login",
            data={
                "username": self._username,
                "password": self._password,
                "_csrf": user,
                "wd": "",
                "target_url": "",
            },
        )

        user = await self._async_parse_user_data()
        if isinstance(user, TritiusUser):
            return user
        raise TritiusApiClientAuthenticationError

    async def _async_parse_user_data(self) -> TritiusUser | str | None:
        """Parse user data from profile page.

        Returns TritiusUser when logged in
                str crfs token for ligin
        """
        html = await self._api_wrapper_soup("get", "profile/personal-data")

        csrf = html.select_one("form.login-form input[name='_csrf']")
        if csrf is not None:
            value = csrf.attrs["value"]
            LOGGER.debug("User not logged in returning csrf:%s", value)
            return value

        pers_data = html.select_one("#portlet-personal-data")
        if pers_data is None:
            LOGGER.debug("Pers data not found")
            return None
        LOGGER.debug("User logged in")

        registration_expiration_tag = html.select_one(
            "#navbar li.dropdown-user li.hidden-xs span.dropdown-text"
        )
        registration_expiration = (
            None
            if registration_expiration_tag is None
            else datetime.strptime(registration_expiration_tag.text, "%d.%m.%Y").date()
        )

        inputs = pers_data.select("input")
        input_data = (
            {
                x.attrs["name"]: x.attrs["value"]
                for x in inputs
                if x.attrs is not None and "name" in x.attrs and "value" in x.attrs
            }
            if inputs is not None
            else {}
        )

        return TritiusUser(
            input_data.get("values[readerNumber]", ""),
            input_data.get("values[firstname]", ""),
            input_data.get("values[lastname]", ""),
            registration_expiration,
        )

    async def async_get_borrowings(self) -> list[TritiusBorrowing] | None:
        """Parse borrowings.

        Returns list of borrowings
        """

        def _format(tag: PageElement | None) -> str:
            if tag is None:
                return ""
            return tag.text.removeprefix("\n").removesuffix("\n")

        def _formatdate(tag: PageElement) -> date:
            return datetime.strptime(_format(tag), "%d.%m.%Y").date()

        borrowings_page = await self.async_get_borrowings_page()

        items = borrowings_page.select(
            "#borrowings-portlet .portlet-content table tbody tr"
        )

        borrowings: list[TritiusBorrowing] = []
        for item in items:
            tds = item.select("td")
            form = tds[7].select_one("form")
            if form is None:
                continue
            id_tag = form.select_one("input[name='id']")
            borrowing_id = 0
            if id_tag is not None:
                borrowing_id = int(id_tag.attrs["value"])
            due_date = _formatdate(tds[2])
            borrowings.append(
                TritiusBorrowing(
                    author=_format(tds[5]),
                    title=_format(tds[4].select_one("a")),
                    id=borrowing_id,
                    due_date=due_date,
                )
            )
        borrowings.sort(key=lambda x: (x.due_date, x.title))
        return borrowings

    async def async_renew_all(self) -> bool:
        """Renew all borrowings."""
        borrowings_page = await self.async_get_borrowings_page()
        renew_all_url = "profile/renew-all"
        csrf = borrowings_page.select_one(
            f"form[action='/{renew_all_url}'] input[name='_csrf']"
        )
        if csrf is None:
            LOGGER.debug("Nothing to renew")
            return False
        await self._api_wrapper("post", renew_all_url, data={"_csrf": csrf})
        return True

    async def async_get_borrowings_page(self) -> BeautifulSoup:
        """Get convenience borrowing page."""
        return await self._api_wrapper_soup("get", "profile/borrowings/current")

    async def _api_wrapper_soup(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> BeautifulSoup:
        page = await self._api_wrapper(method, url, data, headers)
        return await Soup.html(page)

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                LOGGER.debug("Calling %s %s", method, self._url + url)
                response = await self._session.request(
                    method=method, url=self._url + url, headers=headers, data=data
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
