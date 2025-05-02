"""Capteurs pour Piscinexa."""
import logging
from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfVolume, UnitOfTime
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import (
    DOMAIN,
    POOL_TYPE_SQUARE,
    POOL_TYPE_ROUND,
    PI,
    UNIT_CUBIC_METERS,
    UNIT_HOURS,
    UNIT_LITERS,
    UNIT_GRAMS,
    UNIT_MG_PER_LITER,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure les capteurs Piscinexa."""
    log_sensor = PiscinexaLogSensor(hass, entry)
    hass.data[DOMAIN]["log"] = log_sensor  # Stocke pour accès par services
    name = entry.data["name"]
    sensors = [
        PiscinexaVolumeSensor(hass, entry, name),
        PiscinexaTempsFiltrationSensor(hass, entry, name),
        PiscinexaPhSensor(hass, entry, name),
        PiscinexaPhAjouterSensor(hass, entry, name),
        PiscinexaChloreSensor(hass, entry, name),
        PiscinexaChloreAjouterSensor(hass, entry, name),
        log_sensor,
    ]
    async_add_entities(sensors, True)

class PiscinexaVolumeSensor(SensorEntity):
    """Capteur pour le volume d'eau."""
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_volume_eau"
        self._attr_unit_of_measurement = UNIT_CUBIC_METERS
        self._attr_icon = "mdi:pool"
        self._attr_unique_id = f"{entry.entry_id}_volume_eau"

    @property
    def state(self):
        """Calcule le volume à partir des dimensions."""
        try:
            pool_type = self._hass.data[DOMAIN][self._entry.entry_id]["pool_type"]
            depth = float(self._hass.data[DOMAIN][self._entry.entry_id]["depth"])
            if pool_type == POOL_TYPE_SQUARE:
                length = float(self._hass.data[DOMAIN][self._entry.entry_id]["length"])
                width = float(self._hass.data[DOMAIN][self._entry.entry_id]["width"])
                if any(x <= 0 for x in [length, width, depth]):
                    _LOGGER.error("Dimensions invalides: %s, %s, %s", length, width, depth)
                    return None
                return round(length * width * depth, 2)
            else:  # POOL_TYPE_ROUND
                diameter = float(self._hass.data[DOMAIN][self._entry.entry_id]["diameter"])
                if diameter <= 0 or depth <= 0:
                    _LOGGER.error("Dimensions invalides: diamètre %s, profondeur %s", diameter, depth)
                    return None
                radius = diameter / 2
                return round(PI * radius * radius * depth, 2)
        except (KeyError, ValueError) as e:
            _LOGGER.error("Erreur calcul volume: %s", e)
            return None

class PiscinexaTempsFiltrationSensor(SensorEntity):
    """Capteur pour le temps de filtration recommandé."""
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_temps_filtration"
        self._attr_unit_of_measurement = UNIT_HOURS
        self._attr_icon = "mdi:clock"
        self._attr_unique_id = f"{entry.entry_id}_temps_filtration"

    @property
    def state(self):
        """Calcule le temps de filtration basé sur la température."""
        try:
            temperature = float(self._hass.data[DOMAIN][self._entry.entry_id]["temperature"])
            if temperature < 0 or temperature > 50:
                _LOGGER.error("Température invalide: %s", temperature)
                return None
            return round(temperature / 2, 1)
        except (KeyError, ValueError) as e:
            _LOGGER.error("Erreur calcul temps filtration: %s", e)
            return None

class PiscinexaPhSensor(SensorEntity):
    """Capteur pour le pH actuel."""
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_ph"
        self._attr_icon = "mdi:water-ph"
        self._attr_unique_id = f"{entry.entry_id}_ph"

    @property
    def state(self):
        """Retourne la valeur du pH."""
        try:
            ph = float(self._hass.data[DOMAIN][self._entry.entry_id]["ph_current"])
            if not 0 <= ph <= 14:
                _LOGGER.error("Valeur pH invalide: %s", ph)
                return None
            return round(ph, 1)
        except (KeyError, ValueError) as e:
            _LOGGER.error("Erreur lecture pH: %s", e)
            return None

class PiscinexaPhAjouterSensor(SensorEntity):
    """Capteur pour la dose de pH à ajouter."""
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_ph_a_ajouter"
        self._attr_unit_of_measurement = UNIT_LITERS
        self._attr_icon = "mdi:bottle-tonic-plus"
        self._attr_unique_id = f"{entry.entry_id}_ph_a_ajouter"

    @property
    def state(self):
        """Calcule la dose de pH à ajouter."""
        try:
            ph_current = float(self._hass.data[DOMAIN][self._entry.entry_id]["ph_current"])
            ph_target = float(self._hass.data[DOMAIN][self._entry.entry_id]["ph_target"])
            volume = float(self.state_volume)
            if not 0 <= ph_current <= 14 or not 0 <= ph_target <= 14:
                _LOGGER.error("Valeurs pH invalides: %s, %s", ph_current, ph_target)
                return None
            if volume is None:
                _LOGGER.error("Volume non disponible")
                return None
            delta_ph = ph_target - ph_current
            dose = abs(delta_ph) * volume * 10
            return round(dose, 2)
        except (KeyError, ValueError) as e:
            _LOGGER.error("Erreur calcul dose pH: %s", e)
            return None

    @property
    def state_volume(self):
        """Récupère le volume."""
        return self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau").state

class PiscinexaChloreSensor(SensorEntity):
    """Capteur pour le chlore actuel."""
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_chlore"
        self._attr_unit_of_measurement = UNIT_MG_PER_LITER
        self._attr_icon = "mdi:water-check"
        self._attr_unique_id = f"{entry.entry_id}_chlore"

    @property
    def state(self):
        """Retourne la valeur du chlore."""
        try:
            chlore = float(self._hass.data[DOMAIN][self._entry.entry_id]["chlore_current"])
            if chlore < 0:
                _LOGGER.error("Valeur chlore invalide: %s", chlore)
                return None
            return round(chlore, 1)
        except (KeyError, ValueError) as e:
            _LOGGER.error("Erreur lecture chlore: %s", e)
            return None

class PiscinexaChloreAjouterSensor(SensorEntity):
    """Capteur pour la dose de chlore à ajouter."""
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_chlore_a_ajouter"
        self._attr_unit_of_measurement = UNIT_GRAMS
        self._attr_icon = "mdi:bottle-tonic-plus"
        self._attr_unique_id = f"{entry.entry_id}_chlore_a_ajouter"

    @property
    def state(self):
        """Calcule la dose de chlore à ajouter."""
        try:
            chlore_current = float(self._hass.data[DOMAIN][self._entry.entry_id]["chlore_current"])
            chlore_target = float(self._hass.data[DOMAIN][self._entry.entry_id]["chlore_target"])
            volume = float(self.state_volume)
            if chlore_current < 0 or chlore_target < 0:
                _LOGGER.error("Valeurs chlore invalides: %s, %s", chlore_current, chlore_target)
                return None
            if volume is None:
                _LOGGER.error("Volume non disponible")
                return None
            delta_chlore = chlore_target - chlore_current
            dose = delta_chlore * volume * 10
            return round(dose, 2) if dose > 0 else 0
        except (KeyError, ValueError) as e:
            _LOGGER.error("Erreur calcul dose chlore: %s", e)
            return None

    @property
    def state_volume(self):
        """Récupère le volume."""
        return self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau").state

class PiscinexaLogSensor(SensorEntity):
    """Capteur pour le journal des actions."""
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self._hass = hass
        self._entry = entry
        self._name = entry.data["name"]
        self._attr_name = f"{DOMAIN}_{self._name}_log"
        self._attr_icon = "mdi:notebook"
        self._attr_unique_id = f"{entry.entry_id}_log"
        self._state = []

    def log_action(self, action: str):
        """Ajoute une entrée au journal."""
        self._state.append(f"{datetime.now()}: {action}")
        if len(self._state) > 10:
            self._state.pop(0)
        self.async_write_ha_state()

    @property
    def state(self):
        """Retourne le journal."""
        return "\n".join(self._state) if self._state else "Aucune action enregistrée"
