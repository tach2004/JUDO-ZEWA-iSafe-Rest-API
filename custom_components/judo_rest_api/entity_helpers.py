"""Build entitiy List and Update Coordinator."""

import logging
from .configentry import MyConfigEntry
from .items import RestItem
from .const import TYPES
from .coordinator import MyCoordinator
from .entities import MySensorEntity, MyNumberEntity, MyButtonEntity, MySelectEntity, MySwitchEntity, MyCalcSensorEntity

logging.basicConfig()
log = logging.getLogger(__name__)


async def build_entity_list(
    entries,
    config_entry: MyConfigEntry,
    rest_items: RestItem,
    item_type,
    coordinator: MyCoordinator,
):
    """Build entity list.

    function builds a list of entities that can be used as parameter by async_setup_entry()
    type of list is defined by the RestItem's type flag
    so the app only holds one list of entities that is build from a list of RestItem
    stored in hpconst.py so far, will be provided by an external file in future

    :param config_entry: HASS config entry
    :type config_entry: MyConfigEntry
    :param rest_item: definition of rest item
    :type rest_item: RestItem
    :param item_type: type of rest item
    :type item_type: TYPES
    :param coordinator: the update coordinator
    :type coordinator: MyCoordinator
    """

    for index, item in enumerate(rest_items):
        if item.type == item_type:
            match item_type:
                # here the entities are created with the parameters provided
                # by the RestItem object
                case TYPES.SENSOR | TYPES.NUMBER_RO:
                    entries.append(
                        MySensorEntity(config_entry, item, coordinator, index)
                    )
                case TYPES.SENSOR_CALC:
                    entries.append(
                        MyCalcSensorEntity(
                            config_entry,
                            item,
                            coordinator,
                            index,
                        )
                    )
                case TYPES.SELECT | TYPES.SELECT_NOIF:
                    entries.append(
                        MySelectEntity(config_entry, item, coordinator, index)
                    )
                case TYPES.NUMBER:
                    entries.append(
                        MyNumberEntity(config_entry, item, coordinator, index)
                    )
                case TYPES.SWITCH:
                    entries.append(
                        MySwitchEntity(config_entry, item, coordinator, index)
                    )
                case TYPES.BUTTON:
                    entries.append(
                        MyButtonEntity(config_entry, item, coordinator, index)
                    )

    return entries
