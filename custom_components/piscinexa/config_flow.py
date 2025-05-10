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
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_POOL_TYPE): vol.In([POOL_TYPE_SQUARE, POOL_TYPE_ROUND]),
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
        return self.async_show_form(
            step_id="ph_config",
            data_schema=vol.Schema({
                vol.Required("ph_config_choice", default="manual"): vol.In(["manual", "sensor"]),
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
        return self.async_show_form(
            step_id="confirm_ph_sensor",
            data_schema=vol.Schema({
                vol.Required("confirm_choice", default="manual"): vol.In(["manual", "retry"]),
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
        return self.async_show_form(
            step_id="chlore_config",
            data_schema=vol.Schema({
                vol.Required("chlore_config_choice", default="manual"): vol.In(["manual", "sensor"]),
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
        return self.async_show_form(
            step_id="confirm_chlore_sensor",
            data_schema=vol.Schema({
                vol.Required("confirm_choice", default="manual"): vol.In(["manual", "retry"]),
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
        return self.async_show_form(
            step_id="temperature_config",
            data_schema=vol.Schema({
                vol.Required("temperature_config_choice", default="manual"): vol.In(["manual", "sensor"]),
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
        return self.async_show_form(
            step_id="confirm_temperature_sensor",
            data_schema=vol.Schema({
                vol.Required("confirm_choice", default="manual"): vol.In(["manual", "retry"]),
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
        return self.async_show_form(
            step_id="power_config",
            data_schema=vol.Schema({
                vol.Required("power_config_choice", default="manual"): vol.In(["manual", "sensor"]),
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
        return self.async_show_form(
            step_id="confirm_power_sensor",
            data_schema=vol.Schema({
                vol.Required("confirm_choice", default="manual"): vol.In(["manual", "retry"]),
            }),
            errors=self._errors,
        )

    async def async_step_treatment_config(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Gérer l'étape de configuration des types de traitements."""
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_summary()
        return self.async_show_form(
            step_id="treatment_config",
            data_schema=vol.Schema({
                vol.Required("ph_plus_treatment", default="Liquide"): vol.In(["Liquide", "Granulés"]),
                vol.Required("ph_minus_treatment", default="Liquide"): vol.In(["Liquide", "Granulés"]),
                vol.Required("chlore_treatment", default="Chlore choc (poudre)"): vol.In(["Liquide", "Chlore choc (poudre)", "Pastille lente"]),
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
            f"Nom de la piscine: {self._data[CONF_NAME]}\n"
            f"Type de piscine: {self._data[CONF_POOL_TYPE]}\n"
            f"Dimensions:\n"
        )
        if self._data[CONF_POOL_TYPE] == POOL_TYPE_SQUARE:
            summary += (
                f"  Longueur: {self._data[CONF_LENGTH]} m\n"
                f"  Largeur: {self._data[CONF_WIDTH]} m\n"
                f"  Profondeur: {self._data[CONF_DEPTH]} m\n"
            )
        else:
            summary += (
                f"  Diamètre: {self._data[CONF_DIAMETER]} m\n"
                f"  Profondeur: {self._data[CONF_DEPTH]} m\n"
            )
        summary += (
            f"pH actuel: {self._data.get('ph_current', 'Non défini')}\n"
            f"pH cible: {self._data.get('ph_target')}\n"
            f"Source pH: {self._data.get('ph_sensor', 'Manuel')}\n"
            f"Type de traitement pH+: {self._data.get('ph_plus_treatment', 'Non défini')}\n"
            f"Type de traitement pH-: {self._data.get('ph_minus_treatment', 'Non défini')}\n"
            f"Chlore actuel: {self._data.get('chlore_current', 'Non défini')} mg/L\n"
            f"Chlore cible: {self._data.get('chlore_target')} mg/L\n"
            f"Source chlore: {self._data.get('chlore_sensor', 'Manuel')}\n"
            f"Type de traitement chlore: {self._data.get('chlore_treatment', 'Non défini')}\n"
            f"Température: {self._data.get('temperature', 'Non défini')} °C\n"
            f"Source température: {self._data.get('temperature_sensor', 'Manuel')}\n"
            f"Source puissance: {self._data.get('power_sensor_entity_id', 'Non défini')}\n"
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
        self.config_entry = config_entry
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
