"""TritiusEntity class."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import LOGGER
from .coordinator import TritiusDataUpdateCoordinator


class TritiusEntity(CoordinatorEntity[TritiusDataUpdateCoordinator]):
    """TritiusEntity class."""

    def __init__(self, coordinator: TritiusDataUpdateCoordinator, suffix: str) -> None:
        """Initialize."""
        super().__init__(coordinator)
        config_entry = coordinator.config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_{suffix}"
        self._attr_has_entity_name = True

        LOGGER.debug("Entity %s created", self._attr_unique_id)
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    config_entry.domain,
                    config_entry.entry_id,
                ),
            },
            name=f"{config_entry.runtime_data.user.name} {config_entry.runtime_data.user.surname}",
        )
