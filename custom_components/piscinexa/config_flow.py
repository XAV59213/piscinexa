"""Flux de configuration pour Piscinexa."""
import logging
from typing import Any, Dict, Optional
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector
from .const import (
    DOMAIN,
    POOL_TYPE_SQUARE,
    POOL_TYPE_ROUND,
    CONF_POOL_TYPE,
    CONF_LENGTH,
    CONF_WIDTH,
    CONF_DEPTH,
    CONF_DIAMETER,
)

_LOGGER = logging.getLogger(__name__)

def get_translation(hass: HomeAssistant, key: str, default: str = None) -> str:
    """Récupère une traduction depuis le cache, gérant les clés imbriquées."""
    try:
        # Vérifier si les traductions sont bien chargées
        if DOMAIN not in hass.data or "translations" not in hass.data[DOMAIN]:
            _LOGGER.warning(f"Traductions non chargées dans hass.data[{DOMAIN}]['translations']")
            return default or key

        # Diviser la clé en parties pour gérer les sous-dictionnaires
        keys = key.split(".")
        translation = hass.data[DOMAIN]["translations"]
        for k in keys:
            if isinstance(translation, dict):
                translation = translation.get(k)
            else:
                _LOGGER.warning(f"Clé de traduction {key} non trouvée dans la structure")
                return default or key

        if translation is None:
            _LOGGER.warning(f"Valeur pour la clé de traduction {key} est None")
            return default or key

        _LOGGER.debug(f"Traduction récupérée pour la clé {key}: {translation}")
        return translation
    except Exception as e:
        _LOGGER.error(f"Erreur lors de la récupération de la traduction pour la clé {key}: {e}")
        return default or key

class PiscinexaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gérer le flux de configuration pour Piscinexa."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._errors: Dict[str, str] = {}

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Gérer l'étape initiale."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            if not user_input.get(CONF_NAME):
                self._errors["base"] = "name_invalid"
            else:
                # Vérifier si le nom est unique
                for entry in self._async_current_entries():
                    if entry.data.get(CONF_NAME) == user_input[CONF_NAME]:
                        self._errors["base"] = "name_duplicate"
                        break
                if not self._errors:
                    return await self.async_step_dimensions()

        # Utiliser les traductions pour les types de piscine
        pool_type_options = {
            POOL_TYPE_SQUARE: get_translation(self.hass, "config.step.user.pool_types.square", "Square"),
            POOL_TYPE_ROUND: get_translation(self.hass, "config.step.user.pool_types.round", "Round"),
        }
        _LOGGER.debug(f"Options de type de piscine: {pool_type_options}")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_POOL_TYPE): vol.In(pool_type_options),
            }),
            errors=self._errors,
        )

    async def async_step_dimensions(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Gérer l'étape des dimensions."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            if self._data[CONF_POOL_TYPE] == POOL_TYPE_SQUARE:
                if not all(
                    user_input.get(key, 0) > 0
                    for key in [CONF_LENGTH, CONF_WIDTH, CONF_DEPTH]
                ):
                    self._errors["base"] = "dimensions_invalid"
            else:
                if not all(
                    user_input.get(key, 0) > 0
                    for key in [CONF_DIAMETER, CONF_DEPTH]
                ):
                    self._errors["base"] = "dimensions_invalid"
            if not self._errors:
                return await self.async_step_ph_config()

        schema = vol.Schema({
            vol.Required(CONF_DEPTH, default=1.5): vol.Coerce(float),
        })
        if self._data[CONF_POOL_TYPE] == POOL_TYPE_SQUARE:
            schema = schema.extend({
                vol.Required(CONF_LENGTH, default=5.0): vol.Coerce(float),
                vol.Required(CONF_WIDTH, default=4.0): vol.Coerce(float),
            })
        else:
            schema = schema.extend({
                vol.Required(CONF_DIAMETER, default=4.0): vol.Coerce(float),
            })

        return self.async_show_form(
            step_id="dimensions",
            data_schema=schema,
            errors=self._errors,
        )

    async def async_step_ph_config(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Gérer l'étape de configuration du pH."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            choice = user_input.get("ph_config_choice")
            if choice == "manual":
                return await self.async_step_ph_manual()
            return await self.async_step_ph_sensor()

        # Utiliser les traductions pour les options de configuration
        config_options = {
            "manual": get_translation(self.hass, "config.step.ph_config.options.manual", "Manual entry"),
            "sensor": get_translation(self.hass, "config.step.ph_config.options.sensor", "Select a sensor"),
        }

        return self.async_show_form(
            step_id="ph_config",
            data_schema=vol.Schema({
                vol.Required("ph_config_choice", default="manual"): vol.In(config_options),
            }),
            errors=self._errors,
        )

    async def async_step_ph_manual(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Gérer la saisie manuelle du pH."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            ph_target = user_input.get("ph_target")
            ph_current = user_input.get("ph_current", 7.0)
            if ph_target <= 0 or ph_target >= 14:
                self._errors["ph_target"] = "ph_invalid"
            if ph_current and (ph_current <= 0 or ph_current >= 14):
                self._errors["ph_current"] = "ph_invalid"
            if not self._errors:
                return await self.async_step_chlore_config()
        return self.async_show_form(
            step_id="ph_manual",
            data_schema=vol.Schema({
                vol.Optional("ph_current", default=7.0): vol.Coerce(float),
                vol.Required("ph_target", default=7.4): vol.Coerce(float),
            }),
            errors=self._errors,
        )

    async def async_step_ph_sensor(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Gérer la sélection d'un capteur pH."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            ph_target = user_input.get("ph_target")
            if ph_target <= 0 or ph_target >= 14:
                self._errors["ph_target"] = "ph_invalid"
            ph_sensor = user_input.get("ph_sensor")
            if not ph_sensor and not self._data.get("ph_current"):
                return await self.async_step_confirm_ph_sensor()
            if not self._errors:
                return await self.async_step_chlore_config()
        return self.async_show_form(
            step_id="ph_sensor",
            data_schema=vol.Schema({
                vol.Optional("ph_sensor"): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required("ph_target", default=7.4): vol.Coerce(float),
            }),
            errors=self._errors,
        )

    async def async_step_confirm_ph_sensor(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Confirmer l'absence de capteur pH."""
        self._errors = {}
        if user_input is not None:
            choice = user_input.get("confirm_choice")
            if choice == "manual":
                return await self.async_step_ph_manual()
            return await self.async_step_ph_sensor()

        # Utiliser les traductions pour les options de confirmation
        confirm_options = {
            "manual": get_translation(self.hass, "config.step.confirm_ph_sensor.options.manual", "Enter manually"),
            "retry": get_translation(self.hass, "config.step.confirm_ph_sensor.options.retry", "Retry sensor selection"),
        }

        return self.async_show_form(
            step_id="confirm_ph_sensor",
            data_schema=vol.Schema({
                vol.Required("confirm_choice", default="manual"): vol.In(confirm_options),
            }),
            errors=self._errors,
        )

    async def async_step_chlore_config(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Gérer l'étape de configuration du chlore."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            choice = user_input.get("chlore_config_choice")
            if choice == "manual":
                return await self.async_step_chlore_manual()
            return await self.async_step_chlore_sensor()

        # Utiliser les traductions pour les options de configuration
        config_options = {
            "manual": get_translation(self.hass, "config.step.chlore_config.options.manual", "Manual entry"),
            "sensor": get_translation(self.hass, "config.step.chlore_config.options.sensor", "Select a sensor"),
        }

        return self.async_show_form(
            step_id="chlore_config",
            data_schema=vol.Schema({
                vol.Required("chlore_config_choice", default="manual"): vol.In(config_options),
            }),
            errors=self._errors,
        )

    async def async_step_chlore_manual(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Gérer la saisie manuelle du chlore."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            chlore_target = user_input.get("chlore_target")
            chlore_current = user_input.get("chlore_current", 1.0)
            if chlore_target < 0:
                self._errors["chlore_target"] = "chlore_invalid"
            if chlore_current and chlore_current < 0:
                self._errors["chlore_current"] = "chlore_invalid"
            if not self._errors:
                return await self.async_step_temperature_config()
        return self.async_show_form(
            step_id="chlore_manual",
            data_schema=vol.Schema({
                vol.Optional("chlore_current", default=1.0): vol.Coerce(float),
                vol.Required("chlore_target", default=2.0): vol.Coerce(float),
            }),
            errors=self._errors,
        )

    async def async_step_chlore_sensor(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Gérer la sélection d'un capteur chlore."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            chlore_target = user_input.get("chlore_target")
            if chlore_target < 0:
                self._errors["chlore_target"] = "chlore_invalid"
            chlore_sensor = user_input.get("chlore_sensor")
            if not chlore_sensor and not self._data.get("chlore_current"):
                return await self.async_step_confirm_chlore_sensor()
            if not self._errors:
                return await self.async_step_temperature_config()
        return self.async_show_form(
            step_id="chlore_sensor",
            data_schema=vol.Schema({
                vol.Optional("chlore_sensor"): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required("chlore_target", default=2.0): vol.Coerce(float),
            }),
            errors=self._errors,
        )

    async def async_step_confirm_chlore_sensor(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Confirmer l'absence de capteur chlore."""
        self._errors = {}
        if user_input is not None:
            choice = user_input.get("confirm_choice")
            if choice == "manual":
                return await self.async_step_chlore_manual()
            return await self.async_step_chlore_sensor()

        # Utiliser les traductions pour les options de confirmation
        confirm_options = {
            "manual": get_translation(self.hass, "config.step.confirm_chlore_sensor.options.manual", "Enter manually"),
            "retry": get_translation(self.hass, "config.step.confirm_chlore_sensor.options.retry", "Retry sensor selection"),
        }

        return self.async_show_form(
            step_id="confirm_chlore_sensor",
            data_schema=vol.Schema({
                vol.Required("confirm_choice", default="manual"): vol.In(confirm_options),
            }),
            errors=self._errors,
        )

    async def async_step_temperature_config(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Gérer l'étape de configuration de la température."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            choice = user_input.get("temperature_config_choice")
            if choice == "manual":
                return await self.async_step_temperature_manual()
            return await self.async_step_temperature_sensor()

        # Utiliser les traductions pour les options de configuration
        config_options = {
            "manual": get_translation(self.hass, "config.step.temperature_config.options.manual", "Manual entry"),
            "sensor": get_translation(self.hass, "config.step.temperature_config.options.sensor", "Select a sensor"),
        }

        return self.async_show_form(
            step_id="temperature_config",
            data_schema=vol.Schema({
                vol.Required("temperature_config_choice", default="manual"): vol.In(config_options),
            }),
            errors=self._errors,
        )

    async def async_step_temperature_manual(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Gérer la saisie manuelle de la température."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            temperature = user_input.get("temperature", 20.0)
            if temperature < 0 or temperature > 50:
                self._errors["temperature"] = "temperature_invalid"
            if not self._errors:
                return await self.async_step_power_config()
        return self.async_show_form(
            step_id="temperature_manual",
            data_schema=vol.Schema({
                vol.Optional("temperature", default=20.0): vol.Coerce(float),
            }),
            errors=self._errors,
        )

    async def async_step_temperature_sensor(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Gérer la sélection d'un capteur température."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            temperature_sensor = user_input.get("temperature_sensor")
            if not temperature_sensor and not self._data.get("temperature"):
                return await self.async_step_confirm_temperature_sensor()
            if not self._errors:
                return await self.async_step_power_config()
        return self.async_show_form(
            step_id="temperature_sensor",
            data_schema=vol.Schema({
                vol.Optional("temperature_sensor"): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
            }),
            errors=self._errors,
        )

    async def async_step_confirm_temperature_sensor(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Confirmer l'absence de capteur température."""
        self._errors = {}
        if user_input is not None:
            choice = user_input.get("confirm_choice")
            if choice == "manual":
                return await self.async_step_temperature_manual()
            return await self.async_step_temperature_sensor()

        # Utiliser les traductions pour les options de confirmation
        confirm_options = {
            "manual": get_translation(self.hass, "config.step.confirm_temperature_sensor.options.manual", "Enter manually"),
            "retry": get_translation(self.hass, "config.step.confirm_temperature_sensor.options.retry", "Retry sensor selection"),
        }

        return self.async_show_form(
            step_id="confirm_temperature_sensor",
            data_schema=vol.Schema({
                vol.Required("confirm_choice", default="manual"): vol.In(confirm_options),
            }),
            errors=self._errors,
        )

    async def async_step_power_config(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Gérer l'étape de configuration du capteur de puissance."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            choice = user_input.get("power_config_choice")
            if choice == "manual":
                return await self.async_step_power_manual()
            return await self.async_step_power_sensor()

        # Utiliser les traductions pour les options de configuration
        config_options = {
            "manual": get_translation(self.hass, "config.step.power_config.options.manual", "Manual (no sensor)"),
            "sensor": get_translation(self.hass, "config.step.power_config.options.sensor", "Select a sensor"),
        }

        return self.async_show_form(
            step_id="power_config",
            data_schema=vol.Schema({
                vol.Required("power_config_choice", default="manual"): vol.In(config_options),
            }),
            errors=self._errors,
        )

    async def async_step_power_manual(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Gérer l'absence de capteur de puissance."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_treatment_config()
        return self.async_show_form(
            step_id="power_manual",
            data_schema=vol.Schema({}),
            errors=self._errors,
        )

    async def async_step_power_sensor(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Gérer la sélection d'un capteur de puissance."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            power_sensor_entity_id = user_input.get("power_sensor_entity_id")
            if not power_sensor_entity_id:
                return await self.async_step_confirm_power_sensor()
            if not self._errors:
                return await self.async_step_treatment_config()
        return self.async_show_form(
            step_id="power_sensor",
            data_schema=vol.Schema({
                vol.Optional("power_sensor_entity_id"): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
            }),
            errors=self._errors,
        )

    async def async_step_confirm_power_sensor(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Confirmer l'absence de capteur de puissance."""
        self._errors = {}
        if user_input is not None:
            choice = user_input.get("confirm_choice")
            if choice == "manual":
                return await self.async_step_power_manual()
            return await self.async_step_power_sensor()

        # Utiliser les traductions pour les options de confirmation
        confirm_options = {
            "manual": get_translation(self.hass, "config.step.confirm_power_sensor.options.manual", "Continue without sensor"),
            "retry": get_translation(self.hass, "config.step.confirm_power_sensor.options.retry", "Retry sensor selection"),
        }

        return self.async_show_form(
            step_id="confirm_power_sensor",
            data_schema=vol.Schema({
                vol.Required("confirm_choice", default="manual"): vol.In(confirm_options),
            }),
            errors=self._errors,
        )

    async def async_step_treatment_config(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Gérer l'étape de configuration des types de traitements."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_summary()

        # Utiliser les traductions pour les options de traitement
        ph_treatment_options = {
            "Liquid": get_translation(self.hass, "config.step.treatment_config.treatment_options.liquid", "Liquid"),
            "Granules": get_translation(self.hass, "config.step.treatment_config.treatment_options.granules", "Granules"),
        }
        chlore_treatment_options = {
            "Liquid": get_translation(self.hass, "config.step.treatment_config.treatment_options.liquid", "Liquid"),
            "Shock chlorine (powder)": get_translation(self.hass, "config.step.treatment_config.treatment_options.shock_chlorine_powder", "Shock chlorine (powder)"),
            "Slow-dissolving tablet": get_translation(self.hass, "config.step.treatment_config.treatment_options.slow_dissolving_tablet", "Slow-dissolving tablet"),
        }

        return self.async_show_form(
            step_id="treatment_config",
            data_schema=vol.Schema({
                vol.Required("ph_plus_treatment", default="Liquid"): vol.In(ph_treatment_options),
                vol.Required("ph_minus_treatment", default="Liquid"): vol.In(ph_treatment_options),
                vol.Required("chlore_treatment", default="Shock chlorine (powder)"): vol.In(chlore_treatment_options),
            }),
            errors=self._errors,
        )

    async def async_step_summary(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Afficher un récapitulatif de la configuration."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"Piscinexa {self._data[CONF_NAME]}",
                data=self._data
            )

        summary = (
            f"Pool name: {self._data[CONF_NAME]}\n"
            f"Pool type: {self._data[CONF_POOL_TYPE]}\n"
            f"Dimensions:\n"
        )
        if self._data[CONF_POOL_TYPE] == POOL_TYPE_SQUARE:
            summary += (
                f"  Length: {self._data[CONF_LENGTH]} m\n"
                f"  Width: {self._data[CONF_WIDTH]} m\n"
                f"  Depth: {self._data[CONF_DEPTH]} m\n"
            )
        else:
            summary += (
                f"  Diameter: {self._data[CONF_DIAMETER]} m\n"
                f"  Depth: {self._data[CONF_DEPTH]} m\n"
            )
        summary += (
            f"Current pH: {self._data.get('ph_current', 'Not defined')}\n"
            f"Target pH: {self._data.get('ph_target')}\n"
            f"pH source: {self._data.get('ph_sensor', 'Manual')}\n"
            f"pH+ treatment type: {self._data.get('ph_plus_treatment', 'Not defined')}\n"
            f"pH- treatment type: {self._data.get('ph_minus_treatment', 'Not defined')}\n"
            f"Current chlorine: {self._data.get('chlore_current', 'Not defined')} mg/L\n"
            f"Target chlorine: {self._data.get('chlore_target')} mg/L\n"
            f"Chlorine source: {self._data.get('chlore_sensor', 'Manual')}\n"
            f"Chlorine treatment type: {self._data.get('chlore_treatment', 'Not defined')}\n"
            f"Temperature: {self._data.get('temperature', 'Not defined')} °C\n"
            f"Temperature source: {self._data.get('temperature_sensor', 'Manual')}\n"
            f"Power source: {self._data.get('power_sensor_entity_id', 'Not defined')}\n"
        )

        return self.async_show_form(
            step_id="summary",
            description_placeholders={"summary": summary},
            data_schema=vol.Schema({}),
            errors=self._errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Créer le flux d'options."""
        return PiscinexaOptionsFlow(config_entry)

class PiscinexaOptionsFlow(config_entries.OptionsFlow):
    """Gérer le flux des options pour Piscinexa."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        self._data: Dict[str, Any] = dict(config_entry.data)
        self._errors: Dict[str, str] = {}

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Gérer l'étape des options."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            ph_target = user_input.get("ph_target", self._data.get("ph_target", 7.4))
            chlore_target = user_input.get("chlore_target", self._data.get("chlore_target", 2.0))
            if ph_target <= 0 or ph_target >= 14:
                self._errors["ph_target"] = "ph_invalid"
            if chlore_target < 0:
                self._errors["chlore_target"] = "chlore_invalid"
            if not self._errors:
                return self.async_create_entry(
                    title="",
                    data=self._data
                )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("ph_target", default=self._data.get("ph_target", 7.4)): vol.Coerce(float),
                vol.Required("chlore_target", default=self._data.get("chlore_target", 2.0)): vol.Coerce(float),
                vol.Optional("temperature_sensor", default=self._data.get("temperature_sensor", "")): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional("chlore_sensor", default=self._data.get("chlore_sensor", "")): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional("ph_sensor", default=self._data.get("ph_sensor", "")): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional("power_sensor_entity_id", default=self._data.get("power_sensor_entity_id", "")): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
            }),
            errors=self._errors,
        )
