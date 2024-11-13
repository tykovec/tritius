"""Sensor platform for tritius."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import TritiusUser
from .data import (
    TritiusConfigEntry,
    TritiusData,
)
from .entity import TritiusEntity, TritiusEntityMixin


@dataclass(frozen=True, kw_only=True)
class TritiusSensorEntityDescription(SensorEntityDescription, TritiusEntityMixin):
    """Custom sensor entity description with retrieval expression."""


ENTITY_DESCRIPTIONS: tuple[TritiusSensorEntityDescription, ...] = (
    TritiusSensorEntityDescription(
        key="borrowings",
        translation_key="borrowings",
        icon="mdi:book-open-variant-outline",
        value_fn=lambda x: 0 if x.borrowings is None else len(x.borrowings),
        attr_fn=lambda x: {"borrowings": x.borrowings or []},
    ),
    TritiusSensorEntityDescription(
        key="registration_expiration",
        translation_key="registration_expiration",
        icon="mdi:calendar-alert",
        value_fn=lambda x: x.user.registration_expiration
        if isinstance(x.user, TritiusUser)
        else None,
    ),
    TritiusSensorEntityDescription(
        key="borrowing_expiration",
        translation_key="borrowing_expiration",
        icon="mdi:calendar-alert",
        value_fn=lambda x: x.borrowing_expiration,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TritiusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        TritiusSensor(
            data=entry.runtime_data,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class TritiusSensor(TritiusEntity, SensorEntity):
    """Tritius sensor class."""

    entity_description: TritiusSensorEntityDescription

    def __init__(
        self,
        data: TritiusData,
        entity_description: TritiusSensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(data, entity_description.key)
        self.entity_description = entity_description

    @callback
    def _handle_coordinator_update(self):
        self._attr_native_value = self.entity_description.value_fn(
            self.coordinator.data
        )
        if self.entity_description.attr_fn is not None:
            self._attr_extra_state_attributes = self.entity_description.attr_fn(
                self.coordinator.data
            )
        super().async_write_ha_state()
