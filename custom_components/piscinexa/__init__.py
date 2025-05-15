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

    # Charger les traductions de manière asynchrone
    lang = hass.config.language
    translation_file = os.path.join(os.path.dirname(__file__), "translations", f"{lang}.json")
    if not os.path.exists(translation_file):
        # Fallback sur l'anglais si le fichier de langue n'existe pas
        translation_file = os.path.join(os.path.dirname(__file__), "translations", "en.json")
        _LOGGER.warning(f"Fichier de traduction pour la langue {lang} non trouvé, utilisation de en.json")

    try:
        # Utilisation de run_in_executor pour exécuter l'opération de lecture de fichier de manière asynchrone
        def read_file(file_path):
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)

        translations = await hass.loop.run_in_executor(None, read_file, translation_file)
        hass.data[DOMAIN]["translations"] = translations
        _LOGGER.debug(f"Traductions chargées pour la langue {lang}: {translations}")
    except Exception as e:
        _LOGGER.error(f"Échec du chargement des traductions depuis {translation_file}: {e}")
        hass.data[DOMAIN]["translations"] = {}

    # Créer les entités input_number et input_select si elles n'existent pas
    input_numbers = [
        ("input_number.piscine_ph_current", {
            "name": "pH Actuel Piscine",
            "min": 0,
            "max": 14,
            "step": 0.1,
            "initial": 7.0
        }),
        ("input_number.piscine_ph_target", {
            "name": "pH Cible Piscine",
            "min": 0,
            "max": 14,
            "step": 0.1,
            "initial": 7.4
        }),
        ("input_number.piscine_chlore_current", {
            "name": "Chlore Actuel Piscine",
            "min": 0,
            "max": 10,
            "step": 0.1,
            "unit_of_measurement": "mg/L",
            "initial": 1.0
        }),
        ("input_number.piscine_chlore_target", {
            "name": "Chlore Cible Piscine",
            "min": 0,
            "max": 10,
            "step": 0.1,
            "unit_of_measurement": "mg/L",
            "initial": 2.0
        }),
        ("input_number.spa_ph_current", {
            "name": "pH Actuel Spa",
            "min": 0,
            "max": 14,
            "step": 0.1,
            "initial": 7.0
        }),
        ("input_number.spa_ph_target", {
            "name": "pH Cible Spa",
            "min": 0,
            "max": 14,
            "step": 0.1,
            "initial": 7.4
        }),
        ("input_number.spa_chlore_current", {
            "name": "Chlore Actuel Spa",
            "min": 0,
            "max": 10,
            "step": 0.1,
            "unit_of_measurement": "mg/L",
            "initial": 1.0
        }),
        ("input_number.spa_chlore_target", {
            "name": "Chlore Cible Spa",
            "min": 0,
            "max": 10,
            "step": 0.1,
            "unit_of_measurement": "mg/L",
            "initial": 2.0
        }),
        ("input_number.piscine_test_ph_current", {
            "name": "pH Actuel Piscine Test",
            "min": 0,
            "max": 14,
            "step": 0.1,
            "initial": 7.0
        }),
        ("input_number.piscine_test_ph_target", {
            "name": "pH Cible Piscine Test",
            "min": 0,
            "max": 14,
            "step": 0.1,
            "initial": 7.4
        }),
        ("input_number.piscine_test_chlore_current", {
            "name": "Chlore Actuel Piscine Test",
            "min": 0,
            "max": 10,
            "step": 0.1,
            "unit_of_measurement": "mg/L",
            "initial": 1.0
        }),
        ("input_number.piscine_test_chlore_target", {
            "name": "Chlore Cible Piscine Test",
            "min": 0,
            "max": 10,
            "step": 0.1,
            "unit_of_measurement": "mg/L",
            "initial": 2.0
        }),
    ]

    input_selects = [
        ("input_select.piscine_ph_plus_treatment", ["Liquide", "Poudre"]),
        ("input_select.piscine_ph_minus_treatment", ["Liquide", "Poudre"]),
        ("input_select.piscine_chlore_treatment", ["Liquide", "Pastille lente", "Chlore choc (poudre)"]),
        ("input_select.spa_ph_plus_treatment", ["Liquide", "Poudre"]),
        ("input_select.spa_ph_minus_treatment", ["Liquide", "Poudre"]),
        ("input_select.spa_chlore_treatment", ["Liquide", "Pastille lente", "Chlore choc (poudre)"]),
        ("input_select.piscine_test_ph_plus_treatment", ["Liquide", "Poudre"]),
        ("input_select.piscine_test_ph_minus_treatment", ["Liquide", "Poudre"]),
        ("input_select.piscine_test_chlore_treatment", ["Liquide", "Pastille lente", "Chlore choc (poudre)"]),
    ]

    for entity_id, attributes in input_numbers:
        if not hass.states.get(entity_id):
            hass.states.async_set(entity_id, attributes.get("initial", 0), attributes)
            _LOGGER.debug(f"Création de l'entité {entity_id} avec les attributs {attributes}")

    for entity_id, options in input_selects:
        if not hass.states.get(entity_id):
            hass.states.async_set(entity_id, options[0], {
                "options": options,
                "name": entity_id.split(".")[1].replace("_", " ").title()
            })
            _LOGGER.debug(f"Création de l'entité {entity_id} avec les options {options}")

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure une entrée Piscinexa."""
    hass.data[DOMAIN][entry.entry_id] = {"temperature": entry.data.get("temperature", 20.0)}

    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True
    except Exception as e:
        _LOGGER.error(
            hass.data[DOMAIN]["translations"].get(
                "platform_load_error",
                f"Error loading the Piscinexa platform: {e}"
            ),
            {"error": str(e)}
        )
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharge une entrée Piscinexa."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
