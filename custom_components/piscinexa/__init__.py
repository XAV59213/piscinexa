"""Initialisation du composant Piscinexa."""
import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from .const import DOMAIN, POOL_TYPE_SQUARE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data.copy()

    if "chlore_target" not in hass.data[DOMAIN][entry.entry_id]:
        _LOGGER.warning("chlore_target manquant, définition par défaut: 2.0")
        hass.data[DOMAIN][entry.entry_id]["chlore_target"] = 2.0
    if "ph_target" not in hass.data[DOMAIN][entry.entry_id]:
        _LOGGER.warning("ph_target manquant, définition par défaut: 7.4")
        hass.data[DOMAIN][entry.entry_id]["ph_target"] = 7.4

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

        for entity_id in [f"input_number.{name}_chlore_current", f"input_number.{name}_ph_current"]:
            entity = hass.states.get(entity_id)
            if entity:
                if "chlore" in entity_id:
                    await hass.services.async_call(
                        "input_number", "set_value",
                        {"entity_id": entity_id, "value": 1.0}
                    )
                elif "ph" in entity_id:
                    await hass.services.async_call(
                        "input_number", "set_value",
                        {"entity_id": entity_id, "value": 7.0}
                    )

        log_sensor = hass.data[DOMAIN].get("log")
        if log_sensor and name in log_sensor._name:
            log_sensor.log_action("Valeurs réinitialisées")
        await hass.config_entries.async_reload(entry.entry_id)

    async def handle_apply_treatment(call: ServiceCall):
        name = call.data.get("name", hass.data[DOMAIN][entry.entry_id]["name"])
        treatment_type = call.data.get("treatment_type")
        treatment_form = call.data.get("treatment_form")
        quantity = float(call.data.get("quantity", 0.0))

        _LOGGER.info("Service apply_treatment appelé pour %s: %s, %s, %s", name, treatment_type, treatment_form, quantity)

        if treatment_type in ["pH+", "pH-"]:
            ph_current = float(hass.data[DOMAIN][entry.entry_id]["ph_current"])
            volume = float(hass.states.get(f"sensor.{DOMAIN}_{name}_volume_eau").state)
            if treatment_form == "Liquide":
                ph_change = quantity / (volume * (0.01 if treatment_type == "pH+" else 0.012))
            else:  # Granulés
                ph_change = quantity / (volume * (1.0 if treatment_type == "pH+" else 1.2))
            if treatment_type == "pH+":
                new_ph = ph_current + ph_change
            else:
                new_ph = ph_current - ph_change
            hass.data[DOMAIN][entry.entry_id]["ph_current"] = round(new_ph, 1)
            await hass.services.async_call(
                "input_number", "set_value",
                {"entity_id": f"input_number.{name}_ph_current", "value": new_ph}
            )
        elif treatment_type == "Chlore":
            chlore_current = float(hass.data[DOMAIN][entry.entry_id]["chlore_current"])
            volume = float(hass.states.get(f"sensor.{DOMAIN}_{name}_volume_eau").state)
            if treatment_form == "Liquide":
                chlore_change = quantity / (volume * 0.1)
            elif treatment_form == "Pastille lente":
                chlore_change = quantity * 20 / volume
            else:  # Chlore choc (poudre)
                chlore_change = quantity / (volume * 0.01)
            new_chlore = chlore_current + chlore_change
            hass.data[DOMAIN][entry.entry_id]["chlore_current"] = round(new_chlore, 1)
            await hass.services.async_call(
                "input_number", "set_value",
                {"entity_id": f"input_number.{name}_chlore_current", "value": new_chlore}
            )

        log_sensor = hass.data[DOMAIN].get("log")
        if log_sensor and name in log_sensor._name:
            log_sensor.log_action(f"Traitement appliqué: {treatment_type} ({treatment_form}, {quantity})")
        await hass.config_entries.async_reload(entry.entry_id)

    hass.services.async_register(DOMAIN, "test_calcul", handle_test_calcul)
    hass.services.async_register(DOMAIN, "reset_valeurs", handle_reset_valeurs)
    hass.services.async_register(DOMAIN, "apply_treatment", handle_apply_treatment)

    # Charger uniquement les plateformes sensor et button
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "button"])

    # Configurer manuellement les entités input_number et input_select
    from .input_number import async_setup_entry as input_number_setup
    await input_number_setup(hass, entry, None)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_unload_platforms(entry, ["sensor", "button"])
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
