
"""Initialisation du composant Piscinexa."""
import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, POOL_TYPE_SQUARE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data.copy()

    # Services
    async def handle_test_calcul(call: ServiceCall):
        name = hass.data[DOMAIN][entry.entry_id]["name"]
        _LOGGER.info("Service test_calcul appelé pour %s", name)
        for ent in hass.data[DOMAIN].get("log", []):
            if name in ent.name:
                ent.log("Test de calcul déclenché")

    async def handle_reset_valeurs(call: ServiceCall):
        name = hass.data[DOMAIN][entry.entry_id]["name"]
        _LOGGER.info("Service reset_valeurs appelé pour %s", name)
        data = {
            "name": name,
            "pool_type": hass.data[DOMAIN][entry.entry_id]["pool_type"],
            "ph_current": 7.0,
            "ph_target": 7.4,
            "chlore_current": 1.0,
            "chlore_target": 2.0,
            "temperature": 20.0,
        }
        if data["pool_type"] == POOL_TYPE_SQUARE:
            data.update({"length": 0, "width": 0, "depth": 0})
        else:
            data.update({"diameter": 0, "depth": 0})
        hass.data[DOMAIN][entry.entry_id].update(data)
        for ent in hass.data[DOMAIN].get("log", []):
            if name in ent.name:
                ent.log("Valeurs réinitialisées")
        await hass.config_entries.async_reload(entry.entry_id)

    hass.services.async_register(DOMAIN, "test_calcul", handle_test_calcul)
    hass.services.async_register(DOMAIN, "reset_valeurs", handle_reset_valeurs)

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "button"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_unload_platforms(entry, ["sensor", "button"])
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
