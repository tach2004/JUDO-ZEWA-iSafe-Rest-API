"""RESTobject.

A REST object that contains a REST item and communicates with the REST-API.
It contains a REST Client for setting and getting REST response values
"""

# =============================================================================
#  AENDERUNGEN gegenueber der bisherigen Fassung (alle mit
#  "===== GEAENDERT (gather/session) =====" markiert):
#
#   1. Imports: asyncio, contextlib.nullcontext, requests.adapters.HTTPAdapter
#   2. Neue Konstante MAX_PARALLEL_REQUESTS (= die Stellschraube, s.u.)
#   3. RestAPI.__init__: echte requests.Session mit Auth + Connection-Pool
#      statt "self._session = None"; dazu der Parallelitaets-Limiter
#   4. login():   requests.get(..., auth=...) -> self._session.get(...)
#   5. get_rest(): dito + "async with self._limiter"
#   6. set_rest(): dito + "async with self._limiter"
#   7. close():   schliesst die Session (verhindert Socket-Leaks bei Reload)
#
#  NEU (Sammelabfrage), markiert mit "===== GEAENDERT (Sammelabfrage) =====":
#   8. Zyklus-Zwischenspeicher: Adressen, die von mehreren Items gelesen
#      werden (5E00 von drei, 6400 von zwei Items), werden pro Coordinator-
#      Durchlauf nur EINMAL von der API geholt. Welche Adressen das sind,
#      meldet der Coordinator per set_cacheable_commands().
#   9. set_rest() verwirft den Zwischenspeicher nach jedem Schreibzugriff.
#  10. Der eigentliche HTTP-Aufruf steckt jetzt in der Hilfsmethode
#      _request(); "Send command" wird dort direkt vor dem echten Request
#      geloggt (vorher stand die Zeile vor der Bremse, dadurch sah der Log
#      so aus, als gingen alle Kommandos gleichzeitig raus).
#
#  UNVERAENDERT geblieben ist alles Uebrige, insbesondere:
#   - write_value()  (wird von entities.py:494 und :563 benutzt)
#   - saemtliche FORMATS-Filter in value() und setvalue()
#   - die Cases SELECT, SELECT_WO, DATETIME_JUDO, NUMBER_WO, BUTTON_WO_DATETIME
#   - order_hex_buffer(), format_int_message(), format_str_message()
#   - alle Log-Texte und die bestehende Parsing-Logik
# =============================================================================

# ===== GEAENDERT (gather/session) - START =====
# asyncio + nullcontext fuer die Parallelitaets-Begrenzung,
# HTTPAdapter fuer den Connection-Pool der requests.Session.
import asyncio
import logging
from contextlib import nullcontext
from datetime import datetime
from functools import partial
import requests
from requests.adapters import HTTPAdapter
# ===== GEAENDERT (gather/session) - ENDE =====
from homeassistant.core import HomeAssistant

from .configentry import MyConfigEntry
from .const import DEVICETYPES, FORMATS, CONF, TYPES
from .items import RestItem

logging.basicConfig()
log = logging.getLogger(__name__)

# ===== GEAENDERT (gather/session) - START =====
# +---------------------------------------------------------------------+
# |  STELLSCHRAUBE: maximale Anzahl gleichzeitiger Requests zum JUDO.    |
# |                                                                     |
# |    4     -> Standard, schont das kleine Webinterface im JUDO         |
# |    8     -> schneller, mehr Last auf dem Geraet                      |
# |    0     -> UNBEGRENZT (alle Requests gleichzeitig, wie im           |
# |             urspruenglichen gather-Vorschlag ohne Bremse)            |
# |                                                                     |
# |  Nur diesen einen Wert aendern - der Connection-Pool passt sich      |
# |  automatisch an.                                                     |
# +---------------------------------------------------------------------+
MAX_PARALLEL_REQUESTS = 1

# Groesse des HTTP-Connection-Pools. Sie folgt automatisch der Einstellung
# oben; bei "unbegrenzt" ein Festwert, der ueber der Item-Anzahl liegt, damit
# urllib3 keine "Connection pool is full"-Warnungen ins Log schreibt.
_POOL_MAXSIZE = MAX_PARALLEL_REQUESTS if MAX_PARALLEL_REQUESTS else 32
# ===== GEAENDERT (gather/session) - ENDE =====


class RestAPI:
    """
    RestAPI class that provides a connection to the rest api,
    which is used by the RestItems.
    """

    def __init__(self, config_entry: MyConfigEntry, hass: HomeAssistant) -> None:
        """Construct RestAPI.

        :param config_entry: HASS config entry
        :type config_entry: MyConfigEntry
        """
        self._ip = config_entry.data[CONF.HOST]
        self._port = config_entry.data[CONF.PORT]
        self._username = config_entry.data[CONF.USERNAME]
        self._password = config_entry.data[CONF.PASSWORD]
        self._hass = hass
        self._rest_client = None
        self._base_url = (
            "http://"
            # + str(self._user)
            # + ":"
            # + str(self._password)
            # + "@"
            + str(self._ip)
            + ":"
            + str(self._port)
        )
        self._api_url = self._base_url + "/api/rest/"
        self._devicetype = None
        self._connected = False
        # ===== GEAENDERT (gather/session) - START =====
        # Vorher: self._session = None  ->  jede Anfrage baute eine eigene
        # TCP-Verbindung inkl. neuer Basic-Auth auf.
        # Jetzt: eine wiederverwendete Session mit Connection-Pool.
        adapter = HTTPAdapter(pool_connections=1, pool_maxsize=_POOL_MAXSIZE)
        self._session = requests.Session()
        self._session.auth = (self._username, self._password)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        # Bremse fuer parallele Requests (siehe MAX_PARALLEL_REQUESTS oben).
        # Bei 0/None wird nullcontext benutzt -> gar keine Begrenzung.
        self._limiter = (
            asyncio.Semaphore(MAX_PARALLEL_REQUESTS)
            if MAX_PARALLEL_REQUESTS
            else nullcontext()
        )
        # ===== GEAENDERT (gather/session) - ENDE =====
        # ===== GEAENDERT (Sammelabfrage) - START =====
        # Zwischenspeicher fuer Adressen, die innerhalb EINES Coordinator-
        # Durchlaufs mehrfach gelesen werden. Ausserhalb eines Durchlaufs ist
        # er None - dann wird nie zwischengespeichert. Dadurch bekommt der
        # 11s-Wasserfluss-Task immer einen frischen water_total-Wert.
        self._cycle_cache = None
        self._cacheable = frozenset()
        # Adressen, die in diesem Durchlauf mit HTTP 200 aber LEEREN Nutzdaten
        # geantwortet haben. Das ist kein Fehler: der JUDO quittiert so, solange
        # er beschaeftigt ist (Kugelventil faehrt ca. 10 s, Mikroleckagepruefung
        # laeuft). Der Coordinator wertet das aus und meldet es nur als Debug.
        self._busy_commands = set()
        # Adressen, die in diesem Durchlauf ERFOLGREICH gelesen wurden. Nur fuer
        # diese stellt der Coordinator den Zeitstempel des Intervalls weiter -
        # ein Fehlversuch wird dadurch im naechsten Durchlauf wiederholt.
        self._read_ok = set()
        # Merker, ob seit der letzten Abfrage geschrieben wurde. Der Coordinator
        # liest daraufhin im naechsten Durchlauf alles neu, damit ein
        # geschriebener Wert sofort bestaetigt wird und nicht erst nach Ablauf
        # des Intervalls.
        self._write_happened = False
        # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - START =====
        # Adressen, die der JUDO mit HTTP 400 quittiert hat. 400 = "Bad Request"
        # heisst hier: dieses Kommando kennt die Firmware nicht. Das ist ein
        # DAUERHAFTER Zustand - anders als "beschaeftigt" (HTTP 200 mit leeren
        # Nutzdaten) oder eine Ueberlastung (HTTP 503), die beide gleich im
        # naechsten Durchlauf erneut versucht werden.
        #
        # Bewusst NICHT in begin_read_cycle() zurueckgesetzt: das Set gilt fuer
        # die gesamte Laufzeit der Integration. Ein Neustart bzw. ein Neuladen
        # prueft von selbst neu - z.B. nach einem Firmware-Update des JUDO.
        self._unsupported_commands = set()
        # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - ENDE =====
        # Eine Sperre pro Adresse: verhindert, dass zwei Items dieselbe
        # Adresse gleichzeitig holen. Ohne sie wuerde der zweite Task noch
        # ins Leere greifen, weil der Erste den Wert erst nach seinem
        # Request ablegt. Wird VOR der Parallelitaets-Bremse genommen -
        # ein Task, der die Bremse haelt, wartet nie auf eine Sperre,
        # daher kann es keine Verklemmung geben.
        self._cache_locks = {}
        # ===== GEAENDERT (Sammelabfrage) - ENDE =====

    # ===== GEAENDERT (Sammelabfrage) - START =====
    def set_cacheable_commands(self, commands) -> None:
        """Adressen festlegen, die pro Durchlauf nur einmal gelesen werden."""
        self._cacheable = frozenset(c for c in commands if c)
        if self._cacheable:
            log.debug("Sammelabfrage aktiv fuer: %s", sorted(self._cacheable))

    @property
    def busy_commands(self) -> set:
        """Adressen, die in diesem Durchlauf leer quittiert wurden."""
        return self._busy_commands

    @property
    def read_ok(self) -> set:
        """Adressen, die in diesem Durchlauf erfolgreich gelesen wurden."""
        return self._read_ok

    # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - START =====
    @property
    def unsupported_commands(self) -> set:
        """Adressen, die diese Geraete-Firmware nicht beherrscht (HTTP 400)."""
        return self._unsupported_commands
    # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - ENDE =====

    def pop_write_happened(self) -> bool:
        """True, wenn seit dem letzten Aufruf geschrieben wurde (und zuruecksetzen)."""
        happened = self._write_happened
        self._write_happened = False
        return happened

    def begin_read_cycle(self) -> None:
        """Zwischenspeicher aktivieren (Aufruf am Anfang von fetch_data)."""
        self._cycle_cache = {}
        self._busy_commands = set()
        self._read_ok = set()

    def end_read_cycle(self) -> None:
        """Zwischenspeicher verwerfen (Aufruf am Ende von fetch_data)."""
        self._cycle_cache = None
    # ===== GEAENDERT (Sammelabfrage) - ENDE =====

    async def login(self) -> None:
        """Log into the portal. Create cookie to stay logged in for the session."""

        # ===== GEAENDERT (gather/session) - START =====
        # requests.get(..., auth=...) -> self._session.get(...)
        # Die Auth steckt jetzt fest in der Session.
        _useless = await self._hass.async_add_executor_job(
            partial(self._session.get, url=self._base_url, timeout=10)
        )
        # ===== GEAENDERT (gather/session) - ENDE =====

        # r = requests.get(self._base_url, auth=(self._username, self._password), timeout=10 )
        # log.warning(r.text)

    async def get_rest(self, command: str):
        """get raw response from REST api"""
        if command is None:
            return None
        # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - START =====
        # Einmal als "kennt die Firmware nicht" erkannt - nie wieder anfragen.
        # Steht bewusst vor dem Zwischenspeicher, damit auch Aufrufe ausserhalb
        # eines Durchlaufs (z.B. der Wasserfluss-Task) gar nicht erst senden.
        if command in self._unsupported_commands:
            return None
        # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - ENDE =====
        # ===== GEAENDERT (Sammelabfrage) - START =====
        # Nur Adressen, die der Coordinator als mehrfach gelesen gemeldet hat,
        # und nur waehrend eines laufenden Durchlaufs.
        cache = self._cycle_cache
        if cache is not None and command in self._cacheable:
            if command in cache:
                log.debug("Sammelabfrage: %s aus diesem Durchlauf", command)
                return cache[command]
            lock = self._cache_locks.setdefault(command, asyncio.Lock())
            async with lock:
                # Nach dem Warten erneut pruefen - in der Zwischenzeit hat
                # ein anderer Task die Adresse in aller Regel schon geholt.
                if command in cache:
                    log.debug("Sammelabfrage: %s aus diesem Durchlauf", command)
                    return cache[command]
                res = await self._request(command)
                # Auch einen FEHLVERSUCH merken (res is None). Sonst wuerde
                # jedes weitere Item derselben Adresse einzeln neu anfragen -
                # bei den 19 Status-Bits auf 6900 waeren das 19 Requests an ein
                # Geraet, das ohnehin gerade nicht antwortet (z.B. waehrend der
                # Mikroleckagepruefung). Im naechsten Durchlauf wird wieder
                # normal gelesen, der Zwischenspeicher gilt nur fuer diesen.
                cache[command] = res
                return res
        return await self._request(command)

    async def _request(self, command: str):
        """Fuehrt den eigentlichen HTTP-Aufruf aus (frueher Rumpf von get_rest)."""
        # ===== GEAENDERT (Sammelabfrage) - ENDE =====
        response = None
        try:
            url = self._api_url + command
            # ===== GEAENDERT (gather/session) - START =====
            # Session statt requests.get + Begrenzung der Parallelitaet.
            # Nur der Netzwerk-Call haelt einen Slot; response.json() unten
            # ist reine CPU-Arbeit und darf keinen Slot blockieren.
            async with self._limiter:
                # ===== GEAENDERT (Sammelabfrage) - START =====
                # Log steht jetzt direkt vor dem echten Request, damit der
                # Debug-Log den tatsaechlichen Ablauf zeigt.
                log.debug("Send command %s", command)
                # ===== GEAENDERT (Sammelabfrage) - ENDE =====
                response = await self._hass.async_add_executor_job(
                    partial(self._session.get, url=url, timeout=10)
                )
            # ===== GEAENDERT (gather/session) - ENDE =====
            log.debug("Response %s", response.status_code)
            status = response.status_code
            if status == 200:
                res = await self._hass.async_add_executor_job(response.json)
                data = res["data"]
                log.debug("Content %s", str(data))
                if not data:
                    # HTTP 200, aber keine Nutzdaten. Der JUDO antwortet so,
                    # solange er beschaeftigt ist - waehrend das Kugelventil
                    # faehrt oder die Mikroleckagepruefung laeuft. Kein Fehler:
                    # der zuletzt gelesene Wert bleibt einfach stehen.
                    log.debug("Keine Daten fuer %s - Judo gerade beschaeftigt", command)
                    self._busy_commands.add(command)
                    return None
                self._read_ok.add(command)
                return res["data"]
            else:
                # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - START =====
                # HTTP 400 = "Bad Request": der JUDO kennt dieses Kommando
                # nicht. Bei aelterer Connectivity-Modul-Firmware betrifft das
                # 6900 (Leckageschutz-Status) und 6800 (Leckageeinstellungen).
                # Einmal merken, danach nie wieder anfragen - sonst liefe jede
                # Minute derselbe vergebliche Request samt Warnung.
                #
                # Alle anderen Fehlerkennungen (503, 5xx ...) bleiben wie
                # bisher: sie werden im naechsten Durchlauf erneut versucht.
                if status == 400:
                    if command not in self._unsupported_commands:
                        self._unsupported_commands.add(command)
                        log.warning(
                            "Kommando %s wird von dieser Geraete-Firmware nicht "
                            "unterstuetzt (HTTP 400). Es wird ab jetzt nicht mehr "
                            "abgefragt; die zugehoerigen Entitaeten entfallen. "
                            "Nach einem Firmware-Update des JUDO die Integration "
                            "neu laden.",
                            command,
                        )
                    return None
                # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - ENDE =====
                log.warning("Content ignored for API return status %s", str(status))
                return None
        except Exception:
            if response is not None:
                status = str(response.status_code)
            else:
                status = "unknown status"
            log.warning("Judo REST API call failed with %s", status)
            return None

    async def write_value(self, command: str, payload: bytes):  #NEU
        """Write a payload to the REST API."""
        hex_payload = payload.hex().upper()
        await self.set_rest(command, hex_payload)               #BIS hier neu

    async def set_rest(self, command: str, towrite: str):
        """write raw response to REST api"""
        if command is None: 
            return None     
        if towrite is None: 
            return None     
        try:
            url = self._api_url + command + towrite
            # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - START =====
            # Schreibzugriffe tauchten im Debug-Log bisher gar nicht auf. Ein
            # Log war dadurch schwer zu lesen: nach jedem Schreibvorgang liest
            # der Coordinator absichtlich alles neu, was ohne diese Zeile wie
            # ein Intervallfehler aussieht.
            log.debug("Write command %s payload %s", command, towrite)
            # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - ENDE =====
            # ===== GEAENDERT (gather/session) - START =====
            # Session statt requests.get + Begrenzung der Parallelitaet.
            # Das timeout=2 gilt weiterhin nur fuer den HTTP-Request selbst,
            # nicht fuer eine eventuelle Wartezeit auf einen freien Slot.
            async with self._limiter:
                response = await self._hass.async_add_executor_job(
                    partial(self._session.get, url=url, timeout=2)
                )
            # ===== GEAENDERT (gather/session) - ENDE =====
            res = await self._hass.async_add_executor_job(response.json)
            # ===== GEAENDERT (Sammelabfrage) - START =====
            # Nach einem Schreibzugriff sind zwischengespeicherte Rohwerte
            # dieses Durchlaufs veraltet.
            if self._cycle_cache is not None:
                self._cycle_cache.clear()
            self._write_happened = True
            # ===== GEAENDERT (Sammelabfrage) - ENDE =====
            return res["data"]
        except Exception:
            log.warning("Connection to Judo Zewa failed")
            return None

    async def connect(self):
        """Open REST connection to test if available."""
        res = await self.get_rest("FF00")
        if res is None:
            return None
        if res in DEVICETYPES:
            self._devicetype = res
            log.info("Connected to %s", self._devicetype)
            return True

        log.warning("Unknown Device detected, ID=%s", res)
        return None

    def close(self):
        """Close REST connection."""
        # ===== GEAENDERT (gather/session) - START =====
        # Die Session haelt jetzt offene Sockets - beim Entladen/Reload der
        # Integration muessen die geschlossen werden.
        if self._session is not None:
            try:
                self._session.close()
            except Exception:  # pragma: no cover - close soll nie werfen
                log.debug("Fehler beim Schliessen der REST-Session", exc_info=True)
        # ===== GEAENDERT (gather/session) - ENDE =====
        log.info("Connection to Judo Zewa closed")
        return True

    def get_devicetype(self):
        """Return device type."""
        return self._devicetype


class RestObject:
    """RestObject.

    A REST object that contains a REST item and communicates with the REST.
    It contains a REST Client for setting and getting REST register values
    """

    def __init__(self, rest_api: RestAPI, rest_item: RestItem) -> None:
        """Construct RestObject.

        :param rest_api: The REST API
        :type rest_api: RestAPI
        :param rest_item: definition of rest item
        :type rest_item: RestItem
        """
        self._rest_item = rest_item
        self._rest_api = rest_api
        self._divider = 1
        if self._rest_item.params is not None:
            self._divider = self._rest_item.params.get("divider", 1)

    def order_hex_buffer(self, buffer: str, flip) -> str:    
        """brings a hex buffer in the right order"""
        if flip is True:
            little_endian = bytes.fromhex(buffer)[::-1].hex()
            return little_endian
        big_endian = bytes.fromhex(buffer)[::1].hex()
        return big_endian

    def format_int_message(self, number: int, flip) -> str:
        """format int message as hex buffer to be sent to REST APPI"""
        numbytes = str(self._rest_item.write_bytes * 2)
        mask = "%0." + numbytes + "X"
        return self.order_hex_buffer(mask % number, flip)

    def format_str_message(self, text: str, flip) -> str:
        """format str message as hex buffer to be sent to REST APPI"""
        return self.order_hex_buffer(text.encode("utf-8").hex(), flip)

    @property
    async def value(self):
        """Returns the value from the REST API."""
        if self._rest_api is None:
            return None
        if self._rest_item.format is FORMATS.BUTTON:
            return None
        if self._rest_item.format is FORMATS.BUTTON_INTERNAL:
            return None
        if self._rest_item.format is FORMATS.BUTTON_WO_DATETIME:
            return None
        if self._rest_item.format is FORMATS.NUMBER_WO:
            return None
        if self._rest_item.format is FORMATS.NUMBER_INTERNAL:
            return None
        if self._rest_item.format is FORMATS.SWITCH_INTERNAL:
            return None
        if self._rest_item.format is FORMATS.SELECT_WO:
            return None
        if self._rest_item.format is FORMATS.SELECT_WO_ACTION:
            return None
        if self._rest_item.format is FORMATS.SELECT_INTERNAL:
            return None
        if self._rest_item.format is FORMATS.SENSOR_INTERNAL:
            return None
        if self._rest_item.format is FORMATS.SENSOR_INTERNAL_TIMESTAMP:
            return None
        res = await self._rest_api.get_rest(self._rest_item.address_read)

        if res is None:
            return None

        index = self._rest_item.read_index * 2
        big_endian = res[index : index + self._rest_item.read_bytes * 2]
        little_endian = bytes.fromhex(big_endian)[::-1].hex()
        big_endian = bytes.fromhex(big_endian)[::1].hex()

        if big_endian is None:
            return None
        if little_endian is None:
            return None
        if big_endian == "":
            return None
        if little_endian == "":
            return None
        match self._rest_item.format:
            case FORMATS.SWITCH:
                return None
            case FORMATS.NUMBER:
                return float(int(little_endian, 16) / self._divider)
            case FORMATS.SW_VERSION:
                major = str(int(little_endian[0:2], 16))
                minor = str(int(little_endian[2:4], 16)).zfill(2)
                letter = str(bytearray.fromhex(little_endian[4:6]).decode())
                return str(major + "." + minor + letter)
            case FORMATS.TIMESTAMP:
                return str(datetime.fromtimestamp(int(big_endian, 16)))
            case FORMATS.TEXT:
                return bytearray.fromhex(big_endian).decode()
            case FORMATS.STATUS:
                return self._rest_item.get_translation_key_from_number(int(little_endian, 16))
            case FORMATS.STATUS_BIT:
                # Ein einzelnes Bit aus der Bitmaske (z.B. Leckageschutz-Status 6900).
                # Die Bitnummer steht in params["bit"].
                bitmask = int(little_endian, 16)
                bit = 0
                if self._rest_item.params is not None:
                    bit = self._rest_item.params.get("bit", 0)
                return bool(bitmask >> bit & 1)
            case FORMATS.STATUS_BITMASK:
                # Mehrere zusammengehoerende Bits derselben Maske werden zu EINEM
                # Zustand zusammengefasst. In der resultlist ist number = Bitnummer,
                # die Reihenfolge bestimmt die Prioritaet (erstes gesetztes Bit gewinnt).
                bitmask = int(little_endian, 16)
                if self._rest_item.resultlist is not None:
                    for entry in self._rest_item.resultlist:
                        if bitmask >> entry.number & 1:
                            return entry.translation_key
                default_state = "unknown"
                if self._rest_item.params is not None:
                    default_state = self._rest_item.params.get("default_state", "unknown")
                return default_state
            case FORMATS.SELECT:
                return self._rest_item.get_translation_key_from_number(int(little_endian, 16))
            case FORMATS.DATETIME_JUDO:
                try:
                    # Format: DD MM YY HH mm SS (6 bytes / 12 hex chars)
                    day = int(big_endian[0:2], 16)
                    month = int(big_endian[2:4], 16)
                    year = int(big_endian[4:6], 16) + 2000  # Jahr z. B. 0x17 = 23 → 2023
                    hour = int(big_endian[6:8], 16)
                    minute = int(big_endian[8:10], 16)
                    second = int(big_endian[10:12], 16)
                    return datetime(year, month, day, hour, minute, second) 
                except Exception as e:
                    log.warning("Fehler beim Parsen von Judo-Datum: %s", e)
                    return None
            case _:
                log.warning(
                    "Unknown format: %s in %s",
                    str(self._rest_item.type),
                    str(self._rest_item.translation_key),
                )
                return None
        return None

    # @value.setter
    async def setvalue(self, value=None) -> None:
        """Set the value of the rest register, does nothing when not R/W.

        :param val: The value to write to the rest
        :type val: any"""
        towrite = None
        if self._rest_api is None:
            return
        if self._rest_item.type == TYPES.SENSOR:
            return
        if self._rest_item.type == TYPES.BINARY_SENSOR:
            return
        if self._rest_item.format is FORMATS.STATUS_BIT:
            return
        if self._rest_item.format is FORMATS.STATUS_BITMASK:
            return
        if self._rest_item.format is FORMATS.BUTTON:
            await self._rest_api.set_rest(self._rest_item.address_write, "")
            return
        if self._rest_item.format is FORMATS.BUTTON_INTERNAL:
            return
        if self._rest_item.format is FORMATS.NUMBER_INTERNAL:
            return
        if self._rest_item.format is FORMATS.SWITCH_INTERNAL:
            return
        if self._rest_item.format is FORMATS.SELECT_INTERNAL:
            return
        if self._rest_item.format is FORMATS.SENSOR_INTERNAL:
            return
        if self._rest_item.format is FORMATS.SENSOR_INTERNAL_TIMESTAMP:
            return
        if value is None:
            return
        self._rest_item.state = value
        match self._rest_item.format:
            case FORMATS.SWITCH:
                if value == 0:
                    await self._rest_api.set_rest(self._rest_item.address_read, "")
                if value == 1:
                    await self._rest_api.set_rest(self._rest_item.address_write, "")
                return
            case FORMATS.NUMBER:
                towrite = self.format_int_message(int(int(value) * self._divider), True)
            case FORMATS.NUMBER_WO:
                towrite = self.format_int_message(int(int(value) * self._divider), True)
            case FORMATS.TEXT:
                towrite = self.format_str_message((value), True)
            case FORMATS.STATUS:
                towrite = self.format_int_message(
                    self._rest_item.get_number_from_translation_key(value), True
                )
            case FORMATS.SELECT:
                towrite = self.format_int_message(
                    self._rest_item.get_number_from_translation_key(value), True
                )
            case FORMATS.SELECT_WO:
                towrite = self.format_int_message(
                    self._rest_item.get_number_from_translation_key(value), True
                )
            case FORMATS.SELECT_WO_ACTION:
                # Aktions-Select (z.B. Lernmodus quittieren, Kommando 6B).
                # Der Standby-Eintrag wird in entities.py abgefangen und
                # erreicht diese Stelle nie.
                towrite = self.format_int_message(
                    self._rest_item.get_number_from_translation_key(value), True
                )
            case FORMATS.BUTTON_WO_DATETIME:
                towrite = value.upper()  #Adresse?
            case _:
                log.warning(
                    "Unknown format: %s in %s",
                    str(self._rest_item.type),
                    str(self._rest_item.translation_key),
                )
                return
        if towrite is not None:
            await self._rest_api.set_rest(self._rest_item.address_write, towrite)
        return
