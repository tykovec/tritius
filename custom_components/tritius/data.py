"""Custom types for tritius."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import TritiusApiClient
    from .coordinator import TritiusDataUpdateCoordinator


type TritiusConfigEntry = ConfigEntry[TritiusData]


class TritiusCoordinatorData(TypedDict):
    """All data retrieved by api."""

    user: TritiusUser | None
    borrowings: list[TritiusBorrowing] | None


@dataclass(frozen=True, kw_only=True)
class TritiusEntityMixin:
    """Mixin for lambda data retrieval."""

    value_lambda: Callable[[dict[str, Any]], Any]
    attr_lambda: Callable[[dict[str, Any]], Any] | None = None


@dataclass
class TritiusBorrowing:
    """Tritius borrowing information informations."""

    author: str
    title: str
    id: int
    due_date: date


@dataclass
class TritiusUser:
    """Tritius user informations."""

    id: str
    name: str
    surname: str
    registration_expiration: date | None


@dataclass
class TritiusData:
    """Data for the Tritius integration."""

    client: TritiusApiClient
    coordinator: TritiusDataUpdateCoordinator
    integration: Integration
    user: TritiusUser
