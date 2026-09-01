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
    # Eigene Abfrageintervalle, alle Angaben in SEKUNDEN.
    # Werden beim Einrichten bzw. unter "Neu konfigurieren" gesetzt.
    INTERVAL_STATUS = "interval_status"      # 6900 Leckageschutz-Status
    INTERVAL_SETTINGS = "interval_settings"  # 5E00 / 6400 / 6500 / 6800
    INTERVAL_DATETIME = "interval_datetime"  # 5900 Judo-Uhrzeit


CONF = ConfConstants()


@dataclass(frozen=True)
class MainConstants:
    """Main constants."""

    DOMAIN = "judo_rest_api"
    SCAN_INTERVAL = "60"  # timedelta(seconds=60))
    # Standardwerte der Abfrageintervalle in Sekunden
    INTERVAL_STATUS = "60"     # Leckageschutz-Status moeglichst aktuell
    INTERVAL_SETTINGS = "600"  # Einstellungen aendern sich selten
    INTERVAL_DATETIME = "300"  # Uhrzeit nur fuer den Abgleich
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
    SELECT = "select"
    SELECT_WO = "select_wo"  #When a select value should only be written to API and not read
    SELECT_INTERNAL = "select_internal" #Only internal Select without read and write to the api
    UNKNOWN = "unknown"
    SWITCH = "Switch"
    SWITCH_INTERNAL = "switch_internal" #Only internal Switch without read and write to the api
    BUTTON = "Button"
    BUTTON_INTERNAL = "button_interal"
    BUTTON_WO_DATETIME = "button_wo_datetime"
    TIMESTAMP = "Timestamp"
    SW_VERSION = "SW_Version"
    DATETIME_JUDO = "datetime_judo"
    SENSOR_INTERNAL = "sensor_internal" ##Only internal Sensor without read and write to the api
    SENSOR_INTERNAL_TIMESTAMP = "sensor_internal_timestamp" #Only internal Sensor as timestamp without read and write to the api
    STATUS_BIT = "status_bit"              #Ein einzelnes Bit aus einer Bitmaske (params["bit"]) -> binary_sensor
    STATUS_BITMASK = "status_bitmask"      #Mehrere Bits einer Bitmaske -> ein Zustandstext (resultlist: number = Bitnummer)
    SELECT_WO_ACTION = "select_wo_action"  #Aktions-Select: sendet und springt danach auf den Standby-Eintrag zurueck


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
    BINARY_SENSOR = "Binary_Sensor"


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
