
"""Boutons pour Piscinexa."""
import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    name = entry.data["name"]
    entities = [
        PiscinexaServiceButton(hass, entry, name, "test", "Tester", "mdi:calculator", "test_calcul"),
        PiscinexaServiceButton(hass, entry, name, "reset", "Réinitialiser", "mdi:refresh", "reset_valeurs"),
    ]
    async_add_entities(entities)

class PiscinexaServiceButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str, suffix: str, label: str, icon: str, service: str):
        self._hass = hass
        self._entry = entry
        self._service = service
        self._attr_name = f"{name}_{suffix}"
        self._attr_unique_id = f"{entry.entry_id}_{suffix}"
        self._attr_icon = icon
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2"
        )
        self._attr_friendly_name = f"{name.capitalize()} {label}"

    async def async_press(self) -> None:
        _LOGGER.info("Appui sur le bouton %s", self._attr_name)
        await self._hass.services.async_call(DOMAIN, self._service, blocking=True)
