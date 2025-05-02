"""Flux de configuration pour Piscinexa."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, POOL_TYPE_SQUARE, POOL_TYPE_ROUND

class PiscinexaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Flux de configuration pour Piscinexa."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                name = user_input["name"].strip().lower().replace(" ", "_")
                pool_type = user_input["pool_type"]
                data = {
                    "name": name,
                    "pool_type": pool_type,
                }

                numeric_fields = [
                    ("ph_current", "ph_invalid", lambda x: 0 <= x <= 14, True),
                    ("ph_target", "ph_invalid", lambda x: 0 <= x <= 14, True),
                    ("chlore_current", "chlore_invalid", lambda x: x >= 0, True),
                    ("chlore_target", "chlore_invalid", lambda x: x >= 0, True),
                    ("temperature", "temperature_invalid", lambda x: 0 <= x <= 50, False),
                ]
                for field, error_key, validator, required in numeric_fields:
                    try:
                        value = user_input.get(field, "" if required else "20.0")
                        if required and (value is None or value == ""):
                            errors[field] = "required_field"
                            continue
                        value = str(value).replace(",", ".").strip()
                        value = float(value)
                        if not validator(value):
                            errors[field] = error_key
                        data[field] = value
                    except ValueError:
                        errors[field] = "invalid_number"

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
                        data[field] = value
                    except ValueError:
                        errors[field] = "invalid_number"

                if "temperature_sensor" in user_input:
                    data["temperature_sensor"] = user_input["temperature_sensor"]
                if "power_sensor_entity_id" in user_input:
                    data["power_sensor_entity_id"] = user_input["power_sensor_entity_id"]

                if not errors:
                    return self.async_create_entry(title=f"Piscinexa {name}", data=data)

            except Exception as e:
                errors["base"] = f"unexpected_error: {str(e)}"

        schema = {
            vol.Required("name", default="piscine"): str,
            vol.Required("pool_type", default=POOL_TYPE_SQUARE): vol.In({
                POOL_TYPE_SQUARE: "Carrée",
                POOL_TYPE_ROUND: "Ronde"
            }),
            vol.Required("ph_current", default=7.0): vol.Coerce(float),
            vol.Required("ph_target", default=7.4): vol.Coerce(float),
            vol.Required("chlore_current", default=1.0): vol.Coerce(float),
            vol.Required("chlore_target", default=2.0): vol.Coerce(float),
            vol.Optional("temperature", default=20.0): vol.Coerce(float),
            vol.Optional("temperature_sensor", default=""): str,
            vol.Optional("power_sensor_entity_id", default=""): str,
        }
        if user_input and user_input.get("pool_type") == POOL_TYPE_ROUND:
            schema.update({
                vol.Required("diameter", default=4.0): vol.Coerce(float),
                vol.Required("depth", default=1.5): vol.Coerce(float),
            })
        else:
            schema.update({
                vol.Required("length", default=5.0): vol.Coerce(float),
                vol.Required("width", default=4.0): vol.Coerce(float),
                vol.Required("depth", default=1.5): vol.Coerce(float),
            })

        return self.async_show_form(
            step_id="user",
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

        current = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("ph_target", default=current.get("ph_target", 7.4)): vol.Coerce(float),
                vol.Optional("chlore_target", default=current.get("chlore_target", 2.0)): vol.Coerce(float),
                vol.Optional("temperature_sensor", default=current.get("temperature_sensor", "")): str,
            }),
        )
