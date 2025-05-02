"""Flux de configuration pour Piscinexa."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, POOL_TYPE_SQUARE, POOL_TYPE_ROUND

class PiscinexaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Flux de configuration pour Piscinexa."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Étape initiale du flux."""
        errors = {}
        if user_input is not None:
            # Valider les entrées
            try:
                name = user_input["name"].strip().lower().replace(" ", "_")
                if not name:
                    errors["name"] = "name_invalid"

                pool_type = user_input["pool_type"]
                data = {
                    "name": name,
                    "pool_type": pool_type,
                }

                # Validation des champs numériques
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
                        if value == "":
                            value = "20.0" if field == "temperature" else "0"
                        # Remplacer la virgule par un point pour les décimales
                        value = str(value).replace(",", ".").strip()
                        if not value:
                            errors[field] = "required_field"
                            continue
                        value = float(value)
                        if not validator(value):
                            errors[field] = error_key
                        data[field] = value
                    except ValueError:
                        errors[field] = "invalid_number"

                # Validation des dimensions selon le type
                if pool_type == POOL_TYPE_SQUARE:
                    dimension_fields = [
                        ("length", "dimensions_invalid", lambda x: x > 0),
                        ("width", "dimensions_invalid", lambda x: x > 0),
                        ("depth", "dimensions_invalid", lambda x: x > 0),
                    ]
                else:  # POOL_TYPE_ROUND
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
                        if not value:
                            errors[field] = "required_field"
                            continue
                        value = float(value)
                        if not validator(value):
                            errors[field] = error_key
                        data[field] = value
                    except ValueError:
                        errors[field] = "invalid_number"

                if not errors:
                    return self.async_create_entry(title=f"Piscinexa {name}", data=data)
            except KeyError as e:
                errors["base"] = f"missing_field: {e}"

        # Formulaire
        schema = {
            vol.Required("name", default="piscine"): str,
            vol.Required("pool_type", default=POOL_TYPE_SQUARE): vol.In([POOL_TYPE_SQUARE, POOL_TYPE_ROUND]),
            vol.Required("ph_current", default=7.0): vol.Any(str, float, int),
            vol.Required("ph_target", default=7.4): vol.Any(str, float, int),
            vol.Required("chlore_current", default=1.0): vol.Any(str, float, int),
            vol.Required("chlore_target", default=2.0): vol.Any(str, float, int),
            vol.Optional("temperature", default=20.0): vol.Any(str, float, int),
        }
        if user_input and user_input.get("pool_type") == POOL_TYPE_ROUND:
            schema.update({
                vol.Required("diameter", default=4.0): vol.Any(str, float, int),
                vol.Required("depth", default=1.5): vol.Any(str, float, int),
            })
        else:
            schema.update({
                vol.Required("length", default=5.0): vol.Any(str, float, int),
                vol.Required("width", default=4.0): vol.Any(str, float, int),
                vol.Required("depth", default=1.5): vol.Any(str, float, int),
            })

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return config_entries.OptionsFlowHandler(config_entry)
