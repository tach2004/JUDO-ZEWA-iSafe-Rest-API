"""Constants."""

from dataclasses import dataclass

from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_SCAN_INTERVAL,
)


@dataclass(frozen=True)
class ConfConstants:
    """Constants used for configurastion"""

    HOST = CONF_HOST
    PORT = CONF_PORT
    PASSWORD = CONF_PASSWORD
    USERNAME = CONF_USERNAME
    DEVICE_POSTFIX = "Device-Postfix"
    SCAN_INTERVAL = CONF_SCAN_INTERVAL


CONF = ConfConstants()


@dataclass(frozen=True)
class MainConstants:
    """Main constants."""

    DOMAIN = "judo_rest_api"
    SCAN_INTERVAL = "60"  # timedelta(seconds=60))
    UNIQUE_ID = "unique_id"
    APPID = 100


CONST = MainConstants()


@dataclass(frozen=True)
class FormatConstants:
    """Format constants."""

    NUMBER = "number"
    NUMBER_WO = "number_wo" #When a number value should only be written to API and not read
    NUMBER_INTERNAL = "number_internal" #Only internal Number without read and write to the api
    TEXT = "text"
    STATUS = "status" 
    STATUS_WO = "status_wo"  #When a select value should only be written to API and not read
    UNKNOWN = "unknown"
    SWITCH = "Switch"
    SWITCH_INTERNAL = "Switch_internal" #Only internal Switch without read and write to the api
    BUTTON = "Button"
    BUTTON_INTERNAL = "button_interal"
    BUTTON_WO_DATETIME = "button_wo_datetime"
    TIMESTAMP = "Timestamp"
    SW_VERSION = "SW_Version"
    DATETIME_JUDO = "datetime_judo"


FORMATS = FormatConstants()


@dataclass(frozen=True)
class TypeConstants:
    """Type constants."""

    SENSOR = "Sensor"
    SENSOR_CALC = "Sensor_Calc"
    SELECT = "Select"
    SELECT_NOIF = "Select_noif"
    NUMBER = "Number"
    NUMBER_RO = "Number_RO"
    SWITCH = "Switch"
    BUTTON = "Button"


TYPES = TypeConstants()


@dataclass(frozen=True)
class DeviceConstants:
    """Device constants."""

    SYS = "dev_system"
    ST = "dev_statistics"
    UK = "dev_unknown"


DEVICES = DeviceConstants()

COMMANDS = {
    "Geraetetyp": "FF00",
    "Geraetenummer": "0600",
    "SW-Version": "0100",
    "Inbetriebnahmedatum": "0E00",
    "Betriebsstundenzaehler": "2500",
    "Kundendienst-Serviceadresse": "5800",
    "Wunschwasserhaerte": "5100",
    "Salzvorrat": "5600",
    "Salzreichweite": "5700",
    "Gesamtwassermenge": "2800",
    "Weichwassermenge": "2900",
    "Tagesstatistik": "FB00",
    "Wochenstatistik": "FC00",
    "Monatsstatistik": "FD00",
    "Jahresstatistik": "FE00",
}


DEVICETYPES = {
    "33": "i-soft SAFE+",
    "42": "i-soft K SAFE+",
    "58": "i-soft PRO",
    "4B": "i-soft PRO",
    "4C": "i-soft PRO L",
    "32": "i-soft",
    "43": "i-soft K",
    "34": "SOFTwell P",
    "35": "SOFTwell S",
    "36": "SOFTwell K",
    "47": "SOFTwell KP",
    "72": "SOFTwell KS",
    "44": "ZEWA/PROM i-SAFE (FILT)",
    "41": "i-dos eco",
    "3c": "i-fill",
}
