"""Sensor platform for tritius."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import date
from typing import Any

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .api import TritiusApiClient, TritiusApiClientError
from .const import _LOGGER
from .data import (
    TritiusConfigEntry,
    TritiusData,
)
from .entity import TritiusEntity

ENTITY_DESCRIPTIONS: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key="auto_renew_borrowings",
        translation_key="auto_renew_borrowings",
        icon="mdi:autorenew",
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
        self._last_run = None
        self._state = False
        self.entity_description = entity_description

    async def async_added_to_hass(self) -> None:
        """Call when the switch is added to hass."""
        await super().async_added_to_hass()
        if not (last_state := await self.async_get_last_state()):
            _LOGGER.debug("No old state detected")
            return
        _LOGGER.debug("Last state %s", last_state.attributes)
        _LOGGER.debug("Last state %s", last_state.state)
        self._state = last_state.state == STATE_ON
        self._last_run = last_state.attributes.get("last_run")

    @property
    def is_on(self) -> bool | None:
        """Return true if device is on."""
        return self._state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        self._state = False
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> Mapping[Any, Any]:
        """Return the state attributes."""
        return {"last_run": self._last_run}

    @callback
    def _handle_coordinator_update(self):
        now = date.today()
        result = False

        # Run update only once a day
        if (
            self.coordinator.data.has_borrowing_alert()
            and self._last_run != now
            and self._state
        ):
            try:
                result = asyncio.run_coroutine_threadsafe(
                    self._client.async_renew_borrowings(),
                    self.hass.loop,
                ).result()
            except TritiusApiClientError as ex:
                _LOGGER.debug("Unable to renew borrowings %s", ex)
            else:
                if result:
                    self.hass.async_create_task(
                        self.coordinator.async_request_refresh()
                    )
            finally:
                self._last_run = now
