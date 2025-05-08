import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.components.input_number import InputNumber
from homeassistant.components.input_select import InputSelect
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.translation import async_get_translations
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    name = entry.data["name"]
    entities = [
        PiscinexaButton(hass, entry, name, "test"),
        PiscinexaButton(hass, entry, name, "reset"),
        PiscinexaInputNumber(hass, entry, name, "ph_current", 0, 14, 7.0),
        PiscinexaInputNumber(hass, entry, name, "chlore_current", 0, 10, 1.0),
        PiscinexaInputSelect(hass, entry, name, "ph_plus_treatment", ["Liquide", "Granulés"], "Liquide"),
        PiscinexaInputSelect(hass, entry, name, "ph_minus_treatment", ["Liquide", "Granulés"], "Liquide"),
        PiscinexaInputSelect(hass, entry, name, "chlore_treatment", ["Liquide", "Chlore choc (poudre)", "Pastille lente"], "Chlore choc (poudre)"),
    ]
    async_add_entities(entities, True)

class PiscinexaButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str, action: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._action = action
        self._attr_unique_id = f"{entry.entry_id}_{action}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:cog"

    async def async_added_to_hass(self):
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
        )
        self._attr_name = self._translations.get(
            f"entity.button.piscinexa_{self._action}.name",
            self._action.capitalize()
        )

    async def async_press(self):
        service_name = f"{self._action}_calcul" if self._action == "test" else f"{self._action}_valeurs"
        await self._hass.services.async_call(
            DOMAIN,
            service_name,
            {"name": self._name},
        )

class PiscinexaInputNumber(InputNumber):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str, type_: str, min_val: float, max_val: float, default_val: float):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._type = type_
        self._attr_unique_id = f"{entry.entry_id}_{type_}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:numeric"
        self._attr_min_value = min_val
        self._attr_max_value = max_val
        self._attr_step = 0.1
        self._attr_value = default_val

    async def async_added_to_hass(self):
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
        )
        self._attr_name = self._translations.get(
            f"entity.input_number.piscinexa_{self._type}.name",
            self._type.replace("_", " ").capitalize()
        )

    async def async_set_value(self, value: float) -> None:
        self._attr_value = value
        self.async_write_ha_state()
        await self._hass.config_entries.async_reload(self._entry.entry_id)

class PiscinexaInputSelect(InputSelect):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str, type_: str, options: list, default_option: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._type = type_
        self._attr_unique_id = f"{entry.entry_id}_{type_}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:menu-down"
        self._attr_options = options
        self._attr_current_option = default_option

    async def async_added_to_hass(self):
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
        )
        self._attr_name = self._translations.get(
            f"entity.input_select.piscinexa_{self._type}.name",
            self._type.replace("_", " ").capitalize()
        )
        options_key = f"entity.input_select.piscinexa_{self._type}.options"
        translated_options = []
        for option in self._attr_options:
            option_key = f"{options_key}.{option.lower().replace(' ', '_')}"
            translated_option = self._translations.get(option_key, option)
            translated_options.append(translated_option)
        self._attr_options = translated_options

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self.async_write_ha_state()
