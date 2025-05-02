
"""Capteurs pour Piscinexa."""
import logging
from datetime import datetime
from math import pi as PI
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, POOL_TYPE_SQUARE, POOL_TYPE_ROUND

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    name = entry.data["name"]
    sensors = [
        PiscinexaVolumeSensor(entry, name),
        PiscinexaTempsFiltrationSensor(entry, name),
        PiscinexaPhSensor(entry, name),
        PiscinexaChloreSensor(entry, name),
        PiscinexaLogSensor(name, entry.entry_id),
    ]
    async_add_entities(sensors)
    hass.data[DOMAIN].setdefault("log", []).append(sensors[-1])

class PiscinexaVolumeSensor(SensorEntity):
    def __init__(self, entry, name):
        self._entry = entry
        self._attr_name = f"{DOMAIN}_{name}_volume_eau"
        self._attr_unique_id = f"{entry.entry_id}_volume"
        self._attr_unit_of_measurement = "m³"

    @property
    def native_value(self):
        try:
            data = self._entry.data
            if data["pool_type"] == POOL_TYPE_SQUARE:
                return round(data["length"] * data["width"] * data["depth"], 2)
            else:
                r = data["diameter"] / 2
                return round(PI * r * r * data["depth"], 2)
        except Exception as e:
            _LOGGER.error("Erreur volume: %s", e)
            return None

class PiscinexaTempsFiltrationSensor(SensorEntity):
    def __init__(self, entry, name):
        self._entry = entry
        self._attr_name = f"{DOMAIN}_{name}_temps_filtration"
        self._attr_unique_id = f"{entry.entry_id}_filtration"
        self._attr_unit_of_measurement = "h"

    @property
    def native_value(self):
        try:
            return round(self._entry.data["temperature"] / 2, 1)
        except Exception as e:
            _LOGGER.error("Erreur filtration: %s", e)
            return None

class PiscinexaPhSensor(SensorEntity):
    def __init__(self, entry, name):
        self._entry = entry
        self._attr_name = f"{DOMAIN}_{name}_ph"
        self._attr_unique_id = f"{entry.entry_id}_ph"
        self._attr_unit_of_measurement = "pH"

    @property
    def native_value(self):
        return round(self._entry.data["ph_current"], 2)

class PiscinexaChloreSensor(SensorEntity):
    def __init__(self, entry, name):
        self._entry = entry
        self._attr_name = f"{DOMAIN}_{name}_chlore"
        self._attr_unique_id = f"{entry.entry_id}_chlore"
        self._attr_unit_of_measurement = "mg/L"

    @property
    def native_value(self):
        return round(self._entry.data["chlore_current"], 2)

class PiscinexaLogSensor(SensorEntity):
    def __init__(self, name, entry_id):
        self._attr_name = f"{DOMAIN}_{name}_log"
        self._attr_unique_id = f"{entry_id}_log"
        self._state = []

    def log(self, message):
        self._state.append(f"{datetime.now().strftime('%H:%M:%S')} - {message}")
        if len(self._state) > 10:
            self._state.pop(0)
        self.async_write_ha_state()

    @property
    def native_value(self):
        return "\n".join(self._state) if self._state else "Aucune action"

    @property
    def extra_state_attributes(self):
        return {"entries": self._state}
