"""Flux de configuration pour l'intégration Piscinexa."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_NAME, TEMP_CELSIUS
from .const import (
    DOMAIN,
    POOL_TYPE_SQUARE,
    POOL_TYPE_ROUND,
    CONF_SENSOR,
    CONF_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)

class PiscinexaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Flux de configuration pour Piscinexa."""
    VERSION = 1

    def __init__(self):
        """Initialiser le flux de configuration."""
        self._data = {}

    async def async_step_user(self, user_input=None):
        """Étape 1 : demander le nom et le type de piscine."""
        errors = {}
        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            pool_type = user_input["pool_type"]

            if not name:
                errors[CONF_NAME] = "name_invalid"
            elif await self.async_check_duplicate_name(name):
                errors[CONF_NAME] = "name_duplicate"
            else:
                self._data[CONF_NAME] = name
                self._data["pool_type"] = pool_type
                return await self.async_step_dimensions()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME): str,
                vol.Required("pool_type", default=POOL_TYPE_SQUARE): vol.In([POOL_TYPE_SQUARE, POOL_TYPE_ROUND]),
            }),
            errors=errors,
        )

    async def async_check_duplicate_name(self, name):
        """Vérifier si le nom est déjà utilisé."""
        for entry in self._async_current_entries():
            if entry.data[CONF_NAME].lower() == name.lower():
                return True
        return False

    async def async_step_dimensions(self, user_input=None):
        """Étape 2 : demander les dimensions en fonction du type de piscine."""
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
            schema = vol.Schema({
                vol.Required("length"): str,
                vol.Required("width"): str,
                vol.Required("depth"): str,
            })
        else:
            schema = vol.Schema({
                vol.Required("diameter"): str,
                vol.Required("depth"): str,
            })

        return self.async_show_form(
            step_id="dimensions",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_ph_config(self, user_input=None):
        """Étape 3 : configuration du pH."""
        errors = {}
        if user_input is not None:
            choice = user_input["ph_config_choice"]
            self._data["use_ph_sensor"] = choice == "sensor"
            if choice == "sensor":
                return await self.async_step_ph_sensor()
            return await self.async_step_ph_manual()

        return self.async_show_form(
            step_id="ph_config",
            data_schema=vol.Schema({
                vol.Required("ph_config_choice", default="manual"): vol.In(["manual", "sensor"]),
            }),
            errors=errors,
        )

    async def async_step_ph_manual(self, user_input=None):
        """Étape 3 : saisie manuelle du pH."""
        errors = {}
        if user_input is not None:
            try:
                ph_target = float(user_input["ph_target"])
                if not 0 <= ph_target <= 14:
                    errors["ph_target"] = "ph_invalid"
                self._data["ph_target"] = ph_target

                ph_current = user_input.get("ph_current", "")
                if ph_current:
                    ph_current = float(ph_current)
                    if not 0 <= ph_current <= 14:
                        errors["ph_current"] = "ph_invalid"
                    self._data["ph_current"] = ph_current
                else:
                    self._data["ph_current"] = ph_target

                if not errors:
                    return await self.async_step_chlore_config()
            except ValueError:
                errors["ph_current"] = "invalid_number"
                errors["ph_target"] = "invalid_number"

        return self.async_show_form(
            step_id="ph_manual",
            data_schema=vol.Schema({
                vol.Optional("ph_current"): str,
                vol.Required("ph_target", default="7.4"): str,
            }),
            errors=errors,
        )

    async def async_step_ph_sensor(self, user_input=None):
        """Étape 3 : sélection du capteur pH."""
        errors = {}
        if user_input is not None:
            try:
                ph_target = float(user_input["ph_target"])
                if not 0 <= ph_target <= 14:
                    errors["ph_target"] = "ph_invalid"
                self._data["ph_target"] = ph_target

                sensor = user_input.get("ph_sensor", "")
                if sensor:
                    self._data[CONF_SENSOR] = sensor
                    return await self.async_step_chlore_config()
                return await self.async_step_confirm_ph_sensor()
            except ValueError:
                errors["ph_target"] = "invalid_number"

        return self.async_show_form(
            step_id="ph_sensor",
            data_schema=vol.Schema({
                vol.Optional("ph_sensor"): str,
                vol.Required("ph_target", default="7.4"): str,
            }),
            errors=errors,
        )

    async def async_step_confirm_ph_sensor(self, user_input=None):
        """Étape 3 : confirmation si aucun capteur pH n'est sélectionné."""
        if user_input is not None:
            choice = user_input["confirm_choice"]
            if choice == "manual":
                return await self.async_step_ph_manual()
            return await self.async_step_ph_sensor()

        return self.async_show_form(
            step_id="confirm_ph_sensor",
            data_schema=vol.Schema({
                vol.Required("confirm_choice", default="manual"): vol.In(["manual", "retry"]),
            }),
        )

    async def async_step_chlore_config(self, user_input=None):
        """Étape 4 : configuration du chlore."""
        errors = {}
        if user_input is not None:
            choice = user_input["chlore_config_choice"]
            self._data["use_chlore_sensor"] = choice == "sensor"
            if choice == "sensor":
                return await self.async_step_chlore_sensor()
            return await self.async_step_chlore_manual()

        return self.async_show_form(
            step_id="chlore_config",
            data_schema=vol.Schema({
                vol.Required("chlore_config_choice", default="manual"): vol.In(["manual", "sensor"]),
            }),
            errors=errors,
        )

    async def async_step_chlore_manual(self, user_input=None):
        """Étape 4 : saisie manuelle du chlore."""
        errors = {}
        if user_input is not None:
            try:
                chlore_target = float(user_input["chlore_target"])
                if chlore_target < 0:
                    errors["chlore_target"] = "chlore_invalid"
                self._data["chlore_target"] = chlore_target

                chlore_current = user_input.get("chlore_current", "")
                if chlore_current:
                    chlore_current = float(chlore_current)
                    if chlore_current < 0:
                        errors["chlore_current"] = "chlore_invalid"
                    self._data["chlore_current"] = chlore_current
                else:
                    self._data["chlore_current"] = chlore_target

                if not errors:
                    return await self.async_step_temperature_config()
            except ValueError:
                errors["chlore_current"] = "invalid_number"
                errors["chlore_target"] = "invalid_number"

        return self.async_show_form(
            step_id="chlore_manual",
            data_schema=vol.Schema({
                vol.Optional("chlore_current"): str,
                vol.Required("chlore_target", default="2.0"): str,
            }),
            errors=errors,
        )

    async def async_step_chlore_sensor(self, user_input=None):
        """Étape 4 : sélection du capteur chlore."""
        errors = {}
        if user_input is not None:
            try:
                chlore_target = float(user_input["chlore_target"])
                if chlore_target < 0:
                    errors["chlore_target"] = "chlore_invalid"
                self._data["chlore_target"] = chlore_target

                sensor = user_input.get("chlore_sensor", "")
                if sensor:
                    self._data["chlore_sensor"] = sensor
                    return await self.async_step_temperature_config()
                return await self.async_step_confirm_chlore_sensor()
            except ValueError:
                errors["chlore_target"] = "invalid_number"

        return self.async_show_form(
            step_id="chlore_sensor",
            data_schema=vol.Schema({
                vol.Optional("chlore_sensor"): str,
                vol.Required("chlore_target", default="2.0"): str,
            }),
            errors=errors,
        )

    async def async_step_confirm_chlore_sensor(self, user_input=None):
        """Étape 4 : confirmation si aucun capteur chlore n'est sélectionné."""
        if user_input is not None:
            choice = user_input["confirm_choice"]
            if choice == "manual":
                return await self.async_step_chlore_manual()
            return await self.async_step_chlore_sensor()

        return self.async_show_form(
            step_id="confirm_chlore_sensor",
            data_schema=vol.Schema({
                vol.Required("confirm_choice", default="manual"): vol.In(["manual", "retry"]),
            }),
        )

    async def async_step_temperature_config(self, user_input=None):
        """Étape 5 : configuration de la température."""
        errors = {}
        if user_input is not None:
            choice = user_input["temperature_config_choice"]
            self._data["use_temperature_sensor"] = choice == "sensor"
            if choice == "sensor":
                return await self.async_step_temperature_sensor()
            return await self.async_step_temperature_manual()

        return self.async_show_form(
            step_id="temperature_config",
            data_schema=vol.Schema({
                vol.Required("temperature_config_choice", default="manual"): vol.In(["manual", "sensor"]),
            }),
            errors=errors,
        )

    async def async_step_temperature_manual(self, user_input=None):
        """Étape 5 : saisie manuelle de la température."""
        errors = {}
        if user_input is not None:
            try:
                temperature = float(user_input["temperature"])
                if not 0 <= temperature <= 50:
                    errors["temperature"] = "temperature_invalid"
                self._data[CONF_TEMPERATURE] = temperature

                if not errors:
                    return await self.async_step_power_config()
            except ValueError:
                errors["temperature"] = "invalid_number"

        return self.async_show_form(
            step_id="temperature_manual",
            data_schema=vol.Schema({
                vol.Required("temperature", default="20.0"): str,
            }),
            errors=errors,
        )

    async def async_step_temperature_sensor(self, user_input=None):
        """Étape 5 : sélection du capteur température."""
        errors = {}
        if user_input is not None:
            sensor = user_input.get("temperature_sensor", "")
            if sensor:
                self._data["temperature_sensor"] = sensor
                return await self.async_step_power_config()
            return await self.async_step_confirm_temperature_sensor()

        return self.async_show_form(
            step_id="temperature_sensor",
            data_schema=vol.Schema({
                vol.Optional("temperature_sensor"): str,
            }),
            errors=errors,
        )

    async def async_step_confirm_temperature_sensor(self, user_input=None):
        """Étape 5 : confirmation si aucun capteur température n'est sélectionné."""
        if user_input is not None:
            choice = user_input["confirm_choice"]
            if choice == "manual":
                return await self.async_step_temperature_manual()
            return await self.async_step_temperature_sensor()

        return self.async_show_form(
            step_id="confirm_temperature_sensor",
            data_schema=vol.Schema({
                vol.Required("confirm_choice", default="manual"): vol.In(["manual", "retry"]),
            }),
        )

    async def async_step_power_config(self, user_input=None):
        """Étape 6 : configuration du capteur de puissance."""
        errors = {}
        if user_input is not None:
            choice = user_input["power_config_choice"]
            self._data["use_power_sensor"] = choice == "sensor"
            if choice == "sensor":
                return await self.async_step_power_sensor()
            return await self.async_step_power_manual()

        return self.async_show_form(
            step_id="power_config",
            data_schema=vol.Schema({
                vol.Required("power_config_choice", default="manual"): vol.In(["manual", "sensor"]),
            }),
            errors=errors,
        )

    async def async_step_power_manual(self, user_input=None):
        """Étape 6 : saisie manuelle de la puissance (vide)."""
        self._data["power_sensor_entity_id"] = ""
        return await self.async_step_summary()

    async def async_step_power_sensor(self, user_input=None):
        """Étape 6 : sélection du capteur de puissance."""
        if user_input is not None:
            self._data["power_sensor_entity_id"] = user_input.get("power_sensor_entity_id", "")
            return await self.async_step_summary()

        return self.async_show_form(
            step_id="power_sensor",
            data_schema=vol.Schema({
                vol.Optional("power_sensor_entity_id"): str,
            }),
        )

    async def async_step_summary(self, user_input=None):
        """Étape 7 : récapitulatif de la configuration."""
        if user_input is not None:
            return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)

        summary = []
        summary.append(f"Nom de la piscine : {self._data[CONF_NAME]}")
        summary.append(f"Type de piscine : {self._data['pool_type']}")
        if self._data["pool_type"] == POOL_TYPE_SQUARE:
            summary.append(f"Dimensions : {self._data['length']}m x {self._data['width']}m x {self._data['depth']}m")
        else:
            summary.append(f"Dimensions : Diamètre {self._data['diameter']}m, Profondeur {self._data['depth']}m")

        summary.append(f"pH Cible : {self._data['ph_target']}")
        if self._data.get("use_ph_sensor", False):
            summary.append(f"Capteur pH : {self._data.get('ph_sensor', 'Aucun capteur')}")
        else:
            summary.append(f"pH Actuel (manuel) : {self._data.get('ph_current', 'Non défini')}")

        summary.append(f"Chlore Cible : {self._data['chlore_target']} mg/L")
        if self._data.get("use_chlore_sensor", False):
            summary.append(f"Capteur Chlore : {self._data.get('chlore_sensor', 'Aucun capteur')}")
        else:
            summary.append(f"Chlore Actuel (manuel) : {self._data.get('chlore_current', 'Non défini')} mg/L")

        if self._data.get("use_temperature_sensor", False):
            summary.append(f"Capteur Température : {self._data.get('temperature_sensor', 'Aucun capteur')}")
        else:
            summary.append(f"Température (manuelle) : {self._data.get('temperature', 'Non défini')} °C")

        summary.append(f"Capteur Puissance : {self._data.get('power_sensor_entity_id', 'Aucun capteur')}")

        return self.async_show_form(
            step_id="summary",
            description_placeholders={"summary": "\n".join(summary)},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Obtenir le flux d'options pour l'entrée de configuration."""
        return PiscinexaOptionsFlow(config_entry)

class PiscinexaOptionsFlow(config_entries.OptionsFlow):
    """Flux d'options pour Piscinexa."""
    def __init__(self, config_entry):
        """Initialiser le flux d'options."""
        self.config_entry = config_entry
        self._data = dict(config_entry.data)

    async def async_step_init(self, user_input=None):
        """Gérer le flux d'options."""
        errors = {}
        if user_input is not None:
            try:
                self._data["ph_target"] = float(user_input["ph_target"])
                if not 0 <= self._data["ph_target"] <= 14:
                    errors["ph_target"] = "ph_invalid"

                self._data["chlore_target"] = float(user_input["chlore_target"])
                if self._data["chlore_target"] < 0:
                    errors["chlore_target"] = "chlore_invalid"

                self._data["temperature_sensor"] = user_input.get("temperature_sensor", "")
                self._data["chlore_sensor"] = user_input.get("chlore_sensor", "")
                self._data["ph_sensor"] = user_input.get("ph_sensor", "")

                if not errors:
                    return self.async_create_entry(title="", data=self._data)
            except ValueError:
                errors["ph_target"] = "invalid_number"
                errors["chlore_target"] = "invalid_number"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("ph_target", default=str(self._data["ph_target"])): str,
                vol.Required("chlore_target", default=str(self._data["chlore_target"])): str,
                vol.Optional("temperature_sensor", default=self._data.get("temperature_sensor", "")): str,
                vol.Optional("chlore_sensor", default=self._data.get("chlore_sensor", "")): str,
                vol.Optional("ph_sensor", default=self._data.get("ph_sensor", "")): str,
            }),
            errors=errors,
        )