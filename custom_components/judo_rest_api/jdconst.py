"""Heatpump constants."""

from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass
from homeassistant.const import (
    UnitOfVolumeFlowRate,
    UnitOfMass,
    UnitOfVolume,
    UnitOfTime,
)

from .const import DEVICES, FORMATS, TYPES
from .items import RestItem, StatusItem

reverse_device_list: dict[str, str] = {
    "dev_system": "SYS",
    "dev_statistik": "ST",
}

################################################################################
# Listen mit Fehlermeldungen, Warnmeldungen und Statustexte
# Beschreibungstext ist ebenfalls möglich
# class StatusItem(): def __init__(self, number, text, description = None):
################################################################################

# fmt: off

UNIT_STATUS: list[StatusItem] = [
    StatusItem(number=0, translation_key="ge_hardness"),
    StatusItem(number=1, translation_key="en_hardness"),
    StatusItem(number=2, translation_key="fr_hardness"),
    StatusItem(number=3, translation_key="ppm"),
    StatusItem(number=4, translation_key="mmol"),
    StatusItem(number=5, translation_key="mval"),
]
UNIT_TYPE: list[StatusItem] = [
    StatusItem(number=0x33, translation_key= "i_soft_safe_plus"),
    StatusItem(number=0x42, translation_key=  "i_soft_k_safe_plus"),
    StatusItem(number=0x58, translation_key=  "i_soft_pro"),
    StatusItem(number=0x4B, translation_key=  "i_soft_pro"),
    StatusItem(number=0x4C, translation_key=  "i_soft_pro_l"),
    StatusItem(number=0x32, translation_key=  "i_soft"),
    StatusItem(number=0x43, translation_key=  "i_soft_k"),
    StatusItem(number=0x34, translation_key=  "softwell_p"),
    StatusItem(number=0x35, translation_key=  "softwell_s"),
    StatusItem(number=0x36, translation_key=  "softwell_k"),
    StatusItem(number=0x47, translation_key=  "softwell_kp"),
    StatusItem(number=0x72, translation_key=  "softwell_ks"),
    StatusItem(number=0x44, translation_key=  "zewa_prom_i_safe"),
    StatusItem(number=0x41, translation_key=  "i_dos_eco"),
    StatusItem(number=0x3c, translation_key=  "i_fill"),
]

LEAKAGEPROTECTION_MAX_WATERFLOWRATE_LIST: list[StatusItem] = [
    StatusItem(number=0, translation_key="unlimited"),
    StatusItem(number=500, translation_key="500_l_h"),
    StatusItem(number=1000, translation_key="1000_l_h"),
    StatusItem(number=1500, translation_key="1500_l_h"),
    StatusItem(number=2000, translation_key="2000_l_h"),
    StatusItem(number=2500, translation_key="2500_l_h"),
    StatusItem(number=3000, translation_key="3000_l_h"),
    StatusItem(number=3500, translation_key="3500_l_h"),
    StatusItem(number=4000, translation_key="4000_l_h"),
    StatusItem(number=4500, translation_key="4500_l_h"),
    StatusItem(number=5000, translation_key="5000_l_h"),
]

LEAKAGEPROTECTION_MAX_WATERFLOW_LIST: list[StatusItem] = [
    StatusItem(number=0, translation_key="unlimited"),
    StatusItem(number=100, translation_key="100_l"),
    StatusItem(number=200, translation_key="200_l"),
    StatusItem(number=300, translation_key="300_l"),
    StatusItem(number=400, translation_key="400_l"),
    StatusItem(number=500, translation_key="500_l"),
    StatusItem(number=600, translation_key="600_l"),
    StatusItem(number=700, translation_key="700_l"),
    StatusItem(number=800, translation_key="800_l"),
    StatusItem(number=900, translation_key="900_l"),
    StatusItem(number=1000, translation_key="1000_l"),
    StatusItem(number=1100, translation_key="1100_l"),
    StatusItem(number=1200, translation_key="1200_l"),
    StatusItem(number=1300, translation_key="1300_l"),
    StatusItem(number=1500, translation_key="1500_l"),
    StatusItem(number=2000, translation_key="2000_l"),
    StatusItem(number=2500, translation_key="2500_l"),
    StatusItem(number=3000, translation_key="3000_l"),
]

LEAKAGEPROTECTION_MAX_WATERFLOWTIME_LIST: list[StatusItem] = [
    StatusItem(number=0, translation_key="unlimited"),
    StatusItem(number=10, translation_key="10_min"),
    StatusItem(number=20, translation_key="20_min"),
    StatusItem(number=30, translation_key="30_min"),
    StatusItem(number=40, translation_key="40_min"),
    StatusItem(number=50, translation_key="50_min"),
    StatusItem(number=60, translation_key="60_min"),
    StatusItem(number=75, translation_key="75_min"),
    StatusItem(number=90, translation_key="90_min"),
    StatusItem(number=120, translation_key="2_h"),
    StatusItem(number=150, translation_key="2_5_h"),
    StatusItem(number=180, translation_key="3_h"),
    StatusItem(number=210, translation_key="3_5_h"),
    StatusItem(number=240, translation_key="4_h"),
    StatusItem(number=270, translation_key="4_5_h"),
    StatusItem(number=300, translation_key="5_h"),
]


ABSENCE_LIMIT_MAX_WATERFLOWRATE_LIST: list[StatusItem] = [
    StatusItem(number=0, translation_key="deactivated"),
    StatusItem(number=100, translation_key="100_l_h"),
    StatusItem(number=200, translation_key="200_l_h"),
    StatusItem(number=300, translation_key="300_l_h"),
    StatusItem(number=400, translation_key="400_l_h"),
    StatusItem(number=500, translation_key="500_l_h"),
    StatusItem(number=1000, translation_key="1000_l_h"),
    StatusItem(number=1500, translation_key="1500_l_h"),
    StatusItem(number=2000, translation_key="2000_l_h"),
    StatusItem(number=2500, translation_key="2500_l_h"),
    StatusItem(number=3000, translation_key="3000_l_h"),
    StatusItem(number=3500, translation_key="3500_l_h"),
    StatusItem(number=4000, translation_key="4000_l_h"),
    StatusItem(number=4500, translation_key="4500_l_h"),
    StatusItem(number=5000, translation_key="5000_l_h"),
]

ABSENCE_LIMIT_MAX_WATERFLOW_LIST: list[StatusItem] = [
    StatusItem(number=0, translation_key="deactivated"),
    StatusItem(number=5, translation_key="5_l"),
    StatusItem(number=10, translation_key="10_l"),
    StatusItem(number=15, translation_key="15_l"),
    StatusItem(number=20, translation_key="20_l"),
    StatusItem(number=25, translation_key="25_l"),
    StatusItem(number=50, translation_key="50_l"),
    StatusItem(number=100, translation_key="100_l"),
    StatusItem(number=150, translation_key="150_l"),
    StatusItem(number=200, translation_key="200_l"),
    StatusItem(number=250, translation_key="250_l"),
    StatusItem(number=300, translation_key="300_l"),
    StatusItem(number=500, translation_key="500_l"),
    StatusItem(number=1000, translation_key="1000_l"),
    StatusItem(number=1500, translation_key="1500_l"),
    StatusItem(number=2000, translation_key="2000_l"),
    StatusItem(number=2500, translation_key="2500_l"),
    StatusItem(number=3000, translation_key="3000_l"),
]

ABSENCE_LIMIT_MAX_WATERFLOWTIME_LIST: list[StatusItem] = [
    StatusItem(number=0, translation_key="deactivated"),
    StatusItem(number=5, translation_key="5_min"),
    StatusItem(number=10, translation_key="10_min"),
    StatusItem(number=20, translation_key="20_min"),
    StatusItem(number=30, translation_key="30_min"),
    StatusItem(number=60, translation_key="60_min"),
    StatusItem(number=90, translation_key="90_min"),
    StatusItem(number=120, translation_key="120_min"),
    StatusItem(number=180, translation_key="180_min"),
    StatusItem(number=240, translation_key="240_min"),
    StatusItem(number=300, translation_key="300_min"),
]

HOLIDAY_MODE_WRITE_LIST: list[StatusItem] = [
    StatusItem(number=0, translation_key="deactivated"),
    StatusItem(number=1, translation_key="h1"),
    StatusItem(number=2, translation_key="h2"),
    StatusItem(number=3, translation_key="h3_water_closed"),
]

SLEEP_MODE_DURATION_LIST: list[StatusItem] = [
    StatusItem(number=1, translation_key="1h"),
    StatusItem(number=2, translation_key="2h"),
    StatusItem(number=3, translation_key="3h"),
    StatusItem(number=4, translation_key="4h"),
    StatusItem(number=5, translation_key="5h"),
    StatusItem(number=6, translation_key="6h"),
    StatusItem(number=7, translation_key="7h"),
    StatusItem(number=8, translation_key="8h"),
    StatusItem(number=9, translation_key="9h"),
    StatusItem(number=10, translation_key="10h"),
]

AUTO_MICROLEAKAGECHECK_LIST: list[StatusItem] = [
    StatusItem(number=0, translation_key="no_auto_check"),
    StatusItem(number=1, translation_key="with_message"),
    StatusItem(number=2, translation_key="with_message_close"),
]
#####################################################
# Description of physical units via the status list #
#####################################################

PARAMS_FLOWRATE: dict = {
    "min": 0,
    "max": 5,
    "step": 0.1,
    "divider": 100,
    "precision": 2,
    "unit": UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
    "stateclass": SensorStateClass.MEASUREMENT,
    "icon": "mdi:waves-arrow-right"
}

PARAMS_FLOWRATE2: dict = {
    "min": 0,
    "max": 5000,
    "step": 100,
    "divider": 1,
    "precision": 0,
    "unit": UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
    "stateclass": SensorStateClass.MEASUREMENT,
    "icon": "mdi:waves-arrow-right"
}

PARAMS_FLOWRATE3: dict = {
    "divider": 1,
    "precision": 2,
    "unit": UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
    "stateclass": SensorStateClass.MEASUREMENT,
    "icon": "mdi:waves-arrow-right"
}

PARAMS_FLOW: dict = {
    "min": 0,
    "max": 3000,
    "step": 5,
    "divider": 1,
    "precision": 0,
    "unit": UnitOfVolume.LITERS,
    "stateclass": SensorStateClass.MEASUREMENT,
    "icon": "mdi:waves"
}

PARAMS_FLOW_CM: dict = {
    "min": 0,
    "max": 10000,
    "step": 0.001,
    "divider": 1000,
    "precision": 3,
    "unit": UnitOfVolume.CUBIC_METERS,
    "stateclass": SensorStateClass.MEASUREMENT,
    "icon": "mdi:water"
}

PARAMS_MASS: dict = {
    "min": 0,
    "max": 100,
    "step": 1,
    "divider": 1000,
    "preciosion": 2,
    "unit": UnitOfMass.KILOGRAMS,
    "stateclass": SensorStateClass.MEASUREMENT,
    "icon": "mdi:weight-kilogram"
}

PARAMS_DAYS: dict = {
    "min": 1,
    "max": 255,
    "step": 1,
    "preciosion": 0,
    "unit": "Tage",
    "stateclass": SensorStateClass.MEASUREMENT,
    "icon": "mdi:timelapse"
}

PARAMS_MINUTES: dict = {
    "step": 1,
    "preciosion": 0,
    "unit": UnitOfTime.MINUTES,
    "stateclass": SensorStateClass.MEASUREMENT,
    "icon": "mdi:timelapse"
}

PARAMS_MINUTES2: dict = {
    "min": 0,
    "max": 600,
    "step": 5,
    "preciosion": 0,
    "unit": UnitOfTime.MINUTES,
    "stateclass": SensorStateClass.MEASUREMENT,
    "icon": "mdi:timelapse"
}

PARAMS_HOURS: dict = {
    "step": 1,
    "preciosion": 0,
    "unit": UnitOfTime.HOURS,
    "stateclass": SensorStateClass.MEASUREMENT,
    "icon": "mdi:timelapse"
}

PARAMS_HOURS2: dict = {
    "min": 1,
    "max": 10,
    "step": 1,
    "preciosion": 0,
    "unit": UnitOfTime.HOURS,
    "stateclass": SensorStateClass.MEASUREMENT,
    "icon": "mdi:timelapse"
}

PARAMS_GDH: dict = {
    "min": 1,
    "max": 13,
    "step": 1,
    "preciosion": 1,
    "unit": "°dH",
    "divider": 1,
    "stateclass": SensorStateClass.MEASUREMENT,
    "icon": "mdi:water-opacity"
}

PARAMS_QBM_H: dict = {
    "min": 0,
    "max": 100,
    "step": 1,
    "divider": 1000,
    "preciosion": 3,
    "unit": UnitOfVolume.CUBIC_METERS,
    "stateclass": SensorStateClass.TOTAL_INCREASING,
    "deviceclass": SensorDeviceClass.WATER,
    "icon": "mdi:water"
}

PARAMS_QBM_W: dict = {
    "min": 0,
    "max": 100,
    "step": 1,
    "divider": 1000,
    "preciosion": 3,
    "unit": UnitOfVolume.CUBIC_METERS,
    "stateclass": SensorStateClass.TOTAL_INCREASING,
    "deviceclass": SensorDeviceClass.WATER,
    "icon": "mdi:water-outline"
}


PARAMS_CONTACT: dict = {
    "icon": "mdi:phone"
}
PARAMS_CLOSE: dict = {
    "icon": "mdi:water-pump-off"
}
PARAMS_OPEN: dict = {
    "icon": "mdi:water-pump"
}
PARAMS_REG: dict = {
    "icon": "mdi:water-check-outline"
}
PARAMS_MICROLEAK: dict = {
    "icon":"mdi:pipe-leak"
}
PARAMS_SLEEP_ON: dict = {
    "icon":"mdi:sleep"
}
PARAMS_SLEEP_OFF: dict = {
    "icon":"mdi:sleep-off"
}
PARAMS_HOLIDAY_OFF: dict = {
    "icon":"mdi:home-import-outline"
}
PARAMS_HOLIDAY_ON: dict = {
    "icon":"mdi:home-export-outline"
}
PARAMS_LEARN: dict = {
    "icon":"mdi:school"
}
PARAMS_STATUS: dict = {
    "icon":"mdi:list-status",
    "preciosion": 0
}
PARAMS_RESET: dict = {
    "icon":"mdi:lock-reset",
}
PARAMS_INFO: dict = {
    "icon": "mdi:information-box-outline"
}
PARAMS_SWITCH_WF: dict = {
    "icon": "mdi:toggle-switch-outline"
}
PARAMS_DATETIME: dict = {
    "deviceclass": SensorDeviceClass.TIMESTAMP,
    "icon": "mdi:clock"
}
PARAMS_DATETIME_BUTTON: dict = {
    "icon": "mdi:clock-edit-outline"
}

# pylint: disable=line-too-long

# fmt: off
REST_SYS_ITEMS: list[RestItem] = [
    RestItem( address_read="FF00", read_bytes = 2, read_index=0, mformat=FORMATS.STATUS, mtype=TYPES.SENSOR, device=DEVICES.SYS, resultlist=UNIT_TYPE, params= PARAMS_INFO, translation_key="device_type"),
    RestItem( address_read="0600", read_bytes = 4, read_index=0, mformat=FORMATS.NUMBER, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_INFO, translation_key="device_number"),
    RestItem( address_read="0100", read_bytes = 3, read_index=0, mformat=FORMATS.SW_VERSION, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_INFO, translation_key="software_version"),

#Number
#    RestItem( address_read="5100", read_bytes = 2, read_index=0, address_write="3000", write_bytes = 1, write_index=0, mformat=FORMATS.NUMBER, mtype=TYPES.NUMBER, device=DEVICES.SYS, params= PARAMS_GDH,translation_key="water_hardeness"),


#Select    
#    RestItem( address_read="5700", read_bytes = 1, read_index=0, address_write="5700", write_bytes = 1, write_index=0, mformat=FORMATS.NUMBER, mtype=TYPES.NUMBER, device=DEVICES.SYS, params= PARAMS_DAYS,translation_key="salt_warning"),
    RestItem( address_read="5E00", read_bytes = 2, read_index=0,  mformat=FORMATS.STATUS, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_FLOWRATE2, resultlist=ABSENCE_LIMIT_MAX_WATERFLOWRATE_LIST, translation_key="absence_limit_max_waterflowrate"),
    RestItem( address_read="5E00", read_bytes = 2, read_index=2,  mformat=FORMATS.STATUS, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_FLOW, resultlist=ABSENCE_LIMIT_MAX_WATERFLOW_LIST, translation_key="absence_limit_max_water_flow"),
    RestItem( address_read="5E00", read_bytes = 2, read_index=4,  mformat=FORMATS.STATUS, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_MINUTES2, resultlist=ABSENCE_LIMIT_MAX_WATERFLOWTIME_LIST, translation_key="absence_limit_max_waterflow_time"),
    RestItem( address_write="5300", write_bytes = 1, write_index=0, mformat=FORMATS.STATUS_WO, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_HOURS2, resultlist=SLEEP_MODE_DURATION_LIST, translation_key="sleep_mode_duration"),
    RestItem( address_write="5600", write_bytes = 1, write_index=0,  mformat=FORMATS.STATUS_WO, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_HOLIDAY_ON, resultlist=HOLIDAY_MODE_WRITE_LIST, translation_key="holiday_mode_write"),
    RestItem( address_read="6500", read_bytes = 1, read_index=0, address_write="5B00", write_bytes = 1, write_index=0,  mformat=FORMATS.STATUS, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_MICROLEAK, resultlist=AUTO_MICROLEAKAGECHECK_LIST, translation_key="auto_microleakage_check"),

    RestItem( mformat=FORMATS.STATUS_WO, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_FLOWRATE2, resultlist=LEAKAGEPROTECTION_MAX_WATERFLOWRATE_LIST, translation_key="leakageprotection_max_waterflowrate"),
    RestItem( mformat=FORMATS.STATUS_WO, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_FLOW, resultlist=LEAKAGEPROTECTION_MAX_WATERFLOW_LIST, translation_key="leakageprotection_max_waterflow"),
    RestItem( mformat=FORMATS.STATUS_WO, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_MINUTES2, resultlist=LEAKAGEPROTECTION_MAX_WATERFLOWTIME_LIST, translation_key="leakageprotection_max_waterflowtime"),
#Sensor
#    RestItem( address_read="5600", read_bytes = 2, read_index=0, mformat=FORMATS.NUMBER, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_MASS, translation_key="salt_storage_mass"),
#    RestItem( address_read="5600", read_bytes = 2, read_index=2, mformat=FORMATS.NUMBER, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_DAYS,translation_key="salt_storage_days"),
#    RestItem( address_read="2900", read_bytes = 4, read_index=0, mformat=FORMATS.NUMBER, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_QBM_W, translation_key="water_treated"),
#    RestItem( address_read="5800", read_bytes = 16, read_index=0, mformat=FORMATS.TEXT, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_CONTACT,translation_key="service_contact"),
    RestItem( address_read="2800", read_bytes = 4, read_index=0, mformat=FORMATS.NUMBER, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_QBM_H, translation_key="water_total"),
    RestItem( mformat=FORMATS.NUMBER_INTERNAL, mtype=TYPES.SENSOR_CALC, device=DEVICES.SYS, params= PARAMS_FLOWRATE3, translation_key="water_flow"),
#    RestItem( address_read="2500", read_bytes = 1, read_index=0, mformat=FORMATS.NUMBER, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_MINUTES,translation_key="operating_minutes"),
#    RestItem( address_read="2500", read_bytes = 1, read_index=1, mformat=FORMATS.NUMBER, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_HOURS,translation_key="operating_hours"),
    RestItem( address_read="2500", read_bytes = 2, read_index=2, mformat=FORMATS.NUMBER, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_DAYS,translation_key="operating_days"),
    RestItem( address_read="6400", read_bytes = 1, read_index=0, mformat=FORMATS.NUMBER, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_STATUS, translation_key="learning_mode_status"),
    RestItem( address_read="6400", read_bytes = 2, read_index=1, mformat=FORMATS.NUMBER, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_FLOW_CM, translation_key="learning_water_quantity"),
    RestItem( address_read="0E00", read_bytes = 4, read_index=0, mformat=FORMATS.TIMESTAMP, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_INFO, translation_key="install_date"),

#Time_Date
    RestItem( address_read="5900", read_bytes = 6, read_index=0, mformat=FORMATS.DATETIME_JUDO, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_DATETIME, translation_key="datetime_judo"),

#Button
    RestItem(address_write="5100", write_bytes = 0, write_index=0, mformat=FORMATS.BUTTON, mtype=TYPES.BUTTON, device=DEVICES.SYS, params= PARAMS_CLOSE, translation_key="leakage_protection_close"),
    RestItem(address_write="5200", write_bytes = 0, write_index=0, mformat=FORMATS.BUTTON, mtype=TYPES.BUTTON, device=DEVICES.SYS, params= PARAMS_OPEN, translation_key="leakage_protection_open"),
    RestItem(address_write="5400", write_bytes = 0, write_index=0, mformat=FORMATS.BUTTON, mtype=TYPES.BUTTON, device=DEVICES.SYS, params= PARAMS_SLEEP_ON, translation_key="sleep_mode_on"),
    RestItem(address_write="5500", write_bytes = 0, write_index=0, mformat=FORMATS.BUTTON, mtype=TYPES.BUTTON, device=DEVICES.SYS, params= PARAMS_SLEEP_OFF, translation_key="sleep_mode_off"),
    RestItem(address_write="5800", write_bytes = 0, write_index=0, mformat=FORMATS.BUTTON, mtype=TYPES.BUTTON, device=DEVICES.SYS, params= PARAMS_HOLIDAY_OFF, translation_key="holiday_mode_off"),
    RestItem(address_write="5700", write_bytes = 0, write_index=0, mformat=FORMATS.BUTTON, mtype=TYPES.BUTTON, device=DEVICES.SYS, params= PARAMS_HOLIDAY_ON, translation_key="holiday_mode_on"),
    RestItem(address_write="5C00", write_bytes = 0, write_index=0, mformat=FORMATS.BUTTON, mtype=TYPES.BUTTON, device=DEVICES.SYS, params= PARAMS_MICROLEAK, translation_key="microleakage_check"),
    RestItem(address_write="5D00", write_bytes = 0, write_index=0, mformat=FORMATS.BUTTON, mtype=TYPES.BUTTON, device=DEVICES.SYS, params= PARAMS_LEARN, translation_key="learning_mode_on"),
    RestItem(address_write="6300", write_bytes = 0, write_index=0, mformat=FORMATS.BUTTON, mtype=TYPES.BUTTON, device=DEVICES.SYS, params= PARAMS_RESET, translation_key="message_reset"),
    
    RestItem(address_write="5A00", write_bytes = 6, write_index=0, mformat=FORMATS.BUTTON_WO_DATETIME, mtype=TYPES.BUTTON, device=DEVICES.SYS, params= PARAMS_DATETIME_BUTTON, translation_key="set_judo_time"),

# RestItem(mformat=FORMATS.STATUS, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_MASS_REFILL, resultlist=SALT_MASS, translation_key="salt_refill_mass"),
#Switch
    RestItem( mformat=FORMATS.SWITCH_INTERNAL, mtype=TYPES.SWITCH, device=DEVICES.SYS, params= PARAMS_SWITCH_WF, translation_key="water_flow_check_on_off"),
]

REST_ST_ITEMS: list[RestItem] = [
#ANPASSEN!!!    RestItem( address_read="FB00", mformat=FORMATS.NUMBER, mtype=TYPES.SENSOR, device=DEVICES.ST, params=PARAMS_QBM_H, translation_key="day_statistics"),
]

DEVICELISTS: list = [
    REST_SYS_ITEMS,
    REST_ST_ITEMS,
]

# fmt: on
# DO
# - Format für SW siehe GIT HUB
