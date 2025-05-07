"""Initialisation du composant Piscinexa."""
import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from .const import DOMAIN, POOL_TYPE_SQUARE

DEFAULTS = {
    "chlore_target": 2.0,
    "ph_target": 7.4,
    "temperature": 20.0,
    "ph_current": 7.0,
    "chlore_current": 1.0,
}

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    if entry.entry_id in hass.data[DOMAIN]:
        _LOGGER.warning("Entrée %s déjà configurée, mise à jour des données", entry.entry_id)
        hass.data[DOMAIN][entry.entry_id].update(entry.data)
    else:
        hass.data[DOMAIN][entry.entry_id] = entry.data.copy()

    for key, default_value in DEFAULTS.items():
        if key not in hass.data[DOMAIN][entry.entry_id]:
            _LOGGER.info("%s manquant, définition par défaut: %s", key, default_value)
            hass.data[DOMAIN][entry.entry_id][key] = default_value

    async def handle_test_calcul(call: ServiceCall):
        name = hass.data[DOMAIN][entry.entry_id]["name"]
        _LOGGER.info("Service test_calcul appelé pour %s", name)
        log_sensor = hass.data[DOMAIN].get("log")
        if log_sensor and name in getattr(log_sensor, "_name", ""):
            log_sensor.log_action("Test de calcul déclenché")

    async def handle_reset_valeurs(call: ServiceCall):
        name = hass.data[DOMAIN][entry.entry_id]["name"]
        _LOGGER.info("Service reset_valeurs appelé pour %s", name)

        data = {
            "name": name,
            "pool_type": hass.data[DOMAIN][entry.entry_id]["pool_type"],
            **DEFAULTS
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

        for entity_id, value in [
            (f"input_number.{name}_ph_current", DEFAULTS["ph_current"]),
            (f"input_number.{name}_chlore_current", DEFAULTS["chlore_current"])
        ]:
            entity = hass.states.get(entity_id)
            if entity:
                await hass.services.async_call(
                    "input_number", "set_value",
                    {"entity_id": entity_id, "value": value}
                )

        log_sensor = hass.data[DOMAIN].get("log")
        if log_sensor and name in getattr(log_sensor, "_name", ""):
            log_sensor.log_action("Valeurs réinitialisées")

        await hass.config_entries.async_reload(entry.entry_id)

    async def handle_apply_treatment(call: ServiceCall):
        name = call.data.get("name", hass.data[DOMAIN][entry.entry_id]["name"])
        treatment_type = call.data.get("treatment_type")
        treatment_form = call.data.get("treatment_form")
        quantity = float(call.data.get("quantity", 0.0))

        _LOGGER.info("Service apply_treatment appelé pour %s: %s, %s, %s", name, treatment_type, treatment_form, quantity)

        volume_entity = hass.states.get(f"sensor.{DOMAIN}_{name}_volume_eau")
        if not volume_entity or volume_entity.state in ("unknown", "unavailable"):
            _LOGGER.error("Capteur de volume indisponible pour %s", name)
            return

        try:
            volume = float(volume_entity.state)
        except ValueError:
            _LOGGER.error("Volume non numérique pour %s", name)
            return

        if treatment_type in ["pH+", "pH-"]:
            ph_current = float(hass.data[DOMAIN][entry.entry_id].get("ph_current", 7.0))
            if treatment_form == "Liquide":
                ph_change = quantity / (volume * (0.01 if treatment_type == "pH+" else 0.012))
            else:  # Granulés
                ph_change = quantity / (volume * (1.0 if treatment_type == "pH+" else 1.2))
            new_ph = ph_current + ph_change if treatment_type == "pH+" else ph_current - ph_change
            new_ph = round(new_ph, 1)
            hass.data[DOMAIN][entry.entry_id]["ph_current"] = new_ph
            await hass.services.async_call("input_number", "set_value", {
                "entity_id": f"input_number.{name}_ph_current", "value": new_ph
            })

        elif treatment_type == "Chlore":
            chlore_current = float(hass.data[DOMAIN][entry.entry_id].get("chlore_current", 1.0))
            if treatment_form == "Liquide":
                chlore_change = quantity / (volume * 0.1)
            elif treatment_form == "Pastille lente":
                chlore_change = quantity * 20 / volume
            else:  # Chlore choc (poudre)
                chlore_change = quantity / (volume * 0.01)
            new_chlore = round(chlore_current + chlore_change, 1)
            hass.data[DOMAIN][entry.entry_id]["chlore_current"] = new_chlore
            await hass.services.async_call("input_number", "set_value", {
                "entity_id": f"input_number.{name}_chlore_current", "value": new_chlore
            })

        log_sensor = hass.data[DOMAIN].get("log")
        if log_sensor and name in getattr(log_sensor, "_name", ""):
            log_sensor.log_action(f"Traitement appliqué: {treatment_type} ({treatment_form}, {quantity})")

        await hass.config_entries.async_reload(entry.entry_id)

    hass.services.async_register(DOMAIN, "test_calcul", handle_test_calcul)
    hass.services.async_register(DOMAIN, "reset_valeurs", handle_reset_valeurs)
    hass.services.async_register(DOMAIN, "apply_treatment", handle_apply_treatment)

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "button"])

    from .input_number import async_setup_entry as input_number_setup
    await input_number_setup(hass, entry, None)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_unload_platforms(entry, ["sensor", "button"])
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True