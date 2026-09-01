"""Heatpump constants."""

from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import (
    UnitOfVolumeFlowRate,
    UnitOfMass,
    UnitOfVolume,
    UnitOfTime,
    EntityCategory,
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

################################################################################
# Lernmodus quittieren (Kommando 6B, 1 Byte)
# 0 = ermittelte Grenzwerte verwerfen, 1 = Grenzwerte uebernehmen
# "standby" ist die Ruhestellung: sie wird NIE an den JUDO gesendet. Nach dem
# Senden springt der Select automatisch dorthin zurueck, damit dieselbe Aktion
# beim naechsten Mal wieder ausloest.
################################################################################
LEARNING_MODE_ACK_LIST: list[StatusItem] = [
    StatusItem(number=255, translation_key="standby"),
    StatusItem(number=1, translation_key="accept_limits"),
    StatusItem(number=0, translation_key="discard_limits"),
]

################################################################################
# Leckageschutz-Status (Kommando 6900, 4 Byte, bitcodiert)
# Bei diesen beiden Listen ist number = BITNUMMER, nicht der Zahlenwert.
# Die Reihenfolge bestimmt die Prioritaet: das erste gesetzte Bit gewinnt.
################################################################################
VALVE_STATE_LIST: list[StatusItem] = [
    StatusItem(number=12, translation_key="opening"),   # Oeffnungsvorgang Kugelventil
    StatusItem(number=13, translation_key="closing"),   # Schliessvorgang Kugelventil
    StatusItem(number=14, translation_key="open"),      # Ventil offen
    StatusItem(number=15, translation_key="closed"),    # Ventil geschlossen
]

MICROLEAKAGE_RESULT_LIST: list[StatusItem] = [
    StatusItem(number=8, translation_key="message_and_close"),  # Meldung + Schliessen
    StatusItem(number=9, translation_key="message_only"),       # nur Meldung
    StatusItem(number=11, translation_key="not_possible"),      # Pruefung nicht moeglich
    StatusItem(number=10, translation_key="none_detected"),     # keine Kleinleckage erkannt
]

FLUSH_INTERVAL_LIST: list[StatusItem] = [
    StatusItem(number=0, translation_key="deactivated"),
    StatusItem(number=1, translation_key="1m"),
    StatusItem(number=2, translation_key="2m"),
    StatusItem(number=3, translation_key="3m"),
    StatusItem(number=4, translation_key="4m"),
    StatusItem(number=6, translation_key="6m"),
    StatusItem(number=12, translation_key="12m"),
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
    "deviceclass": SensorDeviceClass.VOLUME_FLOW_RATE,
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
    "deviceclass": SensorDeviceClass.VOLUME_FLOW_RATE,
    "icon": "mdi:waves-arrow-right"
}

PARAMS_FLOWRATE3: dict = {
    "divider": 1,
    "precision": 2,
    "unit": UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
    "stateclass": SensorStateClass.MEASUREMENT,
    "deviceclass": SensorDeviceClass.VOLUME_FLOW_RATE,
    "icon": "mdi:waves-arrow-right"
}

PARAMS_FLOW: dict = {
    "min": 0,
    "max": 3000,
    "step": 5,
    "divider": 1,
    "precision": 0,
    "unit": UnitOfVolume.LITERS,
    "stateclass": SensorStateClass.TOTAL,
    "deviceclass": SensorDeviceClass.VOLUME,
    "icon": "mdi:waves"
}

PARAMS_FLOW_CM: dict = {
    "min": 0,
    "max": 10000,
    "step": 0.001,
    "divider": 1000,
    "precision": 3,
    "unit": UnitOfVolume.CUBIC_METERS,
    "stateclass": SensorStateClass.TOTAL,
    "deviceclass": SensorDeviceClass.VOLUME,
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
    "icon": "mdi:timelapse"
}

PARAMS_MINUTES: dict = {
    "step": 1,
    "preciosion": 0,
    "unit": UnitOfTime.MINUTES,
    "icon": "mdi:timelapse"
}

PARAMS_MINUTES2: dict = {
    "min": 0,
    "max": 600,
    "step": 5,
    "preciosion": 0,
    "unit": UnitOfTime.MINUTES,
    "icon": "mdi:timelapse"
}

PARAMS_HOURS: dict = {
    "step": 1,
    "preciosion": 0,
    "unit": UnitOfTime.HOURS,
    "icon": "mdi:timelapse"
}

PARAMS_HOURS2: dict = {
    "min": 0,
    "max": 100,
    "step": 1,
    "preciosion": 0,
    "unit": UnitOfTime.HOURS,
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
PARAMS_LEARN_ACK: dict = {
    "icon": "mdi:clipboard-check-outline",
    "idle_option": "standby",   # Eintrag, auf den nach dem Senden zurueckgesprungen wird
}

################################################################################
# Parameter fuer den Leckageschutz-Status (6900).
# "bit" = Bitnummer in der 32-Bit-Maske, "entity_category" sortiert die
# Entitaeten in HA unter "Diagnose" ein.
################################################################################
def _ls(bit=None, icon=None, deviceclass=None, default_state=None) -> dict:
    """Kleine Hilfe, damit die 19 Status-Eintraege unten lesbar bleiben."""
    d: dict = {"entity_category": EntityCategory.DIAGNOSTIC}
    if bit is not None:
        d["bit"] = bit
    if icon is not None:
        d["icon"] = icon
    if deviceclass is not None:
        d["deviceclass"] = deviceclass
    if default_state is not None:
        d["default_state"] = default_state
    return d

_PROBLEM = BinarySensorDeviceClass.PROBLEM
_RUNNING = BinarySensorDeviceClass.RUNNING
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
PARAMS_INFO_TIMESTAMP: dict = {
    #"deviceclass": SensorDeviceClass.TIMESTAMP, # Wert ist keine korrekte TIMESTAMP DEVICE_CLASS
    "icon": "mdi:information-box-outline"
}
PARAMS_SWITCH_WF: dict = {
    "icon": "mdi:toggle-switch-outline"
}
PARAMS_TIMESTAMP: dict = {
    "deviceclass": SensorDeviceClass.TIMESTAMP,
    "icon": "mdi:clock"
}
PARAMS_TIMESTAMP2: dict = {
    "deviceclass": SensorDeviceClass.TIMESTAMP,
    "icon": "mdi:information-box-outline"
}
PARAMS_DATETIME: dict = {
    #"deviceclass": SensorDeviceClass.TIMESTAMP,
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
    RestItem( address_read="5E00", read_bytes = 2, read_index=0,  mformat=FORMATS.SELECT, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_FLOWRATE2, resultlist=ABSENCE_LIMIT_MAX_WATERFLOWRATE_LIST, translation_key="absence_limit_max_waterflowrate"),
    RestItem( address_read="5E00", read_bytes = 2, read_index=2,  mformat=FORMATS.SELECT, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_FLOW, resultlist=ABSENCE_LIMIT_MAX_WATERFLOW_LIST, translation_key="absence_limit_max_water_flow"),
    RestItem( address_read="5E00", read_bytes = 2, read_index=4,  mformat=FORMATS.SELECT, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_MINUTES2, resultlist=ABSENCE_LIMIT_MAX_WATERFLOWTIME_LIST, translation_key="absence_limit_max_waterflow_time"),
    RestItem( address_write="5300", write_bytes = 1, write_index=0, mformat=FORMATS.SELECT_WO, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_HOURS2, resultlist=SLEEP_MODE_DURATION_LIST, translation_key="sleep_mode_duration"),
    RestItem( address_read="6800", read_bytes = 1, read_index=0, address_write="5600", write_bytes = 1, write_index=0,  mformat=FORMATS.SELECT, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_HOLIDAY_ON, resultlist=HOLIDAY_MODE_WRITE_LIST, translation_key="holiday_mode_write"),
    RestItem( address_read="6500", read_bytes = 1, read_index=0, address_write="5B00", write_bytes = 1, write_index=0,  mformat=FORMATS.SELECT, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_MICROLEAK, resultlist=AUTO_MICROLEAKAGECHECK_LIST, translation_key="auto_microleakage_check"),

    # Leckageeinstellungen lesen (Kommando 6800, 7 Byte):
    #   Byte 0    = Urlaubsmodus          -> holiday_mode_write (oben)
    #   Byte 1+2  = Max. Volumenstrom l/h -> read_index=1
    #   Byte 3+4  = Max. Entnahmemenge l  -> read_index=3
    #   Byte 5+6  = Max. Entnahmedauer min-> read_index=5
    # Geschrieben wird weiterhin gebuendelt ueber Kommando 5000 in entities.py.
    RestItem( address_read="6800", read_bytes = 2, read_index=1, mformat=FORMATS.SELECT, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_FLOWRATE2, resultlist=LEAKAGEPROTECTION_MAX_WATERFLOWRATE_LIST, translation_key="leakageprotection_max_waterflowrate"),
    RestItem( address_read="6800", read_bytes = 2, read_index=3, mformat=FORMATS.SELECT, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_FLOW, resultlist=LEAKAGEPROTECTION_MAX_WATERFLOW_LIST, translation_key="leakageprotection_max_waterflow"),
    RestItem( address_read="6800", read_bytes = 2, read_index=5, mformat=FORMATS.SELECT, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_MINUTES2, resultlist=LEAKAGEPROTECTION_MAX_WATERFLOWTIME_LIST, translation_key="leakageprotection_max_waterflowtime"),
    # Lernmodus quittieren (Kommando 6B, reines Schreib-Kommando)
    RestItem( address_write="6B00", write_bytes = 1, write_index=0, mformat=FORMATS.SELECT_WO_ACTION, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_LEARN_ACK, resultlist=LEARNING_MODE_ACK_LIST, translation_key="learning_mode_acknowledge"),

    RestItem( mformat=FORMATS.SELECT_INTERNAL, mtype=TYPES.SELECT_NOIF, device=DEVICES.SYS, params= PARAMS_HOURS2, resultlist=FLUSH_INTERVAL_LIST, translation_key="flush_interval"),
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
    RestItem( address_read="0E00", read_bytes = 4, read_index=0, mformat=FORMATS.TIMESTAMP, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_INFO_TIMESTAMP, translation_key="install_date_judo"),

#Time_Date
    RestItem( address_read="5900", read_bytes = 6, read_index=0, mformat=FORMATS.DATETIME_JUDO, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_DATETIME, translation_key="datetime_judo"),
    RestItem( mformat=FORMATS.SENSOR_INTERNAL_TIMESTAMP, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_TIMESTAMP, translation_key="last_reset_flush_interval"),
    RestItem( mformat=FORMATS.SENSOR_INTERNAL_TIMESTAMP, mtype=TYPES.SENSOR, device=DEVICES.SYS, params= PARAMS_TIMESTAMP2, translation_key="install_date"),

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
    RestItem(mformat=FORMATS.BUTTON_INTERNAL, mtype=TYPES.BUTTON, device=DEVICES.SYS, params= PARAMS_RESET, translation_key="reset_flush_interval"),


#Leckageschutz-Status (Kommando 6900, 4 Byte bitcodiert)
#Alle Eintraege teilen sich EINE Adresse - der Coordinator holt sie dank
#der Sammelabfrage pro Durchlauf trotzdem nur ein einziges Mal.
#Zwei Sensoren fassen zusammengehoerende Bits zu einem Zustand zusammen:
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BITMASK, mtype=TYPES.SENSOR, device=DEVICES.SYS, resultlist=VALVE_STATE_LIST, params= _ls(icon="mdi:valve", default_state="unknown"), translation_key="ls_valve_state"),
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BITMASK, mtype=TYPES.SENSOR, device=DEVICES.SYS, resultlist=MICROLEAKAGE_RESULT_LIST, params= _ls(icon="mdi:magnify-scan", default_state="no_result"), translation_key="ls_microleakage_result"),
#Die uebrigen benannten Bits je als eigener binary_sensor:
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BIT, mtype=TYPES.BINARY_SENSOR, device=DEVICES.SYS, params= _ls(bit=0, icon="mdi:magnify-scan"), translation_key="ls_homing"),  # Bit 0
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BIT, mtype=TYPES.BINARY_SENSOR, device=DEVICES.SYS, params= _ls(bit=1, icon="mdi:lock"), translation_key="ls_closed_manual_u3"),  # Bit 1
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BIT, mtype=TYPES.BINARY_SENSOR, device=DEVICES.SYS, params= _ls(bit=2, icon="mdi:home-export-outline"), translation_key="ls_holiday_mode"),  # Bit 2
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BIT, mtype=TYPES.BINARY_SENSOR, device=DEVICES.SYS, params= _ls(bit=3, deviceclass=_PROBLEM, icon="mdi:cup-water"), translation_key="ls_waterquantity_exceeded"),  # Bit 3
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BIT, mtype=TYPES.BINARY_SENSOR, device=DEVICES.SYS, params= _ls(bit=4, deviceclass=_PROBLEM, icon="mdi:water-alert"), translation_key="ls_waterflow_exceeded"),  # Bit 4
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BIT, mtype=TYPES.BINARY_SENSOR, device=DEVICES.SYS, params= _ls(bit=5, deviceclass=_PROBLEM, icon="mdi:timer-alert-outline"), translation_key="ls_withdrawaltime_exceeded"),  # Bit 5
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BIT, mtype=TYPES.BINARY_SENSOR, device=DEVICES.SYS, params= _ls(bit=6, deviceclass=_PROBLEM, icon="mdi:water-alert-outline"), translation_key="ls_leakage"),  # Bit 6
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BIT, mtype=TYPES.BINARY_SENSOR, device=DEVICES.SYS, params= _ls(bit=7, icon="mdi:sleep"), translation_key="ls_sleep_mode"),  # Bit 7
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BIT, mtype=TYPES.BINARY_SENSOR, device=DEVICES.SYS, params= _ls(bit=16, deviceclass=_PROBLEM, icon="mdi:cup-water"), translation_key="ls_learning_waterquantity_exceeded"),  # Bit 16
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BIT, mtype=TYPES.BINARY_SENSOR, device=DEVICES.SYS, params= _ls(bit=17, deviceclass=_PROBLEM, icon="mdi:water-alert"), translation_key="ls_learning_waterflow_exceeded"),  # Bit 17
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BIT, mtype=TYPES.BINARY_SENSOR, device=DEVICES.SYS, params= _ls(bit=18, deviceclass=_PROBLEM, icon="mdi:timer-alert-outline"), translation_key="ls_learning_withdrawaltime_exceeded"),  # Bit 18
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BIT, mtype=TYPES.BINARY_SENSOR, device=DEVICES.SYS, params= _ls(bit=19, deviceclass=_PROBLEM, icon="mdi:water-off-outline"), translation_key="ls_no_waterflow_15days"),  # Bit 19
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BIT, mtype=TYPES.BINARY_SENSOR, device=DEVICES.SYS, params= _ls(bit=20, icon="mdi:school-outline"), translation_key="ls_learning_mode_finished"),  # Bit 20
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BIT, mtype=TYPES.BINARY_SENSOR, device=DEVICES.SYS, params= _ls(bit=21, icon="mdi:electric-switch"), translation_key="ls_closed_by_input"),  # Bit 21
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BIT, mtype=TYPES.BINARY_SENSOR, device=DEVICES.SYS, params= _ls(bit=22, icon="mdi:electric-switch"), translation_key="ls_sleep_mode_by_input"),  # Bit 22
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BIT, mtype=TYPES.BINARY_SENSOR, device=DEVICES.SYS, params= _ls(bit=24, deviceclass=_RUNNING, icon="mdi:school"), translation_key="ls_learning_mode_active"),  # Bit 24
    RestItem( address_read="6900", read_bytes = 4, read_index=0, mformat=FORMATS.STATUS_BIT, mtype=TYPES.BINARY_SENSOR, device=DEVICES.SYS, params= _ls(bit=25, deviceclass=_RUNNING, icon="mdi:cog-sync-outline"), translation_key="ls_special_mode_active"),  # Bit 25

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
