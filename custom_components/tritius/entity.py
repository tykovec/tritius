"""TritiusEntity class."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import _LOGGER, DOMAIN
from .coordinator import TritiusDataUpdateCoordinator
from .data import TritiusData


class TritiusEntity(CoordinatorEntity[TritiusDataUpdateCoordinator]):
    """TritiusEntity class."""

    def __init__(self, data: TritiusData, suffix: str) -> None:
        """Initialize."""
        coordinator = data.coordinator
        # config_entry = data.integration.confi()

        super().__init__(coordinator)
        device_id = f"{data.user.url}_{data.user.id}"
        self._attr_unique_id = f"{device_id}_{suffix}"
        self._attr_has_entity_name = True
        device_name = f"{data.user.name} {data.user.surname}"
        _LOGGER.debug(
            "Entity %s for device %s created", self._attr_unique_id, device_name
        )
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    device_id,
                ),
            },
            name=device_name,
        )


@dataclass(frozen=True, kw_only=True)
class TritiusEntityMixin:
    """Mixin for lambda data retrieval."""

    value_fn: Callable[[dict[str, Any]], Any]
    attr_fn: Callable[[dict[str, Any]], Any] | None = None
