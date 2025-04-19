"""init."""

import logging
# from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .configentry import MyConfigEntry, MyData
from .const import CONF, CONST
from .jdconst import DEVICELISTS
from .coordinator import MyCoordinator
from .restobject import RestAPI

logging.basicConfig()
log = logging.getLogger(__name__)

PLATFORMS: list[str] = [
    "number",
    "select",
    "sensor",
    "switch",
    "button",
]


# Return boolean to indicate that initialization was successful.
# return True
async def async_setup_entry(hass: HomeAssistant, entry: MyConfigEntry) -> bool:
    """Set up entry."""
    # Store an instance of the "connecting" class that does the work of speaking
    # with your actual devices.
    # hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub.Hub(hass, entry.data["host"])
    restapi = RestAPI(config_entry=entry, hass=hass)
    # await restapi.login()

    itemlist = []

    for device in DEVICELISTS:
        for item in device:
            itemlist.append(item)

    coordinator = MyCoordinator(
        hass=hass, my_api=restapi, api_items=itemlist, p_config_entry=entry
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = MyData(
        rest_api=restapi,
        hass=hass,
        coordinator=coordinator,
    )

    # see https://community.home-assistant.io/t/config-flow-how-to-update-an-existing-entity/522442/8
    entry.async_on_unload(entry.add_update_listener(update_listener))

    # This creates each HA object for each platform your device requires.
    # It's done by calling the `async_setup_entry` function in each platform module.
    #    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    log.info("Setup entities")

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    log.info("Init done")

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(
        entry.entry_id
    )  # list of entry_ids created for file


async def async_migrate_entry(hass: HomeAssistant, config_entry: MyConfigEntry):
    """Migrate old entry."""

    new_data = {**config_entry.data}

    if config_entry.version > 1:
        # This means the user has downgraded from a future version
        return True

    # to ensure all update paths we have to check every version to not overwrite existing entries
    if config_entry.version < 1:
        log.warning("Old Version detected")

    if config_entry.version < 2:
        log.warning("Version <2 detected")
        new_data[CONF.SCAN_INTERVAL] = CONST.SCAN_INTERVAL

    hass.config_entries.async_update_entry(
        config_entry, data=new_data, minor_version=1, version=2
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
    entry.runtime_data.rest_api.close()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok
