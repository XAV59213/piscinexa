"""Input selects pour Piscinexa."""
import logging
from homeassistant.components.input_select import InputSelect
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.translation import async_get_translations
from homeassistant.const import CONF_ID, ATTR_EDITABLE
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
            CONF_ID: unique_id,
            "name": f"{name}_ph_plus_treatment",
            "options": [
                "Liquide",
                "Granulés",
            ],
        })
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{name}_ph_plus_treatment"
        self._attr_translation_key = "ph_plus_treatment"
        self._attr_translation_placeholders = {"name": name.capitalize()}
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:water-plus"
        self._attr_editable = True  # Ajout de l'attribut editable
        self._attr_current_option = self._entry.data.get("ph_plus_treatment", "Liquide")
        self._translations = None
        _LOGGER.debug("Entité input_select %s créée avec valeur initiale %s", self._attr_name, self._attr_current_option)

    async def async_added_to_hass(self):
        """Charge les traductions lors de l'ajout à Home Assistant."""
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
            integrations={DOMAIN},  # Changé de components à integrations
        )
        # Mettre à jour les options avec les traductions
        options = [
            self._translations.get(f"entity.input_select.{self._name}_ph_plus_treatment.options.liquid", "Liquide"),
            self._translations.get(f"entity.input_select.{self._name}_ph_plus_treatment.options.granules", "Granulés"),
        ]
        self._attr_options = options
        self.async_write_ha_state()

class PiscinexaPhMinusTreatmentSelect(InputSelect):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        unique_id = f"{entry.entry_id}_ph_minus_treatment"
        super().__init__(config={
            CONF_ID: unique_id,
            "name": f"{name}_ph_minus_treatment",
            "options": [
                "Liquide",
                "Granulés",
            ],
        })
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{name}_ph_minus_treatment"
        self._attr_translation_key = "ph_minus_treatment"
        self._attr_translation_placeholders = {"name": name.capitalize()}
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:water-minus"
        self._attr_editable = True  # Ajout de l'attribut editable
        self._attr_current_option = self._entry.data.get("ph_minus_treatment", "Liquide")
        self._translations = None
        _LOGGER.debug("Entité input_select %s créée avec valeur initiale %s", self._attr_name, self._attr_current_option)

    async def async_added_to_hass(self):
        """Charge les traductions lors de l'ajout à Home Assistant."""
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
            integrations={DOMAIN},  # Changé de components à integrations
        )
        # Mettre à jour les options avec les traductions
        options = [
            self._translations.get(f"entity.input_select.{self._name}_ph_minus_treatment.options.liquid", "Liquide"),
            self._translations.get(f"entity.input_select.{self._name}_ph_minus_treatment.options.granules", "Granulés"),
        ]
        self._attr_options = options
        self.async_write_ha_state()

class PiscinexaChloreTreatmentSelect(InputSelect):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        unique_id = f"{entry.entry_id}_chlore_treatment"
        super().__init__(config={
            CONF_ID: unique_id,
            "name": f"{name}_chlore_treatment",
            "options": [
                "Chlore choc (poudre)",
                "Pastille lente",
                "Liquide",
            ],
        })
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{name}_chlore_treatment"
        self._attr_translation_key = "chlore_treatment"
        self._attr_translation_placeholders = {"name": name.capitalize()}
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:water-check"
        self._attr_editable = True  # Ajout de l'attribut editable
        self._attr_current_option = self._entry.data.get("chlore_treatment", "Chlore choc (poudre)")
        self._translations = None
        _LOGGER.debug("Entité input_select %s créée avec valeur initiale %s", self._attr_name, self._attr_current_option)

    async def async_added_to_hass(self):
        """Charge les traductions lors de l'ajout à Home Assistant."""
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
            integrations={DOMAIN},  # Changé de components à integrations
        )
        # Mettre à jour les options avec les traductions
        options = [
            self._translations.get(f"entity.input_select.{self._name}_chlore_treatment.options.shock", "Chlore choc (poudre)"),
            self._translations.get(f"entity.input_select.{self._name}_chlore_treatment.options.tablet", "Pastille lente"),
            self._translations.get(f"entity.input_select.{self._name}_chlore_treatment.options.liquid", "Liquide"),
        ]
        self._attr_options = options
        self.async_write_ha_state()