"""Sensor platform for tritius."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from custom_components.tritius.const import _LOGGER

from .api import TritiusApiClient
from .data import (
    TritiusConfigEntry,
    TritiusData,
)
from .entity import TritiusEntity

ENTITY_DESCRIPTIONS: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key="auto_renew_borrowings",
        translation_key="auto_renew_borrowings",
        icon="mdi:book-open-variant-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TritiusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        TritiusSwitchSensor(
            data=entry.runtime_data,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class TritiusSwitchSensor(TritiusEntity, RestoreEntity, SwitchEntity):
    """Tritius sensor class."""

    entity_description: SwitchEntityDescription
    _last_run: date | None
    _client: TritiusApiClient

    def __init__(
        self,
        data: TritiusData,
        entity_description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch class."""
        super().__init__(data, entity_description.key)
        self._client = data.client
        self.entity_description = entity_description

    async def async_added_to_hass(self) -> None:
        """Call when the switch is added to hass."""
        if not (last_state := await self.async_get_last_state()):
            return
        self._attr_is_on = last_state.state == STATE_ON
        self._last_run = last_state.attributes.get("last_run")
        await super().async_added_to_hass()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        self._attr_is_on = False
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> Mapping[Any, Any]:
        """Return the state attributes."""
        return {"last_run": self._last_run}

    @callback
    async def _handle_coordinator_update(self):
        now = datetime.date.now()
        result = False

        # Run update only once a day
        if self.coordinator.data.has_borrowing_alert() and self._last_run != now:
            try:
                result = asyncio.run_coroutine_threadsafe(
                    self._client.async_renew_borrowings(),
                    self.hass.loop,
                ).result()
            except:  # noqa: E722
                _LOGGER.debug("Unable to renew borrowings")
            else:
                if result:
                    self.hass.async_create_task(
                        self.coordinator.async_request_refresh()
                    )
            finally:
                self._last_run = now
