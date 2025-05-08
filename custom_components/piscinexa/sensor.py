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
from homeassistant.helpers.translation import async_get_translations
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
        PiscinexaPhPlusAjouterSensor(hass, entry, name),
        PiscinexaPhMinusAjouterSensor(hass, entry, name),
        PiscinexaPhTargetSensor(hass, entry, name),
        PiscinexaChloreSensor(hass, entry, name),
        PiscinexaChloreTargetSensor(hass, entry, name),
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
        self._attr_unique_id = f"{entry.entry_id}_volume_eau"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:pool"
        self._attr_unit_of_measurement = UNIT_CUBIC_METERS
        self._translations = None

    async def async_added_to_hass(self):
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
            integrations={DOMAIN},
        )
        if not self._translations:
            _LOGGER.error("Failed to load translations for Volume Eau")
        self._attr_name = self._translations.get("entity.sensor.piscinexa_volume_eau.name", "Volume Eau")
        _LOGGER.debug(f"Setting friendly_name for Volume Eau: {self._attr_name} (entity_id: {self.entity_id})")
        self.async_write_ha_state()

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
        self._attr_unique_id = f"{entry.entry_id}_temps_filtration"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:clock"
        self._attr_unit_of_measurement = UNIT_HOURS
        self._subscriptions = []
        self._translations = None
        sensor_id = self._entry.data.get("temperature_sensor")
        if sensor_id:
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [sensor_id], self._async_update_from_sensor
                )
            )

    async def async_added_to_hass(self):
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
            integrations={DOMAIN},
        )
        if not self._translations:
            _LOGGER.error("Failed to load translations for Temps Filtration")
        self._attr_name = self._translations.get("entity.sensor.piscinexa_tempsfiltration.name", "Temps Filtration")
        _LOGGER.debug(f"Setting friendly_name for Temps Filtration: {self._attr_name} (entity_id: {self.entity_id})")
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_sensor(self, event):
        self.async_schedule_update_ha_state(True)

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
            return round(float(self._entry.data["temperature"]) / 2, 1)
        except Exception as e:
            _LOGGER.error("Température par défaut invalide : %s", e)
            return None

class PiscinexaTemperatureSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_unique_id = f"{entry.entry_id}_temperature"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:thermometer"
        self._attr_unit_of_measurement = "°C"
        self._subscriptions = []
        self._translations = None
        sensor_id = self._entry.data.get("temperature_sensor")
        if sensor_id:
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [sensor_id], self._async_update_from_sensor
                )
            )

    async def async_added_to_hass(self):
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
            integrations={DOMAIN},
        )
        if not self._translations:
            _LOGGER.error("Failed to load translations for Température Eau")
        self._attr_name = self._translations.get("entity.sensor.piscinexa_temperature.name", "Température Eau")
        _LOGGER.debug(f"Setting friendly_name for Température Eau: {self._attr_name} (entity_id: {self.entity_id})")
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_sensor(self, event):
        self.async_schedule_update_ha_state(True)

    @property
    def native_value(self):
        sensor_id = self._entry.data.get("temperature_sensor")
        if sensor_id:
            state = self._hass.states.get(sensor_id)
            if state:
                if state.state in ("unknown", "unavailable"):
                    _LOGGER.warning("Capteur de température %s indisponible", sensor_id)
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
                    _LOGGER.error("Valeur non numérique pour capteur %s: %s", sensor_id, state.state)
                    return None
        try:
            return round(float(self._entry.data["temperature"]), 1)
        except Exception as e:
            _LOGGER.error("Température par défaut invalide : %s", e)
            return None

class PiscinexaPhSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._entry = entry
        self._name = name
        self._hass = hass
        self._attr_unique_id = f"{entry.entry_id}_ph"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:water"
        self._subscriptions = []
        self._translations = None
        sensor_id = self._entry.data.get("ph_sensor")
        if sensor_id:
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [sensor_id], self._async_update_from_sensor
                )
            )
        input_id = f"input_number.{name}_ph_current"
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [input_id], self._async_update_from_input
            )
        )

    async def async_added_to_hass(self):
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
            integrations={DOMAIN},
        )
        if not self._translations:
            _LOGGER.error("Failed to load translations for pH")
        self._attr_name = self._translations.get("entity.sensor.piscinexa_ph.name", "pH")
        _LOGGER.debug(f"Setting friendly_name for pH: {self._attr_name} (entity_id: {self.entity_id})")
        self.async_write_ha_state()

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
    def native_value(self):
        sensor_id = self._entry.data.get("ph_sensor")
        if sensor_id:
            state = self._hass.states.get(sensor_id)
            if state:
                if state.state in ("unknown", "unavailable"):
                    _LOGGER.warning("Capteur de pH %s indisponible", sensor_id)
                    return None
                try:
                    value = round(float(state.state), 1)
                    self._hass.data[DOMAIN][self._entry.entry_id]["ph_current"] = value
                    return value
                except ValueError as e:
                    _LOGGER.error("Valeur non numérique pour capteur %s: %s", sensor_id, state.state)
                    return None
        input_state = self._hass.states.get(f"input_number.{self._name}_ph_current")
        if input_state and input_state.state not in ("unknown", "unavailable"):
            try:
                value = round(float(input_state.state), 1)
                self._hass.data[DOMAIN][self._entry.entry_id]["ph_current"] = value
                return value
            except Exception as e:
                _LOGGER.warning("Erreur lecture pH depuis input_number : %s", e)
        try:
            return round(float(self._entry.data["ph_current"]), 1)
        except Exception as e:
            _LOGGER.error("Erreur lecture pH: %s", e)
            return None

class PiscinexaPhPlusAjouterSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_unique_id = f"{entry.entry_id}_ph_plus_ajouter"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:bottle-tonic-plus"
        self._subscriptions = []
        self._translations = None
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
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"input_select.{name}_ph_plus_treatment"], self._async_update_from_select
            )
        )

    async def async_added_to_hass(self):
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
            integrations={DOMAIN},
        )
        if not self._translations:
            _LOGGER.error("Failed to load translations for pH+ à Ajouter")
        self._attr_name = self._translations.get("entity.sensor.piscinexa_ph_plus_ajouter.name", "pH+ à Ajouter")
        _LOGGER.debug(f"Setting friendly_name for pH+ à Ajouter: {self._attr_name} (entity_id: {self.entity_id})")
        self.async_write_ha_state()

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
    def unit_of_measurement(self):
        try:
            select_state = self._hass.states.get(f"input_select.{self._name}_ph_plus_treatment")
            if select_state and select_state.state == "Liquide":
                return UNIT_LITERS
            return UNIT_GRAMS
        except Exception as e:
            _LOGGER.error("Erreur détermination unité pH+: %s", e)
            return UNIT_LITERS

    @property
    def native_value(self):
        try:
            ph_current = float(self._entry.data["ph_current"])
            ph_target = float(self._entry.data["ph_target"])
            if ph_current >= ph_target:
                return 0  # Pas besoin de pH+ si le pH est déjà trop élevé ou correct

            volume = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if volume and volume.state not in ("unknown", "unavailable"):
                volume_val = float(volume.state)
                ph_difference = ph_target - ph_current
                select_state = self._hass.states.get(f"input_select.{self._name}_ph_plus_treatment")
                treatment = select_state.state if select_state else "Liquide"
                if treatment == "Liquide":
                    dose = ph_difference * volume_val * 0.01  # 10 mL par m³ pour 0.1 pH
                else:  # Granulés
                    dose = ph_difference * volume_val * 1.0  # 100 g par m³ pour 0.1 pH
                return round(dose, 2)
            return None
        except Exception as e:
            _LOGGER.error("Erreur calcul dose pH+ pour %s: %s", self._name, e)
            return None

    @property
    def extra_state_attributes(self):
        attributes = {}
        try:
            ph_current = float(self._entry.data["ph_current"])
            ph_target = float(self._entry.data["ph_target"])
            volume = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if volume:
                attributes["volume"] = str(float(volume.state))
            attributes["ph_current"] = str(ph_current)
            attributes["ph_target"] = str(ph_target)
        except Exception as e:
            _LOGGER.error("Erreur récupération attributs pH+: %s", e)
        return attributes

class PiscinexaPhMinusAjouterSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_unique_id = f"{entry.entry_id}_ph_minus_ajouter"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:bottle-tonic-minus"
        self._subscriptions = []
        self._translations = None
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
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"input_select.{name}_ph_minus_treatment"], self._async_update_from_select
            )
        )

    async def async_added_to_hass(self):
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
            integrations={DOMAIN},
        )
        if not self._translations:
            _LOGGER.error("Failed to load translations for pH- à Ajouter")
        self._attr_name = self._translations.get("entity.sensor.piscinexa_ph_minus_ajouter.name", "pH- à Ajouter")
        _LOGGER.debug(f"Setting friendly_name for pH- à Ajouter: {self._attr_name} (entity_id: {self.entity_id})")
        self.async_write_ha_state()

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
    def unit_of_measurement(self):
        try:
            select_state = self._hass.states.get(f"input_select.{self._name}_ph_minus_treatment")
            if select_state and select_state.state == "Liquide":
                return UNIT_LITERS
            return UNIT_GRAMS
        except Exception as e:
            _LOGGER.error("Erreur détermination unité pH-: %s", e)
            return UNIT_LITERS

    @property
    def native_value(self):
        try:
            ph_current = float(self._entry.data["ph_current"])
            ph_target = float(self._entry.data["ph_target"])
            if ph_current <= ph_target:
                return 0  # Pas besoin de pH- si le pH est déjà trop bas ou correct

            volume = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if volume and volume.state not in ("unknown", "unavailable"):
                volume_val = float(volume.state)
                ph_difference = ph_current - ph_target
                select_state = self._hass.states.get(f"input_select.{self._name}_ph_minus_treatment")
                treatment = select_state.state if select_state else "Liquide"
                if treatment == "Liquide":
                    dose = ph_difference * volume_val * 0.012  # 12 mL par m³ pour 0.1 pH
                else:  # Granulés
                    dose = ph_difference * volume_val * 1.2  # 120 g par m³ pour 0.1 pH
                return round(dose, 2)
            return None
        except Exception as e:
            _LOGGER.error("Erreur calcul dose pH- pour %s: %s", self._name, e)
            return None

    @property
    def extra_state_attributes(self):
        attributes = {}
        try:
            ph_current = float(self._entry.data["ph_current"])
            ph_target = float(self._entry.data["ph_target"])
            volume = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if volume:
                attributes["volume"] = str(float(volume.state))
            attributes["ph_current"] = str(ph_current)
            attributes["ph_target"] = str(ph_target)
        except Exception as e:
            _LOGGER.error("Erreur récupération attributs pH-: %s", e)
        return attributes

class PiscinexaPhTargetSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._entry = entry
        self._name = name
        self._hass = hass
        self._attr_unique_id = f"{entry.entry_id}_ph_target"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:target"
        self._subscriptions = []
        self._translations = None
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"input_number.{name}_ph_target"], self._async_update_from_input
            )
        )

    async def async_added_to_hass(self):
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
            integrations={DOMAIN},
        )
        if not self._translations:
            _LOGGER.error("Failed to load translations for pH Cible")
        self._attr_name = self._translations.get("entity.sensor.piscinexa_ph_target.name", "pH Cible")
        _LOGGER.debug(f"Setting friendly_name for pH Cible: {self._attr_name} (entity_id: {self.entity_id})")
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_input(self, event):
        self.async_schedule_update_ha_state(True)

    @property
    def native_value(self):
        try:
            return round(float(self._entry.data["ph_target"]), 1)
        except Exception as e:
            _LOGGER.error("Erreur lecture pH cible: %s", e)
            return None

class PiscinexaChloreSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._entry = entry
        self._name = name
        self._hass = hass
        self._attr_unique_id = f"{entry.entry_id}_chlore"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:water-check"
        self._attr_unit_of_measurement = UNIT_MG_PER_LITER
        self._subscriptions = []
        self._translations = None
        sensor_id = self._entry.data.get("chlore_sensor")
        if sensor_id:
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [sensor_id], self._async_update_from_sensor
                )
            )
        input_id = f"input_number.{name}_chlore_current"
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [input_id], self._async_update_from_input
            )
        )

    async def async_added_to_hass(self):
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
            integrations={DOMAIN},
        )
        if not self._translations:
            _LOGGER.error("Failed to load translations for Chlore")
        self._attr_name = self._translations.get("entity.sensor.piscinexa_chlore.name", "Chlore")
        _LOGGER.debug(f"Setting friendly_name for Chlore: {self._attr_name} (entity_id: {self.entity_id})")
        self.async_write_ha_state()

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
    def native_value(self):
        sensor_id = self._entry.data.get("chlore_sensor")
        if sensor_id:
            state = self._hass.states.get(sensor_id)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    value = round(float(state.state), 1)
                    self._hass.data[DOMAIN][self._entry.entry_id]["chlore_current"] = value
                    return value
                except Exception as e:
                    _LOGGER.warning("Erreur lecture chlore depuis capteur %s : %s", sensor_id, e)
        input_state = self._hass.states.get(f"input_number.{self._name}_chlore_current")
        if input_state and input_state.state not in ("unknown", "unavailable"):
            try:
                value = round(float(input_state.state), 1)
                self._hass.data[DOMAIN][self._entry.entry_id]["chlore_current"] = value
                return value
            except Exception as e:
                _LOGGER.warning("Erreur lecture chlore depuis input_number : %s", e)
        try:
            return round(float(self._entry.data["chlore_current"]), 1)
        except Exception as e:
            _LOGGER.error("Erreur lecture chlore: %s", e)
            return None

class PiscinexaChloreTargetSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._entry = entry
        self._name = name
        self._hass = hass
        self._attr_unique_id = f"{entry.entry_id}_chlore_target"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:target"
        self._attr_unit_of_measurement = UNIT_MG_PER_LITER
        self._subscriptions = []
        self._translations = None
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"input_number.{name}_chlore_target"], self._async_update_from_input
            )
        )

    async def async_added_to_hass(self):
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
            integrations={DOMAIN},
        )
        if not self._translations:
            _LOGGER.error("Failed to load translations for Chlore Cible")
        self._attr_name = self._translations.get("entity.sensor.piscinexa_chlore_target.name", "Chlore Cible")
        _LOGGER.debug(f"Setting friendly_name for Chlore Cible: {self._attr_name} (entity_id: {self.entity_id})")
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_input(self, event):
        self.async_schedule_update_ha_state(True)

    @property
    def native_value(self):
        try:
            return round(float(self._entry.data["chlore_target"]), 1)
        except Exception as e:
            _LOGGER.error("Erreur lecture chlore cible: %s", e)
            return None

class PiscinexaChloreAjouterSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_unique_id = f"{entry.entry_id}_chlore_a_ajouter"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:bottle-tonic-plus"
        self._message = None
        self._translations = {}
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
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"input_select.{name}_chlore_treatment"], self._async_update_from_select
            )
        )

    async def async_added_to_hass(self):
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
            integrations={DOMAIN},
        )
        if not self._translations:
            _LOGGER.error("Failed to load translations for Chlore à Ajouter")
        self._attr_name = self._translations.get("entity.sensor.piscinexa_chloreaajouter.name", "Chlore à Ajouter")
        _LOGGER.debug(f"Setting friendly_name for Chlore à Ajouter: {self._attr_name} (entity_id: {self.entity_id})")
        self.async_write_ha_state()

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

    def _get_translation(self, key: str) -> str:
        translation_key = key.format(name=self._name)
        translated = self._translations.get(translation_key, translation_key)
        return translated

    @property
    def unit_of_measurement(self):
        select_state = self._hass.states.get(f"input_select.{self._name}_chlore_treatment")
        if select_state:
            if select_state.state == "Liquide":
                return UNIT_LITERS
            elif select_state.state == "Pastille lente":
                return "unités"
            return UNIT_GRAMS
        return UNIT_GRAMS

    @property
    def native_value(self):
        try:
            chlore_current = float(self._entry.data["chlore_current"])
            chlore_target = float(self._entry.data["chlore_target"])
            chlore_difference = chlore_target - chlore_current
            if chlore_difference <= 0:
                self._message = self._get_translation(
                    "entity.sensor.piscinexa_{name}_chloreaajouter.messages.remove_chlorine"
                )
                return 0

            volume_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if volume_entity and volume_entity.state not in ("unknown", "unavailable"):
                volume_val = float(volume_entity.state)
            else:
                self._message = self._get_translation(
                    "entity.sensor.piscinexa_{name}_chloreaajouter.messages.volume_unavailable"
                )
                return None

            temp_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_temperature")
            if temp_entity and temp_entity.state not in ("unknown", "unavailable"):
                temperature = float(temp_entity.state)
                temp_factor = max(1, 1 + (temperature - 20) * 0.02)
            else:
                self._message = self._get_translation(
                    "entity.sensor.piscinexa_{name}_chloreaajouter.messages.temperature_unavailable"
                )
                return None

            select_state = self._hass.states.get(f"input_select.{self._name}_chlore_treatment")
            treatment = select_state.state if select_state else "Chlore choc (poudre)"
            self._treatment_type = treatment

            if treatment == "Liquide":
                dose_per_mg_L = volume_val * 0.1
                dose = chlore_difference * dose_per_mg_L * temp_factor
                self._dose_unit = UNIT_LITERS
            elif treatment == "Pastille lente":
                dose_per_mg_L = volume_val / 20
                dose = chlore_difference * dose_per_mg_L * temp_factor
                self._dose_unit = "unités"
            else:
                dose_per_mg_L = volume_val * 10
                dose = chlore_difference * dose_per_mg_L * temp_factor
                self._dose_unit = UNIT_GRAMS

            self._calculated_dose = dose
            self._dose_per_mg_L = dose_per_mg_L
            self._message = None
            return round(dose, 2)
        except Exception as e:
            _LOGGER.error("Erreur calcul dose chlore pour %s: %s", self._name, e)
            self._message = self._get_translation(
                "entity.sensor.piscinexa_{name}_chloreaajouter.messages.calculation_error"
            )
            return None

    @property
    def extra_state_attributes(self):
        attributes = {}
        try:
            attributes["chlore_current"] = str(float(self._entry.data["chlore_current"]))
            attributes["chlore_target"] = str(float(self._entry.data["chlore_target"]))
            volume_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_volume_eau")
            if volume_entity:
                attributes["volume"] = str(float(volume_entity.state))
            temp_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_temperature")
            if temp_entity:
                attributes["temperature"] = str(float(temp_entity.state))
                attributes["temp_factor"] = str(max(1, 1 + (float(temp_entity.state) - 20) * 0.02))
            if self._message:
                attributes["message"] = self._message
            attributes["treatment_type"] = getattr(self, '_treatment_type', "Chlore choc (poudre)")
            attributes["dose_unit"] = getattr(self, '_dose_unit', UNIT_GRAMS)
            attributes["calculated_dose"] = str(getattr(self, '_calculated_dose', 0.0))
            attributes["dose_per_mg_L"] = str(getattr(self, '_dose_per_mg_L', 0.0))
        except Exception as e:
            _LOGGER.error("Erreur récupération attributs supplémentaires: %s", e)
        return attributes

class PiscinexaChloreDifferenceSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_unique_id = f"{entry.entry_id}_chlore_difference"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:delta"
        self._attr_unit_of_measurement = UNIT_MG_PER_LITER
        self._subscriptions = []
        self._translations = None
        self._subscriptions.append(
            async_track_state_change_event(
                hass, [f"sensor.{DOMAIN}_{name}_chlore"], self._async_update_from_chlore
            )
        )

    async def async_added_to_hass(self):
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
            integrations={DOMAIN},
        )
        if not self._translations:
            _LOGGER.error("Failed to load translations for Différence Chlore")
        self._attr_name = self._translations.get("entity.sensor.piscinexa_chloredifference.name", "Différence Chlore")
        _LOGGER.debug(f"Setting friendly_name for Différence Chlore: {self._attr_name} (entity_id: {self.entity_id})")
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_chlore(self, event):
        self.async_schedule_update_ha_state(True)

    @property
    def native_value(self):
        try:
            chlore_current = float(self._entry.data["chlore_current"])
            chlore_target = float(self._entry.data["chlore_target"])
            difference = chlore_target - chlore_current
            return round(difference, 1)
        except Exception as e:
            _LOGGER.error("Erreur calcul différence chlore pour %s: %s", self._name, e)
            return None

class PiscinexaLogSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self._hass = hass
        self._entry = entry
        self._name = entry.data["name"]
        self._attr_unique_id = f"{entry.entry_id}_log"
        self._state = deque(maxlen=10)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{self._name}")},
            name=self._name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:book"
        self._translations = {}
        self._default_value = "No actions"

    async def async_added_to_hass(self):
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
            integrations={DOMAIN},
        )
        if not self._translations:
            _LOGGER.error("Failed to load translations for Journal Piscine")
        self._attr_name = self._translations.get("entity.sensor.piscinexa_log.name", "Journal Piscine")
        self._default_value = self._translations.get(
            "entity.sensor.piscinexa_log.default_value", "Aucune action"
        )
        _LOGGER.debug(f"Setting friendly_name for Journal Piscine: {self._attr_name} (entity_id: {self.entity_id})")
        self.async_write_ha_state()

    def _get_translation(self, key: str) -> str:
        translation_key = key.format(name=self._name)
        translated = self._translations.get(translation_key, translation_key)
        return translated.format(name=self._name)

    def log_action(self, action: str):
        self._state.append(f"{datetime.now()}: {action}")
        self.async_write_ha_state()

    @property
    def native_value(self):
        return "\n".join(self._state) if self._state else self._default_value

class PiscinexaPowerSensor(SensorEntity):
    def __init__(self, hass, entry, name):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_unique_id = f"{entry.entry_id}_conso_puissance"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:flash"
        self._attr_unit_of_measurement = "W"
        self._subscriptions = []
        self._translations = None
        sensor_id = self._entry.data.get("power_sensor_entity_id")
        if sensor_id:
            self._subscriptions.append(
                async_track_state_change_event(
                    hass, [sensor_id], self._async_update_from_sensor
                )
            )

    async def async_added_to_hass(self):
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
            integrations={DOMAIN},
        )
        if not self._translations:
            _LOGGER.error("Failed to load translations for Consommation Puissance")
        self._attr_name = self._translations.get("entity.sensor.piscinexa_consopuissance.name", "Consommation Puissance")
        _LOGGER.debug(f"Setting friendly_name for Consommation Puissance: {self._attr_name} (entity_id: {self.entity_id})")
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_sensor(self, event):
        self.async_schedule_update_ha_state(True)

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
            _LOGGER.warning("Erreur lecture capteur puissance : %s", e)
        return None

class PiscinexaPoolStateSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str):
        self._hass = hass
        self._entry = entry
        self._name = name
        self._attr_unique_id = f"{entry.entry_id}_pool_state"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"piscinexa_{name}")},
            name=name.capitalize(),
            manufacturer="Piscinexa",
            model="Piscine",
            sw_version="1.0.2",
        )
        self._attr_icon = "mdi:pool"
        self._translations = {}
        self._subscriptions = []
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

    async def async_added_to_hass(self):
        self._translations = await async_get_translations(
            self._hass,
            self._hass.config.language,
            "entity",
            integrations={DOMAIN},
        )
        if not self._translations:
            _LOGGER.error("Failed to load translations for État Piscine")
        self._attr_name = self._translations.get("entity.sensor.piscinexa_pool_state.name", "État Piscine")
        _LOGGER.debug(f"Setting friendly_name for État Piscine: {self._attr_name} (entity_id: {self.entity_id})")
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        for subscription in self._subscriptions:
            subscription()
        self._subscriptions.clear()

    @callback
    def _async_update_from_sensors(self, event):
        self.async_schedule_update_ha_state(True)

    def _get_translation(self, key: str) -> str:
        translation_key = key.format(name=self._name)
        translated = self._translations.get(translation_key, translation_key)
        return translated.format(name=self._name)

    @property
    def native_value(self):
        try:
            issues = []
            temp_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_temperature")
            temperature = None
            if temp_entity and temp_entity.state not in ("unknown", "unavailable"):
                temperature = float(temp_entity.state)
                if temperature < 22:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.temperature_too_cold"
                    ))
                elif temperature > 28:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.temperature_too_hot"
                    ))
                else:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.temperature_ideal"
                    ))
            else:
                issues.append(self._get_translation(
                    "entity.sensor.piscinexa_{name}_pool_state.states.temperature_unavailable"
                ))

            chlore_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_chlore")
            if chlore_entity and chlore_entity.state not in ("unknown", "unavailable"):
                chlore = float(chlore_entity.state)
                if chlore < 1:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.chlore_too_low"
                    ))
                elif chlore > 3:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.chlore_too_high"
                    ))
                else:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.chlore_ideal"
                    ))
            else:
                issues.append(self._get_translation(
                    "entity.sensor.piscinexa_{name}_pool_state.states.chlore_unavailable"
                ))

            ph_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_ph")
            if ph_entity and ph_entity.state not in ("unknown", "unavailable"):
                ph = float(ph_entity.state)
                if ph < 7.2:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.ph_too_low"
                    ))
                elif ph > 7.6:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.ph_too_high"
                    ))
                else:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.ph_ideal"
                    ))
            else:
                issues.append(self._get_translation(
                    "entity.sensor.piscinexa_{name}_pool_state.states.ph_unavailable"
                ))

            filtration_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_tempsfiltration")
            if filtration_entity and filtration_entity.state not in ("unknown", "unavailable") and temp_entity:
                filtration_time = float(filtration_entity.state)
                required_filtration = temperature / 2
                if filtration_time < required_filtration:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.filtration_insufficient"
                    ))
                else:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.filtration_ideal"
                    ))
            else:
                issues.append(self._get_translation(
                    "entity.sensor.piscinexa_{name}_pool_state.states.filtration_unavailable"
                ))

            ideal_states = [
                self._get_translation(
                    "entity.sensor.piscinexa_{name}_pool_state.states.temperature_ideal"
                ),
                self._get_translation(
                    "entity.sensor.piscinexa_{name}_pool_state.states.chlore_ideal"
                ),
                self._get_translation(
                    "entity.sensor.piscinexa_{name}_pool_state.states.ph_ideal"
                ),
                self._get_translation(
                    "entity.sensor.piscinexa_{name}_pool_state.states.filtration_ideal"
                ),
            ]

            if all(issue in ideal_states for issue in issues):
                return self._get_translation(
                    "entity.sensor.piscinexa_{name}_pool_state.states.swimming_allowed"
                )
            else:
                return issues[0]
        except Exception as e:
            _LOGGER.error("Erreur calcul état piscine pour %s: %s", self._name, e)
            return self._get_translation(
                "entity.sensor.piscinexa_{name}_pool_state.states.evaluation_error"
            )

    @property
    def extra_state_attributes(self):
        attributes = {}
        try:
            issues = []
            temp_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_temperature")
            if temp_entity and temp_entity.state not in ("unknown", "unavailable"):
                temperature = float(temp_entity.state)
                attributes["temperature"] = str(temperature)
                if temperature < 22:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.temperature_too_cold"
                    ))
                elif temperature > 28:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.temperature_too_hot"
                    ))
                else:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.temperature_ideal"
                    ))
            else:
                issues.append(self._get_translation(
                    "entity.sensor.piscinexa_{name}_pool_state.states.temperature_unavailable"
                ))

            chlore_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_chlore")
            if chlore_entity and chlore_entity.state not in ("unknown", "unavailable"):
                chlore = float(chlore_entity.state)
                attributes["chlore"] = str(chlore)
                if chlore < 1:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.chlore_too_low"
                    ))
                elif chlore > 3:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.chlore_too_high"
                    ))
                else:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.chlore_ideal"
                    ))
            else:
                issues.append(self._get_translation(
                    "entity.sensor.piscinexa_{name}_pool_state.states.chlore_unavailable"
                ))

            ph_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_ph")
            if ph_entity and ph_entity.state not in ("unknown", "unavailable"):
                ph = float(ph_entity.state)
                attributes["ph"] = str(ph)
                if ph < 7.2:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.ph_too_low"
                    ))
                elif ph > 7.6:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.ph_too_high"
                    ))
                else:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.ph_ideal"
                    ))
            else:
                issues.append(self._get_translation(
                    "entity.sensor.piscinexa_{name}_pool_state.states.ph_unavailable"
                ))

            filtration_entity = self._hass.states.get(f"sensor.{DOMAIN}_{self._name}_tempsfiltration")
            if filtration_entity and filtration_entity.state not in ("unknown", "unavailable"):
                filtration_time = float(filtration_entity.state)
                attributes["temps_filtration"] = str(filtration_time)
                if temp_entity and temp_entity.state not in ("unknown", "unavailable"):
                    temperature = float(temp_entity.state)
                    required_filtration = temperature / 2
                    if filtration_time < required_filtration:
                        issues.append(self._get_translation(
                            "entity.sensor.piscinexa_{name}_pool_state.states.filtration_insufficient"
                        ))
                    else:
                        issues.append(self._get_translation(
                            "entity.sensor.piscinexa_{name}_pool_state.states.filtration_ideal"
                        ))
                else:
                    issues.append(self._get_translation(
                        "entity.sensor.piscinexa_{name}_pool_state.states.filtration_unavailable"
                    ))
            else:
                issues.append(self._get_translation(
                    "entity.sensor.piscinexa_{name}_pool_state.states.filtration_unavailable"
                ))

            attributes["issues"] = ", ".join(issues)
        except Exception as e:
            _LOGGER.error("Erreur récupération attributs état piscine: %s", e)
        return attributes
