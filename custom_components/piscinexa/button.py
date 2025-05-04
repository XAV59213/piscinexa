"""Boutons pour Piscinexa."""
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    name = entry.data["name"]
    async_add_entities([
        PiscinexaTestButton(hass, entry, name),
        PiscinexaResetButton(hass, entry, name),
    ])

class PiscinexaTestButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._attr_name = f"{DOMAIN}_{name}_test"
        self._attr_icon = "mdi:calculator"
        self._attr_unique_id = f"{entry.entry_id}_test"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),  # Changement ici
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.0",
        )

    async def async_press(self) -> None:
        await self._hass.services.async_call(DOMAIN, "test_calcul", blocking=True)

class PiscinexaResetButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._attr_name = f"{DOMAIN}_{name}_reset"
        self._attr_icon = "mdi:refresh"
        self._attr_unique_id = f"{entry.entry_id}_reset"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),  # Changement ici
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.0",
        )

    async def async_press(self) -> None:
        await self._hass.services.async_call(DOMAIN, "reset_valeurs", blocking=True)
