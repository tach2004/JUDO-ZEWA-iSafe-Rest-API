"""The Update Coordinator for the RestItems."""

import asyncio
import logging
##
import calendar
##
from datetime import timedelta
from datetime import datetime
from datetime import time
from homeassistant.components.persistent_notification import async_create as create_notification
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
##
from homeassistant.helpers.event import async_track_time_change
##
from .configentry import MyConfigEntry
from .const import CONF, FORMATS
from .items import RestItem
from .restobject import RestAPI, RestObject
##
from homeassistant.util import dt as dt_util
from .storage import save_last_written_value, load_last_written_values, PERSISTENT_ENTITIES
##
logging.basicConfig()
log = logging.getLogger(__name__)


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
                log.warning("None value for Item %s ignored", rest_item.translation_key)
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
        for index in to_update:
            item = self._restitems[index]
            try:
                await self.get_value(item)

            except Exception:
                log.warning(
                    "connection to Judo Zewa failed for %s",
                    item.translation_key,
                )
        #Zeitabweichung prüfen – nur einmalig nach dem Durchlauf
        judo_time = self.get_value_from_item("datetime_judo")
        ha_time = datetime.now().replace(microsecond=0)
        
        log.debug("judo_time %s", judo_time)
        log.debug("ha_time %s", ha_time)
        
        if isinstance(judo_time, datetime):
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
