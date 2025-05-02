"""Initialisation du composant Piscinexa."""
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, POOL_TYPE_SQUARE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure une entrée Piscinexa."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data.copy()

    # Enregistrer les services
    async def handle_test_calcul(call):
        """Service pour tester les calculs."""
        name = hass.data[DOMAIN][entry.entry_id]["name"]
        _LOGGER.info("Service test_calcul appelé pour %s", name)
        hass.data[DOMAIN]["log"].log_action(f"Test des calculs effectué pour {name}")

    async def handle_reset_valeurs(call):
        """Service pour réinitialiser les valeurs."""
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
        hass.data[DOMAIN]["log"].log_action(f"Valeurs réinitialisées pour {name}")
        await hass.config_entries.async_reload(entry.entry_id)

    hass.services.async_register(DOMAIN, "test_calcul", handle_test_calcul)
    hass.services.async_register(DOMAIN, "reset_valeurs", handle_reset_valeurs)

    # Charger les plateformes
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "button"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharge une entrée Piscinexa."""
    await hass.config_entries.async_unload_platforms(entry, ["sensor", "button"])
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
