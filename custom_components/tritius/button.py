"""Button platform for tritius."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)

from .api import TritiusApiClient
from .const import _LOGGER, SERVICE_RENEW_BORROWINGS, TritiusEntityFeature
from .data import TritiusConfigEntry, TritiusData
from .entity import TritiusEntity


@dataclass(frozen=True, kw_only=True)
class TritiusButtonEntityDescription(ButtonEntityDescription):
    """Class for button entity description."""

    supported_features: int | None = None


ENTITY_DESCRIPTIONS: tuple[TritiusButtonEntityDescription, ...] = (
    TritiusButtonEntityDescription(
        key="renew_borrowings",
        translation_key="renew_borrowings",
        icon="mdi:book-open-variant-outline",
        supported_features=TritiusEntityFeature.RENEW_BORROWINGS,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: TritiusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    async_add_entities(
        TritiusButton(
            data=entry.runtime_data,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )

    platform = async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_RENEW_BORROWINGS,
        {},
        "async_press",
    )


class TritiusButton(TritiusEntity, ButtonEntity):
    """Tritius Button class."""

    _client: TritiusApiClient

    def __init__(
        self,
        data: TritiusData,
        entity_description: TritiusButtonEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(data, entity_description.key)
        self._client = data.client
        self.entity_description = entity_description

        if entity_description.supported_features is not None:
            self._attr_supported_features = entity_description.supported_features

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug("Renew pressed")
        await self._client.async_renew_all()
        await self.coordinator.async_request_refresh()
