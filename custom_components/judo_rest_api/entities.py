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
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .configentry import MyConfigEntry
from .const import CONF, CONST, FORMATS
from .coordinator import MyCoordinator
from .items import RestItem
from .restobject import RestAPI, RestObject

from .storage import save_last_written_value, load_last_written_values, PERSISTENT_ENTITIES

from homeassistant.util import dt as dt_util

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
            case FORMATS.STATUS | FORMATS.TEXT | FORMATS.TIMESTAMP | FORMATS.SW_VERSION | FORMATS.DATETIME_JUDO | FORMATS.SENSOR_INTERNAL_TIMESTAMP:
                self._divider = 1
                if (
                    self._rest_item.format
                    in (FORMATS.STATUS, FORMATS.TEXT, FORMATS.TIMESTAMP, FORMATS.SW_VERSION, FORMATS.DATETIME_JUDO, FORMATS.SENSOR_INTERNAL_TIMESTAMP)
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

    def my_device_info(self) -> DeviceInfo:
        """Build the device info."""
        return {
            "identifiers": {(CONST.DOMAIN, self._dev_device)},
            "translation_key": self._dev_device,
            "translation_placeholders": self._dev_translation_placeholders,
            "sw_version": self.coordinator.get_value_from_item("software_version"),
            "model": self.coordinator.get_value_from_item("device_type"),
            "manufacturer": "Judo",
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

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        ro = RestObject(self._rest_api, self._rest_item)
        await ro.setvalue(0)  # rest_item.state will be set inside ro.setvalue
        self._rest_item.state = False ####schreibt den state direkt in den coordinator ohne über die API zu lesen
        self._attr_is_on = False ##Ersetzt Zeile darunter weil nicht mehr über Api sondern nur intern
        #self._attr_is_on = self._rest_item.state   ####Wird nicht mehr durch API geupdatet!
        self.async_write_ha_state()

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

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        if self._rest_item.translation_key in PERSISTENT_ENTITIES:
            stored_values = await load_last_written_values(self.hass)
            if self._rest_item.translation_key in stored_values:
                self._attr_current_option = stored_values[self._rest_item.translation_key]
                self._rest_item.state = stored_values[self._rest_item.translation_key]
                log.debug("Geladene Werte nach If: %s", stored_values)

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

            # Lade gespeicherte Werte
            stored_values = await load_last_written_values(self.hass)
            selected_values = {}

            # Sammle alle benötigten Werte
            for key in ["holiday_mode_write", "leakageprotection_max_waterflowrate", "leakageprotection_max_waterflow", "leakageprotection_max_waterflowtime"]:
                selected_value = None
                if key == self._rest_item.translation_key:
                    # Für die aktuelle Entity nehmen wir den neuen Wert
                    selected_value = next(
                        (entry.number for entry in self._rest_item.resultlist if entry.translation_key == option),
                        None
                    )
                    if selected_value is not None:
                        # Speichere den neuen Wert
                        await save_last_written_value(self.hass, key, option)
                        log.debug("Gespeicherter Wert oben: %s", selected_value)
                else:
                    # Für die anderen Entities nehmen wir den gespeicherten Wert
                    stored_option = stored_values.get(key)
                    if stored_option:
                        # Finde den numerischen Wert für die gespeicherte Option
                        for item in self.coordinator._restitems:
                            if item.translation_key == key:
                                selected_value = next(
                                    (entry.number for entry in item.resultlist if entry.translation_key == stored_option),
                                    None
                                )
                                break

                if selected_value is not None:
                    selected_values[key] = selected_value

            # Debug Ausgabe
            log.debug("Gesammelte Werte für Leakageprotection: %s", selected_values)

            if len(selected_values) != 4:
                raise ValueError(f"Erwartet 4 Werte, aber {len(selected_values)} erhalten: {selected_values}")

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
                if self._rest_item.translation_key in PERSISTENT_ENTITIES:
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
        else:
            try: #Speichern der Werte die nur geschrieben werden
                if self._rest_item.translation_key in PERSISTENT_ENTITIES:
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
        self._attr_current_option = self._rest_item.state
        self.async_write_ha_state()
    
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
        self._flow_history = collections.deque(maxlen=3) #Mittelwertbildung über X Werte

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
                    self.async_write_ha_state() 

                elif current_value == self._previous_value:
                    log.debug("Kein Unterschied mehr bei water_total, stoppe 10s Task")
                    self._attr_native_value = 0
                    self._polling_active = False
                    self._skip_handle_update_calc = False
                    self._initial_poll_skip = False
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
