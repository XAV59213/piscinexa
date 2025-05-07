# Fichier sensor.py optimisé pour l'intégration Piscinexa
import logging
from datetime import datetime
from collections import deque

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DOMAIN,
    PI,
    POOL_TYPE_SQUARE,
    UNIT_CUBIC_METERS,
    UNIT_HOURS,
    UNIT_LITERS,
    UNIT_GRAMS,
    UNIT_MG_PER_LITER
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    name = entry.data["name"]
    sensors = [
        PiscinexaVolumeSensor(hass, entry),
        PiscinexaTempsFiltrationSensor(hass, entry),
        PiscinexaTemperatureSensor(hass, entry),
        PiscinexaPhSensor(hass, entry),
        PiscinexaChloreSensor(hass, entry),
        PiscinexaPhAjouterSensor(hass, entry),
        PiscinexaPhPlusAjouterSensor(hass, entry),
        PiscinexaPhMinusAjouterSensor(hass, entry),
        PiscinexaChloreAjouterSensor(hass, entry),
        PiscinexaChloreDifferenceSensor(hass, entry),
        PiscinexaPoolStateSensor(hass, entry),
        PiscinexaPowerSensor(hass, entry),
    ]
    log_sensor = PiscinexaLogSensor(hass, entry)
    hass.data[DOMAIN]["log"] = log_sensor
    sensors.append(log_sensor)
    async_add_entities(sensors, True)

class PiscinexaBaseSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str, sensor_type: str, unit=None, icon=None):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_{sensor_type}"
        self._attr_friendly_name = f"{name.capitalize()} {sensor_type.replace('_', ' ').capitalize()}"
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )

    @property
    def name(self):
        return self._attr_friendly_name

class PiscinexaVolumeSensor(PiscinexaBaseSensor):
    def __init__(self, hass, entry):
        super().__init__(hass, entry, entry.data["name"], "volume_eau", UNIT_CUBIC_METERS, "mdi:pool")

    @property
    def native_value(self):
        try:
            data = self._entry.data
            depth = float(data["depth"])
            if data["pool_type"] == POOL_TYPE_SQUARE:
                volume = float(data["length"]) * float(data["width"]) * depth
            else:
                radius = float(data["diameter"]) / 2
                volume = PI * radius * radius * depth
            return round(volume, 2)
        except Exception as e:
            _LOGGER.error("Erreur calcul volume pour %s: %s", self._name, e)
            return None

class PiscinexaTempsFiltrationSensor(PiscinexaBaseSensor):
    def __init__(self, hass, entry):
        super().__init__(hass, entry, entry.data["name"], "tempsfiltration", UNIT_HOURS, "mdi:clock")

    @property
    def native_value(self):
        try:
            temperature = float(self._hass.data[DOMAIN][self._entry.entry_id].get("temperature", 20.0))
            filtration_time = max(8, min(24, temperature / 2))
            return round(filtration_time, 1)
        except Exception as e:
            _LOGGER.error("Erreur calcul temps de filtration pour %s: %s", self._name, e)
            return None

class PiscinexaLogSensor(PiscinexaBaseSensor):
    def __init__(self, hass, entry):
        super().__init__(hass, entry, entry.data["name"], "log", None, "mdi:book")
        self._state = deque(maxlen=10)

    def log_action(self, action: str):
        self._state.append(f"{datetime.now()}: {action}")
        self.async_write_ha_state()

    @property
    def native_value(self):
        return "\n".join(self._state) if self._state else "Aucune action"

class PiscinexaTemperatureSensor(PiscinexaBaseSensor):
    def __init__(self, hass, entry):
        super().__init__(hass, entry, entry.data["name"], "temperature", "°C", "mdi:thermometer")
        self._sensor_id = entry.data.get("temperature_sensor")

    @property
    def native_value(self):
        try:
            if self._sensor_id:
                state = self._hass.states.get(self._sensor_id)
                if state and state.state not in ("unknown", "unavailable"):
                    temp = float(state.state)
                    if state.attributes.get("unit_of_measurement", "").lower() in ("°f", "f", "fahrenheit"):
                        temp = (temp - 32) * 5 / 9
                    self._hass.data[DOMAIN][self._entry.entry_id]["temperature"] = round(temp, 1)
                    return round(temp, 1)
            return float(self._entry.data.get("temperature", 20.0))
        except Exception as e:
            _LOGGER.error("Erreur lecture température : %s", e)
            return None

class PiscinexaPhSensor(PiscinexaBaseSensor):
    def __init__(self, hass, entry):
        super().__init__(hass, entry, entry.data["name"], "ph", "pH", "mdi:water")
        self._sensor_id = entry.data.get("ph_sensor")

    @property
    def native_value(self):
        try:
            if self._sensor_id:
                state = self._hass.states.get(self._sensor_id)
                if state and state.state not in ("unknown", "unavailable"):
                    ph = round(float(state.state), 1)
                    self._hass.data[DOMAIN][self._entry.entry_id]["ph_current"] = ph
                    return ph
            return float(self._entry.data.get("ph_current", 7.0))
        except Exception as e:
            _LOGGER.error("Erreur lecture pH : %s", e)
            return None

class PiscinexaChloreSensor(PiscinexaBaseSensor):
    def __init__(self, hass, entry):
        super().__init__(hass, entry, entry.data["name"], "chlore", UNIT_MG_PER_LITER, "mdi:water-check")
        self._sensor_id = entry.data.get("chlore_sensor")

    @property
    def native_value(self):
        try:
            if self._sensor_id:
                state = self._hass.states.get(self._sensor_id)
                if state and state.state not in ("unknown", "unavailable"):
                    chlore = round(float(state.state), 1)
                    self._hass.data[DOMAIN][self._entry.entry_id]["chlore_current"] = chlore
                    return chlore
            return float(self._entry.data.get("chlore_current", 1.0))
        except Exception as e:
            _LOGGER.error("Erreur lecture chlore : %s", e)
            return None

class PiscinexaChloreDifferenceSensor(PiscinexaBaseSensor):
    def __init__(self, hass, entry):
        super().__init__(hass, entry, entry.data["name"], "chlore_difference", UNIT_MG_PER_LITER, "mdi:delta")

    @property
    def native_value(self):
        try:
            current = float(self._hass.data[DOMAIN][self._entry.entry_id].get("chlore_current", 1.0))
            target = float(self._hass.data[DOMAIN][self._entry.entry_id].get("chlore_target", 2.0))
            return round(target - current, 1)
        except Exception as e:
            _LOGGER.error("Erreur différence chlore : %s", e)
            return None

class PiscinexaPowerSensor(PiscinexaBaseSensor):
    def __init__(self, hass, entry):
        super().__init__(hass, entry, entry.data["name"], "consopuissance", "W", "mdi:flash")
        self._sensor_id = entry.data.get("power_sensor_entity_id")

    @property
    def native_value(self):
        try:
            if self._sensor_id:
                state = self._hass.states.get(self._sensor_id)
                if state and state.state not in ("unknown", "unavailable"):
                    return round(float(state.state), 2)
            return None
        except Exception as e:
            _LOGGER.warning("Erreur lecture puissance : %s", e)
            return None

class PiscinexaPoolStateSensor(PiscinexaBaseSensor):
    def __init__(self, hass, entry):
        super().__init__(hass, entry, entry.data["name"], "pool_state", None, "mdi:pool")

    @property
    def native_value(self):
        try:
            data = self._hass.data[DOMAIN][self._entry.entry_id]
            temperature = data.get("temperature", 20.0)
            chlore = data.get("chlore_current", 1.0)
            ph = data.get("ph_current", 7.0)

            status = []
            if 22 <= temperature <= 28:
                status.append("Température idéale")
            elif temperature < 22:
                status.append("Trop froide")
            else:
                status.append("Trop chaude")

            if 1 <= chlore <= 3:
                status.append("Chlore idéal")
            elif chlore < 1:
                status.append("Chlore bas")
            else:
                status.append("Chlore haut")

            if 7.2 <= ph <= 7.6:
                status.append("pH idéal")
            elif ph < 7.2:
                status.append("pH bas")
            else:
                status.append("pH haut")

            if all("idéal" in s for s in status):
                return "Baignade autorisée"
            return ", ".join(status)
        except Exception as e:
            _LOGGER.error("Erreur évaluation état piscine : %s", e)
            return "Indisponible"

class PiscinexaPhAjouterSensor(PiscinexaBaseSensor):
    def __init__(self, hass, entry):
        super().__init__(hass, entry, entry.data["name"], "phaajouter", UNIT_LITERS, "mdi:water-plus")
        self._attr_extra_state_attributes = {"treatment_direction": ""}

    @property
    def native_value(self):
        try:
            data = self._hass.data[DOMAIN][self._entry.entry_id]
            current_ph = float(data.get("ph_current", 7.0))
            target_ph = float(data.get("ph_target", 7.4))
            volume_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if not volume_entity or volume_entity.state in ("unknown", "unavailable"):
                _LOGGER.error("Capteur de volume indisponible pour %s", self._name)
                return 0

            volume = float(volume_entity.state)
            delta_ph = target_ph - current_ph
            treatment_form = data.get("ph_plus_treatment" if delta_ph > 0 else "ph_minus_treatment", "Liquide")
            self._attr_extra_state_attributes["treatment_direction"] = "pH+" if delta_ph > 0 else "pH-" if delta_ph < 0 else "Aucun ajustement"

            if delta_ph == 0:
                return 0

            if treatment_form == "Liquide":
                factor = 0.01 if delta_ph > 0 else 0.012
                quantity = abs(delta_ph) * volume * factor
            else:  # Granulés
                factor = 1.0 if delta_ph > 0 else 1.2
                quantity = abs(delta_ph) * volume * factor

            return round(quantity, 2)
        except Exception as e:
            _LOGGER.error("Erreur calcul pH à ajouter pour %s: %s", self._name, e)
            return 0

class PiscinexaPhPlusAjouterSensor(PiscinexaBaseSensor):
    def __init__(self, hass, entry):
        super().__init__(hass, entry, entry.data["name"], "phplusaajouter", UNIT_LITERS, "mdi:water-plus")
        self._attr_extra_state_attributes = {"treatment_type": "pH+"}

    @property
    def native_value(self):
        try:
            data = self._hass.data[DOMAIN][self._entry.entry_id]
            current_ph = float(data.get("ph_current", 7.0))
            target_ph = float(data.get("ph_target", 7.4))
            volume_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if not volume_entity or volume_entity.state in ("unknown", "unavailable"):
                _LOGGER.error("Capteur de volume indisponible pour %s", self._name)
                return 0

            volume = float(volume_entity.state)
            delta_ph = target_ph - current_ph
            treatment_form = data.get("ph_plus_treatment", "Liquide")

            if delta_ph <= 0:
                return 0

            if treatment_form == "Liquide":
                quantity = delta_ph * volume * 0.01
            else:  # Granulés
                quantity = delta_ph * volume * 1.0

            return round(quantity, 2)
        except Exception as e:
            _LOGGER.error("Erreur calcul pH+ à ajouter pour %s: %s", self._name, e)
            return 0

class PiscinexaPhMinusAjouterSensor(PiscinexaBaseSensor):
    def __init__(self, hass, entry):
        super().__init__(hass, entry, entry.data["name"], "phminusaajouter", UNIT_LITERS, "mdi:water-minus")
        self._attr_extra_state_attributes = {"treatment_type": "pH-"}

    @property
    def native_value(self):
        try:
            data = self._hass.data[DOMAIN][self._entry.entry_id]
            current_ph = float(data.get("ph_current", 7.0))
            target_ph = float(data.get("ph_target", 7.4))
            volume_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if not volume_entity or volume_entity.state in ("unknown", "unavailable"):
                _LOGGER.error("Capteur de volume indisponible pour %s", self._name)
                return 0

            volume = float(volume_entity.state)
            delta_ph = current_ph - target_ph
            treatment_form = data.get("ph_minus_treatment", "Liquide")

            if delta_ph <= 0:
                return 0

            if treatment_form == "Liquide":
                quantity = delta_ph * volume * 0.012
            else:  # Granulés
                quantity = delta_ph * volume * 1.2

            return round(quantity, 2)
        except Exception as e:
            _LOGGER.error("Erreur calcul pH- à ajouter pour %s: %s", self._name, e)
            return 0

class PiscinexaChloreAjouterSensor(PiscinexaBaseSensor):
    def __init__(self, hass, entry):
        super().__init__(hass, entry, entry.data["name"], "chloreaajouter", UNIT_GRAMS, "mdi:water-check")
        self._attr_extra_state_attributes = {"message": ""}

    @property
    def native_value(self):
        try:
            data = self._hass.data[DOMAIN][self._entry.entry_id]
            current_chlore = float(data.get("chlore_current", 1.0))
            target_chlore = float(data.get("chlore_target", 2.0))
            volume_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if not volume_entity or volume_entity.state in ("unknown", "unavailable"):
                _LOGGER.error("Capteur de volume indisponible pour %s", self._name)
                return 0

            volume = float(volume_entity.state)
            delta_chlore = target_chlore - current_chlore
            treatment_form = data.get("chlore_treatment", "Chlore choc (poudre)")
            self._attr_extra_state_attributes["message"] = ""

            if delta_chlore <= 0:
                self._attr_extra_state_attributes["message"] = "Retirer le chlore, pas de besoin actuellement"
                return 0

            if treatment_form == "Liquide":
                quantity = delta_chlore * volume * 0.1
            elif treatment_form == "Pastille lente":
                quantity = delta_chlore * volume / 20
            else:  # Chlore choc (poudre)
                quantity = delta_chlore * volume * 0.01

            return round(quantity, 2)
        except Exception as e:
            _LOGGER.error("Erreur calcul chlore à ajouter pour %s: %s", self._name, e)
            return 0