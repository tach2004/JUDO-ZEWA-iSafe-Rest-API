"""my config entry."""

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

@dataclass
class MyData:
    """My config data."""

    rest_api: any
    hass: HomeAssistant
    coordinator: any  # MyCoordinator

type MyConfigEntry = ConfigEntry[MyData]
