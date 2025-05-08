import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
            identifiers={(DOMAIN, f"piscinexa_{name}_{action}")},
            name=f"Bouton {action.capitalize()}",
            manufacturer="Piscinexa",
            model="Bouton",
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
        self._attr_device_info.name = self._attr_name

    async def async_press(self):
        service_name = f"{self._action}_calcul" if self._action == "test" else f"{self._action}_valeurs"
        await self._hass.services.async_call(
            DOMAIN,
            service_name,
            {"name": self._name},
        )
