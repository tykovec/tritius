"""Custom types for tritius."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.loader import Integration

from .api import TritiusApiClient, TritiusUser
from .coordinator import TritiusDataUpdateCoordinator

type TritiusConfigEntry = ConfigEntry[TritiusData]


@dataclass
class TritiusData:
    """Data for the Tritius integration."""

    client: TritiusApiClient
    coordinator: TritiusDataUpdateCoordinator
    integration: Integration
    user: TritiusUser
