"""DataUpdateCoordinator for tritius."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, TypedDict

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    TritiusApiClient,
    TritiusApiClientAuthenticationError,
    TritiusApiClientError,
    TritiusBorrowing,
    TritiusUser,
)
from .const import _LOGGER, DOMAIN


class TritiusCoordinatorData(TypedDict):
    """All data retrieved by api."""

    user: TritiusUser | None
    borrowings: list[TritiusBorrowing] | None


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class TritiusDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, client: TritiusApiClient) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=1),
        )
        self._client = client

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            async with self._client.authorized():
                return TritiusCoordinatorData(
                    user=await self._client.async_get_user_data(),
                    borrowings=await self._client.async_get_borrowings(),
                )
        except TritiusApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except TritiusApiClientError as exception:
            raise UpdateFailed(exception) from exception
