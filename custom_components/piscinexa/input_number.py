"""Input numbers et selects pour Piscinexa."""
import logging
from homeassistant.components.input_number import InputNumber
from homeassistant.components.input_select import InputSelect
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    name = entry.data["name"]
    _LOGGER.info("Configuration des entités input_number et input_select pour %s", name)
    entities = [
        PiscinexaPhCurrentInput(hass, entry, name),
        PiscinexaChloreCurrentInput(hass, entry, name),
        PiscinexaPhPlusTreatmentSelect(hass, entry, name),
        PiscinexaPhMinusTreatmentSelect(hass, entry, name),
        PiscinexaChloreTreatmentSelect(hass, entry, name),
    ]
    async_add_entities(entities)
    _LOGGER.info("Entités ajoutées: %s", [entity.name for entity in entities])

class PiscinexaPhCurrentInput(InputNumber):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        config = {
            "min": 0,
            "max": 14,
            "step": 0.1,
            "unit_of_measurement": "pH",
            "mode": "box",
            "name": f"{name}_ph_current",
            "initial": float(entry.data.get("ph_current", 7.0)),
        }
        super().__init__(config)
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_unique_id = f"{entry.entry_id}_ph_current"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        _LOGGER.debug("Entité input_number '%s' créée avec valeur initiale %s", self.name, config["initial"])

    async def async_set_value(self, value: float) -> None:
        await super().async_set_value(value)
        self._hass.data[DOMAIN][self._entry.entry_id]["ph_current"] = value
        _LOGGER.debug("pH actuel mis à jour via input_number: %s", value)

class PiscinexaChloreCurrentInput(InputNumber):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        config = {
            "min": 0,
            "max": 10,
            "step": 0.1,
            "unit_of_measurement": "mg/L",
            "mode": "box",
            "name": f"{name}_chlore_current",
            "initial": float(entry.data.get("chlore_current", 1.0)),
        }
        super().__init__(config)
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_unique_id = f"{entry.entry_id}_chlore_current"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        _LOGGER.debug("Entité input_number '%s' créée avec valeur initiale %s", self.name, config["initial"])

    async def async_set_value(self, value: float) -> None:
        await super().async_set_value(value)
        self._hass.data[DOMAIN][self._entry.entry_id]["chlore_current"] = value
        _LOGGER.debug("Chlore actuel mis à jour via input_number: %s mg/L", value)

class PiscinexaPhPlusTreatmentSelect(InputSelect):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        super().__init__(
            options=["Liquide", "Granulés"],
            name=f"{name}_ph_plus_treatment",
            initial=entry.data.get("ph_plus_treatment", "Liquide"),
        )
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_unique_id = f"{entry.entry_id}_ph_plus_treatment"
        self._attr_icon = "mdi:water-plus"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        _LOGGER.debug("Entité input_select '%s' créée avec valeur initiale %s", self.name, self.current_option)

class PiscinexaPhMinusTreatmentSelect(InputSelect):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        super().__init__(
            options=["Liquide", "Granulés"],
            name=f"{name}_ph_minus_treatment",
            initial=entry.data.get("ph_minus_treatment", "Liquide"),
        )
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_unique_id = f"{entry.entry_id}_ph_minus_treatment"
        self._attr_icon = "mdi:water-minus"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        _LOGGER.debug("Entité input_select '%s' créée avec valeur initiale %s", self.name, self.current_option)

class PiscinexaChloreTreatmentSelect(InputSelect):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        super().__init__(
            options=["Chlore choc (poudre)", "Pastille lente", "Liquide"],
            name=f"{name}_chlore_treatment",
            initial=entry.data.get("chlore_treatment", "Chlore choc (poudre)"),
        )
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_unique_id = f"{entry.entry_id}_chlore_treatment"
        self._attr_icon = "mdi:water-check"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        _LOGGER.debug("Entité input_select '%s' créée avec valeur initiale %s", self.name, self.current_option)
