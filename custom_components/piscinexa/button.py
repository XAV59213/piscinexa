
"""Bouton de démonstration pour Piscinexa."""
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configurer les boutons pour une entrée de configuration."""
    name = entry.data.get("name", "piscine")
    async_add_entities([PiscinexaTestButton(entry, name)])

class PiscinexaTestButton(ButtonEntity):
    """Bouton de test pour Piscinexa."""

    def __init__(self, entry: ConfigEntry, name: str):
        self._attr_name = f"{name}_test_bouton"
        self._attr_unique_id = f"{entry.entry_id}_test_button"
        self._attr_icon = "mdi:flask"

    async def async_press(self) -> None:
        """Action du bouton."""
        print(f"Bouton de test appuyé pour {self._attr_name}")
