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
    if async_add_entities:
        async_add_entities(entities)
    else:
        from homeassistant.helpers.entity_platform import async_add_entities
        async_add_entities(entities)
    _LOGGER.info("Entités ajoutées: %s", [entity.entity_id for entity in entities])

class PiscinexaPhCurrentInput(InputNumber):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        super().__init__()
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
            sw_version="1.0.2",
        )
        self._attr_min_value = 0
        self._attr_max_value = 14
        self._attr_step = 0.1
        self._attr_unit_of_measurement = "pH"
        self._attr_mode = "box"
        self._attr_value = float(self._entry.data.get("ph_current", 7.0))
        _LOGGER.debug("Entité input_number %s créée avec valeur initiale %s", self._attr_name, self._attr_value)

    async def async_set_value(self, value: float) -> None:
        await super().async_set_value(value)
        self._hass.data[DOMAIN][self._entry.entry_id]["ph_current"] = value
        _LOGGER.debug("pH actuel mis à jour via input_number: %s", value)

class PiscinexaChloreCurrentInput(InputNumber):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        super().__init__()
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
            sw_version="1.0.2",
        )
        self._attr_min_value = 0
        self._attr_max_value = 10
        self._attr_step = 0.1
        self._attr_unit_of_measurement = "mg/L"
        self._attr_mode = "box"
        self._attr_value = float(self._entry.data.get("chlore_current", 1.0))
        _LOGGER.debug("Entité input_number %s créée avec valeur initiale %s", self._attr_name, self._attr_value)

    async def async_set_value(self, value: float) -> None:
        await super().async_set_value(value)
        self._hass.data[DOMAIN][self._entry.entry_id]["chlore_current"] = value
        _LOGGER.debug("Chlore actuel mis à jour via input_number: %s mg/L", value)

class PiscinexaPhPlusTreatmentSelect(InputSelect):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        super().__init__(
            options=["Liquide", "Granulés"],
            name=f"{name}_ph_plus_treatment",
        )
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{name}_ph_plus_treatment"
        self._attr_friendly_name = f"{name.capitalize()} Type de traitement pH+"
        self._attr_unique_id = f"{entry.entry_id}_ph_plus_treatment"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:water-plus"
        self._attr_value = entry.data.get("ph_plus_treatment", "Liquide")
        _LOGGER.debug("Entité input_select %s créée avec valeur initiale %s", self._attr_name, self._attr_value)

class PiscinexaPhMinusTreatmentSelect(InputSelect):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        super().__init__(
            options=["Liquide", "Granulés"],
            name=f"{name}_ph_minus_treatment",
        )
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{name}_ph_minus_treatment"
        self._attr_friendly_name = f"{name.capitalize()} Type de traitement pH-"
        self._attr_unique_id = f"{entry.entry_id}_ph_minus_treatment"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:water-minus"
        self._attr_value = entry.data.get("ph_minus_treatment", "Liquide")
        _LOGGER.debug("Entité input_select %s créée avec valeur initiale %s", self._attr_name, self._attr_value)

class PiscinexaChloreTreatmentSelect(InputSelect):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        super().__init__(
            options=["Chlore choc (poudre)", "Pastille lente", "Liquide"],
            name=f"{name}_chlore_treatment",
        )
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{name}_chlore_treatment"
        self._attr_friendly_name = f"{name.capitalize()} Type de traitement Chlore"
        self._attr_unique_id = f"{entry.entry_id}_chlore_treatment"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:water-check"
        self._attr_value = entry.data.get("chlore_treatment", "Chlore choc (poudre)")
        _LOGGER.debug("Entité input_select %s créée avec valeur initiale %s", self._attr_name, self._attr_value)
