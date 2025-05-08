"""Initialisation du composant Piscinexa."""
import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.exceptions import ConfigEntryNotReady
from .const import DOMAIN, POOL_TYPE_SQUARE

_LOGGER = logging.getLogger(__name__)

# Liste des plateformes à charger
PLATFORMS = ["sensor", "button"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurez une entrée de configuration pour Piscinexa."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data.copy()

    # Vérification et définition des valeurs par défaut pour chlore_target et ph_target
    if "chlore_target" not in hass.data[DOMAIN][entry.entry_id]:
        _LOGGER.warning(hass.helpers.template.render(
            "logs.chlore_target_missing",
            {"default_value": "2.0"}
        ))
        hass.data[DOMAIN][entry.entry_id]["chlore_target"] = 2.0
    if "ph_target" not in hass.data[DOMAIN][entry.entry_id]:
        _LOGGER.warning(hass.helpers.template.render(
            "logs.ph_target_missing",
            {"default_value": "7.4"}
        ))
        hass.data[DOMAIN][entry.entry_id]["ph_target"] = 7.4

    async def handle_test_calcul(call: ServiceCall):
        name = hass.data[DOMAIN][entry.entry_id]["name"]
        _LOGGER.info(hass.helpers.template.render(
            "logs.test_calcul_called",
            {"name": name}
        ))
        log_sensor = hass.data[DOMAIN].get("log")
        if log_sensor and name in log_sensor._name:
            log_sensor.log_action(hass.helpers.template.render(
                "logs.test_calcul_action",
                {}
            ))

    async def handle_reset_valeurs(call: ServiceCall):
        name = hass.data[DOMAIN][entry.entry_id]["name"]
        _LOGGER.info(hass.helpers.template.render(
            "logs.reset_valeurs_called",
            {"name": name}
        ))
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
                "length": float(entry.data.get("length", 5.0)),
                "width": float(entry.data.get("width", 4.0)),
                "depth": float(entry.data.get("depth", 1.5))
            })
        else:
            data.update({
                "diameter": float(entry.data.get("diameter", 4.0)),
                "depth": float(entry.data.get("depth", 1.5))
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
            log_sensor.log_action(hass.helpers.template.render(
                "logs.reset_valeurs_action",
                {}
            ))
        await hass.config_entries.async_reload(entry.entry_id)

    async def handle_apply_treatment(call: ServiceCall):
        name = call.data.get("name", hass.data[DOMAIN][entry.entry_id]["name"])
        treatment_type = call.data.get("treatment_type")  # pH+, pH-, Chlore
        treatment_form = call.data.get("treatment_form")  # Liquide, Granulés, etc.
        quantity = float(call.data.get("quantity", 0.0))

        _LOGGER.info(hass.helpers.template.render(
            "logs.apply_treatment_called",
            {"name": name, "treatment_type": treatment_type, "treatment_form": treatment_form, "quantity": str(quantity)}
        ))

        # Mettre à jour les capteurs en fonction du traitement
        if treatment_type in ["pH+", "pH-"]:
            ph_current = float(hass.data[DOMAIN][entry.entry_id]["ph_current"])
            volume = float(hass.states.get(f"sensor.{DOMAIN}_{name}_volume_eau").state)
            # Facteurs de conversion (hypothétiques, ajuster selon produits réels)
            if treatment_form == "Liquide":
                ph_change = quantity / (volume * 10)  # 10 L par unité de pH par m³
            else:  # Granulés
                ph_change = quantity / (volume * 100)  # 100 g par unité de pH par m³
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
                chlore_change = quantity / (volume * 10)  # 10 L par mg/L par m³
            elif treatment_form == "Pastille lente":
                chlore_change = quantity / (volume * 0.5)  # 0.5 unité par mg/L par m³
            else:  # Chlore choc (poudre)
                chlore_change = quantity / (volume * 10)  # 10 g par mg/L par m³
            new_chlore = chlore_current + chlore_change
            hass.data[DOMAIN][entry.entry_id]["chlore_current"] = round(new_chlore, 1)
            await hass.services.async_call(
                "input_number", "set_value",
                {"entity_id": f"input_number.{name}_chlore_current", "value": new_chlore}
            )

        log_sensor = hass.data[DOMAIN].get("log")
        if log_sensor and name in log_sensor._name:
            log_sensor.log_action(hass.helpers.template.render(
                "logs.apply_treatment_action",
                {"treatment_type": treatment_type, "treatment_form": treatment_form, "quantity": str(quantity)}
            ))
        await hass.config_entries.async_reload(entry.entry_id)

    # Enregistrement des services avec descriptions traduites
    hass.services.async_register(DOMAIN, "test_calcul", handle_test_calcul)
    hass.services.async_register(DOMAIN, "reset_valeurs", handle_reset_valeurs)
    hass.services.async_register(DOMAIN, "apply_treatment", handle_apply_treatment)

    # Chargement des plateformes
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception as e:
        _LOGGER.error(hass.helpers.template.render(
            "logs.platform_load_error",
            {"error": str(e)}
        ))
        raise ConfigEntryNotReady from e

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Déchargez une entrée de configuration pour Piscinexa."""
    # Décharger les plateformes
    try:
        await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    except Exception as e:
        _LOGGER.error(hass.helpers.template.render(
            "logs.platform_unload_error",
            {"error": str(e)}
        ))
        return False

    # Nettoyer les données globales
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
