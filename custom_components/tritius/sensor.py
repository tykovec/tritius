"""Sensor platform for tritius."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import LOGGER
from .coordinator import TritiusDataUpdateCoordinator
from .data import (
    TritiusBorrowing,
    TritiusConfigEntry,
    TritiusEntityMixin,
    TritiusUser,
)
from .entity import TritiusEntity


@dataclass(frozen=True, kw_only=True)
class TritiusSensorEntityDescription(SensorEntityDescription, TritiusEntityMixin):
    """Custom sensor entity description with retrieval expression."""


ENTITY_DESCRIPTIONS: tuple[TritiusSensorEntityDescription, ...] = (
    TritiusSensorEntityDescription(
        key="borrowings",
        name="Borrowings",
        icon="mdi:book-open-variant-outline",
        value_lambda=lambda x: len(x.get("borrowings", [])),
        attr_lambda=lambda x: {"borrowings": x.get("borrowings", [])},
    ),
    TritiusSensorEntityDescription(
        key="registration_expiration",
        name="Registration expiration",
        icon="mdi:calendar-alert",
        value_lambda=lambda x: cast(TritiusUser, x.get("user")).registration_expiration
        if "user" in x and isinstance(x.get("user"), TritiusUser)
        else None,
    ),
    TritiusSensorEntityDescription(
        key="borrowing_expiration",
        name="Borrowing expiration",
        icon="mdi:calendar-alert",
        value_lambda=lambda x: cast(
            TritiusBorrowing, x.get("borrowings", [])[0]
        ).due_date
        if bool(x.get("borrowings", []))
        else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: TritiusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        TritiusSensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class TritiusSensor(TritiusEntity, SensorEntity):
    """Tritius Sensor class."""

    entity_description: TritiusSensorEntityDescription

    def __init__(
        self,
        coordinator: TritiusDataUpdateCoordinator,
        entity_description: TritiusSensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator, entity_description.key)
        self.entity_description = entity_description

    @callback
    def _handle_coordinator_update(self):
        LOGGER.debug("Update called")
        self._attr_native_value = self.entity_description.value_lambda(
            self.coordinator.data
        )
        if self.entity_description.attr_lambda is not None:
            self._attr_extra_state_attributes = self.entity_description.attr_lambda(
                self.coordinator.data
            )
        super().async_write_ha_state()
