"""Setting up my valve entities.

Leckageschutz-Ventil: Zustand aus Kommando 6900, Schalten ueber 5100/5200.
Wird nur angelegt, wenn das Geraet 6900 beantwortet - siehe
coordinator.should_create_entity().
"""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .configentry import MyConfigEntry
from .const import TYPES
from .entity_helpers import build_entity_list
from .jdconst import DEVICELISTS

logging.basicConfig()
log: logging.Logger = logging.getLogger(name=__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the valve platform."""
    _useless = hass
    # start with an empty list of entries
    entries = []

    # we create one communicator per integration only for better performance and to allow dynamic parameters
    coordinator = config_entry.runtime_data.coordinator

    for device in DEVICELISTS:
        entries = await build_entity_list(
            entries=entries,
            config_entry=config_entry,
            rest_items=device,
            item_type=TYPES.VALVE,
            coordinator=coordinator,
        )

    async_add_entities(
        entries,
        update_before_add=True,
    )
