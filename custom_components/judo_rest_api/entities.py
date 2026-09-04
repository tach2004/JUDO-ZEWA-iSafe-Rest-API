"""Entity classes used in this integration"""

import logging
import time
import asyncio
import collections

from datetime import datetime
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.components.number import NumberEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.button import ButtonEntity
from homeassistant.components.select import SelectEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.translation import async_translate_state

from .configentry import MyConfigEntry
from .const import CONF, CONST, FORMATS
from .coordinator import MyCoordinator
from .items import RestItem
from .restobject import RestAPI, RestObject

from .storage import save_last_written_value, load_last_written_values, PERSISTENT_ENTITIES, FALLBACK_ENTITIES

from homeassistant.util import dt as dt_util

# ============================================================================
# ==   WASSERFLUSS-BERECHNUNG (MyCalcSensorEntity)                          ==
# ==                                                                        ==
# ==   water_total hat 1 Liter Aufloesung. Bei 11 s Abtastung springt der   ==
# ==   Zaehler erst ab rund 5,5 l/min - darunter kann eine Messung          ==
# ==   unveraendert bleiben, obwohl noch Wasser laeuft.                     ==
# ==                                                                        ==
# ==   FLOW_STOP_AFTER_UNCHANGED: so viele unveraenderte Messungen          ==
# ==       hintereinander gelten als "kein Durchfluss mehr". Bei 3 sind das ==
# ==       rund 33 s, das erkennt auch einen kleinen Hahn zuverlaessig.     ==
# ==   FLOW_AVERAGE_SAMPLES: Groesse des Mittelwertfensters. Groesser =     ==
# ==       ruhigerer Wert, aber traegere Reaktion.                          ==
# ============================================================================
FLOW_STOP_AFTER_UNCHANGED = 3
FLOW_AVERAGE_SAMPLES = 5

logging.basicConfig()
log = logging.getLogger(__name__)


class MyEntity(Entity):
    """An entity using CoordinatorEntity.

    The CoordinatorEntity class provides:
    should_poll
    async_update
    async_added_to_hass
    available

    The base class for entities that hold general parameters
    """

    _attr_should_poll = True
    _attr_has_entity_name = True
    _attr_entity_name = None
    _divider = 1

    def __init__(
        self,
        config_entry: MyConfigEntry,
        rest_item: RestItem,
        rest_api: RestAPI,
    ) -> None:
        """Initialize the entity."""
        self._config_entry = config_entry
        self._rest_item = rest_item
        self._rest_api = rest_api

        dev_postfix = "_" + self._config_entry.data[CONF.DEVICE_POSTFIX]

        if dev_postfix == "_":
            dev_postfix = ""

        self._dev_device = self._rest_item.device + dev_postfix

        self._attr_translation_key = self._rest_item.translation_key
        self._dev_translation_placeholders = {"postfix": dev_postfix}

        dev_postfix = "_" + config_entry.data[CONF.DEVICE_POSTFIX]
        if dev_postfix == "_":
            dev_postfix = ""

        # self._dev_device = self._rest_api.get_devicetype()
        self._dev_device = self._rest_item.device

        self._attr_unique_id = (
            CONST.DOMAIN
            + "_"
            + self._dev_device
            + "_"
            + self._rest_item.translation_key
        )

        self._rest_api = rest_api

        match self._rest_item.format:
            #case FORMATS.STATUS | FORMATS.TEXT | FORMATS.SW_VERSION:
            #case FORMATS.STATUS |FORMATS.SELECT_WO | FORMATS.SELECT | FORMATS.TEXT | FORMATS.TIMESTAMP | FORMATS.SW_VERSION | FORMATS.DATETIME_JUDO | FORMATS.SELECT_INTERNAL | FORMATS.SENSOR_INTERNAL_TIMESTAMP:
            case FORMATS.STATUS | FORMATS.TEXT | FORMATS.TIMESTAMP | FORMATS.SW_VERSION | FORMATS.DATETIME_JUDO | FORMATS.SENSOR_INTERNAL_TIMESTAMP | FORMATS.STATUS_BIT | FORMATS.STATUS_BITMASK:
                self._divider = 1
                if (
                    self._rest_item.format
                    in (FORMATS.STATUS, FORMATS.TEXT, FORMATS.TIMESTAMP, FORMATS.SW_VERSION, FORMATS.DATETIME_JUDO, FORMATS.SENSOR_INTERNAL_TIMESTAMP, FORMATS.STATUS_BIT, FORMATS.STATUS_BITMASK)
                    and self._rest_item.params is not None
                ):
                    self._attr_device_class = self._rest_item.params.get("deviceclass", None)
                    self._attr_state_class = None
            case _:
                # default state class to record all entities by default
                self._attr_state_class = SensorStateClass.MEASUREMENT
                if self._rest_item.params is not None:
                    self._attr_state_class = self._rest_item.params.get(
                        "stateclass", SensorStateClass.MEASUREMENT
                    )
                    self._attr_native_unit_of_measurement = self._rest_item.params.get(
                        "unit", ""
                    )
                    self._attr_native_step = self._rest_item.params.get("step", 1)
                    self._divider = self._rest_item.params.get("divider", 1)
                    self._attr_device_class = self._rest_item.params.get(
                        "deviceclass", None
                    )
                    self._attr_suggested_display_precision = self._rest_item.params.get(
                        "precision", 2
                    )
                    self._attr_native_min_value = self._rest_item.params.get(
                        "min", -999999
                    )
                    self._attr_native_max_value = self._rest_item.params.get(
                        "max", 999999
                    )

        if self._rest_item.params is not None:
            icon = self._rest_item.params.get("icon", None)
            if icon is not None:
                self._attr_icon = icon
            # Sortiert die Entitaet in HA unter "Diagnose" ein
            entity_category = self._rest_item.params.get("entity_category", None)
            if entity_category is not None:
                self._attr_entity_category = entity_category

    def my_device_info(self) -> DeviceInfo:
        """Build the device info. Anzeige oben links unter Geräteinformationen"""

        device_type = self.coordinator.get_value_from_item("device_type")
        device_number = self.coordinator.get_value_from_item("device_number")

        return {
            "identifiers": {(CONST.DOMAIN, self._dev_device)},
            "translation_key": self._dev_device,
            "translation_placeholders": self._dev_translation_placeholders,
            "sw_version": self.coordinator.get_value_from_item("software_version"), #Sotwareversion zb 1.39 
                #Model = Gerätetyp zb Zewa/Prom iSafe...
            "model": async_translate_state( 
                hass=self.hass,
                state=device_type,
                domain="sensor",
                platform=CONST.DOMAIN,
                translation_key="device_type",
                device_class=None,
            ),        
            "manufacturer": "JUDO Wasseraufbereitung GmbH",
            "serial_number": (str(int(device_number)) if device_number is not None else None), #Seriennummer Judo Gerät 
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return MySensorEntity.my_device_info(self)


class MySensorEntity(CoordinatorEntity, SensorEntity, MyEntity):
    """Class that represents a sensor entity.

    Derived from Sensorentity
    and decorated with general parameters from MyEntity
    """

    def __init__(
        self,
        config_entry: MyConfigEntry,
        rest_item: RestItem,
        coordinator: MyCoordinator,
        idx,
    ) -> None:
        """Initialize of MySensorEntity."""
        super().__init__(coordinator, context=idx)
        self.idx = idx
        MyEntity.__init__(self, config_entry, rest_item, coordinator.rest_api)

    ##Spülintervall
    async def async_added_to_hass(self) -> None:
        """Restore persisted internal timestamp when entity is added."""
        await super().async_added_to_hass()

        if self._rest_item.translation_key == "last_reset_flush_interval":
            stored_values = await load_last_written_values(self.hass)
            iso = stored_values.get("last_reset_flush_interval")
            if iso:
                dt_utc = dt_util.parse_datetime(iso)
                if dt_utc is not None and dt_utc.tzinfo is None:
                    dt_utc = dt_utc.replace(tzinfo=dt_util.UTC)

                # RestItem + Entity sofort synchron halten
                self._rest_item.state = dt_utc
                self._attr_native_value = dt_utc
                self.async_write_ha_state()
    ##
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self._rest_item.state
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return MyEntity.my_device_info(self)


class MyNumberEntity(CoordinatorEntity, NumberEntity, MyEntity):  # pylint: disable=W0223
    """Represent a Number Entity.

    Class that represents a number entity derived from NumberEntity
    and decorated with general parameters from MyEntity
    """

    def __init__(
        self,
        config_entry: MyConfigEntry,
        rest_item: RestItem,
        coordinator: MyCoordinator,
        idx,
    ) -> None:
        """Initialize MyNumberEntity."""
        super().__init__(coordinator, context=idx)
        self._idx = idx
        self._coordinator = coordinator
        MyEntity.__init__(self, config_entry, rest_item, coordinator.rest_api)
        
        self._attr_mode = "box"  # Setzt die Eingabebox statt des Sliders

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self._rest_item.state
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Send value over modbus and refresh HA."""
        # Ensure we are dealing with the correct translation keys
        ro = RestObject(self._rest_api, self._rest_item)
        await ro.setvalue(value)  # rest_item.state will be set inside ro.setvalue
        #self._rest_item.state = value #SPÄTER AUSKOMMENTIEREN
        self._attr_native_value = self._rest_item.state
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return MyEntity.my_device_info(self)


class MySwitchEntity(CoordinatorEntity, SwitchEntity, MyEntity):  # pylint: disable=W0223
    """Represent a Switch Entity.

    Class that represents a switch entity derived from SwitchEntity
    and decorated with general parameters from MyEntity
    """

    def __init__(
        self,
        config_entry: MyConfigEntry,
        rest_item: RestItem,
        coordinator: MyCoordinator,
        idx,
    ) -> None:
        """Initialize MySwitchEntity."""
        super().__init__(coordinator, context=idx)
        self._idx = idx
        MyEntity.__init__(self, config_entry, rest_item, coordinator.rest_api)

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass (restore last state for persistent switches)."""
        await super().async_added_to_hass()

        if self._rest_item.translation_key in PERSISTENT_ENTITIES:
            stored_values = await load_last_written_values(self.hass)
            if self._rest_item.translation_key in stored_values:
                stored = stored_values[self._rest_item.translation_key]

                # robust: akzeptiert True/False oder 0/1 oder "0"/"1"
                if isinstance(stored, str):
                    stored_norm = stored.strip().lower()
                    if stored_norm in ("1", "true", "on", "yes"):
                        stored = True
                    elif stored_norm in ("0", "false", "off", "no"):
                        stored = False

                self._rest_item.state = stored
                self._attr_is_on = bool(stored)
                self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        #self._attr_is_on = self._rest_item.state   ####Wird nicht mehr durch API geupdatet!
        self._attr_is_on = self._rest_item.state == 1   ##Ersetzt Zeile darüber weil nicht mehr über Api sondern nur intern
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        ro = RestObject(self._rest_api, self._rest_item)
        await ro.setvalue(1)  # rest_item.state will be set inside ro.setvalue
        self._rest_item.state = True  ####schreibt den state direkt in den coordinator ohne über die API zu lesen
        self._attr_is_on = True ##Ersetzt Zeile darunter weil nicht mehr über Api sondern nur intern
        #self._attr_is_on = self._rest_item.state ####Wird nicht mehr durch API geupdatet!
        self.async_write_ha_state()
        if self._rest_item.translation_key in PERSISTENT_ENTITIES:
            await save_last_written_value(self.hass, self._rest_item.translation_key, True)

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        ro = RestObject(self._rest_api, self._rest_item)
        await ro.setvalue(0)  # rest_item.state will be set inside ro.setvalue
        self._rest_item.state = False ####schreibt den state direkt in den coordinator ohne über die API zu lesen
        self._attr_is_on = False ##Ersetzt Zeile darunter weil nicht mehr über Api sondern nur intern
        #self._attr_is_on = self._rest_item.state   ####Wird nicht mehr durch API geupdatet!
        self.async_write_ha_state()
        if self._rest_item.translation_key in PERSISTENT_ENTITIES:
            await save_last_written_value(self.hass, self._rest_item.translation_key, False)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return MyEntity.my_device_info(self)

class MyButtonEntity(CoordinatorEntity, ButtonEntity, MyEntity):  # pylint: disable=W0223
    """Represent a Button Entity.

    Class that represents a Button entity derived from ButtonEntity
    and decorated with general parameters from MyEntity
    """

    def __init__(
        self,
        config_entry: MyConfigEntry,
        rest_item: RestItem,
        coordinator: MyCoordinator,
        idx,
    ) -> None:
        """Initialize NyNumberEntity."""
        super().__init__(coordinator, context=idx)
        self._idx = idx
        MyEntity.__init__(self, config_entry, rest_item, coordinator.rest_api)

    async def async_press(self):
        """Turn the entity on."""
        if self._rest_item.translation_key == "set_judo_time":
            try:
                now = datetime.now()
                # Sicherheit: Ist es ein datetime-Objekt?
                if not isinstance(now, datetime):
                    raise ValueError("Ungültiger datetime-Wert")
                
                if not (2000 <= now.year <= 2099):
                    raise ValueError(f"Jahr außerhalb des gültigen Bereichs: {now.year}")
                
                payload = (
                    f"{now.day:02X}"
                    f"{now.month:02X}"
                    f"{now.year % 100:02X}"
                    f"{now.hour:02X}"
                    f"{now.minute:02X}"
                    f"{now.second:02X}"
                )

                #Abweichung erfassen
                delta_seconds = getattr(self.coordinator, "_last_time_drift", None)

                #Zeit setzten    
                ro = RestObject(self._rest_api, self._rest_item)
                await ro.setvalue(payload)

                #Meldung ausgeben
                if delta_seconds is not None:
                    log.warn(
                        "Zeit an Judo gesendet und gesetzt: %s (Hex: %s), vorherige Abweichung: %.1f Sekunden",
                        now.strftime("%d.%m.%Y %H:%M:%S"),
                        payload,
                        delta_seconds,
                    )
                else:
                    log.warn(
                        "Zeit an Judo gesendet und gesetzt: %s (Hex: %s), vorherige Abweichung unbekannt",
                        now.strftime("%d.%m.%Y %H:%M:%S"),
                        payload,
                    )
            
            
            except Exception as e:
                log.error("Fehler beim Erzeugen oder Senden der Uhrzeit: %s", e)
        ##Spülintervall        
        elif self._rest_item.translation_key == "reset_flush_interval":
            try:
                now_utc = dt_util.utcnow()

                # Persistieren (ISO-Format) unter dem Sensor-Key
                await save_last_written_value(
                    self.hass,
                    "last_reset_flush_interval",
                    now_utc.isoformat(),
                )

                # Sofort im Coordinator/RestItem reflektieren (UI aktualisiert sofort)
                self.coordinator.set_internal_timestamp("last_reset_flush_interval", now_utc)

                # Alte Meldung (falls vorhanden) schließen
                await self.hass.services.async_call(
                    "persistent_notification",
                    "dismiss",
                    {"notification_id": "judo_flush_interval_due"},
                    blocking=False,
                )

                # Direkt neu prüfen (falls Intervall z.B. geändert/deaktiviert wurde)
                self.hass.async_create_task(self.coordinator.async_check_flush_interval_due())

            except Exception as e:
                log.error("Fehler beim Reset des Spülintervalls: %s", e)
        ##
        else:
            ro = RestObject(self._rest_api, self._rest_item)
            await ro.setvalue()  # rest_item.state will be set inside ro.setvalue

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return MyEntity.my_device_info(self)


class MySelectEntity(CoordinatorEntity, SelectEntity, MyEntity):  # pylint: disable=W0223
    """Class that represents a sensor entity.
    Class that represents a sensor entity derived from Sensorentity
    and decorated with general parameters from MyEntity
    """
    def __init__(
        self,
        config_entry: MyConfigEntry,
        rest_item: RestItem,
        coordinator: MyCoordinator,
        idx,
    ) -> None:
        """Initialize MySelectEntity."""
        super().__init__(coordinator, context=idx)
        self._idx = idx
        MyEntity.__init__(self, config_entry, rest_item, coordinator.rest_api)
        # option list build from the status list of the ModbusItem
        self.options = []
        for _useless, item in enumerate(self._rest_item.resultlist):
            self.options.append(item.translation_key)
        self._attr_current_option = "FEHLER"
        # Aktions-Select (z.B. Lernmodus quittieren) startet in der Ruhestellung.
        if self._rest_item.format is FORMATS.SELECT_WO_ACTION:
            idle_option = "standby"
            if self._rest_item.params is not None:
                idle_option = self._rest_item.params.get("idle_option", "standby")
            self._attr_current_option = idle_option
            self._rest_item.state = idle_option

    # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - START =====
    def _leakage_fallback_active(self) -> bool:
        """True, wenn die Geraete-Firmware Kommando 6800 nicht beherrscht.

        Nur dann wird auf die alte Speicherdatei zurueckgegriffen. Auf einem
        Geraet, das 6800 beantwortet, ist das immer False - der gesamte
        Rueckfallpfad ist dort also wirkungslos.
        """
        try:
            return "6800" in self.coordinator.rest_api.unsupported_commands
        except AttributeError:
            return False
    # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - ENDE =====

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        if self._rest_item.translation_key in PERSISTENT_ENTITIES:
            stored_values = await load_last_written_values(self.hass)
            if self._rest_item.translation_key in stored_values:
                self._attr_current_option = stored_values[self._rest_item.translation_key]
                self._rest_item.state = stored_values[self._rest_item.translation_key]
                # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - START =====
                # Vorher wurde hier die GESAMTE Speicherdatei ausgegeben. Das
                # las sich so, als kaemen alle darin enthaltenen Werte aus der
                # Datei - auch die, die in Wahrheit vom Geraet gelesen wurden.
                # Jetzt steht nur noch der tatsaechlich wiederhergestellte
                # Eintrag im Log.
                log.debug(
                    "%s aus der Speicherdatei uebernommen: %r",
                    self._rest_item.translation_key,
                    stored_values[self._rest_item.translation_key],
                )
                # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - ENDE =====

        # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - START =====
        # Rueckfallebene fuer Geraete ohne Kommando 6800. Drei Bedingungen
        # muessen zusammenkommen, damit hier ueberhaupt etwas passiert:
        #   1. der Schluessel gehoert zu den Leckageeinstellungen,
        #   2. das Geraet hat 6800 mit HTTP 400 abgelehnt,
        #   3. es liegt kein vom Geraet gelesener Wert vor.
        # Auf einem Geraet mit aktueller Firmware scheitert es schon an 2. -
        # der frisch gelesene Wert wird also nie ueberschrieben.
        if (
            self._rest_item.translation_key in FALLBACK_ENTITIES
            and self._rest_item.state is None
            and self._leakage_fallback_active()
        ):
            stored_values = await load_last_written_values(self.hass)
            stored_option = stored_values.get(self._rest_item.translation_key)
            # Nur uebernehmen, wenn der gespeicherte Eintrag heute noch eine
            # gueltige Auswahl ist. Ein Wert aus einer aelteren Version wuerde
            # sonst als ungueltiger Zustand stehenbleiben und spaeter den
            # gebuendelten Schreibvorgang scheitern lassen.
            gueltig = stored_option is not None and any(
                entry.translation_key == stored_option
                for entry in (self._rest_item.resultlist or [])
            )
            if stored_option is not None and not gueltig:
                log.warning(
                    "Gespeicherter Wert %r fuer %s ist keine gueltige Auswahl "
                    "und wird verworfen",
                    stored_option,
                    self._rest_item.translation_key,
                )
            if gueltig:
                self._attr_current_option = stored_option
                self._rest_item.state = stored_option
                log.debug(
                    "%s aus der Speicherdatei wiederhergestellt (Firmware "
                    "kennt Kommando 6800 nicht): %s",
                    self._rest_item.translation_key,
                    stored_option,
                )
        # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - ENDE =====

    async def async_select_option(self, option: str) -> None:
        """Aktualisiert die Auswahl der Entität und synchronisiert sie mit Home Assistant."""

        #1 special mode absence limit
        if self._rest_item.translation_key in ["absence_limit_max_waterflowrate", "absence_limit_max_water_flow", "absence_limit_max_waterflow_time"]:
            if not self.coordinator._restitems:
                raise ValueError("coordinator._restitems ist None oder leer. Keine Entitäten zum Verarbeiten.")

            selected_values = {}

            for item in self.coordinator._restitems:
                if item.translation_key in ["absence_limit_max_waterflowrate", "absence_limit_max_water_flow", "absence_limit_max_waterflow_time"]:
                    if item.translation_key == self._rest_item.translation_key:
                        # Falls es die aktuelle Entität ist, nehmen wir den neuen Wert (option)
                        selected_value = next(
                            (entry.number for entry in item.resultlist if entry.translation_key == option),
                            None
                        )
                    else:
                        # Für die anderen beiden nehmen wir den alten Wert aus state
                        selected_value = next(
                            (entry.number for entry in item.resultlist if entry.translation_key == item.state),
                            None
                        )

                    if selected_value is not None:
                        selected_values[item.translation_key] = selected_value

            # Sicherstellen, dass alle drei Werte erfasst wurden
            if len(selected_values) != 3:
                raise ValueError(f"Erwartet 3 Werte, aber {len(selected_values)} erhalten: {selected_values}")

            # Werte in der richtigen Reihenfolge in Little-Endian umwandeln
            ordered_keys = ["absence_limit_max_waterflowrate", "absence_limit_max_water_flow", "absence_limit_max_waterflow_time"]
            payload = "".join([selected_values[key].to_bytes(2, byteorder="little").hex() for key in ordered_keys])

            # Debugging: Welche Werte wurden gesendet?
            log.debug("Gesammelte Werte für Little-Endian Umwandlung: %s", selected_values)
            log.debug("Sende Payload an Judo: %s", payload)
            
            try:
                if self._rest_item.translation_key in PERSISTENT_ENTITIES:
                    await save_last_written_value(self.hass, self._rest_item.translation_key, option)
                # Senden des kombinierten Zustands
                await self.coordinator.rest_api.write_value("5F00", bytes.fromhex(payload))
                self._rest_item.state = option #schreibt den state direkt in den coordinator ohne über die API zu lesen
                self._attr_current_option = self._rest_item.state
                self.async_write_ha_state()
            except Exception as e:
                log.error("Fehler beim Senden an Judo: %s", e)
        
        #2 Special mode leakageprotection
        elif self._rest_item.translation_key in ["leakageprotection_max_waterflowrate", "leakageprotection_max_waterflow", "leakageprotection_max_waterflowtime"]:
            if not self.coordinator._restitems:
                raise ValueError("coordinator._restitems ist None oder leer. Keine Entitäten zum Verarbeiten.")

            # Die Nachbarwerte kommen direkt aus dem Coordinator-State. Der
            # wird per Kommando 6800 ("Leckageeinstellungen lesen") vom JUDO
            # gelesen - damit wird auch eine Aenderung am Geraet selbst korrekt
            # beruecksichtigt. Gleiche Vorgehensweise wie oben beim
            # absence_limit-Pfad.
            #
            # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - START =====
            # Kennt die Firmware 6800 nicht, bleiben alle vier States leer und
            # der Payload liesse sich nicht bauen - das Schreiben scheiterte
            # dann mit einem ValueError. Fuer diesen Fall wird wieder die
            # Speicherdatei herangezogen, genau wie in Version 1.2.1.
            # Die Datei wird nur dann ueberhaupt gelesen.
            fallback_aktiv = self._leakage_fallback_active()
            stored_values = (
                await load_last_written_values(self.hass) if fallback_aktiv else {}
            )
            # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - ENDE =====
            selected_values = {}

            for item in self.coordinator._restitems:
                if item.translation_key in ["holiday_mode_write", "leakageprotection_max_waterflowrate", "leakageprotection_max_waterflow", "leakageprotection_max_waterflowtime"]:
                    if item.translation_key == self._rest_item.translation_key:
                        # Falls es die aktuelle Entität ist, nehmen wir den neuen Wert (option)
                        selected_value = next(
                            (entry.number for entry in item.resultlist if entry.translation_key == option),
                            None
                        )
                    else:
                        # Für die anderen nehmen wir den aktuell gelesenen Wert aus state
                        selected_value = next(
                            (entry.number for entry in item.resultlist if entry.translation_key == item.state),
                            None
                        )
                        # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - START =====
                        # Kein Geraetewert vorhanden und 6800 nicht unterstuetzt:
                        # zuletzt geschriebenen Wert aus der Datei nehmen.
                        if selected_value is None and fallback_aktiv:
                            stored_option = stored_values.get(item.translation_key)
                            if stored_option is not None:
                                selected_value = next(
                                    (entry.number for entry in item.resultlist if entry.translation_key == stored_option),
                                    None
                                )
                        # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - ENDE =====

                    if selected_value is not None:
                        selected_values[item.translation_key] = selected_value

            # Debug Ausgabe
            log.debug("Gesammelte Werte für Leakageprotection: %s", selected_values)

            # ===== GEAENDERT (Rueckfallebene erreichbar 2.0.2) - START =====
            # Den gerade gewaehlten Wert VOR der Vollstaendigkeitspruefung
            # sichern - genau wie in Version 1.2.1. Nur so laesst sich eine
            # leere Speicherdatei ueberhaupt befuellen: Kommando 5000 schreibt
            # alle vier Werte gemeinsam, ein einzelner Wert reicht dafuer nie.
            # Der Nutzer setzt die vier also nacheinander; die ersten drei
            # Versuche brechen ab, landen aber in der Datei, und beim vierten
            # geht der Schreibvorgang durch.
            #
            # Greift ausschliesslich bei aktiver Rueckfallebene. Auf einem
            # Geraet, das 6800 beantwortet, wird hier nichts gespeichert.
            if fallback_aktiv and self._rest_item.translation_key in FALLBACK_ENTITIES:
                await save_last_written_value(
                    self.hass, self._rest_item.translation_key, option
                )
                # ===== GEAENDERT (Anzeige beim Anlauf 2.0.3) - START =====
                # Die Anzeige gleich mitziehen. Bricht der gebuendelte
                # Schreibvorgang unten mangels vollstaendiger Werte ab, wird
                # der State weiter unten nie gesetzt - das Auswahlfeld stuende
                # dann auf "FEHLER", obwohl der Wert laengst vorgemerkt ist.
                # Beim naechsten Neuladen kaeme er ohnehin aus der Datei
                # zurueck; hier stimmt die Anzeige nur sofort statt erst dann.
                #
                # Betrifft ausschliesslich den einmaligen Anlauf auf einem
                # Geraet ohne Kommando 6800 (fallback_aktiv).
                self._rest_item.state = option
                self._attr_current_option = option
                self.async_write_ha_state()
                # ===== GEAENDERT (Anzeige beim Anlauf 2.0.3) - ENDE =====
                log.debug(
                    "%s in der Speicherdatei vorgemerkt und angezeigt: %r "
                    "(Firmware kennt Kommando 6800 nicht)",
                    self._rest_item.translation_key,
                    option,
                )
            # ===== GEAENDERT (Rueckfallebene erreichbar 2.0.2) - ENDE =====

            if len(selected_values) != 4:
                # Ohne alle vier Werte laesst sich der gebuendelte Payload nicht
                # bauen. Bewusst abbrechen statt unvollstaendig zu senden:
                # Kommando 5000 schreibt Urlaubsmodus, Volumenstrom, Menge und
                # Dauer gemeinsam - ein geratener Wert wuerde am Geraet echte
                # Einstellungen ueberschreiben.
                raise ValueError(
                    f"Erwartet 4 Werte, aber {len(selected_values)} erhalten: {selected_values}. "
                    "Bei aelterer Geraete-Firmware ohne Kommando 6800 muss jeder der vier "
                    "Werte einmal ueber Home Assistant gesetzt worden sein."
                )

            # Werte in der richtigen Reihenfolge in Little-Endian umwandeln
            ordered_keys = ["holiday_mode_write", "leakageprotection_max_waterflowrate", "leakageprotection_max_waterflow", "leakageprotection_max_waterflowtime",]
            #payload = "".join([selected_values[key].to_bytes(2, byteorder="little").hex() for key in ordered_keys])
            payload = ""
            for key in ordered_keys:
                if key == "holiday_mode_write":
                    payload += selected_values[key].to_bytes(1, byteorder="little").hex()
                else:
                    payload += selected_values[key].to_bytes(2, byteorder="little").hex()

            log.debug("Sende Leakageprotection Payload an Judo: %s", payload)
            
            try:
                # ===== GEAENDERT (Rueckfallebene erreichbar 2.0.2) - START =====
                # Der Rueckfall-Fall ist oben bereits gespeichert worden (vor
                # der Vollstaendigkeitspruefung). Hier bleibt nur noch
                # PERSISTENT_ENTITIES uebrig - sonst wuerde derselbe Wert ein
                # zweites Mal in die Datei geschrieben.
                if self._rest_item.translation_key in PERSISTENT_ENTITIES:
                # ===== GEAENDERT (Rueckfallebene erreichbar 2.0.2) - ENDE =====
                    await save_last_written_value(self.hass, self._rest_item.translation_key, option)
                    logmeldung = (self.hass, self._rest_item.translation_key, option)
                    log.debug("Gespeicherter Wert unten: %s", logmeldung)
                # Senden des kombinierten Zustands
                await self.coordinator.rest_api.write_value("5000", bytes.fromhex(payload))
                self._rest_item.state = option #schreibt den state direkt in den coordinator ohne über die API zu lesen
                self._attr_current_option = self._rest_item.state
                self.async_write_ha_state()
            except Exception as e:
                log.error("Fehler beim Senden an Judo: %s", e)
        #3 Aktions-Select: senden und sofort zurueck in die Ruhestellung
        elif self._rest_item.format is FORMATS.SELECT_WO_ACTION:
            idle_option = "standby"
            if self._rest_item.params is not None:
                idle_option = self._rest_item.params.get("idle_option", "standby")

            if option != idle_option:
                try:
                    ro = RestObject(self._rest_api, self._rest_item)
                    await ro.setvalue(option)
                    log.debug(
                        "Aktion '%s' fuer %s an Judo gesendet",
                        option,
                        self._rest_item.translation_key,
                    )
                except Exception as e:
                    log.error("Fehler beim Senden an Judo: %s", e)

            # Immer zurueck in die Ruhestellung - sonst liesse sich dieselbe
            # Aktion beim naechsten Mal nicht erneut ausloesen, weil HA bei
            # unveraenderter Auswahl kein Ereignis mehr erzeugt.
            self._rest_item.state = idle_option
            self._attr_current_option = idle_option
            self.async_write_ha_state()

        else:
            try: #Speichern der Werte die nur geschrieben werden
                # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - START =====
                # holiday_mode_write laeuft ueber diesen Zweig (Kommando 5600).
                # Bei fehlendem 6800 muss der Wert gespeichert werden, damit er
                # nach einem Neustart und beim gebuendelten 5000-Schreibvorgang
                # wieder zur Verfuegung steht.
                if self._rest_item.translation_key in PERSISTENT_ENTITIES or (
                    self._rest_item.translation_key in FALLBACK_ENTITIES
                    and self._leakage_fallback_active()
                ):
                # ===== GEAENDERT (Firmware-Erkennung 2.0.1) - ENDE =====
                    await save_last_written_value(self.hass, self._rest_item.translation_key, option)
                    logmeldung = (self.hass, self._rest_item.translation_key, option)
                    log.debug("Gespeicherter Wert unten ohne Sonder: %s", logmeldung)

                #Daten aktuallisieren und schreiben
                ro = RestObject(self._rest_api, self._rest_item)
                await ro.setvalue(option)  # Use the RestObject setvalue method
                # Update the entity's state with the new value
                self._rest_item.state = option #schreibt den state direkt in den coordinator ohne über die API zu lesen
                self._attr_current_option = self._rest_item.state
                self.async_write_ha_state()

            except Exception as e:
                log.error("Fehler beim Senden an Judo: %s", e)
            ##Spülintervall
            try: 
                # Flush-Intervall: nach Änderung sofort neu bewerten (Meldung ggf. löschen/erzeugen)
                if self._rest_item.translation_key == "flush_interval":
                    self.hass.async_create_task(self.coordinator.async_check_flush_interval_due())
            except Exception as f:
                log.error("Fehler beim löschen/erzeugen flush_interval: %s", f)                 
            ##
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Nur uebernehmen, wenn der gelesene Wert auch eine gueltige Option ist.
        # get_translation_key_from_number liefert bei unbekannten Zahlen
        # "unbekannt <x>" zurueck - das wuerde HA als ungueltige Option melden.
        if self._rest_item.state in self.options:
            self._attr_current_option = self._rest_item.state
            self.async_write_ha_state()
        elif self._rest_item.state is not None:
            log.warning(
                "Wert '%s' fuer %s ist keine gueltige Auswahl und wird ignoriert",
                self._rest_item.state,
                self._rest_item.translation_key,
            )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return MyEntity.my_device_info(self)


class MyCalcSensorEntity(CoordinatorEntity, SensorEntity, MyEntity):
    """Class that represents a calculated sensor entity."""

    def __init__(self, config_entry: MyConfigEntry, rest_item: RestItem, coordinator: MyCoordinator, idx) -> None:
        """Initialize of MyCalcSensorEntity."""
        super().__init__(coordinator, context=idx)
        self.idx = idx
        MyEntity.__init__(self, config_entry, rest_item, coordinator.rest_api)
        self._previous_value = None
        self._previous_time = None

        self._polling_active = False
        self._flow_task = None
        self._skip_handle_update_calc = False
        self._initial_poll_skip = False
        self._flow_history = collections.deque(maxlen=FLOW_AVERAGE_SAMPLES) #Mittelwertbildung über X Werte
        # Zaehlt aufeinanderfolgende Messungen ohne Zaehleraenderung
        self._unchanged_count = 0

    async def _poll_water_total_task(self):
        """Fragt water_total alle 10s ab und berechnet Durchfluss."""
        log.debug("Starte 10s Polling für water_total")

        rest_item = next((i for i in self.coordinator._restitems if i.translation_key == "water_total"), None)
        if not rest_item:
            log.warning("RestItem water_total nicht gefunden")
            return

        ro = RestObject(self._rest_api, rest_item)
        #log.warn("10s Task: ro_value: %s", ro)

        try:
            while self._polling_active:
                if self._initial_poll_skip:
                    raw_value = self.coordinator.get_value_from_item("water_total")
                    log.debug("10s Task: update water_total VOM Coordinator: %s", raw_value)
                else:
                    raw_value = await ro.value #ruft den wert über die api ab (nur water_total!) und wandelt ihn direkt um
                    if raw_value is not None:
                        rest_item.state = raw_value
                        log.debug("10s Task: update water_total ZUM coordinator: %s", raw_value)

                if raw_value is not None:
                    current_value = raw_value * 1000
                    #log.debug("10s Task: check raw value nach Abruf: %s", current_value)
                else:
                    current_value = None

                current_time = time.time()

                log.debug("10s:current_value: %s", current_value)
                log.debug("10s:previous_value: %s", self._previous_value)

                if (
                    self._previous_value is not None
                    and current_value is not None
                    and current_value != self._previous_value
                ):
                    time_diff = current_time - self._previous_time
                    value_diff = current_value - self._previous_value
                    flow_rate = (value_diff / time_diff) * 60

                    # Mittelwertbildung
                    self._flow_history.append(flow_rate)
                    if len(self._flow_history) > 1:
                        avg_flow = sum(self._flow_history) / len(self._flow_history)
                        self._attr_native_value = avg_flow
                        log.debug("10s Task: avg_flow: %s", avg_flow)
                    else:
                        self._attr_native_value = flow_rate  # erster Wert ungeglättet

                    #self._attr_native_value = flow_rate
                    log.debug("10s Task: flow_rate: %s", flow_rate)
                    log.debug("10s Task: value_diff: %s", value_diff)
                    log.debug("10s Task: time_diff: %s", time_diff)
                    self._previous_value = current_value 
                    self._previous_time = current_time  
                    self._initial_poll_skip = False
                    self._unchanged_count = 0
                    self.async_write_ha_state() 

                elif current_value == self._previous_value:
                    # Zaehler steht - das heisst NICHT zwangslaeufig, dass kein
                    # Wasser mehr laeuft: unter rund 5,5 l/min reicht ein 11s-
                    # Fenster nicht fuer einen ganzen Liter. Deshalb erst nach
                    # FLOW_STOP_AFTER_UNCHANGED Messungen abbrechen.
                    #
                    # _previous_value und _previous_time bleiben dabei bewusst
                    # stehen. Springt der Zaehler spaeter doch, wird ueber das
                    # gesamte Fenster gerechnet (z.B. 1 Liter in 33 s statt in
                    # 11 s) - das ergibt bei kleinem Durchfluss sogar den
                    # genaueren Wert.
                    self._unchanged_count += 1
                    log.debug(
                        "10s Task: water_total unveraendert (%d von %d)",
                        self._unchanged_count,
                        FLOW_STOP_AFTER_UNCHANGED,
                    )
                    if self._unchanged_count >= FLOW_STOP_AFTER_UNCHANGED:
                        log.debug("Kein Durchfluss mehr, stoppe 10s Task")
                        self._attr_native_value = 0
                        self._polling_active = False
                        self._skip_handle_update_calc = False
                        self._initial_poll_skip = False
                        self._unchanged_count = 0
                        self._previous_value = current_value
                        self._previous_time = current_time
                        self._flow_history.clear()  # Verlauf Mittelwertbildung zurücksetzen  
                        self.async_write_ha_state() 
                        return

                await asyncio.sleep(11)

        except Exception as e:
            log.error("Fehler im 10s Task: %s", e)
            self._polling_active = False
            self._skip_handle_update_calc = False
            self._initial_poll_skip = False
            self._unchanged_count = 0
            self._flow_history.clear()   # Verlauf Mittelwertbildung zurücksetzen 

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        current_time = time.time()
        raw_value = self.coordinator.get_value_from_item("water_total")
        if raw_value is not None:
            current_value = raw_value * 1000
        else:
            current_value = None

        #log.warn("Coordinator_start: current_time: %s", current_time)
        #log.warn("Coordinator_start: current_value: %s", current_value)
        #log.warn("Coordinator_start: previous_time: %s", self._previous_time)
        #log.warn("Coordinator_start: previous_value: %s", self._previous_value)

        flow_check = self.coordinator.get_value_from_item("water_flow_check_on_off")
        #log.warn("switch status entities: %s", flow_check)

        if flow_check:
            if (
                self._previous_value is not None
                and current_value is not None
                and current_value != self._previous_value
            ):
                # Änderung erkannt → 10s Task starten
                if not self._polling_active:
                    self._polling_active = True
                    self._skip_handle_update_calc = True
                    self._initial_poll_skip = True
                    self._unchanged_count = 0
                    self._flow_task = asyncio.create_task(self._poll_water_total_task())
                    log.debug("Änderung erkannt, wechsle zu 10s Polling-Modus")

            if not self._skip_handle_update_calc:
                # Berechnung weiterhin im coordinator erlaubt
                if self._previous_value is not None and current_value is not None:
                    time_diff = current_time - self._previous_time
                    value_diff = current_value - self._previous_value
                    flow_rate = (value_diff / time_diff) * 60
                    self._attr_native_value = flow_rate
                    #log.warn("Coordinator-Update: flow_rate: %s", flow_rate)
                    #log.warn("Coordinator-Update: value_diff: %s", value_diff)
                    #log.warn("Coordinator-Update: time_diff: %s", time_diff)
                    self._previous_value = current_value
                    self._previous_time = current_time 
                    self.async_write_ha_state()
                else:
                    self._attr_native_value = 0
                    # Initialen 0-Wert auch an HA publishen (sonst bleibt "unknown")
                    if self._previous_value is None:
                        self._previous_value = current_value
                        self._previous_time = current_time
                    self.async_write_ha_state()
            else:
                log.debug("Berechnung aktuell deaktiviert (läuft über 10s-Task)")
        else:
            self._attr_native_value = 0 #Update mycalcsensor (water_flow)
            self._polling_active = False
            self._skip_handle_update_calc = False
            self._initial_poll_skip = False
            self._previous_value = current_value #Initialisierung ansonsten ist es none
            self._previous_time = current_time 
            self.async_write_ha_state() #Update mycalcsensor HA (water_flow)

        #log.warn("Coordinator-Update: skip_handle_update_calc: %s", self._skip_handle_update_calc)
        #log.warn("Coordinator-Update: polling_active: %s", self._polling_active)
        #log.warn("Coordinator_end: current_time: %s", current_time)
        #log.warn("Coordinator_end: current_value: %s", current_value)
        #log.warn("Coordinator_end: previous_time: %s", self._previous_time)
        #log.warn("Coordinator_end: previous_value: %s", self._previous_value)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return MyEntity.my_device_info(self)

####################################################################################
########Alter Versuch######Update der kompletten Werte über den Coordinator#########
####Bei Verwendung auch Code im Coordniator einblenden Zeile 118-128########
####################################################################################
#class MyCalcSensorEntity(CoordinatorEntity, SensorEntity, MyEntity):
#    """Class that represents a calculated sensor entity."""
#
#    def __init__(self, config_entry: MyConfigEntry, rest_item: RestItem, coordinator: MyCoordinator, idx) -> None:
#        """Initialize of MyCalcSensorEntity."""
#        super().__init__(coordinator, context=idx)
#        self.idx = idx
#        MyEntity.__init__(self, config_entry, rest_item, coordinator.rest_api)
#        self._previous_value = None
#        self._previous_time = None
#
#    @callback
#    def _handle_coordinator_update(self) -> None:
#        """#Handle updated data from the coordinator."""
#        current_time = time.time()
#        raw_value = self.coordinator.get_value_from_item("water_total")
#        if raw_value is not None:
#            current_value = raw_value * 1000
#        else:
#            current_value = None
#        log.debug("current_time: %s", current_time)
#        log.debug("current_value: %s", current_value)
#        log.debug("previous_time: %s", self._previous_time)
#        log.debug("previous_value: %s", self._previous_value)
#
#        flow_check = self.coordinator.get_value_from_item("water_flow_check_on_off")
#        log.debug("switch status entities: %s", flow_check)
#        if flow_check:
#            if self._previous_value is not None and current_value is not None:
#                time_diff = current_time - self._previous_time
#                value_diff = current_value - self._previous_value
#                flow_rate = (value_diff / time_diff) * 60  # l/min   #Achtung wenn original dann in mynumber zeile raus!!
#                self._attr_native_value = flow_rate
#                log.debug("time_diff: %s", time_diff)
#                log.debug("value_diff: %s", value_diff)
#                log.debug("flow_rate: %s", flow_rate)
#            else:
#                self._attr_native_value = 0
#
#        else:
#            self._attr_native_value = 0
#        self._previous_value = current_value
#        self._previous_time = current_time
#        self.async_write_ha_state()
#
#    @property
#    def device_info(self) -> DeviceInfo:
#        """Return device info."""
#        return MyEntity.my_device_info(self)
##############################################################


class MyBinarySensorEntity(CoordinatorEntity, BinarySensorEntity, MyEntity):  # pylint: disable=W0223
    """Represent a binary sensor entity.

    Wird fuer die Einzelbits des Leckageschutz-Status (Kommando 6900) benutzt.
    Das restobject loest das Bit aus der 32-Bit-Maske heraus und legt bereits
    ein bool im RestItem ab - hier muss nur noch durchgereicht werden.
    """

    def __init__(
        self,
        config_entry: MyConfigEntry,
        rest_item: RestItem,
        coordinator: MyCoordinator,
        idx,
    ) -> None:
        """Initialize MyBinarySensorEntity."""
        super().__init__(coordinator, context=idx)
        self._idx = idx
        MyEntity.__init__(self, config_entry, rest_item, coordinator.rest_api)
        if rest_item.state is None:
            self._attr_is_on = None
        else:
            self._attr_is_on = bool(rest_item.state)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        state = self._rest_item.state
        self._attr_is_on = None if state is None else bool(state)
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return MyEntity.my_device_info(self)
