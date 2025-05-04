import logging
from datetime import datetime
from collections import deque
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
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
        PiscinexaTemperatureSensor(hass, entry, name),  # Ajout du nouveau capteur de température
        PiscinexaPhSensor(hass, entry, name),
        PiscinexaPhAjouterSensor(hass, entry, name),
        PiscinexaChloreSensor(hass, entry, name),
        PiscinexaChloreAjouterSensor(hass, entry, name),
        PiscinexaPowerSensor(hass, entry, name),
        log_sensor,
    ]
    async_add_entities(sensors, True)

class PiscinexaVolumeSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_volume_eau"
        self._attr_unit_of_measurement = UNIT_CUBIC_METERS
        self._attr_icon = "mdi:pool"
        self._attr_unique_id = f"{entry.entry_id}_volume_eau"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=f"Piscinexa {name.capitalize()}",
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.0",
        )

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

class PiscinexaTempsFiltrationSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_temps_filtration"
        self._attr_unit_of_measurement = UNIT_HOURS
        self._attr_icon = "mdi:clock"
        self._attr_unique_id = f"{entry.entry_id}_temps_filtration"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=f"Piscinexa {name.capitalize()}",
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.0",
        )

    @property
    def native_value(self):
        sensor_id = self._entry.data.get("temperature_sensor")
        if sensor_id:
            state = self._hass.states.get(sensor_id)
            if state:
                try:
                    return round(float(state.state) / 2, 1)
                except Exception as e:
                    _LOGGER.warning("Erreur de conversion température depuis %s : %s", sensor_id, e)
        try:
            return round(self._entry.data["temperature"] / 2, 1)
        except Exception as e:
            _LOGGER.error("Température par défaut invalide : %s", e)
            return None

class PiscinexaTemperatureSensor(SensorEntity):
    """Capteur pour afficher la température mesurée ou par défaut."""
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_temperature"
        self._attr_unit_of_measurement = "°C"
        self._attr_icon = "mdi:thermometer"
        self._attr_unique_id = f"{entry.entry_id}_temperature"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=f"Piscinexa {name.capitalize()}",
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.0",
        )

    @property
    def native_value(self):
        sensor_id = self._entry.data.get("temperature_sensor")
        if sensor_id:
            state = self._hass.states.get(sensor_id)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    return round(float(state.state), 1)
                except Exception as e:
                    _LOGGER.warning("Erreur lecture température depuis %s : %s", sensor_id, e)
        try:
            return round(float(self._entry.data["temperature"]), 1)
        except Exception as e:
            _LOGGER.error("Température par défaut invalide : %s", e)
            return None

class PiscinexaPhSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_ph"
        self._attr_icon = "mdi:water-ph"
        self._attr_unique_id = f"{entry.entry_id}_ph"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=f"Piscinexa {name.capitalize()}",
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.0",
        )

    @property
    def native_value(self):
        try:
            ph = float(self._entry.data["ph_current"])
            return round(ph, 1)
        except Exception as e:
            _LOGGER.error("Erreur lecture pH: %s", e)
            return None

class PiscinexaPhAjouterSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_ph_a_ajouter"
        self._attr_unit_of_measurement = UNIT_LITERS
        self._attr_icon = "mdi:bottle-tonic-plus"
        self._attr_unique_id = f"{entry.entry_id}_ph_a_ajouter"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=f"Piscinexa {name.capitalize()}",
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.0",
        )

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

class PiscinexaChloreSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_chlore"
        self._attr_unit_of_measurement = UNIT_MG_PER_LITER
        self._attr_icon = "mdi:water-check"
        self._attr_unique_id = f"{entry.entry_id}_chlore"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=f"Piscinexa {name.capitalize()}",
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.0",
        )

    @property
    def native_value(self):
        try:
            chlore = float(self._entry.data["chlore_current"])
            return round(chlore, 1)
        except Exception as e:
            _LOGGER.error("Erreur lecture chlore: %s", e)
            return None

class PiscinexaChloreAjouterSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_name = f"{DOMAIN}_{name}_chlore_a_ajouter"
        self._attr_unit_of_measurement = UNIT_GRAMS
        self._attr_icon = "mdi:bottle-tonic-plus"
        self._attr_unique_id = f"{entry.entry_id}_chlore_a_ajouter"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=f"Piscinexa {name.capitalize()}",
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.0",
        )

    @property
    def native_value(self):
        try:
            chlore_current = float(self._entry.data["chlore_current"])
            chlore_target = float(self._entry.data["chlore_target"])
            volume = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if volume:
                volume_val = float(volume.state)
                dose = (chlore_target - chlore_current) * volume_val * 10
                return round(dose, 2) if dose > 0 else 0
            return None
        except Exception as e:
            _LOGGER.error("Erreur calcul dose chlore: %s", e)
            return None

class PiscinexaLogSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self._hass = hass
        self._entry = entry
        self._name = entry.data["name"]
        self._attr_name = f"{DOMAIN}_{self._name}_log"
        self._attr_icon = "mdi:book"  # Changement de l'icône de mdi:notebook à mdi:book
        self._attr_unique_id = f"{entry.entry_id}_log"
        self._state = deque(maxlen=10)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{self._name}")},
            name=f"Piscinexa {self._name.capitalize()}",
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.0",
        )

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
        self._attr_name = f"{DOMAIN}_{name}_conso_puissance"
        self._attr_icon = "mdi:flash"
        self._attr_unit_of_measurement = "W"
        self._attr_unique_id = f"{entry.entry_id}_conso_puissance"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=f"Piscinexa {name.capitalize()}",
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.0",
        )

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
