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
        """Première étape : demander le nom et le type de piscine."""
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
        """Deuxième étape : demander les dimensions en fonction du type de piscine."""
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
                return await self.async_step_parameters()

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

    async def async_step_parameters(self, user_input=None):
        """Troisième étape : demander les paramètres (pH, chlore, température, etc.)."""
        errors = {}
        if user_input is not None:
            # Validation des champs numériques
            numeric_fields = [
                ("ph_current", "ph_invalid", lambda x: 0 <= x <= 14, False),  # Rendu facultatif
                ("ph_target", "ph_invalid", lambda x: 0 <= x <= 14, True),
                ("chlore_current", "chlore_invalid", lambda x: x >= 0, False),  # Rendu facultatif
                ("chlore_target", "chlore_invalid", lambda x: x >= 0, True),
                ("temperature", "temperature_invalid", lambda x: 0 <= x <= 50, False),
            ]
            for field, error_key, validator, required in numeric_fields:
                try:
                    value = user_input.get(field, "" if required else "20.0")
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

            # Validation conditionnelle : capteur ou valeur manuelle pour pH
            ph_sensor = user_input.get("ph_sensor", "")
            if not ph_sensor and ("ph_current" not in self._data or self._data["ph_current"] is None or self._data["ph_current"] == ""):
                errors["ph_current"] = "ph_required_if_no_sensor"
                errors["ph_sensor"] = "sensor_required_if_no_ph"

            # Validation conditionnelle : capteur ou valeur manuelle pour chlore
            chlore_sensor = user_input.get("chlore_sensor", "")
            if not chlore_sensor and ("chlore_current" not in self._data or self._data["chlore_current"] is None or self._data["chlore_current"] == ""):
                errors["chlore_current"] = "chlore_required_if_no_sensor"
                errors["chlore_sensor"] = "sensor_required_if_no_chlore"

            # Enregistrement des capteurs
            if "temperature_sensor" in user_input:
                self._data["temperature_sensor"] = user_input["temperature_sensor"]
            if "chlore_sensor" in user_input:
                self._data["chlore_sensor"] = user_input["chlore_sensor"]
            if "ph_sensor" in user_input:
                self._data["ph_sensor"] = user_input["ph_sensor"]
            if "power_sensor_entity_id" in user_input:
                self._data["power_sensor_entity_id"] = user_input["power_sensor_entity_id"]

            # Si pas d'erreurs, créer l'entrée
            if not errors:
                # Définir des valeurs par défaut si non fournies
                if "ph_current" not in self._data or self._data["ph_current"] is None:
                    self._data["ph_current"] = 7.0
                if "chlore_current" not in self._data or self._data["chlore_current"] is None:
                    self._data["chlore_current"] = 1.0
                if "temperature" not in self._data or self._data["temperature"] is None:
                    self._data["temperature"] = 20.0
                return self.async_create_entry(title=f"Piscinexa {self._data['name']}", data=self._data)

        # Récupérer les capteurs de température disponibles
        temp_sensors = [""]  # Option vide pour rendre le champ optionnel
        temp_sensors_dict = {"": "Aucun"}
        for state in self.hass.states.async_all("sensor"):
            attributes = state.attributes
            if (attributes.get("device_class") == "temperature" or
                attributes.get("unit_of_measurement") in ("°C", "°F")):
                entity_id = state.entity_id
                friendly_name = attributes.get("friendly_name", entity_id)
                temp_sensors.append(entity_id)
                temp_sensors_dict[entity_id] = f"{friendly_name} ({entity_id})"

        # Récupérer les capteurs de chlore disponibles (basé sur unit_of_measurement mg/L ou ppm)
        chlore_sensors = [""]
        chlore_sensors_dict = {"": "Aucun"}
        for state in self.hass.states.async_all("sensor"):
            attributes = state.attributes
            if attributes.get("unit_of_measurement") in ("mg/L", "ppm"):
                entity_id = state.entity_id
                friendly_name = attributes.get("friendly_name", entity_id)
                chlore_sensors.append(entity_id)
                chlore_sensors_dict[entity_id] = f"{friendly_name} ({entity_id})"

        # Récupérer les capteurs de pH disponibles (basé sur unit_of_measurement pH)
        ph_sensors = [""]
        ph_sensors_dict = {"": "Aucun"}
        for state in self.hass.states.async_all("sensor"):
            attributes = state.attributes
            if attributes.get("unit_of_measurement") == "pH":
                entity_id = state.entity_id
                friendly_name = attributes.get("friendly_name", entity_id)
                ph_sensors.append(entity_id)
                ph_sensors_dict[entity_id] = f"{friendly_name} ({entity_id})"

        _LOGGER.debug("Capteurs de température trouvés : %s", temp_sensors)
        _LOGGER.debug("Capteurs de chlore trouvés : %s", chlore_sensors)
        _LOGGER.debug("Capteurs de pH trouvés : %s", ph_sensors)

        schema = {
            vol.Optional("ph_current", default=7.0): vol.Coerce(float),
            vol.Required("ph_target", default=7.4): vol.Coerce(float),
            vol.Optional("chlore_current", default=1.0): vol.Coerce(float),
            vol.Required("chlore_target", default=2.0): vol.Coerce(float),
            vol.Optional("temperature", default=20.0): vol.Coerce(float),
            vol.Optional("temperature_sensor", default=""): vol.In(temp_sensors_dict),
            vol.Optional("chlore_sensor", default=""): vol.In(chlore_sensors_dict),
            vol.Optional("ph_sensor", default=""): vol.In(ph_sensors_dict),
            vol.Optional("power_sensor_entity_id", default=""): str,
        }

        return self.async_show_form(
            step_id="parameters",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

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
        temp_sensors_dict = {"": "Aucun"}
        for state in self.hass.states.async_all("sensor"):
            attributes = state.attributes
            if (attributes.get("device_class") == "temperature" or
                attributes.get("unit_of_measurement") in ("°C", "°F")):
                entity_id = state.entity_id
                friendly_name = attributes.get("friendly_name", entity_id)
                temp_sensors.append(entity_id)
                temp_sensors_dict[entity_id] = f"{friendly_name} ({entity_id})"

        # Récupérer les capteurs de chlore disponibles
        chlore_sensors = [""]
        chlore_sensors_dict = {"": "Aucun"}
        for state in self.hass.states.async_all("sensor"):
            attributes = state.attributes
            if attributes.get("unit_of_measurement") in ("mg/L", "ppm"):
                entity_id = state.entity_id
                friendly_name = attributes.get("friendly_name", entity_id)
                chlore_sensors.append(entity_id)
                chlore_sensors_dict[entity_id] = f"{friendly_name} ({entity_id})"

        # Récupérer les capteurs de pH disponibles
        ph_sensors = [""]
        ph_sensors_dict = {"": "Aucun"}
        for state in self.hass.states.async_all("sensor"):
            attributes = state.attributes
            if attributes.get("unit_of_measurement") == "pH":
                entity_id = state.entity_id
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
