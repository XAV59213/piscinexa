"""Initialisation du composant Piscinexa."""
import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.input_number import DOMAIN as INPUT_NUMBER_DOMAIN
from homeassistant.const import CONF_NAME
from .const import DOMAIN, POOL_TYPE_SQUARE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data.copy()

    # Créer des entités input_number pour chlore_current et ph_current
    name = entry.data[CONF_NAME]
    input_number_configs = [
        {
            "id": f"{name}_chlore_current",
            "name": f"{name.capitalize()} Chlore Actuel",
            "min": 0,
            "max": 10,
            "step": 0.1,
            "unit": "mg/L",
            "initial": entry.data["chlore_current"],
        },
        {
            "id": f"{name}_ph_current",
            "name": f"{name.capitalize()} pH Actuel",
            "min": 0,
            "max": 14,
            "step": 0.1,
            "unit": "pH",
            "initial": entry.data["ph_current"],
        },
    ]

    for config in input_number_configs:
        hass.states.async_set(
            f"{INPUT_NUMBER_DOMAIN}.{config['id']}",
            config["initial"],
            {
                "friendly_name": config["name"],
                "min": config["min"],
                "max": config["max"],
                "step": config["step"],
                "unit_of_measurement": config["unit"],
            },
        )

    # Services
    async def handle_test_calcul(call: ServiceCall):
        name = hass.data[DOMAIN][entry.entry_id]["name"]
        _LOGGER.info("Service test_calcul appelé pour %s", name)
        log_sensor = hass.data[DOMAIN].get("log")
        if log_sensor and name in log_sensor._name:
            log_sensor.log_action("Test de calcul déclenché")

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
            data.update({
                "length": entry.data.get("length", 5.0),
                "width": entry.data.get("width", 4.0),
                "depth": entry.data.get("depth", 1.5)
            })
        else:
            data.update({
                "diameter": entry.data.get("diameter", 4.0),
                "depth": entry.data.get("depth", 1.5)
            })
        hass.data[DOMAIN][entry.entry_id].update(data)

        # Réinitialiser les input_number
        hass.states.async_set(
            f"{INPUT_NUMBER_DOMAIN}.{name}_chlore_current",
            1.0,
            {
                "friendly_name": f"{name.capitalize()} Chlore Actuel",
                "min": 0,
                "max": 10,
                "step": 0.1,
                "unit_of_measurement": "mg/L",
            },
        )
        hass.states.async_set(
            f"{INPUT_NUMBER_DOMAIN}.{name}_ph_current",
            7.0,
            {
                "friendly_name": f"{name.capitalize()} pH Actuel",
                "min": 0,
                "max": 14,
                "step": 0.1,
                "unit_of_measurement": "pH",
            },
        )

        log_sensor = hass.data[DOMAIN].get("log")
        if log_sensor and name in log_sensor._name:
            log_sensor.log_action("Valeurs réinitialisées")
        await hass.config_entries.async_reload(entry.entry_id)

    hass.services.async_register(DOMAIN, "test_calcul", handle_test_calcul)
    hass.services.async_register(DOMAIN, "reset_valeurs", handle_reset_valeurs)

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "button"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_unload_platforms(entry, ["sensor", "button"])
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
