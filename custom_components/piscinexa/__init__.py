"""Intégration Piscinexa pour Home Assistant."""
import logging
from datetime import datetime
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.const import Platform
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.BUTTON, Platform.SENSOR, Platform.INPUT_NUMBER, Platform.INPUT_SELECT]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurer l'intégration Piscinexa via une entrée de configuration."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "ph_current": float(entry.data.get("ph_current", 7.0)),
        "ph_target": float(entry.data.get("ph_target", 7.4)),
        "chlore_current": float(entry.data.get("chlore_current", 1.0)),
        "chlore_target": float(entry.data.get("chlore_target", 2.0)),
        "temperature": float(entry.data.get("temperature", 20.0)),
    }

    # Enregistrer les services personnalisés
    async def handle_test_calcul(call: ServiceCall) -> None:
        """Service pour tester les calculs de Piscinexa."""
        entry_id = call.data.get("entry_id")
        if entry_id not in hass.data[DOMAIN]:
            _LOGGER.error("Entrée %s non trouvée pour le service test_calcul", entry_id)
            return

        log_sensor = hass.data[DOMAIN].get("log")
        if not log_sensor:
            _LOGGER.error("Capteur de journal non trouvé pour enregistrer les résultats")
            return

        # Récupérer les valeurs actuelles des capteurs et des entrées
        ph_current = hass.states.get(f"sensor.{DOMAIN}_{entry.data['name']}_ph")
        ph_target = hass.states.get(f"input_number.{entry.data['name']}_ph_target")
        chlore_current = hass.states.get(f"sensor.{DOMAIN}_{entry.data['name']}_chlore")
        chlore_difference = hass.states.get(f"sensor.{DOMAIN}_{entry.data['name']}_chlore_difference")
        volume = hass.states.get(f"sensor.{DOMAIN}_{entry.data['name']}_volume_eau")
        ph_plus_to_add = hass.states.get(f"sensor.{DOMAIN}_{entry.data['name']}_ph_plus_a_ajouter")
        ph_minus_to_add = hass.states.get(f"sensor.{DOMAIN}_{entry.data['name']}_ph_minus_a_ajouter")
        chlore_to_add = hass.states.get(f"sensor.{DOMAIN}_{entry.data['name']}_chlore_a_ajouter")
        filtration_time = hass.states.get(f"sensor.{DOMAIN}_{entry.data['name']}_temps_filtration")
        pool_state = hass.states.get(f"sensor.{DOMAIN}_{entry.data['name']}_pool_state")

        # Construire le message de journal avec plus de clarté
        log_message = []
        log_message.append(f"===== Rapport d'état de la piscine ({datetime.now()}) =====")
        log_message.append(f"Nom de la piscine: {entry.data['name'].capitalize()}")

        # Section Volume
        volume_value = volume.state if volume and volume.state != 'unavailable' else 'Indisponible'
        volume_error = volume.attributes.get('configuration_error', '') if volume and volume.state == 'unavailable' else ''
        log_message.append(f"Volume d'eau: {volume_value} m³{'' if not volume_error else f' (Erreur: {volume_error})'}")

        # Section pH
        log_message.append(f"--- État du pH ---")
        log_message.append(f"pH Actuel: {ph_current.state if ph_current and ph_current.state != 'unavailable' else 'Indisponible (vérifiez le capteur pH ou la configuration)'}")
        log_message.append(f"pH Cible: {ph_target.state if ph_target and ph_target.state != 'unavailable' else 'Indisponible'}")
        log_message.append(f"pH+ à ajouter: {ph_plus_to_add.state if ph_plus_to_add and ph_plus_to_add.state != 'unavailable' else '0'} L")
        log_message.append(f"pH- à ajouter: {ph_minus_to_add.state if ph_minus_to_add and ph_minus_to_add.state != 'unavailable' else '0'} L")

        # Section Chlore
        log_message.append(f"--- État du Chlore ---")
        log_message.append(f"Chlore Actuel: {chlore_current.state if chlore_current and chlore_current.state != 'unavailable' else 'Indisponible (vérifiez le capteur chlore ou la configuration)'} mg/L")
        log_message.append(f"Différence Chlore: {chlore_difference.state if chlore_difference and chlore_difference.state != 'unavailable' else 'Indisponible'} mg/L")
        log_message.append(f"Chlore à ajouter: {chlore_to_add.state if chlore_to_add and chlore_to_add.state != 'unavailable' else '0'} g")

        # Autres informations
        log_message.append(f"--- Autres informations ---")
        log_message.append(f"Temps de filtration recommandé: {filtration_time.state if filtration_time and filtration_time.state != 'unavailable' else 'Indisponible'} h")
        log_message.append(f"État global de la piscine: {pool_state.state if pool_state and pool_state.state != 'unavailable' else 'Indisponible'}")
        log_message.append(f"==========================================")

        # Enregistrer dans le capteur de journal
        log_sensor.log_action("\n".join(log_message))
        _LOGGER.info("Rapport d'état généré pour %s", entry.data["name"])

    async def handle_reset_valeurs(call: ServiceCall) -> None:
        """Service pour réinitialiser les valeurs de Piscinexa."""
        entry_id = call.data.get("entry_id")
        if entry_id not in hass.data[DOMAIN]:
            _LOGGER.error("Entrée %s non trouvée pour le service reset_valeurs", entry_id)
            return

        log_sensor = hass.data[DOMAIN].get("log")
        if not log_sensor:
            _LOGGER.error("Capteur de journal non trouvé pour enregistrer les résultats")
            return

        # Réinitialiser les valeurs
        hass.data[DOMAIN][entry_id]["ph_current"] = float(entry.data.get("ph_current", 7.0))
        hass.data[DOMAIN][entry_id]["ph_target"] = float(entry.data.get("ph_target", 7.4))
        hass.data[DOMAIN][entry_id]["chlore_current"] = float(entry.data.get("chlore_current", 1.0))
        hass.data[DOMAIN][entry_id]["chlore_target"] = float(entry.data.get("chlore_target", 2.0))
        hass.data[DOMAIN][entry_id]["temperature"] = float(entry.data.get("temperature", 20.0))

        # Mettre à jour les entités correspondantes
        ph_current_input = hass.states.get(f"input_number.{entry.data['name']}_ph_current")
        if ph_current_input:
            await hass.services.async_call(
                "input_number", "set_value",
                {"entity_id": f"input_number.{entry.data['name']}_ph_current", "value": hass.data[DOMAIN][entry_id]["ph_current"]}
            )

        ph_target_input = hass.states.get(f"input_number.{entry.data['name']}_ph_target")
        if ph_target_input:
            await hass.services.async_call(
                "input_number", "set_value",
                {"entity_id": f"input_number.{entry.data['name']}_ph_target", "value": hass.data[DOMAIN][entry_id]["ph_target"]}
            )

        chlore_current_input = hass.states.get(f"input_number.{entry.data['name']}_chlore_current")
        if chlore_current_input:
            await hass.services.async_call(
                "input_number", "set_value",
                {"entity_id": f"input_number.{entry.data['name']}_chlore_current", "value": hass.data[DOMAIN][entry_id]["chlore_current"]}
            )

        log_sensor.log_action(f"Réinitialisation des valeurs pour {entry.data['name']} effectuée à {datetime.now()}")
        _LOGGER.info("Valeurs réinitialisées pour %s", entry.data["name"])

    hass.services.async_register(DOMAIN, "test_calcul", handle_test_calcul)
    hass.services.async_register(DOMAIN, "reset_valeurs", handle_reset_valeurs)

    # Charger les plateformes (button, sensor, input_number, input_select)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharger l'intégration Piscinexa."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        hass.services.async_remove(DOMAIN, "test_calcul")
        hass.services.async_remove(DOMAIN, "reset_valeurs")
    return unload_ok