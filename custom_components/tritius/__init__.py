"""Custom integration to integrate tritius with Home Assistant.

For more details about this integration, please refer to
https://github.com/tykovec/home-assistant-tritius

"""

from __future__ import annotations

from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import TritiusApiClient
from .coordinator import TritiusDataUpdateCoordinator
from .data import TritiusConfigEntry, TritiusData
from .services import async_setup_services

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TritiusConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    client = TritiusApiClient(
        url=entry.data[CONF_URL],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        session=async_create_clientsession(hass),
    )

    user = await client.async_get_user_data()

    coordinator = TritiusDataUpdateCoordinator(hass, client)
    entry.runtime_data = TritiusData(
        client=client,
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
        user=user,
    )

    # load first entities
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # fill them with value from first coordimnator loading
    await coordinator.async_config_entry_first_refresh()

    await async_setup_services(hass)

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
