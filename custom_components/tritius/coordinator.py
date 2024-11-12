"""DataUpdateCoordinator for tritius."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

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
from .const import _LOGGER, ALERT_DELTA, DOMAIN


@dataclass  # noqa: F821
class TritiusCoordinatorData:
    """All data retrieved by api."""

    user: TritiusUser | None
    borrowings: list[TritiusBorrowing] | None
    borrowing_expiration: date | None

    def has_borrowing_alert(self) -> bool:
        """Borrowing alert of data."""
        return self.borrowing_expiration is not None and self.borrowing_expiration <= (
            date.today() + ALERT_DELTA
        )


class TritiusDataUpdateCoordinator(DataUpdateCoordinator[TritiusCoordinatorData]):
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
                borrowings = await self._client.async_get_borrowings()
                return TritiusCoordinatorData(
                    user=await self._client.async_get_user_data(),
                    borrowings=borrowings,
                    borrowing_expiration=borrowings[0].expiration
                    if bool(borrowings)
                    else None,
                )
        except TritiusApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except TritiusApiClientError as exception:
            raise UpdateFailed(exception) from exception
