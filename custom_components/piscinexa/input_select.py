"""Input selects pour Piscinexa."""
import logging
from homeassistant.components.input_select import InputSelect
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    name = entry.data["name"]
    _LOGGER.info("Configuration des entités input_select pour %s", name)
    entities = [
        PiscinexaPhPlusTreatmentSelect(hass, entry, name),
        PiscinexaPhMinusTreatmentSelect(hass, entry, name),
        PiscinexaChloreTreatmentSelect(hass, entry, name),
    ]
    async_add_entities(entities)
    _LOGGER.info("Entités input_select ajoutées: %s", [entity.entity_id for entity in entities])

class PiscinexaPhPlusTreatmentSelect(InputSelect):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        unique_id = f"{entry.entry_id}_ph_plus_treatment"
        super().__init__(config={
            "id": unique_id,
            "name": f"{name}_ph_plus_treatment",
            "options": [
                hass.helpers.template.render("entity.input_select.{name}_ph_plus_treatment.options.liquid", {"name": name}),
                hass.helpers.template.render("entity.input_select.{name}_ph_plus_treatment.options.granules", {"name": name}),
            ],
        })
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{name}_ph_plus_treatment"
        self._attr_friendly_name = hass.helpers.template.render(
            "entity.input_select.{name}_ph_plus_treatment.name",
            {"name": name.capitalize()}
        )
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:water-plus"
        self._attr_current_option = self._entry.data.get("ph_plus_treatment", "Liquide")
        _LOGGER.debug("Entité input_select %s créée avec valeur initiale %s", self._attr_name, self._attr_current_option)

class PiscinexaPhMinusTreatmentSelect(InputSelect):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        unique_id = f"{entry.entry_id}_ph_minus_treatment"
        super().__init__(config={
            "id": unique_id,
            "name": f"{name}_ph_minus_treatment",
            "options": [
                hass.helpers.template.render("entity.input_select.{name}_ph_minus_treatment.options.liquid", {"name": name}),
                hass.helpers.template.render("entity.input_select.{name}_ph_minus_treatment.options.granules", {"name": name}),
            ],
        })
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{name}_ph_minus_treatment"
        self._attr_friendly_name = hass.helpers.template.render(
            "entity.input_select.{name}_ph_minus_treatment.name",
            {"name": name.capitalize()}
        )
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:water-minus"
        self._attr_current_option = self._entry.data.get("ph_minus_treatment", "Liquide")
        _LOGGER.debug("Entité input_select %s créée avec valeur initiale %s", self._attr_name, self._attr_current_option)

class PiscinexaChloreTreatmentSelect(InputSelect):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        unique_id = f"{entry.entry_id}_chlore_treatment"
        super().__init__(config={
            "id": unique_id,
            "name": f"{name}_chlore_treatment",
            "options": [
                hass.helpers.template.render("entity.input_select.{name}_chlore_treatment.options.shock", {"name": name}),
                hass.helpers.template.render("entity.input_select.{name}_chlore_treatment.options.tablet", {"name": name}),
                hass.helpers.template.render("entity.input_select.{name}_chlore_treatment.options.liquid", {"name": name}),
            ],
        })
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{name}_chlore_treatment"
        self._attr_friendly_name = hass.helpers.template.render(
            "entity.input_select.{name}_chlore_treatment.name",
            {"name": name.capitalize()}
        )
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:water-check"
        self._attr_current_option = self._entry.data.get("chlore_treatment", "Chlore choc (poudre)")
        _LOGGER.debug("Entité input_select %s créée avec valeur initiale %s", self._attr_name, self._attr_current_option)
