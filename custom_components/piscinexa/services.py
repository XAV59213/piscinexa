"""Actions (services) de l'intégration Piscinexa.

Enregistrées une seule fois dans ``async_setup`` :
- ``piscinexa.test_calcul`` : relance tous les calculs de la piscine ;
- ``piscinexa.reset_valeurs`` : remet le pH et le chlore actuels aux valeurs saisies
  lors de la configuration (ou 7.0 / 1.0) et la température à celle de la configuration ;
- ``piscinexa.apply_treatment`` : estime le nouveau pH ou chlore après l'ajout d'un produit.
"""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, callback, valid_entity_id
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.entity_component import async_update_entity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_TEST_CALCUL = "test_calcul"
SERVICE_RESET_VALEURS = "reset_valeurs"
SERVICE_APPLY_TREATMENT = "apply_treatment"

ATTR_NAME = "name"
ATTR_TREATMENT_TYPE = "treatment_type"
ATTR_TREATMENT_FORM = "treatment_form"
ATTR_QUANTITY = "quantity"

TREATMENT_TYPES = ["pH+", "pH-", "Chlore"]
TREATMENT_FORMS = ["Liquide", "Granulés", "Poudre", "Pastille lente", "Chlore choc (poudre)"]

# Valeurs par défaut identiques à celles du flux de configuration / des capteurs
DEFAULTS = {"ph_current": 7.0, "chlore_current": 1.0, "temperature": 20.0}

# Attributs des entrées input_number gérées par l'intégration (comme dans async_setup)
INPUT_ATTRIBUTES = {
    "ph_current": {"label": "pH Actuel", "min": 0, "max": 14, "step": 0.1},
    "chlore_current": {"label": "Chlore Actuel", "min": 0, "max": 10, "step": 0.1, "unit_of_measurement": "mg/L"},
}
SENSOR_KEYS = {"ph_current": "ph_sensor", "chlore_current": "chlore_sensor"}

POOL_SCHEMA = vol.Schema({vol.Optional(ATTR_NAME): cv.string})
APPLY_TREATMENT_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_NAME): cv.string,
        vol.Required(ATTR_TREATMENT_TYPE): vol.In(TREATMENT_TYPES),
        vol.Required(ATTR_TREATMENT_FORM): cv.string,
        vol.Required(ATTR_QUANTITY): vol.All(vol.Coerce(float), vol.Range(min=0, min_included=False)),
    }
)


def _loaded_entries(hass: HomeAssistant) -> list[ConfigEntry]:
    return [e for e in hass.config_entries.async_entries(DOMAIN) if e.state is ConfigEntryState.LOADED]


def _resolve_entry(hass: HomeAssistant, call: ServiceCall) -> ConfigEntry:
    """Trouve la piscine visée : par son nom, ou la seule piscine configurée."""
    entries = _loaded_entries(hass)
    name = call.data.get(ATTR_NAME)
    if name:
        wanted = name.strip().casefold()
        for entry in entries:
            if str(entry.data.get("name", "")).strip().casefold() == wanted:
                return entry
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="pool_not_found",
            translation_placeholders={"name": name},
        )
    if len(entries) == 1:
        return entries[0]
    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="pool_name_required" if entries else "no_pool",
    )


async def _async_refresh(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Recalcule toutes les entités de la piscine."""
    registry = er.async_get(hass)
    for reg_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if hass.states.get(reg_entry.entity_id) is not None:
            await async_update_entity(hass, reg_entry.entity_id)


def _input_id(entry: ConfigEntry, key: str) -> str:
    return f"input_number.{entry.data.get('name')}_{key}"


@callback
def _set_input(hass: HomeAssistant, entry: ConfigEntry, key: str, value: float, create: bool) -> bool:
    """Met à jour l'entrée input_number lue par les capteurs (pH / chlore actuels)."""
    entity_id = _input_id(entry, key)
    if not valid_entity_id(entity_id):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_pool_name",
            translation_placeholders={"name": str(entry.data.get("name"))},
        )
    state = hass.states.get(entity_id)
    if state is None and not create:
        return False
    if state is not None:
        attributes = dict(state.attributes)
    else:
        spec = INPUT_ATTRIBUTES[key]
        attributes = {k: v for k, v in spec.items() if k != "label"}
        attributes["friendly_name"] = f"{str(entry.data.get('name')).capitalize()} {spec['label']}"
    hass.states.async_set(entity_id, round(value, 1), attributes)
    hass.data[DOMAIN][entry.entry_id][key] = round(value, 1)
    return True


def _current_value(hass: HomeAssistant, entry: ConfigEntry, key: str) -> float:
    state = hass.states.get(_input_id(entry, key))
    if state is not None:
        try:
            return float(state.state)
        except (TypeError, ValueError):
            pass
    try:
        return float(entry.data.get(key, DEFAULTS[key]))
    except (TypeError, ValueError):
        return DEFAULTS[key]


def _pool_volume(hass: HomeAssistant, entry: ConfigEntry) -> float:
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_volume_eau")
    state = hass.states.get(entity_id) if entity_id else None
    try:
        volume = float(state.state) if state is not None else 0.0
    except (TypeError, ValueError):
        volume = 0.0
    if volume <= 0:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="volume_unavailable",
            translation_placeholders={"name": str(entry.data.get("name"))},
        )
    return volume


async def _async_test_calcul(hass: HomeAssistant, call: ServiceCall) -> None:
    entry = _resolve_entry(hass, call)
    _LOGGER.info(
        hass.data[DOMAIN].get("translations", {}).get(
            "test_calcul_called", "Service test_calcul called for pool {name}"
        ).format(name=entry.data.get("name"))
    )
    await _async_refresh(hass, entry)


async def _async_reset_valeurs(hass: HomeAssistant, call: ServiceCall) -> None:
    entry = _resolve_entry(hass, call)
    for key in ("ph_current", "chlore_current"):
        if entry.data.get(SENSOR_KEYS[key]):
            continue  # valeur mesurée par un capteur : rien à réinitialiser
        try:
            value = float(entry.data.get(key, DEFAULTS[key]))
        except (TypeError, ValueError):
            value = DEFAULTS[key]
        _set_input(hass, entry, key, value, create=False)
        hass.data[DOMAIN][entry.entry_id][key] = value
    try:
        temperature = float(entry.data.get("temperature", DEFAULTS["temperature"]))
    except (TypeError, ValueError):
        temperature = DEFAULTS["temperature"]
    hass.data[DOMAIN][entry.entry_id]["temperature"] = temperature
    _LOGGER.info("Piscinexa : valeurs de la piscine %s réinitialisées", entry.data.get("name"))
    await _async_refresh(hass, entry)


async def _async_apply_treatment(hass: HomeAssistant, call: ServiceCall) -> None:
    entry = _resolve_entry(hass, call)
    treatment_type = call.data[ATTR_TREATMENT_TYPE]
    treatment_form = call.data[ATTR_TREATMENT_FORM]
    quantity = call.data[ATTR_QUANTITY]
    key = "chlore_current" if treatment_type == "Chlore" else "ph_current"
    if entry.data.get(SENSOR_KEYS[key]):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="value_measured_by_sensor",
            translation_placeholders={"sensor": str(entry.data.get(SENSOR_KEYS[key]))},
        )
    volume = _pool_volume(hass, entry)
    current = _current_value(hass, entry, key)
    liquid = treatment_form.casefold() == "liquide"
    # Formules historiques de Piscinexa (version 1.0.x)
    if key == "ph_current":
        change = quantity / (volume * (10 if liquid else 100))
        new_value = current + change if treatment_type == "pH+" else current - change
        new_value = min(max(new_value, 0.0), 14.0)
    else:
        divisor = 0.5 if treatment_form.casefold() == "pastille lente" else 10
        new_value = max(current + quantity / (volume * divisor), 0.0)
    _set_input(hass, entry, key, new_value, create=True)
    _LOGGER.info(
        "Piscinexa : traitement %s (%s, %s) appliqué à %s : %s %s → %s",
        treatment_type, treatment_form, quantity, entry.data.get("name"), key, current, round(new_value, 1),
    )
    await _async_refresh(hass, entry)


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Enregistre les actions Piscinexa (une seule fois)."""
    if hass.services.has_service(DOMAIN, SERVICE_TEST_CALCUL):
        return

    async def test_calcul(call: ServiceCall) -> None:
        await _async_test_calcul(hass, call)

    async def reset_valeurs(call: ServiceCall) -> None:
        await _async_reset_valeurs(hass, call)

    async def apply_treatment(call: ServiceCall) -> None:
        await _async_apply_treatment(hass, call)

    hass.services.async_register(DOMAIN, SERVICE_TEST_CALCUL, test_calcul, schema=POOL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_RESET_VALEURS, reset_valeurs, schema=POOL_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_APPLY_TREATMENT, apply_treatment, schema=APPLY_TREATMENT_SCHEMA)
