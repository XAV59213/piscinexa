
"""Capteur de démonstration pour Piscinexa."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configurer les capteurs pour une entrée de configuration."""
    name = entry.data.get("name", "piscine")
    async_add_entities([PiscinexaExampleSensor(entry, name)])

class PiscinexaExampleSensor(SensorEntity):
    """Capteur de démonstration."""

    def __init__(self, entry: ConfigEntry, name: str):
        self._attr_name = f"{name}_exemple"
        self._attr_unique_id = f"{entry.entry_id}_sensor_exemple"
        self._attr_native_value = 42
        self._attr_icon = "mdi:water"
        self._attr_unit_of_measurement = "°C"
