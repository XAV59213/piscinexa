import logging
from datetime import datetime
from collections import deque
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import CONF_NAME
from homeassistant.helpers.event import async_track_state_change_event
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
    log_sensor = PiscinexaLogSensor(hass, entry)
    hass.data[DOMAIN]["log"] = log_sensor
    name = entry.data["name"]
    sensors = [
        PiscinexaVolumeSensor(hass, entry, name),
        PiscinexaTempsFiltrationSensor(hass, entry, name),
        PiscinexaTemperatureSensor(hass, entry, name),
        PiscinexaPhSensor(hass, entry, name),
        PiscinexaPhAjouterSensor(hass, entry, name),
        PiscinexaChloreSensor(hass, entry, name),
        PiscinexaChloreAjouterSensor(hass, entry, name),
        PiscinexaChloreDifferenceSensor(hass, entry, name),
        PiscinexaPowerSensor(hass, entry, name),
        PiscinexaPoolStateSensor(hass, entry, name),
        log_sensor,
    ]
    async_add_entities(sensors, True)

class PiscinexaVolumeSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_volume_eau"
        self._attr_friendly_name = f"{name.capitalize()} Volume d'eau"
        self._attr_unit_of_measurement = UNIT_CUBIC_METERS  # m³
        self._attr_icon = "mdi:pool"
        self._attr_unique_id = f"{entry.entry_id}_volume_eau"
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

    @property
    def native_value(self):
        try:
            pool_type = self._entry.data["pool_type"]
            depth = float(self._entry.data["depth"])
            if pool_type == POOL_TYPE_SQUARE:
                length = float(self._entry.data["length"])
                width = float(self._entry.data["width"])
                volume = length * width * depth
            else:
                diameter = float(self._entry.data["diameter"])
                radius = diameter / 2
                volume = PI * radius * radius * depth
            return round(volume, 2)
        except Exception as e:
            _LOGGER.error("Erreur calcul volume pour %s: %s", self._name, e)
            return None

    @property
    def unit_of_measurement(self):
        return self._attr_unit_of_measurement

class PiscinexaTempsFiltrationSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_tempsfiltration"
        self._attr_friendly_name = f"{name.capitalize()} Temps de filtration"
        self._attr_unit_of_measurement = UNIT_HOURS  # h
        self._attr_icon = "mdi:clock"
        self._attr_unique_id = f"{entry.entry_id}_temps_filtration"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._subscriptions = []
        # S'abonner aux changements du capteur de température si configuré
        sensor_id = self._entry.data.get("temperature_sensor")
        if sensor_id:
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [sensor_id], self._async_update_from_sensor
                )
            )

    async def async_will_remove_from_hass(self):
        """Nettoyer les subscriptions lors de la suppression."""
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_sensor(self, event):
        """Mettre à jour le capteur lorsque le capteur de température change."""
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        sensor_id = self._entry.data.get("temperature_sensor")
        if sensor_id:
            state = self._hass.states.get(sensor_id)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    return round(float(state.state) / 2, 1)
                except Exception as e:
                    _LOGGER.warning("Erreur de conversion température depuis %s : %s", sensor_id, e)
        try:
            return round(self._entry.data["temperature"] / 2, 1)
        except Exception as e:
            _LOGGER.error("Température par défaut invalide : %s", e)
            return None

    @property
    def unit_of_measurement(self):
        return self._attr_unit_of_measurement

class PiscinexaTemperatureSensor(SensorEntity):
    """Capteur pour afficher la température mesurée ou par défaut."""
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_temperature"
        self._attr_friendly_name = f"{name.capitalize()} Température"
        self._attr_unit_of_measurement = "°C"  # °C
        self._attr_icon = "mdi:thermometer"
        self._attr_unique_id = f"{entry.entry_id}_temperature"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._subscriptions = []
        # S'abonner aux changements du capteur de température si configuré
        sensor_id = self._entry.data.get("temperature_sensor")
        if sensor_id:
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [sensor_id], self._async_update_from_sensor
                )
            )

    async def async_will_remove_from_hass(self):
        """Nettoyer les subscriptions lors de la suppression."""
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_sensor(self, event):
        """Mettre à jour le capteur lorsque le capteur de température change."""
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        sensor_id = self._entry.data.get("temperature_sensor")
        if sensor_id:
            state = self._hass.states.get(sensor_id)
            if state:
                if state.state in ("unknown", "unavailable"):
                    _LOGGER.warning("Capteur de température %s indisponible ou inconnu", sensor_id)
                    return None
                try:
                    value = float(state.state)
                    # Convertir en °C si l'unité est °F
                    unit = state.attributes.get("unit_of_measurement", "").lower()
                    _LOGGER.debug("Capteur %s: valeur=%s, unité=%s", sensor_id, value, unit)
                    if unit in ("°f", "f", "fahrenheit"):
                        value = (value - 32) * 5 / 9
                        _LOGGER.debug("Conversion de °F en °C: %s °F -> %s °C", state.state, value)
                    value = round(value, 1)
                    # Mettre à jour entry.data
                    self._hass.data[DOMAIN][self._entry.entry_id]["temperature"] = value
                    _LOGGER.debug("Température mise à jour depuis capteur %s: %s °C", sensor_id, value)
                    return value
                except ValueError as e:
                    _LOGGER.error("Valeur non numérique pour capteur %s: %s", sensor_id, state.state)
                    return None
                except Exception as e:
                    _LOGGER.warning("Erreur lecture température depuis %s : %s", sensor_id, e)
                    return None
            else:
                _LOGGER.warning("Capteur de température %s introuvable", sensor_id)
                return None
        try:
            return round(float(self._entry.data["temperature"]), 1)
        except Exception as e:
            _LOGGER.error("Température par défaut invalide : %s", e)
            return None

    @property
    def unit_of_measurement(self):
        return self._attr_unit_of_measurement

class PiscinexaPhSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._entry = entry
        self._name = name
        self._hass = hass
        self._attr_name = f"{DOMAIN}_{name}_ph"
        self._attr_friendly_name = f"{name.capitalize()} pH"
        self._attr_icon = "mdi:water"
        self._attr_unique_id = f"{entry.entry_id}_ph"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._subscriptions = []
        # S'abonner aux changements du capteur de pH si configuré
        sensor_id = self._entry.data.get("ph_sensor")
        if sensor_id:
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [sensor_id], self._async_update_from_sensor
                )
            )
        # S'abonner aux changements de l'input_number
        input_id = f"input_number.{name}_ph_current"
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [input_id], self._async_update_from_input
            )
        )

    async def async_will_remove_from_hass(self):
        """Nettoyer les subscriptions lors de la suppression."""
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_sensor(self, event):
        """Mettre à jour le capteur lorsque le capteur de pH change."""
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_input(self, event):
        """Mettre à jour le capteur lorsque l'input_number change."""
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        # Priorité 1 : Capteur de pH
        sensor_id = self._entry.data.get("ph_sensor")
        if sensor_id:
            state = self._hass.states.get(sensor_id)
            if state:
                if state.state in ("unknown", "unavailable"):
                    _LOGGER.warning("Capteur de pH %s indisponible ou inconnu", sensor_id)
                    return None
                try:
                    value = round(float(state.state), 1)
                    # Mettre à jour entry.data
                    self._hass.data[DOMAIN][self._entry.entry_id]["ph_current"] = value
                    # Mettre à jour input_number
                    self._hass.states.async_set(
                        f"input_number.{self._name}_ph_current",
                        value,
                        {
                            "friendly_name": f"{self._name.capitalize()} pH Actuel",
                            "min": 0,
                            "max": 14,
                            "step": 0.1,
                            "unit_of_measurement": "pH",
                        },
                    )
                    _LOGGER.debug("pH mis à jour depuis capteur %s: %s", sensor_id, value)
                    return value
                except ValueError as e:
                    _LOGGER.error("Valeur non numérique pour capteur %s: %s", sensor_id, state.state)
                    return None
                except Exception as e:
                    _LOGGER.warning("Erreur lecture pH depuis capteur %s : %s", sensor_id, e)
                    return None
            else:
                _LOGGER.warning("Capteur de pH %s introuvable", sensor_id)
                return None

        # Priorité 2 : input_number
        input_state = self._hass.states.get(f"input_number.{self._name}_ph_current")
        if input_state and input_state.state not in ("unknown", "unavailable"):
            try:
                value = round(float(input_state.state), 1)
                # Mettre à jour entry.data
                self._hass.data[DOMAIN][self._entry.entry_id]["ph_current"] = value
                return value
            except Exception as e:
                _LOGGER.warning("Erreur lecture pH depuis input_number : %s", e)

        # Priorité 3 : Valeur par défaut dans entry.data
        try:
            return round(float(self._entry.data["ph_current"]), 1)
        except Exception as e:
            _LOGGER.error("Erreur lecture pH: %s", e)
            return None

class PiscinexaPhAjouterSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_phaajouter"
        self._attr_friendly_name = f"{name.capitalize()} pH à ajouter"
        self._attr_unit_of_measurement = UNIT_LITERS  # L
        self._attr_icon = "mdi:bottle-tonic-plus"
        self._attr_unique_id = f"{entry.entry_id}_ph_a_ajouter"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._subscriptions = []
        # S'abonner aux changements du capteur de pH et de volume
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"sensor.{DOMAIN}_{name}_ph"], self._async_update_from_ph
            )
        )
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"sensor.{DOMAIN}_{name}_volume_eau"], self._async_update_from_volume
            )
        )

    async def async_will_remove_from_hass(self):
        """Nettoyer les subscriptions lors de la suppression."""
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_ph(self, event):
        """Mettre à jour le capteur lorsque le pH change."""
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_volume(self, event):
        """Mettre à jour le capteur lorsque le volume change."""
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        try:
            ph_current = float(self._entry.data["ph_current"])
            ph_target = float(self._entry.data["ph_target"])
            volume = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if volume:
                volume_val = float(volume.state)
                dose = abs(ph_target - ph_current) * volume_val * 10
                return round(dose, 2)
            return None
        except Exception as e:
            _LOGGER.error("Erreur calcul dose pH: %s", e)
            return None

    @property
    def unit_of_measurement(self):
        return self._attr_unit_of_measurement

class PiscinexaChloreSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._entry = entry
        self._name = name
        self._hass = hass
        self._attr_name = f"{DOMAIN}_{name}_chlore"
        self._attr_friendly_name = f"{name.capitalize()} Chlore"
        self._attr_unit_of_measurement = UNIT_MG_PER_LITER  # mg/L
        self._attr_icon = "mdi:water-check"
        self._attr_unique_id = f"{entry.entry_id}_chlore"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._subscriptions = []
        # S'abonner aux changements du capteur de chlore si configuré
        sensor_id = self._entry.data.get("chlore_sensor")
        if sensor_id:
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [sensor_id], self._async_update_from_sensor
                )
            )
        # S'abonner aux changements de l'input_number
        input_id = f"input_number.{name}_chlore_current"
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [input_id], self._async_update_from_input
            )
        )

    async def async_will_remove_from_hass(self):
        """Nettoyer les subscriptions lors de la suppression."""
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_sensor(self, event):
        """Mettre à jour le capteur lorsque le capteur de chlore change."""
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_input(self, event):
        """Mettre à jour le capteur lorsque l'input_number change."""
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        # Priorité 1 : Capteur de chlore
        sensor_id = self._entry.data.get("chlore_sensor")
        if sensor_id:
            state = self._hass.states.get(sensor_id)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    value = round(float(state.state), 1)
                    # Mettre à jour entry.data
                    self._hass.data[DOMAIN][self._entry.entry_id]["chlore_current"] = value
                    # Mettre à jour input_number
                    self._hass.states.async_set(
                        f"input_number.{self._name}_chlore_current",
                        value,
                        {
                            "friendly_name": f"{self._name.capitalize()} Chlore Actuel",
                            "min": 0,
                            "max": 10,
                            "step": 0.1,
                            "unit_of_measurement": "mg/L",
                        },
                    )
                    _LOGGER.debug("Chlore mis à jour depuis capteur %s: %s mg/L", sensor_id, value)
                    return value
                except Exception as e:
                    _LOGGER.warning("Erreur lecture chlore depuis capteur %s : %s", sensor_id, e)

        # Priorité 2 : input_number
        input_state = self._hass.states.get(f"input_number.{self._name}_chlore_current")
        if input_state and input_state.state not in ("unknown", "unavailable"):
            try:
                value = round(float(input_state.state), 1)
                # Mettre à jour entry.data
                self._hass.data[DOMAIN][self._entry.entry_id]["chlore_current"] = value
                return value
            except Exception as e:
                _LOGGER.warning("Erreur lecture chlore depuis input_number : %s", e)

        # Priorité 3 : Valeur par défaut dans entry.data
        try:
            return round(float(self._entry.data["chlore_current"]), 1)
        except Exception as e:
            _LOGGER.error("Erreur lecture chlore: %s", e)
            return None

    @property
    def unit_of_measurement(self):
        return self._attr_unit_of_measurement

class PiscinexaChloreAjouterSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_chloreaajouter"
        self._attr_friendly_name = f"{name.capitalize()} Chlore à ajouter"
        self._attr_unit_of_measurement = UNIT_GRAMS  # g
        self._attr_icon = "mdi:bottle-tonic-plus"
        self._attr_unique_id = f"{entry.entry_id}_chlore_a_ajouter"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._message = None
        self._subscriptions = []
        # S'abonner aux changements du chlore, volume et température
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"sensor.{DOMAIN}_{name}_chlore"], self._async_update_from_chlore
            )
        )
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"sensor.{DOMAIN}_{name}_volume_eau"], self._async_update_from_volume
            )
        )
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"sensor.{DOMAIN}_{name}_temperature"], self._async_update_from_temperature
            )
        )

    async def async_will_remove_from_hass(self):
        """Nettoyer les subscriptions lors de la suppression."""
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_chlore(self, event):
        """Mettre à jour le capteur lorsque le chlore change."""
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_volume(self, event):
        """Mettre à jour le capteur lorsque le volume change."""
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_temperature(self, event):
        """Mettre à jour le capteur lorsque la température change."""
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        try:
            # Récupérer chlore_current
            if "chlore_current" not in self._entry.data:
                _LOGGER.error("chlore_current manquant dans entry.data pour %s", self._name)
                self._message = "Chlore actuel manquant"
                return None
            chlore_current = float(self._entry.data["chlore_current"])
            _LOGGER.debug("Chlore actuel pour %s: %s mg/L", self._name, chlore_current)

            # Récupérer chlore_target
            if "chlore_target" not in self._entry.data:
                _LOGGER.error("chlore_target manquant dans entry.data pour %s", self._name)
                self._message = "Chlore cible manquant"
                return None
            chlore_target = float(self._entry.data["chlore_target"])
            _LOGGER.debug("Chlore cible pour %s: %s mg/L", self._name, chlore_target)

            # Récupérer le volume
            volume_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if volume_entity and volume_entity.state not in ("unknown", "unavailable"):
                volume_val = float(volume_entity.state)
                _LOGGER.debug("Volume pour %s: %s m³", self._name, volume_val)

                # Récupérer la température
                temp_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_temperature")
                if temp_entity and temp_entity.state not in ("unknown", "unavailable"):
                    temperature = float(temp_entity.state)
                    _LOGGER.debug("Température pour %s: %s °C", self._name, temperature)

                    # Calculer le facteur de correction basé sur la température
                    # Base : 20°C, augmentation de 2% par degré au-dessus
                    temp_factor = max(1, 1 + (temperature - 20) * 0.02)
                    _LOGGER.debug("Facteur de température pour %s: %s", self._name, temp_factor)

                    # Calculer la dose
                    dose = (chlore_target - chlore_current) * volume_val * 10 * temp_factor
                    _LOGGER.debug("Dose calculée pour %s: %s g (avant arrondi)", self._name, dose)

                    # Définir le message si aucune addition n'est nécessaire
                    if dose <= 0:
                        self._message = "Retirer le chlore, pas de besoin actuellement"
                        return 0
                    else:
                        self._message = None
                        return round(dose, 2)
                else:
                    _LOGGER.warning("Capteur de température indisponible pour %s", self._name)
                    self._message = "Température indisponible"
                    return None
            else:
                _LOGGER.warning("Capteur de volume indisponible pour %s", self._name)
                self._message = "Volume indisponible"
                return None
        except Exception as e:
            _LOGGER.error("Erreur calcul dose chlore pour %s: %s", self._name, e)
            self._message = "Erreur de calcul"
            return None

    @property
    def unit_of_measurement(self):
        return self._attr_unit_of_measurement

    @property
    def extra_state_attributes(self):
        """Retourne des attributs supplémentaires pour le débogage et l'affichage conditionnel."""
        attributes = {}
        try:
            attributes["chlore_current"] = float(self._entry.data["chlore_current"])
            attributes["chlore_target"] = float(self._entry.data["chlore_target"])
            volume_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if volume_entity:
                attributes["volume"] = float(volume_entity.state)
            temp_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_temperature")
            if temp_entity:
                attributes["temperature"] = float(temp_entity.state)
                attributes["temp_factor"] = max(1, 1 + (attributes["temperature"] - 20) * 0.02)
            if self._message:
                attributes["message"] = self._message
        except Exception as e:
            _LOGGER.error("Erreur récupération attributs supplémentaires: %s", e)
        return attributes

class PiscinexaChloreDifferenceSensor(SensorEntity):
    """Capteur pour afficher la différence entre chlore visé et chlore actuel."""
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_chloredifference"
        self._attr_friendly_name = f"{name.capitalize()} Différence Chlore"
        self._attr_unit_of_measurement = UNIT_MG_PER_LITER  # mg/L
        self._attr_icon = "mdi:delta"
        self._attr_unique_id = f"{entry.entry_id}_chlore_difference"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._subscriptions = []
        # S'abonner aux changements du capteur de chlore
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"sensor.{DOMAIN}_{name}_chlore"], self._async_update_from_chlore
            )
        )

    async def async_will_remove_from_hass(self):
        """Nettoyer les subscriptions lors de la suppression."""
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_chlore(self, event):
        """Mettre à jour le capteur lorsque le chlore change."""
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        try:
            # Récupérer chlore_current
            if "chlore_current" not in self._entry.data:
                _LOGGER.error("chlore_current manquant dans entry.data pour %s", self._name)
                return None
            chlore_current = float(self._entry.data["chlore_current"])
            _LOGGER.debug("Chlore actuel pour %s: %s mg/L", self._name, chlore_current)

            # Récupérer chlore_target
            if "chlore_target" not in self._entry.data:
                _LOGGER.error("chlore_target manquant dans entry.data pour %s", self._name)
                return None
            chlore_target = float(self._entry.data["chlore_target"])
            _LOGGER.debug("Chlore cible pour %s: %s mg/L", self._name, chlore_target)

            # Calculer la différence
            difference = chlore_target - chlore_current
            return round(difference, 1)
        except Exception as e:
            _LOGGER.error("Erreur calcul différence chlore pour %s: %s", self._name, e)
            return None

    @property
    def unit_of_measurement(self):
        return self._attr_unit_of_measurement

class PiscinexaLogSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self._hass = hass
        self._entry = entry
        self._name = entry.data["name"]
        self._attr_name = f"{DOMAIN}_{self._name}_log"
        self._attr_friendly_name = f"{self._name.capitalize()} Journal"
        self._attr_icon = "mdi:book"
        self._attr_unique_id = f"{entry.entry_id}_log"
        self._state = deque(maxlen=10)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{self._name}")},
            name=self._name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )

    @property
    def name(self):
        return self._attr_friendly_name

    def log_action(self, action: str):
        self._state.append(f"{datetime.now()}: {action}")
        self.async_write_ha_state()

    @property
    def native_value(self):
        return "\n".join(self._state) if self._state else "Aucune action"

class PiscinexaPowerSensor(SensorEntity):
    """Capteur pour la puissance de la prise connectée à la piscine."""
    def __init__(self, hass, entry, name):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_consopuissance"
        self._attr_friendly_name = f"{name.capitalize()} Consommation puissance"
        self._attr_unit_of_measurement = "W"  # W
        self._attr_icon = "mdi:flash"
        self._attr_unique_id = f"{entry.entry_id}_conso_puissance"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._subscriptions = []
        # S'abonner aux changements du capteur de puissance si configuré
        sensor_id = self._entry.data.get("power_sensor_entity_id")
        if sensor_id:
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [sensor_id], self._async_update_from_sensor
                )
            )

    async def async_will_remove_from_hass(self):
        """Nettoyer les subscriptions lors de la suppression."""
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_sensor(self, event):
        """Mettre à jour le capteur lorsque le capteur de puissance change."""
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def state(self):
        try:
            sensor_id = self._entry.data.get("power_sensor_entity_id")
            if sensor_id:
                power_state = self._hass.states.get(sensor_id)
                if power_state and power_state.state not in ("unknown", "unavailable"):
                    value = round(float(power_state.state), 2)
                    log = self._hass.data[DOMAIN].get("log")
                    if log:
                        log.log_action(f"Conso {self._name} : {value} W")
                    return value
        except Exception as e:
            _LOGGER.warning("Erreur lecture capteur puissance : %s", e)
        return None

    @property
    def unit_of_measurement(self):
        return self._attr_unit_of_measurement

class PiscinexaPoolStateSensor(SensorEntity):
    """Capteur pour évaluer l'état global de la piscine."""
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_pool_state"
        self._attr_friendly_name = f"{name.capitalize()} État de la piscine"
        self._attr_icon = "mdi:pool"
        self._attr_unique_id = f"{entry.entry_id}_pool_state"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._subscriptions = []
        # S'abonner aux changements des capteurs dépendants
        entities_to_track = [
            f"sensor.{DOMAIN}_{name}_temperature",
            f"sensor.{DOMAIN}_{name}_chlore",
            f"sensor.{DOMAIN}_{name}_ph",
            f"sensor.{DOMAIN}_{name}_tempsfiltration",
        ]
        self._subscriptions.append(
            async_track_state_change_event(
                hass, entities_to_track, self._async_update_from_sensors
            )
        )

    async def async_will_remove_from_hass(self):
        """Nettoyer les subscriptions lors de la suppression."""
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_sensors(self, event):
        """Mettre à jour le capteur lorsque les capteurs dépendants changent."""
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        try:
            issues = []

            # Température
            temp_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_temperature")
            if temp_entity and temp_entity.state not in ("unknown", "unavailable"):
                temperature = float(temp_entity.state)
                if temperature < 22:
                    issues.append("Température trop froide")
                elif temperature > 28:
                    issues.append("Température trop chaude")
                else:
                    issues.append("Température idéale")
            else:
                issues.append("Température indisponible")

            # Chlore
            chlore_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_chlore")
            if chlore_entity and chlore_entity.state not in ("unknown", "unavailable"):
                chlore = float(chlore_entity.state)
                if chlore < 1:
                    issues.append("Chlore trop bas")
                elif chlore > 3:
                    issues.append("Chlore trop élevé")
                else:
                    issues.append("Chlore idéal")
            else:
                issues.append("Chlore indisponible")

            # pH
            ph_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_ph")
            if ph_entity and ph_entity.state not in ("unknown", "unavailable"):
                ph = float(ph_entity.state)
                if ph < 7.2:
                    issues.append("pH trop bas")
                elif ph > 7.6:
                    issues.append("pH trop élevé")
                else:
                    issues.append("pH idéal")
            else:
                issues.append("pH indisponible")

            # Temps de filtration
            filtration_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_tempsfiltration")
            if filtration_entity and filtration_entity.state not in ("unknown", "unavailable") and temp_entity:
                filtration_time = float(filtration_entity.state)
                required_filtration = temperature / 2
                if filtration_time < required_filtration:
                    issues.append("Temps de filtration insuffisant")
                else:
                    issues.append("Temps de filtration idéal")
            else:
                issues.append("Temps de filtration indisponible")

            # État global
            if all(issue in ["Température idéale", "Chlore idéal", "pH idéal", "Temps de filtration idéal"] for issue in issues):
                return "Baignade autorisée, profitez-en !"
            else:
                return ", ".join(issues)
        except Exception as e:
            _LOGGER.error("Erreur calcul état piscine pour %s: %s", self._name, e)
            return "Erreur d'évaluation"

    @property
    def extra_state_attributes(self):
        """Retourne les détails des paramètres évalués."""
        attributes = {}
        try:
            temp_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_temperature")
            if temp_entity:
                attributes["temperature"] = float(temp_entity.state)
            chlore_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_chlore")
            if chlore_entity:
                attributes["chlore"] = float(chlore_entity.state)
            ph_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_ph")
            if ph_entity:
                attributes["ph"] = float(ph_entity.state)
            filtration_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_tempsfiltration")
            if filtration_entity:
                attributes["temps_filtration"] = float(filtration_entity.state)
        except Exception as e:
            _LOGGER.error("Erreur récupération attributs état piscine: %s", e)
        return attributes
