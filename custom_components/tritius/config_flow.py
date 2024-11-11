"""Adds config flow for Tritius."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    TritiusApiClient,
    TritiusApiClientAuthenticationError,
    TritiusApiClientCommunicationError,
    TritiusApiClientError,
    TritiusUser,
)
from .const import _LOGGER, DOMAIN


class TritiusFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Tritius."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> data_entry_flow.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                user = await self._test_credentials(
                    url=user_input[CONF_URL],
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )

                if not isinstance(user, TritiusUser):
                    raise TritiusApiClientAuthenticationError

            except TritiusApiClientAuthenticationError as exception:
                _LOGGER.warning(exception)
                _errors["base"] = "auth"
            except TritiusApiClientCommunicationError as exception:
                _LOGGER.error(exception)
                _errors["base"] = "connection"
            except TritiusApiClientError as exception:
                _LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"{user.name} {user.surname}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_URL,
                        default=(user_input or {}).get(CONF_URL, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(
                        CONF_USERNAME,
                        default=(user_input or {}).get(CONF_USERNAME, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def _test_credentials(
        self, url: str, username: str, password: str
    ) -> TritiusUser:
        """Validate credentials."""
        session = async_create_clientsession(self.hass)
        client = TritiusApiClient(
            url=url,
            username=username,
            password=password,
            session=session,
        )
        return await client.async_get_user_data()
