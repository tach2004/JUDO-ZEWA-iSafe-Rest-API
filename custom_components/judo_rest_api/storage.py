#INFO: After installation, these values must be selected once using SELECT-OTION and sent to judo so that the file can be created. 
#The values are then saved in Homeassitan when the integration is restarted or updated 

import json
import os
from homeassistant.core import HomeAssistant

STORAGE_PATH = "/config/judo_storage.json"

# Liste der Entitäten, die gespeichert werden sollen (nur hier anpassen!)
# HINWEIS: holiday_mode_write und die drei leakageprotection_* wurden hier
# entfernt. Seit Kommando 6800 ("Leckageeinstellungen lesen") koennen diese
# Werte direkt vom JUDO zurueckgelesen werden - eine Aenderung am Geraet
# selbst wird dadurch wieder erkannt. Ein Zwischenspeichern wuerde nur noch
# einen veralteten Wert liefern, bis der erste Read durch ist.
PERSISTENT_ENTITIES = [
    "sleep_mode_duration",
    "flush_interval",
    "last_reset_flush_interval",
    "install_date_utc",
    "water_flow_check_on_off"
    ]

# ===== GEAENDERT (Firmware-Erkennung 2.0.1) - START =====
# Rueckfallebene fuer Geraete mit aelterer Connectivity-Modul-Firmware, die
# Kommando 6800 ("Leckageeinstellungen lesen") nicht kennen.
#
# Unterschied zu PERSISTENT_ENTITIES - und der ist wichtig:
#   PERSISTENT_ENTITIES  wird IMMER gespeichert und IMMER zurueckgespielt.
#   FALLBACK_ENTITIES    wird nur benutzt, wenn das Geraet 6800 nicht kann.
#
# Wuerden diese vier Schluessel einfach wieder in PERSISTENT_ENTITIES stehen,
# wuerde der Restore in entities.py den frisch von 6800 gelesenen Geraetewert
# bei jedem Neustart mit dem gespeicherten ueberschreiben. Eine Aenderung
# direkt am Geraetepanel waere danach wieder weg. Genau deshalb sind es zwei
# getrennte Listen; entities.py entscheidet anhand von
# rest_api.unsupported_commands, welche gilt.
FALLBACK_ENTITIES = [
    "holiday_mode_write",
    "leakageprotection_max_waterflowrate",
    "leakageprotection_max_waterflow",
    "leakageprotection_max_waterflowtime",
    ]

# Alles, was ueberhaupt in die Datei geschrieben werden darf.
STORED_ENTITIES = PERSISTENT_ENTITIES + FALLBACK_ENTITIES
# ===== GEAENDERT (Firmware-Erkennung 2.0.1) - ENDE =====

async def save_last_written_value(hass: HomeAssistant, key: str, value: str) -> None:
    """Speichert den letzten geschriebenen Wert in der JSON-Datei."""
    if key not in STORED_ENTITIES:
        return  # Nur speichern, wenn die Entität in einer der Listen steht

    data = await load_last_written_values(hass)  # Vorhandene Werte laden
    data[key] = value  # Neuen Wert speichern
    
    def _write_file():
        with open(STORAGE_PATH, "w") as file:
            json.dump(data, file)
    
    await hass.async_add_executor_job(_write_file)

async def load_last_written_values(hass: HomeAssistant) -> dict:
    """Lädt die gespeicherten Werte aus der JSON-Datei."""
    if not os.path.exists(STORAGE_PATH):
        return {}  # Falls Datei nicht existiert, leeres Dict zurückgeben
    
    def _read_file():
        try:
            with open(STORAGE_PATH, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}  # Falls Datei beschädigt ist, leeres Dict zurückgeben
    
    return await hass.async_add_executor_job(_read_file)
