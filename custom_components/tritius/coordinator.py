"""DataUpdateCoordinator for tritius."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    TritiusApiClientAuthenticationError,
    TritiusApiClientError,
)
from .const import DOMAIN, LOGGER
from .data import TritiusCoordinatorData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import TritiusConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class TritiusDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: TritiusConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=1),
        )

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            user = await self.config_entry.runtime_data.client.login()

            return TritiusCoordinatorData(
                user=user,
                borrowings=await self.config_entry.runtime_data.client.async_get_borrowings(),
            )
        except TritiusApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except TritiusApiClientError as exception:
            raise UpdateFailed(exception) from exception
