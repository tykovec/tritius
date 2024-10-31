"""Button platform for tritius."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription

from .api import TritiusApiClient
from .const import LOGGER
from .entity import TritiusEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import TritiusDataUpdateCoordinator
    from .data import TritiusConfigEntry

ENTITY_DESCRIPTIONS: tuple[ButtonEntityDescription, ...] = (
    ButtonEntityDescription(
        key="renew_borrowings",
        name="Renew borrowings",
        icon="mdi:book-open-variant-outline",
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
            coordinator=entry.runtime_data.coordinator,
            client=entry.runtime_data.client,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class TritiusButton(TritiusEntity, ButtonEntity):
    """Tritius Button class."""

    _client: TritiusApiClient

    def __init__(
        self,
        coordinator: TritiusDataUpdateCoordinator,
        client: TritiusApiClient,
        entity_description: ButtonEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator, entity_description.key)
        self._client = client
        self.entity_description = entity_description

    async def async_press(self) -> None:
        """Handle the button press."""
        LOGGER.debug("Renew pressed")
        await self._client.login()
        await self._client.async_renew_all()
        await self.coordinator.async_request_refresh()
