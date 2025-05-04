"""Flux de configuration pour Piscinexa."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, POOL_TYPE_SQUARE, POOL_TYPE_ROUND

_LOGGER = logging.getLogger(__name__)

class PiscinexaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Flux de configuration pour Piscinexa."""
    VERSION = 1

    def __init__(self):
        self._data = {}

    async def async_step_user(self, user_input=None):
        """Step 1 : demander le nom et le type de piscine."""
        errors = {}
        if user_input is not None:
            try:
                name = user_input["name"].strip().lower().replace(" ", "_")
                # Vérifier si le nom est unique
                for entry in self._async_current_entries():
                    if entry.data.get("name") == name:
                        errors["name"] = "name_duplicate"
                        break
                if not name:
                    errors["name"] = "name_invalid"
                if not errors:
                    self._data["name"] = name
                    self._data["pool_type"] = user_input["pool_type"]
                    return await self.async_step_dimensions()
            except Exception as e:
                errors["base"] = f"unexpected_error: {str(e)}"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("name", default="piscine"): str,
                vol.Required("pool_type", default=POOL_TYPE_SQUARE): vol.In({
                    POOL_TYPE_SQUARE: "Carrée",
                    POOL_TYPE_ROUND: "Ronde"
                }),
            }),
            errors=errors,
        )

    async def async_step_dimensions(self, user_input=None):
        """Step 2 : demander les dimensions en fonction du type de piscine."""
        errors = {}
        pool_type = self._data["pool_type"]

        if user_input is not None:
            dimension_fields = []
            if pool_type == POOL_TYPE_SQUARE:
                dimension_fields = [
                    ("length", "dimensions_invalid", lambda x: x > 0),
                    ("width", "dimensions_invalid", lambda x: x > 0),
                    ("depth", "dimensions_invalid", lambda x: x > 0),
                ]
            else:
                dimension_fields = [
                    ("diameter", "dimensions_invalid", lambda x: x > 0),
                    ("depth", "dimensions_invalid", lambda x: x > 0),
                ]

            for field, error_key, validator in dimension_fields:
                try:
                    value = user_input.get(field)
                    if value is None or value == "":
                        errors[field] = "required_field"
                        continue
                    value = str(value).replace(",", ".").strip()
                    value = float(value)
                    if not validator(value):
                        errors[field] = error_key
                    self._data[field] = value
                except ValueError:
                    errors[field] = "invalid_number"

            if not errors:
                return await self.async_step_ph_config()

        schema = {}
        if pool_type == POOL_TYPE_SQUARE:
            schema.update({
                vol.Required("length", default=5.0): vol.Coerce(float),
                vol.Required("width", default=4.0): vol.Coerce(float),
                vol.Required("depth", default=1.5): vol.Coerce(float),
            })
        else:
            schema.update({
                vol.Required("diameter", default=4.0): vol.Coerce(float),
                vol.Required("depth", default=1.5): vol.Coerce(float),
            })

        return self.async_show_form(
            step_id="dimensions",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_ph_config(self, user_input=None):
        """Step 3 : configuration du pH (valeur manuelle ou capteur)."""
        errors = {}
        if user_input is not None:
            # Validation des champs pH
            numeric_fields = [
                ("ph_current", "ph_invalid", lambda x: 0 <= x <= 14, False),
                ("ph_target", "ph_invalid", lambda x: 0 <= x <= 14, True),
            ]
            for field, error_key, validator, required in numeric_fields:
                try:
                    value = user_input.get(field, "" if required else "7.0")
                    if required and (value is None or value == ""):
                        errors[field] = "required_field"
                        continue
                    if value is not None and value != "":
                        value = str(value).replace(",", ".").strip()
                        value = float(value)
                        if not validator(value):
                            errors[field] = error_key
                        self._data[field] = value
                except ValueError:
                    errors[field] = "invalid_number"

            # Validation du capteur pH
            use_sensor = user_input.get("use_ph_sensor", False)
            if use_sensor:
                ph_sensor = user_input.get("ph_sensor", "")
                if not ph_sensor:
                    errors["ph_sensor"] = "required_field"
                else:
                    self._data["ph_sensor"] = ph_sensor
                    self._data["use_ph_sensor"] = True
            else:
                self._data["use_ph_sensor"] = False
                self._data["ph_sensor"] = ""

            # Validation conditionnelle : capteur ou valeur manuelle pour pH
            if not self._data.get("ph_sensor", "") and ("ph_current" not in self._data or self._data["ph_current"] is None or self._data["ph_current"] == ""):
                errors["ph_current"] = "ph_required_if_no_sensor"
                errors["ph_sensor"] = "sensor_required_if_no_ph"

            if not errors:
                # Définir des valeurs par défaut si non fournies
                if "ph_current" not in self._data or self._data["ph_current"] is None:
                    self._data["ph_current"] = 7.0
                return await self.async_step_chlore_config()

        # Récupérer les capteurs de pH disponibles
        ph_sensors = [""]
        ph_sensors_dict = {"": ""}
        for state in self.hass.states.async_all("sensor"):
            entity_id = state.entity_id
            if entity_id.startswith(f"sensor.{DOMAIN}_"):
                continue
            attributes = state.attributes
            unit = attributes.get("unit_of_measurement", "").lower()
            friendly_name = attributes.get("friendly_name", entity_id).lower()
            if unit == "ph" or "ph" in friendly_name or "ph" in entity_id.lower():
                friendly_name = attributes.get("friendly_name", entity_id)
                ph_sensors.append(entity_id)
                ph_sensors_dict[entity_id] = f"{friendly_name} ({entity_id})"

        _LOGGER.debug("Capteurs de pH trouvés : %s", ph_sensors)

        schema = {
            vol.Optional("ph_current", default=7.0): vol.Coerce(float),
            vol.Required("ph_target", default=7.4): vol.Coerce(float),
            vol.Required("use_ph_sensor", default=False): bool,
        }
        if self.hass.states.get("use_ph_sensor") and self.hass.states.get("use_ph_sensor").state == "True":
            schema[vol.Optional("ph_sensor", default="")] = vol.In(ph_sensors_dict)

        return self.async_show_form(
            step_id="ph_config",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_chlore_config(self, user_input=None):
        """Step 4 : configuration du chlore (valeur manuelle ou capteur)."""
        errors = {}
        if user_input is not None:
            # Validation des champs chlore
            numeric_fields = [
                ("chlore_current", "chlore_invalid", lambda x: x >= 0, False),
                ("chlore_target", "chlore_invalid", lambda x: x >= 0, True),
            ]
            for field, error_key, validator, required in numeric_fields:
                try:
                    value = user_input.get(field, "" if required else "1.0")
                    if required and (value is None or value == ""):
                        errors[field] = "required_field"
                        continue
                    if value is not None and value != "":
                        value = str(value).replace(",", ".").strip()
                        value = float(value)
                        if not validator(value):
                            errors[field] = error_key
                        self._data[field] = value
                except ValueError:
                    errors[field] = "invalid_number"

            # Validation du capteur chlore
            use_sensor = user_input.get("use_chlore_sensor", False)
            if use_sensor:
                chlore_sensor = user_input.get("chlore_sensor", "")
                if not chlore_sensor:
                    errors["chlore_sensor"] = "required_field"
                else:
                    self._data["chlore_sensor"] = chlore_sensor
                    self._data["use_chlore_sensor"] = True
            else:
                self._data["use_chlore_sensor"] = False
                self._data["chlore_sensor"] = ""

            # Validation conditionnelle : capteur ou valeur manuelle pour chlore
            if not self._data.get("chlore_sensor", "") and ("chlore_current" not in self._data or self._data["chlore_current"] is None or self._data["chlore_current"] == ""):
                errors["chlore_current"] = "chlore_required_if_no_sensor"
                errors["chlore_sensor"] = "sensor_required_if_no_chlore"

            if not errors:
                # Définir des valeurs par défaut si non fournies
                if "chlore_current" not in self._data or self._data["chlore_current"] is None:
                    self._data["chlore_current"] = 1.0
                return await self.async_step_temperature_config()

        # Récupérer les capteurs de chlore disponibles
        chlore_sensors = [""]  # Option vide pour rendre le champ optionnel
        chlore_sensors_dict = {"": ""}
        for state in self.hass.states.async_all("sensor"):
            entity_id = state.entity_id
            if entity_id.startswith(f"sensor.{DOMAIN}_"):
                continue
            attributes = state.attributes
            unit = attributes.get("unit_of_measurement", "").lower()
            if unit in ("mg/l", "ppm", "mg per liter", "parts per million"):
                friendly_name = attributes.get("friendly_name", entity_id)
                chlore_sensors.append(entity_id)
                chlore_sensors_dict[entity_id] = f"{friendly_name} ({entity_id})"

        _LOGGER.debug("Capteurs de chlore trouvés : %s", chlore_sensors)

        schema = {
            vol.Optional("chlore_current", default=1.0): vol.Coerce(float),
            vol.Required("chlore_target", default=2.0): vol.Coerce(float),
            vol.Required("use_chlore_sensor", default=False): bool,
        }
        if self.hass.states.get("use_chlore_sensor") and self.hass.states.get("use_chlore_sensor").state == "True":
            schema[vol.Optional("chlore_sensor", default="")] = vol.In(chlore_sensors_dict)

        return self.async_show_form(
            step_id="chlore_config",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_temperature_config(self, user_input=None):
        """Step 5 : configuration de la température (valeur manuelle ou capteur)."""
        errors = {}
        if user_input is not None:
            # Validation de la température
            numeric_fields = [
                ("temperature", "temperature_invalid", lambda x: 0 <= x <= 50, False),
            ]
            for field, error_key, validator, required in numeric_fields:
                try:
                    value = user_input.get(field, "20.0")
                    if value is not None and value != "":
                        value = str(value).replace(",", ".").strip()
                        value = float(value)
                        if not validator(value):
                            errors[field] = error_key
                        self._data[field] = value
                except ValueError:
                    errors[field] = "invalid_number"

            # Validation du capteur température
            use_sensor = user_input.get("use_temperature_sensor", False)
            if use_sensor:
                temperature_sensor = user_input.get("temperature_sensor", "")
                if not temperature_sensor:
                    errors["temperature_sensor"] = "required_field"
                else:
                    self._data["temperature_sensor"] = temperature_sensor
                    self._data["use_temperature_sensor"] = True
            else:
                self._data["use_temperature_sensor"] = False
                self._data["temperature_sensor"] = ""

            if not errors:
                # Définir des valeurs par défaut si non fournies
                if "temperature" not in self._data or self._data["temperature"] is None:
                    self._data["temperature"] = 20.0
                return await self.async_step_power_config()

        # Récupérer les capteurs de température disponibles
        temp_sensors = [""]  # Option vide pour rendre le champ optionnel
        temp_sensors_dict = {"": ""}
        for state in self.hass.states.async_all("sensor"):
            entity_id = state.entity_id
            if entity_id.startswith(f"sensor.{DOMAIN}_"):
                continue
            attributes = state.attributes
            unit = attributes.get("unit_of_measurement", "").lower()
            device_class = attributes.get("device_class", "")
            if (device_class == "temperature" or
                unit in ("°c", "°f", "c", "f", "celsius", "fahrenheit")):
                friendly_name = attributes.get("friendly_name", entity_id)
                temp_sensors.append(entity_id)
                temp_sensors_dict[entity_id] = f"{friendly_name} ({entity_id})"

        _LOGGER.debug("Capteurs de température trouvés : %s", temp_sensors)

        schema = {
            vol.Optional("temperature", default=20.0): vol.Coerce(float),
            vol.Required("use_temperature_sensor", default=False): bool,
        }
        if self.hass.states.get("use_temperature_sensor") and self.hass.states.get("use_temperature_sensor").state == "True":
            schema[vol.Optional("temperature_sensor", default="")] = vol.In(temp_sensors_dict)

        return self.async_show_form(
            step_id="temperature_config",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_power_config(self, user_input=None):
        """Step 6 : configuration de la puissance (valeur manuelle ou capteur)."""
        errors = {}
        if user_input is not None:
            use_sensor = user_input.get("use_power_sensor", False)
            if use_sensor:
                power_sensor = user_input.get("power_sensor_entity_id", "")
                if not power_sensor:
                    errors["power_sensor_entity_id"] = "required_field"
                else:
                    self._data["power_sensor_entity_id"] = power_sensor
                    self._data["use_power_sensor"] = True
            else:
                self._data["use_power_sensor"] = False
                self._data["power_sensor_entity_id"] = ""

            if not errors:
                return await self.async_step_summary()

        schema = {
            vol.Required("use_power_sensor", default=False): bool,
            vol.Optional("power_sensor_entity_id", default=""): str,
        }

        return self.async_show_form(
            step_id="power_config",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_summary(self, user_input=None):
        """Step 7 : récapitulatif avant validation."""
        if user_input is not None:
            return self.async_create_entry(title=f"Piscinexa {self._data['name']}", data=self._data)

        # Préparer le récapitulatif
        summary = [
            f"Nom de la piscine: {self._data['name']}",
            f"Type de piscine: {self._data['pool_type']}",
            f"Dimensions: {self._get_dimensions_summary()}",
            f"pH actuel: {self._data['ph_current']}",
            f"pH cible: {self._data['ph_target']}",
            f"Source pH: {'Capteur' if self._data.get('use_ph_sensor', False) else 'Valeur manuelle'} ({self._data.get('ph_sensor', 'Aucune sélection')})",
            f"Chlore actuel: {self._data['chlore_current']} mg/L",
            f"Chlore cible: {self._data['chlore_target']} mg/L",
            f"Source chlore: {'Capteur' if self._data.get('use_chlore_sensor', False) else 'Valeur manuelle'} ({self._data.get('chlore_sensor', 'Aucune sélection')})",
            f"Température: {self._data['temperature']} °C",
            f"Source température: {'Capteur' if self._data.get('use_temperature_sensor', False) else 'Valeur manuelle'} ({self._data.get('temperature_sensor', 'Aucune sélection')})",
            f"Source puissance: {'Capteur' if self._data.get('use_power_sensor', False) else 'Valeur manuelle'} ({self._data.get('power_sensor_entity_id', 'Aucune sélection')})",
        ]

        return self.async_show_form(
            step_id="summary",
            description_placeholders={"summary": "\n".join(summary)},
            data_schema=vol.Schema({}),
        )

    def _get_dimensions_summary(self):
        """Retourne un résumé des dimensions de la piscine."""
        if self._data["pool_type"] == POOL_TYPE_SQUARE:
            return f"Longueur: {self._data['length']} m, Largeur: {self._data['width']} m, Profondeur: {self._data['depth']} m"
        else:
            return f"Diamètre: {self._data['diameter']} m, Profondeur: {self._data['depth']} m"

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PiscinexaOptionsFlowHandler()

class PiscinexaOptionsFlowHandler(config_entries.OptionsFlow):
    """Gestionnaire des options pour Piscinexa."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Récupérer les capteurs de température disponibles pour les options
        temp_sensors = [""]  # Option vide pour rendre le champ optionnel
        temp_sensors_dict = {"": ""}
        for state in self.hass.states.async_all("sensor"):
            entity_id = state.entity_id
            if entity_id.startswith(f"sensor.{DOMAIN}_"):
                continue
            attributes = state.attributes
            unit = attributes.get("unit_of_measurement", "").lower()
            device_class = attributes.get("device_class", "")
            if (device_class == "temperature" or
                unit in ("°c", "°f", "c", "f", "celsius", "fahrenheit")):
                friendly_name = attributes.get("friendly_name", entity_id)
                temp_sensors.append(entity_id)
                temp_sensors_dict[entity_id] = f"{friendly_name} ({entity_id})"

        # Récupérer les capteurs de chlore disponibles
        chlore_sensors = [""]
        chlore_sensors_dict = {"": ""}
        for state in self.hass.states.async_all("sensor"):
            entity_id = state.entity_id
            if entity_id.startswith(f"sensor.{DOMAIN}_"):
                continue
            attributes = state.attributes
            unit = attributes.get("unit_of_measurement", "").lower()
            if unit in ("mg/l", "ppm", "mg per liter", "parts per million"):
                friendly_name = attributes.get("friendly_name", entity_id)
                chlore_sensors.append(entity_id)
                chlore_sensors_dict[entity_id] = f"{friendly_name} ({entity_id})"

        # Récupérer les capteurs de pH disponibles
        ph_sensors = [""]
        ph_sensors_dict = {"": ""}
        for state in self.hass.states.async_all("sensor"):
            entity_id = state.entity_id
            if entity_id.startswith(f"sensor.{DOMAIN}_"):
                continue
            attributes = state.attributes
            unit = attributes.get("unit_of_measurement", "").lower()
            friendly_name = attributes.get("friendly_name", entity_id).lower()
            if unit == "ph" or "ph" in friendly_name or "ph" in entity_id.lower():
                friendly_name = attributes.get("friendly_name", entity_id)
                ph_sensors.append(entity_id)
                ph_sensors_dict[entity_id] = f"{friendly_name} ({entity_id})"

        _LOGGER.debug("Capteurs de température trouvés dans les options : %s", temp_sensors)
        _LOGGER.debug("Capteurs de chlore trouvés dans les options : %s", chlore_sensors)
        _LOGGER.debug("Capteurs de pH trouvés dans les options : %s", ph_sensors)

        current = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("ph_target", default=current.get("ph_target", 7.4)): vol.Coerce(float),
                vol.Optional("chlore_target", default=current.get("chlore_target", 2.0)): vol.Coerce(float),
                vol.Optional("temperature_sensor", default=current.get("temperature_sensor", "")): vol.In(temp_sensors_dict),
                vol.Optional("chlore_sensor", default=current.get("chlore_sensor", "")): vol.In(chlore_sensors_dict),
                vol.Optional("ph_sensor", default=current.get("ph_sensor", "")): vol.In(ph_sensors_dict),
            }),
        )
