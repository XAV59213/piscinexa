import logging
from datetime import datetime, timedelta
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
    VERSION,
)

_LOGGER = logging.getLogger(__name__)

def get_translation(hass: HomeAssistant, key: str, placeholders: dict = None, default: str = None) -> str:
    """Récupère une traduction depuis le cache avec des placeholders."""
    try:
        translated = hass.data[DOMAIN]["translations"].get(key, default or key)
        if placeholders:
            return translated.format(**placeholders)
        return translated
    except Exception as e:
        _LOGGER.warning("Erreur lors de la récupération de la traduction pour la clé %s: %s", key, e)
        return default or key

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configurez les capteurs pour Piscinexa."""
    # S'assurer que "temperature" est défini dans les données de l'entrée
    data = entry.data.copy()
    if "temperature" not in data or not isinstance(data["temperature"], (int, float)):
        data["temperature"] = 20.0  # Valeur par défaut si manquante ou invalide
        hass.config_entries.async_update_entry(entry, data=data)

    name = entry.data["name"]
    sensors = [
        PiscinexaVolumeSensor(hass, entry, name),
        PiscinexaTempsFiltrationRecommandeSensor(hass, entry, name),
        PiscinexaTempsFiltrationEffectueSensor(hass, entry, name),
        PiscinexaTemperatureSensor(hass, entry, name),
        PiscinexaPhSensor(hass, entry, name),
        PiscinexaPhPlusAjouterSensor(hass, entry, name),
        PiscinexaPhMinusAjouterSensor(hass, entry, name),
        PiscinexaPhTargetSensor(hass, entry, name),
        PiscinexaChloreSensor(hass, entry, name),
        PiscinexaChloreTargetSensor(hass, entry, name),
        PiscinexaChloreAjouterSensor(hass, entry, name),
        PiscinexaChloreDifferenceSensor(hass, entry, name),
        PiscinexaPowerSensor(hass, entry, name),
        PiscinexaPoolStateSensor(hass, entry, name),
        PiscinexaPhDifferenceSensor(hass, entry, name),
        PiscinexaPhTreatmentSensor(hass, entry, name),
        PiscinexaChloreTreatmentSensor(hass, entry, name),
    ]
    async_add_entities(sensors, True)

class PiscinexaVolumeSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_volume_eau"
        self._attr_friendly_name = f"{name.capitalize()} Volume d'eau"
        self._attr_unique_id = f"{entry.entry_id}_volume_eau"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version=VERSION,
        )
        self._attr_icon = "mdi:pool"
        self._attr_native_unit_of_measurement = UNIT_CUBIC_METERS

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
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "volume_calculation_error",
                    {"name": self._name, "error": str(e)}
                )
            )
            return None

class PiscinexaTempsFiltrationRecommandeSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_tempsfiltration_recommande"
        self._attr_friendly_name = f"{name.capitalize()} Temps de filtration recommandé"
        self._attr_unique_id = f"{entry.entry_id}_temps_filtration_recommande"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version=VERSION,
        )
        self._attr_icon = "mdi:clock"
        self._attr_native_unit_of_measurement = UNIT_HOURS
        self._subscriptions = []
        sensor_id = self._entry.data.get("temperature_sensor")
        if sensor_id:
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [sensor_id], self._async_update_from_sensor
                )
            )

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_sensor(self, event):
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
                    _LOGGER.warning(
                        get_translation(
                            self._hass,
                            "temperature_conversion_error",
                            {"sensor_id": sensor_id, "error": str(e)}
                        )
                    )
                    return None
            else:
                _LOGGER.warning(
                    get_translation(
                        self._hass,
                        "temperature_sensor_unavailable",
                        {"sensor_id": sensor_id}
                    )
                )
        try:
            # S'assurer que "temperature" est valide
            temperature = float(self._entry.data.get("temperature", 20.0))
            return round(temperature / 2, 1)
        except (ValueError, TypeError) as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "default_temperature_invalid",
                    {"error": str(e)}
                )
            )
            return None

class PiscinexaTempsFiltrationEffectueSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_tempsfiltration_effectue"
        self._attr_friendly_name = f"{name.capitalize()} Temps de filtration effectué"
        self._attr_unique_id = f"{entry.entry_id}_temps_filtration_effectue"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version=VERSION,
        )
        self._attr_icon = "mdi:clock-check"
        self._attr_native_unit_of_measurement = UNIT_HOURS
        self._subscriptions = []
        self._filtration_time = 0.0
        self._last_active_time = None
        sensor_id = self._entry.data.get("power_sensor_entity_id")
        if sensor_id:
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [sensor_id], self._async_update_from_power_sensor
                )
            )

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_power_sensor(self, event):
        sensor_id = self._entry.data.get("power_sensor_entity_id")
        state = self._hass.states.get(sensor_id)
        current_time = datetime.now()

        if state and state.state not in ("unknown", "unavailable"):
            try:
                power = float(state.state)
                if power > 10:
                    if self._last_active_time is not None:
                        time_diff = (current_time - self._last_active_time).total_seconds() / 3600
                        self._filtration_time += time_diff
                    self._last_active_time = current_time
                else:
                    self._last_active_time = None
            except ValueError as e:
                _LOGGER.warning(
                    get_translation(
                        self._hass,
                        "non_numeric_power_sensor_value",
                        {"sensor_id": sensor_id, "error": str(e)}
                    )
                )
        else:
            self._last_active_time = None

        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        try:
            return round(self._filtration_time, 1)
        except Exception as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "filtration_time_read_error",
                    {"error": str(e)}
                )
            )
            return None

    @property
    def extra_state_attributes(self):
        attributes = {}
        try:
            attributes["last_active_time"] = (
                self._last_active_time.isoformat() if self._last_active_time else None
            )
            attributes["power_sensor"] = self._entry.data.get("power_sensor_entity_id", "N/A")
        except Exception as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "filtration_attributes_error",
                    {"error": str(e)}
                )
            )
        return attributes

class PiscinexaTemperatureSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_temperature"
        self._attr_friendly_name = f"{name.capitalize()} Température"
        self._attr_unique_id = f"{entry.entry_id}_temperature"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version=VERSION,
        )
        self._attr_icon = "mdi:thermometer"
        self._attr_native_unit_of_measurement = "°C"
        self._subscriptions = []
        sensor_id = self._entry.data.get("temperature_sensor")
        if sensor_id:
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [sensor_id], self._async_update_from_sensor
                )
            )

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_sensor(self, event):
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
                    _LOGGER.warning(
                        get_translation(
                            self._hass,
                            "temperature_sensor_unavailable",
                            {"sensor_id": sensor_id}
                        )
                    )
                    # Utiliser la température par défaut si le capteur est indisponible
                    try:
                        temperature = float(self._entry.data.get("temperature", 20.0))
                        return round(temperature, 1)
                    except (ValueError, TypeError) as e:
                        _LOGGER.error(
                            get_translation(
                                self._hass,
                                "default_temperature_invalid",
                                {"error": str(e)}
                            )
                        )
                        return None
                try:
                    value = float(state.state)
                    unit = state.attributes.get("unit_of_measurement", "").lower()
                    if unit in ("°f", "f", "fahrenheit"):
                        value = (value - 32) * 5 / 9
                    value = round(value, 1)
                    self._hass.data[DOMAIN][self._entry.entry_id]["temperature"] = value
                    return value
                except ValueError as e:
                    _LOGGER.error(
                        get_translation(
                            self._hass,
                            "non_numeric_sensor_value",
                            {"sensor_id": sensor_id, "state": state.state}
                        )
                    )
                    return None
        try:
            # S'assurer que "temperature" est valide
            temperature = float(self._entry.data.get("temperature", 20.0))
            return round(temperature, 1)
        except (ValueError, TypeError) as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "default_temperature_invalid",
                    {"error": str(e)}
                )
            )
            return None

class PiscinexaPhSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._entry = entry
        self._name = name
        self._hass = hass
        self._attr_name = f"{DOMAIN}_{name}_ph"
        self._attr_friendly_name = f"{name.capitalize()} pH Actuel"
        self._attr_unique_id = f"{entry.entry_id}_ph"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version=VERSION,
        )
        self._attr_icon = "mdi:water"
        self._attr_native_unit_of_measurement = None
        self._subscriptions = []
        sensor_id = self._entry.data.get("ph_sensor")
        if sensor_id:
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [sensor_id], self._async_update_from_sensor
                )
            )
        input_id = f"input_number.{name}_ph_current"
        if hass.states.get(input_id):  # Vérifier si l'entité existe
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [input_id], self._async_update_from_input
                )
            )
        else:
            _LOGGER.warning(
                get_translation(
                    self._hass,
                    "input_number_missing",
                    {"entity_id": input_id}
                )
            )

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_sensor(self, event):
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_input(self, event):
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        sensor_id = self._entry.data.get("ph_sensor")
        if sensor_id:
            state = self._hass.states.get(sensor_id)
            if state:
                if state.state in ("unknown", "unavailable"):
                    _LOGGER.warning(
                        get_translation(
                            self._hass,
                            "ph_sensor_unavailable",
                            {"sensor_id": sensor_id}
                        )
                    )
                    return None
                try:
                    value = round(float(state.state), 1)
                    self._hass.data[DOMAIN][self._entry.entry_id]["ph_current"] = value
                    input_id = f"input_number.{self._name}_ph_current"
                    if self._hass.states.get(input_id):
                        self._hass.states.async_set(
                            input_id,
                            value,
                            {
                                "friendly_name": f"{self._name.capitalize()} pH Actuel",
                                "min": 0,
                                "max": 14,
                                "step": 0.1,
                                "unit_of_measurement": None,
                            },
                        )
                    return value
                except ValueError as e:
                    _LOGGER.error(
                        get_translation(
                            self._hass,
                            "non_numeric_sensor_value",
                            {"sensor_id": sensor_id, "state": state.state}
                        )
                    )
                    return None
        input_state = self._hass.states.get(f"input_number.{self._name}_ph_current")
        if input_state and input_state.state not in ("unknown", "unavailable"):
            try:
                value = round(float(input_state.state), 1)
                self._hass.data[DOMAIN][self._entry.entry_id]["ph_current"] = value
                return value
            except Exception as e:
                _LOGGER.warning(
                    get_translation(
                        self._hass,
                        "input_number_read_error",
                        {"type": "pH", "error": str(e)}
                    )
                )
                return None
        try:
            return round(float(self._entry.data["ph_current"]), 1)
        except Exception as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "default_value_read_error",
                    {"type": "pH", "error": str(e)}
                )
            )
            return None

class PiscinexaPhPlusAjouterSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_ph_plus_ajouter"
        self._attr_friendly_name = f"{name.capitalize()} pH+ à ajouter"
        self._attr_unique_id = f"{entry.entry_id}_ph_plus_ajouter"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version=VERSION,
        )
        self._attr_icon = "mdi:bottle-tonic-plus"
        self._subscriptions = []
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
        self._input_select_id = f"input_select.{name}_ph_plus_treatment"
        if hass.states.get(self._input_select_id):
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [self._input_select_id], self._async_update_from_select
                )
            )
        else:
            _LOGGER.warning(
                get_translation(
                    self._hass,
                    "input_select_missing",
                    {"entity_id": self._input_select_id}
                )
            )

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_ph(self, event):
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_volume(self, event):
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_select(self, event):
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_unit_of_measurement(self):
        select_state = self._hass.states.get(self._input_select_id)
        if select_state and select_state.state not in ("unknown", "unavailable"):
            return UNIT_LITERS if select_state.state == "Liquide" else UNIT_GRAMS
        _LOGGER.debug(
            get_translation(
                self._hass,
                "ph_plus_unit_error",
                {"error": f"input_select {self._input_select_id} indisponible"}
            )
        )
        return UNIT_LITERS

    @property
    def native_value(self):
        try:
            ph_current = float(self._entry.data["ph_current"])
            ph_target = float(self._entry.data["ph_target"])
            if ph_current >= ph_target:
                return 0
            volume = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if volume and volume.state not in ("unknown", "unavailable"):
                volume_val = float(volume.state)
                ph_difference = ph_target - ph_current
                select_state = self._hass.states.get(self._input_select_id)
                treatment = select_state.state if select_state and select_state.state not in ("unknown", "unavailable") else "Liquide"
                if treatment == "Liquide":
                    dose = ph_difference * volume_val * 0.01
                else:
                    dose = ph_difference * volume_val * 1.0
                return round(dose, 2)
            return None
        except Exception as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "ph_plus_dose_error",
                    {"name": self._name, "error": str(e)}
                )
            )
            return None

    @property
    def extra_state_attributes(self):
        attributes = {}
        try:
            ph_current = float(self._entry.data["ph_current"])
            ph_target = float(self._entry.data["ph_target"])
            volume = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if volume:
                attributes["volume"] = float(volume.state)
            attributes["ph_current"] = ph_current
            attributes["ph_target"] = ph_target
        except Exception as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "ph_attributes_error",
                    {"error": str(e)}
                )
            )
        return attributes

class PiscinexaPhMinusAjouterSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_ph_minus_ajouter"
        self._attr_friendly_name = f"{name.capitalize()} pH- à ajouter"
        self._attr_unique_id = f"{entry.entry_id}_ph_minus_ajouter"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version=VERSION,
        )
        self._attr_icon = "mdi:water-minus"
        self._subscriptions = []
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
        self._input_select_id = f"input_select.{name}_ph_minus_treatment"
        if hass.states.get(self._input_select_id):
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [self._input_select_id], self._async_update_from_select
                )
            )
        else:
            _LOGGER.warning(
                get_translation(
                    self._hass,
                    "input_select_missing",
                    {"entity_id": self._input_select_id}
                )
            )

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_ph(self, event):
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_volume(self, event):
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_select(self, event):
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_unit_of_measurement(self):
        select_state = self._hass.states.get(self._input_select_id)
        if select_state and select_state.state not in ("unknown", "unavailable"):
            return UNIT_LITERS if select_state.state == "Liquide" else UNIT_GRAMS
        _LOGGER.debug(
            get_translation(
                self._hass,
                "ph_minus_unit_error",
                {"error": f"input_select {self._input_select_id} indisponible"}
            )
        )
        return UNIT_LITERS

    @property
    def native_value(self):
        try:
            ph_current = float(self._entry.data["ph_current"])
            ph_target = float(self._entry.data["ph_target"])
            if ph_current <= ph_target:
                return 0
            volume = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if volume and volume.state not in ("unknown", "unavailable"):
                volume_val = float(volume.state)
                ph_difference = ph_current - ph_target
                select_state = self._hass.states.get(self._input_select_id)
                treatment = select_state.state if select_state and select_state.state not in ("unknown", "unavailable") else "Liquide"
                if treatment == "Liquide":
                    dose = ph_difference * volume_val * 0.012
                else:
                    dose = ph_difference * volume_val * 1.2
                return round(dose, 2)
            return None
        except Exception as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "ph_minus_dose_error",
                    {"name": self._name, "error": str(e)}
                )
            )
            return None

    @property
    def extra_state_attributes(self):
        attributes = {}
        try:
            ph_current = float(self._entry.data["ph_current"])
            ph_target = float(self._entry.data["ph_target"])
            volume = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if volume:
                attributes["volume"] = float(volume.state)
            attributes["ph_current"] = ph_current
            attributes["ph_target"] = ph_target
        except Exception as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "ph_minus_attributes_error",
                    {"error": str(e)}
                )
            )
        return attributes

class PiscinexaPhTargetSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._entry = entry
        self._name = name
        self._hass = hass
        self._attr_name = f"{DOMAIN}_{name}_ph_target"
        self._attr_friendly_name = f"{name.capitalize()} pH Cible"
        self._attr_unique_id = f"{entry.entry_id}_ph_target"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version=VERSION,
        )
        self._attr_icon = "mdi:target"
        self._attr_native_unit_of_measurement = None
        self._subscriptions = []
        input_id = f"input_number.{name}_ph_target"
        if hass.states.get(input_id):  # Vérifier si l'entité existe
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [input_id], self._async_update_from_input
                )
            )
        else:
            _LOGGER.warning(
                get_translation(
                    self._hass,
                    "input_number_missing",
                    {"entity_id": input_id}
                )
            )

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_input(self, event):
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        try:
            return round(float(self._entry.data["ph_target"]), 1)
        except Exception as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "default_value_read_error",
                    {"type": "pH cible", "error": str(e)}
                )
            )
            return None

class PiscinexaChloreSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._entry = entry
        self._name = name
        self._hass = hass
        self._attr_name = f"{DOMAIN}_{name}_chlore"
        self._attr_friendly_name = f"{name.capitalize()} Chlore Actuel"
        self._attr_unique_id = f"{entry.entry_id}_chlore"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version=VERSION,
        )
        self._attr_icon = "mdi:water-check"
        self._attr_native_unit_of_measurement = UNIT_MG_PER_LITER
        self._subscriptions = []
        sensor_id = self._entry.data.get("chlore_sensor")
        if sensor_id:
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [sensor_id], self._async_update_from_sensor
                )
            )
        input_id = f"input_number.{name}_chlore_current"
        if hass.states.get(input_id):  # Vérifier si l'entité existe
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [input_id], self._async_update_from_input
                )
            )
        else:
            _LOGGER.warning(
                get_translation(
                    self._hass,
                    "input_number_missing",
                    {"entity_id": input_id}
                )
            )

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_sensor(self, event):
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_input(self, event):
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        sensor_id = self._entry.data.get("chlore_sensor")
        if sensor_id:
            state = self._hass.states.get(sensor_id)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    value = round(float(state.state), 1)
                    self._hass.data[DOMAIN][self._entry.entry_id]["chlore_current"] = value
                    input_id = f"input_number.{self._name}_chlore_current"
                    if self._hass.states.get(input_id):
                        self._hass.states.async_set(
                            input_id,
                            value,
                            {
                                "friendly_name": f"{self._name.capitalize()} Chlore Actuel",
                                "min": 0,
                                "max": 10,
                                "step": 0.1,
                                "unit_of_measurement": UNIT_MG_PER_LITER,
                            },
                        )
                    return value
                except Exception as e:
                    _LOGGER.warning(
                        get_translation(
                            self._hass,
                            "non_numeric_sensor_value",
                            {"sensor_id": sensor_id, "error": str(e)}
                        )
                    )
                    return None
        input_state = self._hass.states.get(f"input_number.{self._name}_chlore_current")
        if input_state and input_state.state not in ("unknown", "unavailable"):
            try:
                value = round(float(input_state.state), 1)
                self._hass.data[DOMAIN][self._entry.entry_id]["chlore_current"] = value
                return value
            except Exception as e:
                _LOGGER.warning(
                    get_translation(
                        self._hass,
                        "input_number_read_error",
                        {"type": "chlore", "error": str(e)}
                    )
                )
                return None
        try:
            return round(float(self._entry.data["chlore_current"]), 1)
        except Exception as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "default_value_read_error",
                    {"type": "chlore", "error": str(e)}
                )
            )
            return None

class PiscinexaChloreTargetSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._entry = entry
        self._name = name
        self._hass = hass
        self._attr_name = f"{DOMAIN}_{name}_chlore_target"
        self._attr_friendly_name = f"{name.capitalize()} Chlore Cible"
        self._attr_unique_id = f"{entry.entry_id}_chlore_target"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version=VERSION,
        )
        self._attr_icon = "mdi:target"
        self._attr_native_unit_of_measurement = UNIT_MG_PER_LITER
        self._subscriptions = []
        input_id = f"input_number.{name}_chlore_target"
        if hass.states.get(input_id):  # Vérifier si l'entité existe
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [input_id], self._async_update_from_input
                )
            )
        else:
            _LOGGER.warning(
                get_translation(
                    self._hass,
                    "input_number_missing",
                    {"entity_id": input_id}
                )
            )

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_input(self, event):
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        try:
            return round(float(self._entry.data["chlore_target"]), 1)
        except Exception as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "default_value_read_error",
                    {"type": "chlore cible", "error": str(e)}
                )
            )
            return None

class PiscinexaChloreAjouterSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_chloreaajouter"
        self._attr_friendly_name = f"{name.capitalize()} Chlore à Ajouter"
        self._attr_unique_id = f"{entry.entry_id}_chlore_a_ajouter"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version=VERSION,
        )
        self._attr_icon = "mdi:bottle-tonic-plus"
        self._message = None
        self._subscriptions = []
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
        self._input_select_id = f"input_select.{name}_chlore_treatment"
        if hass.states.get(self._input_select_id):
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [self._input_select_id], self._async_update_from_select
                )
            )
        else:
            _LOGGER.warning(
                get_translation(
                    self._hass,
                    "input_select_missing",
                    {"entity_id": self._input_select_id}
                )
            )

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_chlore(self, event):
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_volume(self, event):
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_temperature(self, event):
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_select(self, event):
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_unit_of_measurement(self):
        select_state = self._hass.states.get(self._input_select_id)
        if select_state and select_state.state not in ("unknown", "unavailable"):
            if select_state.state == "Liquide":
                return UNIT_LITERS
            elif select_state.state == "Pastille lente":
                return "unités"
            return UNIT_GRAMS
        _LOGGER.debug(
            get_translation(
                self._hass,
                "chlore_unit_error",
                {"error": f"input_select {self._input_select_id} indisponible"}
            )
        )
        return UNIT_GRAMS

    @property
    def native_value(self):
        try:
            chlore_current = float(self._entry.data["chlore_current"])
            chlore_target = float(self._entry.data["chlore_target"])
            volume_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if volume_entity and volume_entity.state not in ("unknown", "unavailable"):
                volume_val = float(volume_entity.state)
                temp_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_temperature")
                if temp_entity and temp_entity.state not in ("unknown", "unavailable"):
                    temperature = float(temp_entity.state)
                    temp_factor = max(1, 1 + (temperature - 20) * 0.02)
                    chlore_difference = chlore_target - chlore_current
                    select_state = self._hass.states.get(self._input_select_id)
                    treatment = select_state.state if select_state and select_state.state not in ("unknown", "unavailable") else "Chlore choc (poudre)"
                    if treatment == "Liquide":
                        dose = chlore_difference * volume_val * 0.1 * temp_factor
                    elif treatment == "Pastille lente":
                        dose = (chlore_difference * volume_val / 20) * temp_factor
                    else:
                        dose = chlore_difference * volume_val * 0.01 * temp_factor
                    if dose <= 0:
                        self._message = get_translation(self._hass, "remove_chlorine_message")
                        return 0
                    self._message = None
                    return round(dose, 2)
                self._message = get_translation(self._hass, "temperature_unavailable_message")
                return None
            self._message = get_translation(self._hass, "volume_unavailable_message")
            return None
        except Exception as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "chlore_dose_error",
                    {"name": self._name, "error": str(e)}
                )
            )
            self._message = get_translation(self._hass, "calculation_error_message")
            return None

    @property
    def extra_state_attributes(self):
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
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "chlore_attributes_error",
                    {"error": str(e)}
                )
            )
        return attributes

class PiscinexaChloreDifferenceSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_chloredifference"
        self._attr_friendly_name = f"{name.capitalize()} Chlore Différence"
        self._attr_unique_id = f"{entry.entry_id}_chlore_difference"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version=VERSION,
        )
        self._attr_icon = "mdi:delta"
        self._attr_native_unit_of_measurement = UNIT_MG_PER_LITER
        self._subscriptions = []
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"sensor.{DOMAIN}_{name}_chlore"], self._async_update_from_chlore
            )
        )

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_chlore(self, event):
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        try:
            chlore_current = float(self._entry.data["chlore_current"])
            chlore_target = float(self._entry.data["chlore_target"])
            difference = chlore_target - chlore_current
            return round(difference, 1)
        except Exception as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "chlore_difference_error",
                    {"name": self._name, "error": str(e)}
                )
            )
            return None

class PiscinexaPowerSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_consopuissance"
        self._attr_friendly_name = f"{name.capitalize()} Consommation puissance"
        self._attr_unique_id = f"{entry.entry_id}_conso_puissance"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version=VERSION,
        )
        self._attr_icon = "mdi:flash"
        self._attr_native_unit_of_measurement = "W"
        self._subscriptions = []
        sensor_id = self._entry.data.get("power_sensor_entity_id")
        if sensor_id:
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [sensor_id], self._async_update_from_sensor
                )
            )

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_sensor(self, event):
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
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
            _LOGGER.warning(
                get_translation(
                    self._hass,
                    "power_sensor_read_error",
                    {"error": str(e)}
                )
            )
            return None

class PiscinexaPoolStateSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_pool_state"
        self._attr_friendly_name = f"{name.capitalize()} État de la piscine"
        self._attr_unique_id = f"{entry.entry_id}_pool_state"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version=VERSION,
        )
        self._attr_icon = "mdi:pool"
        self._attr_native_unit_of_measurement = None
        self._subscriptions = []
        entities_to_track = [
            f"sensor.{DOMAIN}_{name}_temperature",
            f"sensor.{DOMAIN}_{name}_chlore",
            f"sensor.{DOMAIN}_{name}_ph",
            f"sensor.{DOMAIN}_{name}_tempsfiltration_recommande",
        ]
        self._subscriptions.append(
            async_track_state_change_event(
                hass, entities_to_track, self._async_update_from_sensors
            )
        )

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_sensors(self, event):
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        try:
            issues = []
            temp_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_temperature")
            if temp_entity and temp_entity.state not in ("unknown", "unavailable"):
                temperature = float(temp_entity.state)
                if temperature < 22:
                    issues.append(get_translation(self._hass, "temperature_too_cold"))
                elif temperature > 28:
                    issues.append(get_translation(self._hass, "temperature_too_hot"))
                else:
                    issues.append(get_translation(self._hass, "temperature_ideal"))
            else:
                issues.append(get_translation(self._hass, "temperature_unavailable"))
            chlore_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_chlore")
            if chlore_entity and chlore_entity.state not in ("unknown", "unavailable"):
                chlore = float(chlore_entity.state)
                if chlore < 1:
                    issues.append(get_translation(self._hass, "chlore_too_low"))
                elif chlore > 3:
                    issues.append(get_translation(self._hass, "chlore_too_high"))
                else:
                    issues.append(get_translation(self._hass, "chlore_ideal"))
            else:
                issues.append(get_translation(self._hass, "chlore_unavailable"))
            ph_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_ph")
            if ph_entity and ph_entity.state not in ("unknown", "unavailable"):
                ph = float(ph_entity.state)
                if ph < 7.2:
                    issues.append(get_translation(self._hass, "ph_too_low"))
                elif ph > 7.6:
                    issues.append(get_translation(self._hass, "ph_too_high"))
                else:
                    issues.append(get_translation(self._hass, "ph_ideal"))
            else:
                issues.append(get_translation(self._hass, "ph_unavailable"))
            filtration_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_tempsfiltration_recommande")
            if filtration_entity and filtration_entity.state not in ("unknown", "unavailable") and temp_entity:
                filtration_time = float(filtration_entity.state)
                required_filtration = temperature / 2
                if filtration_time < required_filtration:
                    issues.append(get_translation(self._hass, "filtration_insufficient"))
                else:
                    issues.append(get_translation(self._hass, "filtration_ideal"))
            else:
                issues.append(get_translation(self._hass, "filtration_unavailable"))
            if all(issue in [
                get_translation(self._hass, "temperature_ideal"),
                get_translation(self._hass, "chlore_ideal"),
                get_translation(self._hass, "ph_ideal"),
                get_translation(self._hass, "filtration_ideal")
            ] for issue in issues):
                return get_translation(self._hass, "swimming_allowed")
            else:
                return ", ".join(issues)
        except Exception as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "pool_state_error",
                    {"name": self._name, "error": str(e)}
                )
            )
            return get_translation(self._hass, "evaluation_error")

    @property
    def extra_state_attributes(self):
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
            filtration_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_tempsfiltration_recommande")
            if filtration_entity:
                attributes["temps_filtration_recommande"] = float(filtration_entity.state)
        except Exception as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "pool_state_attributes_error",
                    {"error": str(e)}
                )
            )
        return attributes

class PiscinexaPhDifferenceSensor(SensorEntity):
    """Capteur pour la différence entre le pH actuel et le pH cible."""
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_phdifference"
        self._attr_friendly_name = f"{name.capitalize()} pH Différence"
        self._attr_unique_id = f"{entry.entry_id}_ph_difference"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version=VERSION,
        )
        self._attr_icon = "mdi:delta"
        self._attr_native_unit_of_measurement = None
        self._subscriptions = []
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"sensor.{DOMAIN}_{name}_ph"], self._async_update_from_ph
            )
        )
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"sensor.{DOMAIN}_{name}_ph_target"], self._async_update_from_ph_target
            )
        )

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_ph(self, event):
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_ph_target(self, event):
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        try:
            ph_current = float(self._entry.data["ph_current"])
            ph_target = float(self._entry.data["ph_target"])
            difference = ph_target - ph_current
            return round(difference, 1)
        except Exception as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "ph_difference_error",
                    {"name": self._name, "error": str(e)}
                )
            )
            return None

class PiscinexaPhTreatmentSensor(SensorEntity):
    """Capteur pour le type de traitement pH sélectionné (pH+ ou pH-)."""
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_ph_treatment"
        self._attr_friendly_name = f"{name.capitalize()} pH Traitement"
        self._attr_unique_id = f"{entry.entry_id}_ph_treatment"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version=VERSION,
        )
        self._attr_icon = "mdi:water-pump"
        self._attr_native_unit_of_measurement = None
        self._subscriptions = []
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"sensor.{DOMAIN}_{name}_ph"], self._async_update_from_ph
            )
        )
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"sensor.{DOMAIN}_{name}_ph_target"], self._async_update_from_ph_target
            )
        )
        self._input_select_ph_plus = f"input_select.{name}_ph_plus_treatment"
        self._input_select_ph_minus = f"input_select.{name}_ph_minus_treatment"
        if hass.states.get(self._input_select_ph_plus):
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [self._input_select_ph_plus], self._async_update_from_select
                )
            )
        else:
            _LOGGER.warning(
                get_translation(
                    self._hass,
                    "input_select_missing",
                    {"entity_id": self._input_select_ph_plus}
                )
            )
        if hass.states.get(self._input_select_ph_minus):
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [self._input_select_ph_minus], self._async_update_from_select
                )
            )
        else:
            _LOGGER.warning(
                get_translation(
                    self._hass,
                    "input_select_missing",
                    {"entity_id": self._input_select_ph_minus}
                )
            )

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_ph(self, event):
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_ph_target(self, event):
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_select(self, event):
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        try:
            ph_current = float(self._entry.data["ph_current"])
            ph_target = float(self._entry.data["ph_target"])
            if ph_current < ph_target:
                select_state = self._hass.states.get(self._input_select_ph_plus)
                return select_state.state if select_state and select_state.state not in ("unknown", "unavailable") else "Liquide"
            elif ph_current > ph_target:
                select_state = self._hass.states.get(self._input_select_ph_minus)
                return select_state.state if select_state and select_state.state not in ("unknown", "unavailable") else "Liquide"
            return get_translation(self._hass, "no_treatment_needed")
        except Exception as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "ph_treatment_error",
                    {"name": self._name, "error": str(e)}
                )
            )
            return None

class PiscinexaChloreTreatmentSensor(SensorEntity):
    """Capteur pour le type de traitement chlore sélectionné."""
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_chlore_treatment"
        self._attr_friendly_name = f"{name.capitalize()} Chlore Traitement"
        self._attr_unique_id = f"{entry.entry_id}_chlore_treatment"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version=VERSION,
        )
        self._attr_icon = "mdi:water-check"
        self._attr_native_unit_of_measurement = None
        self._subscriptions = []
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"sensor.{DOMAIN}_{name}_chlore"], self._async_update_from_chlore
            )
        )
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"sensor.{DOMAIN}_{name}_chlore_target"], self._async_update_from_chlore_target
            )
        )
        self._input_select_id = f"input_select.{name}_chlore_treatment"
        if hass.states.get(self._input_select_id):
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [self._input_select_id], self._async_update_from_select
                )
            )
        else:
            _LOGGER.warning(
                get_translation(
                    self._hass,
                    "input_select_missing",
                    {"entity_id": self._input_select_id}
                )
            )

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_chlore(self, event):
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_chlore_target(self, event):
        self.async_schedule_update_ha_state(True)

    @callback
    def _async_update_from_select(self, event):
        self.async_schedule_update_ha_state(True)

    @property
    def name(self):
        return self._attr_friendly_name

    @property
    def native_value(self):
        try:
            chlore_current = float(self._entry.data["chlore_current"])
            chlore_target = float(self._entry.data["chlore_target"])
            if chlore_current < chlore_target:
                select_state = self._hass.states.get(self._input_select_id)
                return select_state.state if select_state and select_state.state not in ("unknown", "unavailable") else "Chlore choc (poudre)"
            return get_translation(self._hass, "no_treatment_needed")
        except Exception as e:
            _LOGGER.error(
                get_translation(
                    self._hass,
                    "chlore_treatment_error",
                    {"name": self._name, "error": str(e)}
                )
            )
            return None
