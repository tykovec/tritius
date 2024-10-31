"""Custom integration to integrate tritius with Home Assistant.

For more details about this integration, please refer to
https://github.com/tykovec/tritius

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import TritiusApiClient
from .coordinator import TritiusDataUpdateCoordinator
from .data import TritiusData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import TritiusConfigEntry

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: TritiusConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    client = TritiusApiClient(
        url=entry.data[CONF_URL],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        session=async_get_clientsession(hass),
    )

    user = await client.login()

    coordinator = TritiusDataUpdateCoordinator(
        hass=hass,
    )
    entry.runtime_data = TritiusData(
        client=client,
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
        user=user,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: TritiusConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: TritiusConfigEntry,
) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
