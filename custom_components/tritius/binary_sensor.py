"""Binary sensor platform for tritius."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import TritiusDataUpdateCoordinator
from .data import TritiusConfigEntry
from .entity import TritiusEntity

ENTITY_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="binary_sensor",
        name="Tritius Binary Sensor",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TritiusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    async_add_entities(
        TritiusBinarySensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class TritiusBinarySensor(TritiusEntity, BinarySensorEntity):
    """tritius binary_sensor class."""

    def __init__(
        self,
        coordinator: TritiusDataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator, entity_description.key)
        self.entity_description = entity_description

    @callback
    def _handle_coordinator_update(self):
        self._attr_is_on = False
