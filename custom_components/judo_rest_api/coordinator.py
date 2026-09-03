"""The Update Coordinator for the RestItems."""

# =============================================================================
#  AENDERUNGEN gegenueber der bisherigen Fassung (alle mit
#  "===== GEAENDERT (gather/session) =====" markiert):
#
#   1. Neue Methode _fetch_item(): enthaelt den try/except-Block, der vorher
#      im Rumpf der for-Schleife stand.
#   2. fetch_data(): die sequenzielle for-Schleife wurde durch
#      asyncio.gather() ersetzt. Wie viele Requests wirklich gleichzeitig
#      laufen, steuert MAX_PARALLEL_REQUESTS in restobject.py (aktuell 1,
#      also faktisch sequenziell - der JUDO beantwortet ohnehin nur eine
#      Anfrage gleichzeitig).
#
#  NEU, markiert mit "===== GEAENDERT (Read-Once) =====" bzw.
#  "===== GEAENDERT (Sammelabfrage) =====":
#   3. READ_ONCE_KEYS: unveraenderliche Werte werden nur im ersten Zyklus
#      gelesen und danach uebersprungen.
#   4. Mehrfach gelesene Adressen (5E00, 6400, 6800, 6900) werden pro
#      Durchlauf nur einmal von der API geholt; die Erkennung passiert
#      automatisch anhand der Item-Liste.
#   5. Die Abfrageintervalle stehen in der HA-Konfiguration (in Sekunden) und
#      sind nach API-Adresse aufgeschluesselt, damit Items derselben Adresse
#      zwangslaeufig dasselbe Intervall haben.
#
#  UNVERAENDERT geblieben ist alles Uebrige, insbesondere:
#   - die komplette Spuelintervall-Logik (_add_months,
#     _get_flush_interval_months, _ensure_last_reset_flush_interval,
#     async_check_flush_interval_due, _setup_flush_interval_daily_check)
#   - set_internal_timestamp() und _try_freeze_install_date_from_judo()
#   - der Zeitabweichungs-Check inkl. _last_time_drift und der Meldung
#   - _async_setup() inkl. Wiederherstellung des Installationsdatums
#   - die vollstaendige FORMATS-Filterliste in get_value()
#   - _previous_water_total, _default_scan_interval und alle Imports
# =============================================================================

import asyncio
import logging
##
import calendar
##
# ===== GEAENDERT (Sammelabfrage) - START =====
from collections import Counter
# ===== GEAENDERT (Sammelabfrage) - ENDE =====
from datetime import timedelta
from datetime import datetime
from datetime import time
# Achtung: die Zeile darueber bindet den Namen "time" an datetime.time.
# Ein einfaches "import time" waere dadurch wirkungslos - deshalb wird
# monotonic gezielt importiert.
from time import monotonic
from homeassistant.components.persistent_notification import async_create as create_notification
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
##
from homeassistant.helpers.event import async_track_time_change
##
from .configentry import MyConfigEntry
from .const import CONF, CONST, FORMATS
from .items import RestItem
from .restobject import RestAPI, RestObject
##
from homeassistant.util import dt as dt_util
from .storage import save_last_written_value, load_last_written_values, PERSISTENT_ENTITIES
##
logging.basicConfig()
log = logging.getLogger(__name__)

# ===== GEAENDERT (Read-Once) - START =====
# +---------------------------------------------------------------------+
# |  Werte, die sich im laufenden Betrieb NIE aendern.                  |
# |                                                                     |
# |  Sie werden nur im ersten Durchlauf nach dem Start gelesen und       |
# |  danach uebersprungen. Der gelesene Wert bleibt im RestItem stehen,  |
# |  die Sensoren zeigen also unveraendert weiter an.                    |
# |                                                                     |
# |  Schlaegt der erste Versuch fehl, wird im naechsten Durchlauf erneut |
# |  versucht - erst ein erfolgreicher Read gilt als erledigt.           |
# |                                                                     |
# |  Nach einem Firmware-Update des JUDO einmal HA neu starten bzw. die  |
# |  Integration neu laden, damit software_version neu gelesen wird.     |
# |                                                                     |
# |  Soll ein Wert doch jede Minute gelesen werden: Zeile hier loeschen. |
# +---------------------------------------------------------------------+
READ_ONCE_KEYS = frozenset({
    "device_type",        # FF00 - Geraetetyp
    "device_number",      # 0600 - Seriennummer
    "software_version",   # 0100 - Firmware-Version
    "install_date_judo",  # 0E00 - Installationsdatum
})
# ===== GEAENDERT (Read-Once) - ENDE =====

# ============================================================================
# ==                                                                        ==
# ==   ABFRAGE-INTERVALLE  -  hier stellst du ein, wie oft gelesen wird     ==
# ==                                                                        ==
# ==   Zahl = "nur in jedem N-ten Durchlauf lesen".                         ==
# ==   Bei 60 s Abfrageintervall bedeutet 10 also etwa alle 10 Minuten.     ==
# ==                                                                        ==
# ==       1  = jeden Durchlauf (wie vorher, keine Einsparung)              ==
# ==       5  = jeden 5. Durchlauf                                          ==
# ==      10  = jeden 10. Durchlauf                                         ==
# ==                                                                        ==
# ==   Der ERSTE Durchlauf nach dem Start liest immer alles.                ==
# ==   Wird ein Wert ueber HA geschrieben, setzt entities.py den State      ==
# ==   sofort selbst - die Anzeige stimmt also auch zwischen zwei Reads.    ==
# ==   Nur eine Aenderung direkt am Geraetepanel wird erst beim naechsten   ==
# ==   planmaessigen Read sichtbar.                                         ==
# ==                                                                        ==
# ============================================================================

# Welche API-Adresse haengt an welchem Konfigurationsfeld?
#
# Die Intervalle werden NICHT mehr hier eingestellt, sondern in Home Assistant:
#   Einstellungen -> Geraete & Dienste -> Judo -> "Neu konfigurieren"
# Alle Angaben in SEKUNDEN (10 Minuten sind also 600).
#
# Die Zuordnung erfolgt bewusst nach ADRESSE und nicht nach Item-Name: mehrere
# Items teilen sich eine Adresse (5E00 drei Stueck, 6800 vier, 6900 sogar 19)
# und muessen zwingend dasselbe Intervall haben - sonst wuerde die
# Sammelabfrage nicht mehr greifen und dieselbe Adresse mehrfach gelesen.
#
# Adressen, die hier NICHT stehen, werden in jedem Durchlauf gelesen, also im
# Takt des allgemeinen Abfrageintervalls (z.B. 2800 water_total).
INTERVAL_ADDRESSES = (
    # (Konfigurationsfeld, Standardwert, betroffene API-Adressen)
    (CONF.INTERVAL_STATUS, CONST.INTERVAL_STATUS, ("6900",)),
    (CONF.INTERVAL_SETTINGS, CONST.INTERVAL_SETTINGS, ("5E00", "6400", "6500", "6800")),
    (CONF.INTERVAL_DATETIME, CONST.INTERVAL_DATETIME, ("5900",)),
)


def _interval_seconds(value, default) -> int:
    """Eine Intervallangabe aus der Konfiguration in ganze Sekunden umwandeln."""
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        seconds = int(default)
    return max(1, seconds)

# Diese Werte werden einmal beim Start und danach beim ersten Durchlauf
# nach Tageswechsel (0 Uhr lokale HA-Zeit) gelesen.
READ_ONCE_PER_DAY_KEYS = frozenset({
    "operating_days",     # 2500 - zaehlt nur einmal taeglich hoch
})

# Moegliche Ausloeser fuer ein geschlossenes Ventil. Alle zutreffenden Gruende
# landen in der Meldung; die Reihenfolge bestimmt nur die Reihenfolge im Text.
VALVE_CLOSED_REASONS = (
    ("ls_leakage",                 "Leckage erkannt"),
    ("ls_waterquantity_exceeded",  "Maximale Wassermenge ueberschritten"),
    ("ls_waterflow_exceeded",      "Maximaler Durchfluss ueberschritten"),
    ("ls_withdrawaltime_exceeded", "Maximale Entnahmezeit ueberschritten"),
    ("ls_closed_by_input",         "Schliessung ueber LS-Eingang"),
    ("ls_closed_manual_u3",        "Manuell geschlossen oder Urlaubsmodus U3"),
    ("ls_holiday_mode",            "Urlaubsmodus aktiv"),
)

# ============================================================================


class MyCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        my_api: RestAPI,
        api_items: RestItem,
        p_config_entry: MyConfigEntry,
    ) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            log,
            # Name of the data. For logging purposes.
            name="judo_rest_api-coordinator",
            # Polling interval. Will only be polled if there are subscribers.
            # update_interval=CONST.SCAN_INTERVAL,
            update_interval=timedelta(
                seconds=int(p_config_entry.data[CONF.SCAN_INTERVAL])
            ),
            # Set always_update to `False` if the data returned from the
            # api can be compared via `__eq__` to avoid duplicate updates
            # being dispatched to listeners
            always_update=True,
        )
        self._rest_api = my_api
        self._device = None
        self._restitems = api_items
        self._number_of_items = len(api_items)
        self._config_entry = p_config_entry
        # ===== GEAENDERT (Read-Once) - START =====
        # Merkt sich, welche READ_ONCE_KEYS bereits erfolgreich gelesen wurden.
        self._read_once_done = set()
        # Abfrageintervalle in Sekunden, je API-Adresse. Kommen aus der
        # Konfiguration; .get() mit Standardwert, damit aeltere Konfigurationen
        # ohne diese Felder weiterhin laufen.
        self._read_intervals = {}
        for conf_key, default, addresses in INTERVAL_ADDRESSES:
            seconds = _interval_seconds(p_config_entry.data.get(conf_key), default)
            for address in addresses:
                self._read_intervals[address] = seconds
        log.debug("Abfrageintervalle in Sekunden: %s", self._read_intervals)
        # Basisintervall (scan_interval) in Sekunden. Wird gebraucht, um die
        # Faelligkeit auf den naechstgelegenen Zyklus zu runden - siehe unten.
        self._base_interval = _interval_seconds(
            p_config_entry.data.get(CONF.SCAN_INTERVAL), CONST.SCAN_INTERVAL
        )
        # Zeitpunkt des letzten erfolgreichen Reads je Adresse (monotonic)
        self._last_read = {}
        # In diesem Durchlauf faellige Adressen - wird in fetch_data gefuellt
        self._due_addresses = set()
        # Merkt sich pro Item das Datum des letzten Reads (READ_ONCE_PER_DAY).
        self._daily_done = {}
        # Adressen, zu denen in diesem Durchlauf bereits eine Warnung im Log
        # steht - verhindert 19 identische Meldungen fuer die 6900-Bits.
        self._warned_addresses = set()
        # Fuer die Meldung "Leckageschutz geschlossen"
        self._previous_valve_state = None
        self._valve_notification_id = "judo_valve_closed"
        # ===== GEAENDERT (Read-Once) - ENDE =====
        # ===== GEAENDERT (Sammelabfrage) - START =====
        # Adressen ermitteln, die von mehreren Items gelesen werden - bei
        # diesem Geraet 5E00 (drei absence_limit_*-Items, read_index 0/2/4)
        # und 6400 (learning_mode_status + learning_water_quantity).
        # Die Antwort ist fuer alle Items identisch, nur der read_index
        # unterscheidet sich. Sie wird deshalb pro Durchlauf einmal geholt.
        address_counts = Counter(
            item.address_read for item in api_items if item.address_read
        )
        my_api.set_cacheable_commands(
            addr for addr, count in address_counts.items() if count > 1
        )
        # ===== GEAENDERT (Sammelabfrage) - ENDE =====
        self._previous_water_total = None
        self._default_scan_interval = timedelta(seconds=int(p_config_entry.data[CONF.SCAN_INTERVAL]))
        self._last_time_drift = None  # Letzte bekannte Zeitabweichung in Sekunden
        ##Spülintervall
        self._flush_time_unsub = None
        self._flush_notification_id = "judo_flush_interval_due"
        self._flush_reset_key = "last_reset_flush_interval"
        self._install_date_storage_key = "install_date_utc"
        self._install_date_frozen = False
        ##

    async def get_value(self, rest_item: RestItem):
        """Read a value from the rest API"""

        if rest_item.format is FORMATS.BUTTON:
            return None
        if rest_item.format is FORMATS.BUTTON_INTERNAL:
            return None
        if rest_item.format is FORMATS.BUTTON_WO_DATETIME:
            return None
        if rest_item.format is FORMATS.NUMBER_WO:
            return None
        if rest_item.format is FORMATS.NUMBER_INTERNAL: 
            return None
        if rest_item.format is FORMATS.SWITCH_INTERNAL: 
            return None
        if rest_item.format is FORMATS.SELECT_WO:
            return None
        if rest_item.format is FORMATS.SELECT_WO_ACTION:
            return None
        if rest_item.format is FORMATS.SELECT_INTERNAL:
            return None
        if rest_item.format is FORMATS.SENSOR_INTERNAL:
            return None
        if rest_item.format is FORMATS.SENSOR_INTERNAL_TIMESTAMP:
            return None
        ro = RestObject(self._rest_api, rest_item)
        if ro is None:
            log.warning("RestObject is None for Item %s", rest_item.translation_key)
            # rest_item.state = None
        else:
            val = await ro.value
            if val is not None:
                log.debug(
                    "Set Value %s for Item %s", str(val), rest_item.translation_key
                )
                rest_item.state = val
            else:
                # Mehrere Items teilen sich eine Adresse (6900: 19 Stueck).
                # Ein einziger fehlgeschlagener Read wuerde sonst 19 gleiche
                # Warnungen erzeugen - deshalb pro Adresse nur eine je Durchlauf.
                address = rest_item.address_read
                # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - START =====
                # Kommando von der Firmware nicht unterstuetzt: restobject.py
                # hat das bereits einmal erklaerend gemeldet. Hier waere eine
                # zweite Warnung nur Rauschen. Betrifft ausschliesslich den
                # ersten Durchlauf - danach wird das Item gar nicht mehr
                # angefasst (siehe _fetch_item).
                if address is not None and address in self._rest_api.unsupported_commands:
                    log.debug(
                        "Kein Wert fuer %s - Kommando %s von der Geraete-Firmware "
                        "nicht unterstuetzt",
                        rest_item.translation_key,
                        address,
                    )
                elif address is not None and address in self._rest_api.busy_commands:
                # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - ENDE =====
                    # Der JUDO hat mit HTTP 200, aber leeren Nutzdaten geantwortet.
                    # Das passiert regulaer, solange er beschaeftigt ist: waehrend
                    # das Kugelventil faehrt oder die Mikroleckagepruefung laeuft.
                    # Kein Fehler - der zuletzt gelesene Wert bleibt stehen.
                    log.debug(
                        "Kein Wert fuer %s - Judo war gerade beschaeftigt",
                        rest_item.translation_key,
                    )
                elif address is None or address not in self._warned_addresses:
                    if address is not None:
                        self._warned_addresses.add(address)
                    log.warning(
                        "None value for Item %s ignored", rest_item.translation_key
                    )
        return rest_item.state

    def get_value_from_item(self, translation_key: str) -> int:
        """Read a value from another rest item"""
        for _useless, item in enumerate(self._restitems):
            if item.translation_key == translation_key:
                return item.state
        return None

####Spülintervall
    def set_internal_timestamp(self, translation_key: str, dt_value) -> None:
        """Set an internal datetime state on the matching RestItem and notify listeners."""
        for item in self._restitems:
            if item.translation_key == translation_key:
                item.state = dt_value
                break
        self.async_update_listeners()

    @staticmethod
    def _add_months(start, months: int):
        """Add calendar months to a datetime (keeps time, clamps day to month end)."""
        if months <= 0:
            return start
        year = start.year + (start.month - 1 + months) // 12
        month = (start.month - 1 + months) % 12 + 1
        day = min(start.day, calendar.monthrange(year, month)[1])
        return start.replace(year=year, month=month, day=day)

    def _get_flush_interval_months(self) -> int:
        """Return selected flush interval in months (0 = deactivated)."""
        state = self.get_value_from_item("flush_interval")
        if not state or state == "deactivated":
            return 0
        try:
            return int(str(state).lower().replace("m", ""))
        except Exception:
            log.debug("flush_interval konnte nicht geparst werden: %s", state)
            return 0

    async def _ensure_last_reset_flush_interval(self):
        """Ensure we have a persisted timestamp for last reset (returns UTC datetime)."""
        stored = await load_last_written_values(self.hass)
        iso = stored.get(self._flush_reset_key)

        dt_utc = None
        if iso:
            dt_utc = dt_util.parse_datetime(iso)
            if dt_utc is not None and dt_utc.tzinfo is None:
                dt_utc = dt_utc.replace(tzinfo=dt_util.UTC)

        if dt_utc is None:
            dt_utc = dt_util.utcnow()
            await save_last_written_value(self.hass, self._flush_reset_key, dt_utc.isoformat())

        # internen Sensor-State setzen
        self.set_internal_timestamp(self._flush_reset_key, dt_utc)
        return dt_utc

    async def async_check_flush_interval_due(self) -> None:
        """Check if flush interval is due and (re)create persistent notification daily at 18:00."""
        months = self._get_flush_interval_months()

        if months <= 0:
            # deaktiviert → ggf. alte Meldung entfernen
            await self.hass.services.async_call(
                "persistent_notification",
                "dismiss",
                {"notification_id": self._flush_notification_id},
                blocking=False,
            )
            return

        last_reset_utc = await self._ensure_last_reset_flush_interval()

        last_reset_local = dt_util.as_local(last_reset_utc)
        due_local = self._add_months(last_reset_local, months)
        now_local = dt_util.now()

        if now_local >= due_local:
            msg = (
                f"Spülintervall fällig!\n\n"
                f"Intervall: {months} Monat(e)\n"
                f"Letzte Spülung: {last_reset_local.strftime('%d.%m.%Y %H:%M')}\n"
                f"Fällig seit: {due_local.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Nach der Spülung bitte den Button 'Spülintervall rücksetzten' drücken."
            )
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Judo Spülintervall",
                    "message": msg,
                    "notification_id": self._flush_notification_id,
                },
                blocking=False,
            )

    def _setup_flush_interval_daily_check(self) -> None:
        """Täglicher Check um 18:00 Uhr (lokale HA-Zeit)."""
        if self._flush_time_unsub is not None:
            return

        @callback
        def _handler(now):  
            self.hass.async_create_task(self.async_check_flush_interval_due())

        self._flush_time_unsub = async_track_time_change(
            self.hass,
            _handler,
            hour=18,
            minute=0,
            second=0,
        )
########

    async def _async_setup(self):
        """Set up the coordinator.

        This is the place to set up your coordinator,
        or to load data, that only needs to be loaded once.

        This method will be called automatically during
        coordinator.async_config_entry_first_refresh.
        """
        # await self._rest_api.login()
        await self._rest_api.connect()



    ##Installationsdatum: wenn schon im Storage -> setzen, sonst später nach erstem gültigen API-Read einfrieren ---
        stored = await load_last_written_values(self.hass)
        install_iso = stored.get(self._install_date_storage_key)

        if install_iso:
            dt_utc = dt_util.parse_datetime(install_iso)
            if dt_utc is not None:
                if dt_utc.tzinfo is None:
                    dt_utc = dt_utc.replace(tzinfo=dt_util.UTC)
                self.set_internal_timestamp("install_date", dt_util.as_utc(dt_utc))
                self._install_date_frozen = True
        else:
            self._install_date_frozen = False
    ## Ende Installationsdatum ---

    ##Spülintervall
        # Timestamp initialisieren + internen Sensor-State setzen
        await self._ensure_last_reset_flush_interval()
        # täglicher Check um 12:00
        self._setup_flush_interval_daily_check()
        # nach Neustart sofort einmal prüfen (nicht bis 12:00 warten)
        self.hass.async_create_task(self.async_check_flush_interval_due())
    ##

    # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - START =====
    def is_item_supported(self, item: RestItem) -> bool:
        """False, wenn die Geraete-Firmware das noetige Kommando nicht kennt.

        Grundlage ist ausschliesslich ein HTTP 400 des JUDO (siehe
        restobject.py). Solange kein Kommando abgelehnt wurde, ist das Set leer
        und diese Methode gibt fuer jedes Item True zurueck - auf einem Geraet
        mit aktueller Firmware aendert sich also nichts.

        Geprueft werden zwei Quellen:
          * address_read   - die Leseadresse des Items selbst (6900, 6800)
          * params["depends_on"] - fuer reine SCHREIB-Kommandos, die sich nicht
            abfragen lassen. 6B00 (Lernmodus quittieren) gehoert zur selben
            Firmware-Generation wie der Leckageschutz-Status und wird deshalb
            an 6900 gekoppelt. Das ist eine begruendete Annahme, keine Messung.
        """
        unsupported = self._rest_api.unsupported_commands
        if not unsupported:
            return True
        depends_on = None
        if item.params is not None:
            depends_on = item.params.get("depends_on")
        for address in (item.address_read, depends_on):
            if address and address in unsupported:
                return False
        return True
    # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - ENDE =====

    # ===== GEAENDERT (gather/session) - START =====
    # Neue Hilfsmethode: enthaelt exakt den try/except-Block, der vorher
    # direkt in der for-Schleife von fetch_data() stand. Dadurch kann jedes
    # Item als eigener Task laufen, ohne dass ein Fehler die anderen kippt.
    async def _fetch_item(self, item: RestItem) -> None:
        """Fetch a single item value, logging warnings on failure."""
        # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - START =====
        # Kommando von dieser Firmware nicht unterstuetzt: gar nicht erst
        # versuchen. Ohne diese Zeilen liefe pro Durchlauf ein vergeblicher
        # Request samt Warnung - dauerhaft, weil ein Fehlversuch den
        # Intervall-Zeitstempel bewusst nicht weiterstellt.
        if not self.is_item_supported(item):
            return
        # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - ENDE =====
        # ===== GEAENDERT (Read-Once) - START =====
        # Unveraenderliche Werte nach dem ersten erfolgreichen Read
        # ueberspringen. item.state bleibt dabei erhalten.
        key = item.translation_key
        read_once = key in READ_ONCE_KEYS
        if read_once and key in self._read_once_done:
            return
        # ===== GEAENDERT (Read-Once) - ENDE =====

        # --- Zeitplan: nur einmal pro Tag (siehe READ_ONCE_PER_DAY_KEYS) ---
        daily = key in READ_ONCE_PER_DAY_KEYS
        heute = dt_util.as_local(dt_util.now()).date() if daily else None
        if daily and self._daily_done.get(key) == heute:
            return

        # --- Zeitplan: eigenes Abfrageintervall (siehe HA-Konfiguration) ---
        # Welche Adressen faellig sind, wurde einmalig in fetch_data bestimmt.
        if item.address_read and item.address_read not in self._due_addresses:
            return

        try:
            await self.get_value(item)
            if daily and item.state is not None:
                self._daily_done[key] = heute
            # ===== GEAENDERT (Read-Once) - START =====
            # Nur ein erfolgreicher Read gilt als erledigt - schlaegt er
            # fehl, wird im naechsten Durchlauf erneut versucht.
            if read_once and item.state is not None:
                self._read_once_done.add(key)
                log.debug(
                    "%s einmalig gelesen, wird ab jetzt uebersprungen", key
                )
            # ===== GEAENDERT (Read-Once) - ENDE =====
        except Exception:
            log.warning(
                "connection to Judo Zewa failed for %s",
                item.translation_key,
            )
    # ===== GEAENDERT (gather/session) - ENDE =====

    async def fetch_data(self, idx=None):
        """Fetch all values from the REST."""
        # if idx is not None:
        if idx is None:
            # first run: Update all entitiies
            to_update = tuple(range(len(self._restitems)))
        elif len(idx) == 0:
            # idx exists but is not yet filled up: Update all entitiys.
            to_update = tuple(range(len(self._restitems)))
        else:
            # idx exists and is filled up: Update only entitys requested by the coordinator.
            to_update = idx

        # log.info("Start Scan")
        # ===== GEAENDERT (gather/session) - START =====
        # Vorher: sequenzielle for-Schleife, ein Request nach dem anderen.
        # Jetzt: alle Items parallel per asyncio.gather.
        #
        # WICHTIG: gather wartet auf ALLE Tasks. Der Zeitabweichungs-Check und
        # das Einfrieren des Installationsdatums weiter unten laufen also
        # weiterhin garantiert erst, wenn saemtliche Werte gelesen sind -
        # genau wie bei der alten Schleife.
        #
        # Die Anzahl gleichzeitiger Requests wird in restobject.py ueber
        # MAX_PARALLEL_REQUESTS begrenzt (aktuell 1).
        items = [self._restitems[index] for index in to_update]
        # Judo-Uhrzeit VOR dem Durchlauf merken. Weiter unten laeuft der
        # Zeitabweichungs-Check nur, wenn sich der Wert geaendert hat - also
        # wenn datetime_judo in diesem Durchlauf wirklich frisch gelesen
        # wurde. Sonst wuerde ein alter Wert - je nach eingestelltem Intervall
        # bis zu mehrere Minuten alt - eine Abweichung vortaeuschen.
        judo_time_vorher = self.get_value_from_item("datetime_judo")
        # ===== GEAENDERT (Sammelabfrage) - START =====
        # Zwischenspeicher nur fuer die Dauer dieses Durchlaufs aktivieren.
        # Ausserhalb liest jeder Aufruf wieder frisch von der API - wichtig
        # fuer den 11s-Wasserfluss-Task, der water_total selbst abfragt.
        self._warned_addresses = set()

        # --- Welche Adressen sind jetzt faellig? ---
        # Bewusst EINMAL pro Durchlauf entschieden und nicht je Item: mehrere
        # Items teilen sich eine Adresse. Wuerde man je Item entscheiden, wuerde
        # der erste Leser den Zeitstempel setzen und alle weiteren Items
        # derselben Adresse gingen im selben Durchlauf leer aus.
        jetzt = monotonic()
        # Nach einem Schreibzugriff einmal alles neu lesen, damit ein
        # geschriebener Wert sofort vom Geraet bestaetigt wird und nicht bis
        # zum Ablauf des Intervalls ungeprueft in der Oberflaeche steht.
        nach_schreibzugriff = self._rest_api.pop_write_happened()

        # Auf den NAECHSTGELEGENEN Zyklus runden statt immer aufzurunden.
        #
        # Die Faelligkeit wird nur zu den Zeitpunkten geprueft, an denen ein
        # Durchlauf startet. Ohne Toleranz muesste der Abstand strikt >= dem
        # Intervall sein - startet ein Durchlauf auch nur Millisekunden zu
        # frueh, wird die Adresse uebersprungen und erst im uebernaechsten
        # Durchlauf gelesen. Bei Intervall = Basisintervall waere das effektiv
        # die doppelte Zeit. Ein halber Basiszyklus Toleranz laesst die Adresse
        # in dem Durchlauf laufen, der dem Sollzeitpunkt am naechsten liegt.
        toleranz = self._base_interval / 2
        self._due_addresses = set()
        for item in items:
            address = item.address_read
            if not address:
                continue
            # Nicht unterstuetzte Adressen erst gar nicht als faellig fuehren.
            if address in self._rest_api.unsupported_commands:
                continue
            interval = self._read_intervals.get(address)
            if interval is None:
                self._due_addresses.add(address)   # kein eigenes Intervall
                continue
            letzter = self._last_read.get(address)
            if (
                nach_schreibzugriff
                or letzter is None
                or (jetzt - letzter) >= max(0.0, interval - toleranz)
            ):
                self._due_addresses.add(address)

        self._rest_api.begin_read_cycle()
        try:
            await asyncio.gather(*[self._fetch_item(item) for item in items])
        finally:
            # Zeitstempel nur fuer Adressen weiterstellen, die auch wirklich
            # geantwortet haben - ein Fehlversuch wird so gleich wiederholt.
            for address in self._due_addresses:
                if address in self._rest_api.read_ok:
                    self._last_read[address] = jetzt
            self._rest_api.end_read_cycle()
        # ===== GEAENDERT (Sammelabfrage) - ENDE =====
        # ===== GEAENDERT (gather/session) - ENDE =====
        #Zeitabweichung prüfen – nur einmalig nach dem Durchlauf
        judo_time = self.get_value_from_item("datetime_judo")
        ha_time = datetime.now().replace(microsecond=0)
        
        log.debug("judo_time %s", judo_time)
        log.debug("ha_time %s", ha_time)
        
        # Nur pruefen, wenn datetime_judo in diesem Durchlauf frisch gelesen
        # wurde. Die Judo-Uhr laeuft sekundengenau weiter, ein neuer Read
        # liefert also immer einen anderen Wert als der vorherige.
        if isinstance(judo_time, datetime) and judo_time != judo_time_vorher:
            delta = abs((ha_time - judo_time).total_seconds())
            self._last_time_drift = delta
            log.debug("delta %s", delta)
            
            if delta > 5 * 60:
                minutes = round(delta / 60, 1)
                log.warn("Judo-Zeit weicht von Homeassistant-Zeit ab: %.1f Minuten", minutes)
                try:
                    self.hass.async_create_task(
                        self.hass.services.async_call(
                            "persistent_notification",
                            "create",
                            {
                                "title": "Judo Uhrzeit nicht synchron",
                                "message": f"Die Judo-Zeit weicht von der Homeassistant-Zeit um {minutes} Minuten ab.",
                                "notification_id": "judo_time_drift"
                            }
                        )
                    )
                except Exception as e:
                    log.error("Fehler beim Erstellen der Benachrichtigung über Serviceaufruf: %s", e)

        # Installationsdatum einmalig einfrieren, sobald install_date_judo gültig gelesen wurde
        if not self._install_date_frozen:
            await self._try_freeze_install_date_from_judo()

        # Meldung, sobald der Leckageschutz das Ventil geschlossen hat
        self._check_valve_closed()

    def _check_valve_closed(self) -> None:
        """Persistente Meldung erzeugen, wenn der Leckageschutz geschlossen hat.

        Reagiert auf den WECHSEL des Ventilzustands. Waehrend der Ventilfahrt
        liefert der JUDO keine Daten, ls_valve_state behaelt dann seinen letzten
        Wert - der Wechsel wird also erst erkannt, wenn das Ventil fertig
        gefahren ist und wieder antwortet. Genau so ist es gewollt.
        """
        state = self.get_value_from_item("ls_valve_state")
        if state is None:
            return

        vorher = self._previous_valve_state
        self._previous_valve_state = state

        # Beim ersten Durchlauf nach dem Start nur merken, nicht melden.
        if vorher is None or state == vorher:
            return

        if state == "closed":
            gruende = [
                text
                for key, text in VALVE_CLOSED_REASONS
                if self.get_value_from_item(key)
            ]
            if self.get_value_from_item("ls_microleakage_result") == "message_and_close":
                gruende.append("Kleinleckage erkannt (Meldung und Schliessen)")

            zeitpunkt = dt_util.as_local(dt_util.now()).strftime("%d.%m.%Y %H:%M")
            msg = (
                "Der Leckageschutz hat das Ventil geschlossen.\n\n"
                f"Zeitpunkt: {zeitpunkt}\n"
            )
            if gruende:
                msg += "\nGemeldete Ursache:\n" + "\n".join("- " + g for g in gruende)
            else:
                msg += "\nEs wurde keine Ursache mitgemeldet."
            msg += (
                "\n\nDie Wasserzufuhr ist unterbrochen. "
                "Zum Oeffnen den Button 'Leckageschutz oeffnen' benutzen."
            )

            log.warning(
                "Judo Leckageschutz geschlossen (%s)",
                ", ".join(gruende) if gruende else "ohne gemeldete Ursache",
            )
            try:
                self.hass.async_create_task(
                    self.hass.services.async_call(
                        "persistent_notification",
                        "create",
                        {
                            "title": "Judo Leckageschutz geschlossen",
                            "message": msg,
                            "notification_id": self._valve_notification_id,
                        },
                    )
                )
            except Exception as e:
                log.error("Fehler beim Erstellen der Ventil-Meldung: %s", e)

        elif state == "open":
            # Ventil wieder offen -> alte Meldung entfernen
            try:
                self.hass.async_create_task(
                    self.hass.services.async_call(
                        "persistent_notification",
                        "dismiss",
                        {"notification_id": self._valve_notification_id},
                    )
                )
            except Exception as e:
                log.error("Fehler beim Entfernen der Ventil-Meldung: %s", e)

    ## Installationsdatum setzten
    async def _try_freeze_install_date_from_judo(self) -> None:
        """Speichert install_date_utc genau einmal, sobald install_date_judo valide aus der API da ist."""
        # Wenn inzwischen im Storage vorhanden -> fertig
        stored = await load_last_written_values(self.hass)
        if stored.get(self._install_date_storage_key):
            self._install_date_frozen = True
            return

        install_judo = self.get_value_from_item("install_date_judo")
        # install_date_judo kommt je nach Parser als datetime oder als String "YYYY-MM-DD HH:MM:SS"
        if isinstance(install_judo, str):
            try:
                install_judo = datetime.fromisoformat(install_judo)
            except Exception:
                return

        if not isinstance(install_judo, datetime):
            return
        # Plausibilitätscheck (optional aber sinnvoll gegen Müllwerte)
        now_local_naive = dt_util.as_local(dt_util.now()).replace(tzinfo=None)
        if install_judo.year < 2000 or install_judo > (now_local_naive + timedelta(days=2)):
            return
        # Judo liefert UNIX Timestamp, in der Doku als GMT+1 interpretiert.
        # Kommt es als naive lokale Zeit an -> als lokale HA-Zeit interpretieren -> UTC
        if install_judo.tzinfo is None:
            local_aware = install_judo.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
            install_utc = dt_util.as_utc(local_aware)
        else:
            install_utc = dt_util.as_utc(install_judo)
        # Speichern (nur jetzt, nur einmal)
        await save_last_written_value(self.hass, self._install_date_storage_key, install_utc.isoformat())
        # Interner Sensor "install_date" (timestamp) setzen
        self.set_internal_timestamp("install_date", install_utc)

        self._install_date_frozen = True
    ##Ende##

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with asyncio.timeout(60):
                # Grab active context variables to limit data required to be fetched from API
                # Note: using context is not required if there is no need or ability to limit
                # data retrieved from API.
                # listening_idx = set(self.async_contexts())
                return await self.fetch_data()  # !!!!!using listening_idx will result in some entities nevwer updated !!!!!
        except Exception:
            log.warning("Error fetching Judo Zewa data")

    @property
    def rest_api(self):
        """Return rest_api."""
        return self._rest_api
