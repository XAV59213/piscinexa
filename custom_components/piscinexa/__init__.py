"""Intégration Piscinexa pour Home Assistant."""
import json
import logging
import os
from functools import partial

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

DOMAIN = "piscinexa"
VERSION = "1.0.0"

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BUTTON]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Configure l'intégration Piscinexa."""
    hass.data.setdefault(DOMAIN, {})

    # === CHARGEMENT DES TRADUCTIONS ===
    lang = hass.config.language
    translation_file = os.path.join(os.path.dirname(__file__), "translations", f"{lang}.json")
    if not os.path.exists(translation_file):
        translation_file = os.path.join(os.path.dirname(__file__), "translations", "en.json")
        _LOGGER.warning(f"Fichier de traduction {lang} non trouvé → fallback en.json")

    try:
        def read_file(file_path):
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)

        translations = await hass.loop.run_in_executor(None, read_file, translation_file)
        hass.data[DOMAIN]["translations"] = translations
        _LOGGER.debug(f"Traductions chargées pour {lang}")
    except Exception as e:
        _LOGGER.error(f"Échec du chargement des traductions : {e}")
        hass.data[DOMAIN]["translations"] = {}

    # === INPUT_NUMBERS (inchangés) ===
    input_numbers = [
        ("input_number.piscine_ph_current", {
            "name": "pH Actuel Piscine",
            "min": 0, "max": 14, "step": 0.1, "initial": 7.0
        }),
        ("input_number.piscine_ph_target", {
            "name": "pH Cible Piscine",
            "min": 0, "max": 14, "step": 0.1, "initial": 7.4
        }),
        ("input_number.piscine_chlore_current", {
            "name": "Chlore Actuel Piscine",
            "min": 0, "max": 10, "step": 0.1,
            "unit_of_measurement": "mg/L", "initial": 1.0
        }),
        ("input_number.piscine_chlore_target", {
            "name": "Chlore Cible Piscine",
            "min": 0, "max": 10, "step": 0.1,
            "unit_of_measurement": "mg/L", "initial": 2.0
        }),
        ("input_number.spa_ph_current", {
            "name": "pH Actuel Spa",
            "min": 0, "max": 14, "step": 0.1, "initial": 7.0
        }),
        ("input_number.spa_ph_target", {
            "name": "pH Cible Spa",
            "min": 0, "max": 14, "step": 0.1, "initial": 7.4
        }),
        ("input_number.spa_chlore_current", {
            "name": "Chlore Actuel Spa",
            "min": 0, "max": 10, "step": 0.1,
            "unit_of_measurement": "mg/L", "initial": 1.0
        }),
        ("input_number.spa_chlore_target", {
            "name": "Chlore Cible Spa",
            "min": 0, "max": 10, "step": 0.1,
            "unit_of_measurement": "mg/L", "initial": 2.0
        }),
        ("input_number.piscine_test_ph_current", {
            "name": "pH Actuel Piscine Test",
            "min": 0, "max": 14, "step": 0.1, "initial": 7.0
        }),
        ("input_number.piscine_test_ph_target", {
            "name": "pH Cible Piscine Test",
            "min": 0, "max": 14, "step": 0.1, "initial": 7.4
        }),
        ("input_number.piscine_test_chlore_current", {
            "name": "Chlore Actuel Piscine Test",
            "min": 0, "max": 10, "step": 0.1,
            'unit_of_measurement': "mg/L", "initial": 1.0
        }),
        ("input_number.piscine_test_chlore_target", {
            "name": "Chlore Cible Piscine Test",
            "min": 0, "max": 10, "step": 0.1,
            'unit_of_measurement': "mg/L", "initial": 2.0
        }),
    ]

    # === INPUT_SELECTS (NOUVEAU MODE UNIQUE) ===
    input_selects = [
        ("input_select.piscine_ph_plus_treatment", ["Liquide", "Poudre"]),
        ("input_select.piscine_ph_minus_treatment", ["Liquide", "Poudre"]),
        ("input_select.piscine_chlore_treatment", ["Liquide", "Pastille lente", "Chlore choc (poudre)"]),
        ("191input_select.spa_ph_plus_treatment", ["Liquide", "Poudre"]),
        ("input_select.spa_ph_minus_treatment", ["Liquide", "Poudre"]),
        ("input_select.spa_chlore_treatment", ["Liquide", "Pastille lente", "Chlore choc (poudre)"]),
        ("input_select.piscine_test_ph_plus_treatment", ["Liquide", "Poudre"]),
        ("input_select.piscine_test_ph_minus_treatment", ["Liquide", "Poudre"]),
        ("input_select.piscine_test_chlore_treatment", ["Liquide", "Pastille lente", "Chlore choc (poudre)"]),
        # === MODE PISCINE UNIQUE ===
        ("input_select.piscinexa_mode", {
            "name": "Mode Piscine",
            "options": ["Automatique", "On", "Off"],
            "initial": "Automatique",
            "icon": "mdi:pool"
        }),
    ]

    # === CRÉATION DES ENTITÉS ===
    for entity_id, attributes in input_numbers:
        if not hass.states.get(entity_id):
            hass.states.async_set(
                entity_id,
                attributes.get("initial", 0),
                {k: v for k, v in attributes.items() if k != "initial"}
            )
            _LOGGER.debug(f"Création input_number : {entity_id}")

    for entity_id, config in input_selects:
        if not hass.states.get(entity_id):
            if isinstance(config, list):
                # Ancien format : liste d'options
                hass.states.async_set(
                    entity_id,
                    config[0],
                    {
                        "options": config,
                        "name": entity_id.split(".")[1].replace("_", " ").title()
                    }
                )
            else:
                # Nouveau format : dict complet
                hass.states.async_set(
                    entity_id,
                    config["initial"],
                    {k: v for k, v in config.items() if k != "initial"}
                )
            _LOGGER.debug(f"Création input_select : {entity_id}")

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure une entrée Piscinexa."""
    hass.data[DOMAIN][entry.entry_id] = {
        "temperature": entry.data.get("temperature", 20.0),
        "pumping_calendar": entry.data.get("pumping_calendar"),
        "pump_power": entry.data.get("pump_power", 1.5),
        "filtration_hours_summer": entry.data.get("filtration_hours_summer", 12),
        "filtration_hours_winter": entry.data.get("filtration_hours_winter", 2),
    }

    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.info(f"Intégration Piscinexa chargée pour {entry.title}")
        return True
    except Exception as e:
        _LOGGER.error(f"Erreur lors du chargement des plateformes : {e}")
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharge une entrée Piscinexa."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        _LOGGER.info(f"Intégration Piscinexa déchargée")
    return unload_ok
