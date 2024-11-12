"""Button platform for tritius."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import TritiusApiClient
from .const import _LOGGER
from .data import TritiusConfigEntry, TritiusData
from .entity import TritiusEntity

ENTITY_DESCRIPTIONS: tuple[ButtonEntityDescription, ...] = (
    ButtonEntityDescription(
        key="renew_borrowings",
        translation_key="renew_borrowings",
        icon="mdi:book-open-variant-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
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


class TritiusButton(TritiusEntity, ButtonEntity):
    """Tritius Button class."""

    _client: TritiusApiClient

    def __init__(
        self,
        data: TritiusData,
        entity_description: ButtonEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(data, entity_description.key)
        self._client = data.client
        self.entity_description = entity_description

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug("Renew pressed")
        await self._client.async_renew_borrowings()
        await self.coordinator.async_request_refresh()
