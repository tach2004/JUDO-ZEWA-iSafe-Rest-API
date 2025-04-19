#INFO: After installation, these values must be selected once using SELECT-OTION and sent to judo so that the file can be created. 
#The values are then saved in Homeassitan when the integration is restarted or updated 

import json
import os
from homeassistant.core import HomeAssistant

STORAGE_PATH = "/config/judo_storage.json"

# Liste der Entitäten, die gespeichert werden sollen (nur hier anpassen!)
PERSISTENT_ENTITIES = ["sleep_mode_duration", "holiday_mode_write", "leakageprotection_max_waterflowrate", "leakageprotection_max_waterflow", "leakageprotection_max_waterflowtime"]

async def save_last_written_value(hass: HomeAssistant, key: str, value: str) -> None:
    """Speichert den letzten geschriebenen Wert in der JSON-Datei."""
    if key not in PERSISTENT_ENTITIES:
        return  # Nur speichern, wenn die Entität in der Liste ist

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
