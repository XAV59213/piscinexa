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
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers.translation import async_get_translations

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
    volume_sensor = PiscinexaVolumeSensor(hass, entry)
    sensors = [
        volume_sensor,
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
        self._attr_extra_state_attributes = {"configuration_error": None}
        self._attr_friendly_name = f"{self._name.capitalize()} Volume d'eau"

    @property
    def available(self):
        return self.native_value is not None

    @property
    def native_value(self):
        try:
            data = self._entry.data
            required_fields = ["depth"]
            if "pool_type" not in data or data["pool_type"] not in (POOL_TYPE_SQUARE, POOL_TYPE_ROUND):
                error_msg = f"Valeur invalide pour pool_type dans la configuration pour {self._name}: {data.get('pool_type', 'non défini')}"
                self._attr_extra_state_attributes["configuration_error"] = error_msg
                _LOGGER.error(error_msg)
                return None

            if data["pool_type"] == POOL_TYPE_SQUARE:
                required_fields.extend(["length", "width"])
            else:
                required_fields.append("diameter")

            missing_fields = [field for field in required_fields if field not in data or data[field] is None]
            if missing_fields:
                error_msg = f"Champs manquants dans la configuration pour {self._name}: {', '.join(missing_fields)}"
                self._attr_extra_state_attributes["configuration_error"] = error_msg
                _LOGGER.error(error_msg)
                return None

            for field in required_fields:
                try:
                    value = float(data[field])
                    if value <= 0:
                        error_msg = f"Valeur invalide pour {field} dans la configuration pour {self._name}: {value}"
                        self._attr_extra_state_attributes["configuration_error"] = error_msg
                        _LOGGER.error(error_msg)
                        return None
                except (ValueError, TypeError):
                    error_msg = f"Valeur non numérique pour {field} dans la configuration pour {self._name}: {data[field]}"
                    self._attr_extra_state_attributes["configuration_error"] = error_msg
                    _LOGGER.error(error_msg)
                    return None

            depth = float(data["depth"])
            if data["pool_type"] == POOL_TYPE_SQUARE:
                volume = float(data["length"]) * float(data["width"]) * depth
            else:
                radius = float(data["diameter"]) / 2
                volume = PI * radius * radius * depth

            self._attr_extra_state_attributes["configuration_error"] = None
            return round(volume, 2)
        except Exception as e:
            self._attr_extra_state_attributes["configuration_error"] = str(e)
            _LOGGER.error("Erreur calcul volume pour %s: %s", self._name, e)
            return None

class PiscinexaTempsFiltrationSensor(PiscinexaBaseSensor):
    def __init__(self, hass, entry):
        super().__init__(hass, entry, entry.data["name"], "temps_filtration", UNIT_HOURS, "mdi:clock")
        self._attr_friendly_name = f"{self._name.capitalize()} Temps de filtration"

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
        self._attr_friendly_name = f"{self._name.capitalize()} Journal"
        self._state = deque(maxlen=10)

    def log_action(self, action: str):
        if not hasattr(self, '_state') or self._state is None:
            self._state = deque(maxlen=10)
        self._state.append(f"{datetime.now()}: {action}")
        self.async_write_ha_state()

    @property
    def native_value(self):
        if not hasattr(self, '_state') or self._state is None:
            self._state = deque(maxlen=10)
            return "Aucune action"
        return "\n".join(self._state) if self._state else "Aucune action"

class PiscinexaTemperatureSensor(PiscinexaBaseSensor):
    def __init__(self, hass, entry):
        super().__init__(hass, entry, entry.data["name"], "temperature", "°C", "mdi:thermometer")
        self._sensor_id = entry.data.get("temperature_sensor")
        self._attr_friendly_name = f"{self._name.capitalize()} Température"

    @property
    def native_value(self):
        try:
            if self._sensor_id:
                state = self._hass.states.get(self._sensor_id)
                if state and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
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
        self._attr_friendly_name = f"{self._name.capitalize()} pH"

    @property
    def native_value(self):
        try:
            if self._sensor_id:
                state = self._hass.states.get(self._sensor_id)
                if state and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
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
        self._attr_friendly_name = f"{self._name.capitalize()} Chlore"

    @property
    def native_value(self):
        try:
            if self._sensor_id:
                state = self._hass.states.get(self._sensor_id)
                if state and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
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
        self._attr_friendly_name = f"{self._name.capitalize()} Différence Chlore"

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
        self._attr_friendly_name = f"{self._name.capitalize()} Consommation Puissance"

    @property
    def native_value(self):
        try:
            if self._sensor_id:
                state = self._hass.states.get(self._sensor_id)
                if state and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                    return round(float(state.state), 2)
            return None
        except Exception as e:
            _LOGGER.warning("Erreur lecture puissance : %s", e)
            return None

class PiscinexaPoolStateSensor(PiscinexaBaseSensor):
    def __init__(self, hass, entry):
        super().__init__(hass, entry, entry.data["name"], "pool_state", None, "mdi:pool")
        self._attr_friendly_name = f"{self._name.capitalize()} État de la piscine"
        self._translations = None

    async def async_update_translations(self):
        # Récupérer la langue de l'utilisateur
        language = self.hass.config.language
        # Charger les traductions pour l'entité pool_state
        self._translations = await async_get_translations(
            self.hass, language, "entity", components=[DOMAIN]
        )

    @property
    def native_value(self):
        try:
            # Charger les traductions si elles ne sont pas encore chargées
            if self._translations is None:
                self.hass.async_create_task(self.async_update_translations())
                # Valeurs par défaut en cas de traduction non disponible
                translations = {
                    "temperature_ideal": "Température idéale",
                    "too_cold": "Trop froide",
                    "too_hot": "Trop chaude",
                    "chlorine_ideal": "Chlore idéal",
                    "chlorine_low": "Chlore bas",
                    "chlorine_high": "Chlore haut",
                    "ph_ideal": "pH idéal",
                    "ph_low": "pH bas",
                    "ph_high": "pH haut",
                    "swimming_allowed": "Baignade autorisée",
                    "unavailable": "Indisponible"
                }
            else:
                translations = {
                    "temperature_ideal": self._translations.get("entity.sensor.piscinexa_piscine_pool_state.states.temperature_ideal", "Température idéale"),
                    "too_cold": self._translations.get("entity.sensor.piscinexa_piscine_pool_state.states.too_cold", "Trop froide"),
                    "too_hot": self._translations.get("entity.sensor.piscinexa_piscine_pool_state.states.too_hot", "Trop chaude"),
                    "chlorine_ideal": self._translations.get("entity.sensor.piscinexa_piscine_pool_state.states.chlorine_ideal", "Chlore idéal"),
                    "chlorine_low": self._translations.get("entity.sensor.piscinexa_piscine_pool_state.states.chlorine_low", "Chlore bas"),
                    "chlorine_high": self._translations.get("entity.sensor.piscinexa_piscine_pool_state.states.chlorine_high", "Chlore haut"),
                    "ph_ideal": self._translations.get("entity.sensor.piscinexa_piscine_pool_state.states.ph_ideal", "pH idéal"),
                    "ph_low": self._translations.get("entity.sensor.piscinexa_piscine_pool_state.states.ph_low", "pH bas"),
                    "ph_high": self._translations.get("entity.sensor.piscinexa_piscine_pool_state.states.ph_high", "pH haut"),
                    "swimming_allowed": self._translations.get("entity.sensor.piscinexa_piscine_pool_state.states.swimming_allowed", "Baignade autorisée"),
                    "unavailable": self._translations.get("entity.sensor.piscinexa_piscine_pool_state.states.unavailable", "Indisponible")
                }

            data = self._hass.data[DOMAIN][self._entry.entry_id]
            temperature = data.get("temperature", 20.0)
            chlore = data.get("chlore_current", 1.0)
            ph = data.get("ph_current", 7.0)

            status = []
            if 22 <= temperature <= 28:
                status.append(translations["temperature_ideal"])
            elif temperature < 22:
                status.append(translations["too_cold"])
            else:
                status.append(translations["too_hot"])

            if 1 <= chlore <= 3:
                status.append(translations["chlorine_ideal"])
            elif chlore < 1:
                status.append(translations["chlorine_low"])
            else:
                status.append(translations["chlorine_high"])

            if 7.2 <= ph <= 7.6:
                status.append(translations["ph_ideal"])
            elif ph < 7.2:
                status.append(translations["ph_low"])
            else:
                status.append(translations["ph_high"])

            if all("ideal" in s.lower() for s in status):
                return translations["swimming_allowed"]
            return ", ".join(status)
        except Exception as e:
            _LOGGER.error("Erreur évaluation état piscine : %s", e)
            return translations.get("unavailable", "Indisponible")

class PiscinexaPhAjouterSensor(PiscinexaBaseSensor):
    def __init__(self, hass, entry):
        super().__init__(hass, entry, entry.data["name"], "ph_a_ajouter", UNIT_LITERS, "mdi:water-plus")
        self._attr_friendly_name = f"{self._name.capitalize()} pH à ajouter"
        self._attr_extra_state_attributes = {"treatment_direction": ""}

    @property
    def available(self):
        volume_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
        return volume_entity and volume_entity.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)

    @property
    def native_value(self):
        if not self.available:
            _LOGGER.warning("Capteur de volume indisponible pour %s", self._name)
            return 0

        try:
            data = self._hass.data[DOMAIN][self._entry.entry_id]
            current_ph = float(data.get("ph_current", 7.0))
            target_ph = float(data.get("ph_target", 7.4))
            volume_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
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
        super().__init__(hass, entry, entry.data["name"], "ph_plus_a_ajouter", UNIT_LITERS, "mdi:water-plus")
        self._attr_friendly_name = f"{self._name.capitalize()} pH+ à ajouter"
        self._attr_extra_state_attributes = {"treatment_type": "pH+"}

    @property
    def available(self):
        volume_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
        return volume_entity and volume_entity.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)

    @property
    def native_value(self):
        if not self.available:
            _LOGGER.warning("Capteur de volume indisponible pour %s", self._name)
            return 0

        try:
            data = self._hass.data[DOMAIN][self._entry.entry_id]
            current_ph = float(data.get("ph_current", 7.0))
            target_ph = float(data.get("ph_target", 7.4))
            volume_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
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
        super().__init__(hass, entry, entry.data["name"], "ph_minus_a_ajouter", UNIT_LITERS, "mdi:water-minus")
        self._attr_friendly_name = f"{self._name.capitalize()} pH- à ajouter"
        self._attr_extra_state_attributes = {"treatment_type": "pH-"}

    @property
    def available(self):
        volume_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
        return volume_entity and volume_entity.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)

    @property
    def native_value(self):
        if not self.available:
            _LOGGER.warning("Capteur de volume indisponible pour %s", self._name)
            return 0

        try:
            data = self._hass.data[DOMAIN][self._entry.entry_id]
            current_ph = float(data.get("ph_current", 7.0))
            target_ph = float(data.get("ph_target", 7.4))
            volume_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
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
        super().__init__(hass, entry, entry.data["name"], "chlore_a_ajouter", UNIT_GRAMS, "mdi:water-check")
        self._attr_friendly_name = f"{self._name.capitalize()} Chlore à ajouter"
        self._attr_extra_state_attributes = {"message": ""}

    @property
    def available(self):
        volume_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
        return volume_entity and volume_entity.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)

    @property
    def native_value(self):
        if not self.available:
            _LOGGER.warning("Capteur de volume indisponible pour %s", self._name)
            return 0

        try:
            data = self._hass.data[DOMAIN][self._entry.entry_id]
            current_chlore = float(data.get("chlore_current", 1.0))
            target_chlore = float(data.get("chlore_target", 2.0))
            volume_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
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