"""Input numbers pour Piscinexa."""
import logging
from homeassistant.components.input_number import InputNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    name = entry.data["name"]
    _LOGGER.debug("Configuration des entités input_number pour %s", name)
    entities = [
        PiscinexaPhCurrentInput(hass, entry, name),
        PiscinexaChloreCurrentInput(hass, entry, name),
    ]
    async_add_entities(entities)
    _LOGGER.debug("Entités input_number ajoutées: %s", [entity.entity_id for entity in entities])

class PiscinexaPhCurrentInput(InputNumber):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        super().__init__(
            min_value=0,
            max_value=14,
            step=0.1,
            unit_of_measurement="pH",
            mode="box",
        )
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{name}_ph_current"
        self._attr_friendly_name = f"{name.capitalize()} pH Actuel"
        self._attr_unique_id = f"{entry.entry_id}_ph_current"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.0",
        )
        # Initialiser avec la valeur actuelle
        self._attr_value = float(self._entry.data["ph_current"])
        _LOGGER.debug("Entité input_number %s créée avec valeur initiale %s", self._attr_name, self._attr_value)

    async def async_set_value(self, value: float) -> None:
        """Mettre à jour la valeur et synchroniser avec entry.data."""
        await super().async_set_value(value)
        self._hass.data[DOMAIN][self._entry.entry_id]["ph_current"] = value
        _LOGGER.debug("pH actuel mis à jour via input_number: %s", value)

class PiscinexaChloreCurrentInput(InputNumber):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        super().__init__(
            min_value=0,
            max_value=10,
            step=0.1,
            unit_of_measurement="mg/L",
            mode="box",
        )
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{name}_chlore_current"
        self._attr_friendly_name = f"{name.capitalize()} Chlore Actuel"
        self._attr_unique_id = f"{entry.entry_id}_chlore_current"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.0",
        )
        # Initialiser avec la valeur actuelle
        self._attr_value = float(self._entry.data["chlore_current"])
        _LOGGER.debug("Entité input_number %s créée avec valeur initiale %s", self._attr_name, self._attr_value)

    async def async_set_value(self, value: float) -> None:
        """Mettre à jour la valeur et synchroniser avec entry.data."""
        await super().async_set_value(value)
        self._hass.data[DOMAIN][self._entry.entry_id]["chlore_current"] = value
        _LOGGER.debug("Chlore actuel mis à jour via input_number: %s mg/L", value)
