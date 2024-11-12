"""Button platform for tritius."""

from __future__ import annotations

import homeassistant.helpers.config_validation as cv
import homeassistant.helpers.device_registry as dr
import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_DEVICE_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .const import _LOGGER, DOMAIN, SERVICE_RENEW_BORROWINGS
from .data import TritiusConfigEntry


async def async_setup_services(
    hass: HomeAssistant,
) -> None:
    """Set up the services."""

    async def collect_entries(
        device_ids: list[str],
    ) -> list[TritiusConfigEntry]:
        config_entries = list[TritiusConfigEntry]()
        registry = dr.async_get(hass)
        for target in device_ids:
            device = registry.async_get(target)
            if device:
                device_entries = list[TritiusConfigEntry]()
                for entry_id in device.config_entries:
                    entry = hass.config_entries.async_get_entry(entry_id)
                    if entry and entry.domain == DOMAIN:
                        device_entries.append(entry)
                if not device_entries:
                    raise HomeAssistantError(
                        f"Device '{target}' is not a {DOMAIN} device"
                    )
                config_entries.extend(device_entries)
            else:
                raise HomeAssistantError(
                    f"Device '{target}' not found in device registry"
                )
        entries = list[TritiusConfigEntry]()
        for config_entry in config_entries:
            if config_entry.state != ConfigEntryState.LOADED:
                raise HomeAssistantError(f"{config_entry.title} is not loaded")
            entries.append(config_entry)
        return entries

    async def async_renew_borrowings(call: ServiceCall) -> None:
        """Renew borrowings."""
        for config_entry in await collect_entries(call.data[ATTR_DEVICE_ID]):
            _LOGGER.debug("Renew service called for %s", ATTR_DEVICE_ID)
            await config_entry.runtime_data.client.async_renew_borrowings()
            await config_entry.runtime_data.coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        SERVICE_RENEW_BORROWINGS,
        async_renew_borrowings,
        schema=vol.Schema(
            vol.All(
                {
                    vol.Required(ATTR_DEVICE_ID): cv.ensure_list,
                }
            )
        ),
    )
