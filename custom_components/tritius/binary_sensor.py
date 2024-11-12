"""Sensor platform for tritius."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .data import (
    TritiusConfigEntry,
    TritiusData,
)
from .entity import TritiusEntity, TritiusEntityMixin


@dataclass(frozen=True, kw_only=True)
class TritiusBinarySensorEntityDescription(
    BinarySensorEntityDescription, TritiusEntityMixin
):
    """Custom binary sensor entity description with expression."""


ENTITY_DESCRIPTIONS: tuple[TritiusBinarySensorEntityDescription, ...] = (
    TritiusBinarySensorEntityDescription(
        key="borrowings_alert",
        translation_key="borrowings_alert",
        icon="mdi:alert",
        value_fn=lambda x: x.has_borrowing_alert(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TritiusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        TritiusBinarySensor(
            data=entry.runtime_data,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class TritiusBinarySensor(TritiusEntity, BinarySensorEntity):
    """Tritius binary sensor class."""

    entity_description: TritiusBinarySensorEntityDescription

    def __init__(
        self,
        data: TritiusData,
        entity_description: TritiusBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor class."""
        super().__init__(data, entity_description.key)
        self.entity_description = entity_description

    @callback
    def _handle_coordinator_update(self):
        self._attr_is_on = self.entity_description.value_fn(self.coordinator.data)
        super().async_write_ha_state()
