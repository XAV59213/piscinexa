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
                pool_type = user_input["pool_type"]
                ph_current = float(user_input["ph_current"])
                ph_target = float(user_input["ph_target"])
                chlore_current = float(user_input["chlore_current"])
                chlore_target = float(user_input["chlore_target"])
                temperature = float(user_input.get("temperature", 20.0))

                # Validation des dimensions selon le type
                if pool_type == POOL_TYPE_SQUARE:
                    length = float(user_input["length"])
                    width = float(user_input["width"])
                    depth = float(user_input["depth"])
                    if any(x <= 0 for x in [length, width, depth]):
                        errors["base"] = "dimensions_invalid"
                else:  # POOL_TYPE_ROUND
                    diameter = float(user_input["diameter"])
                    depth = float(user_input["depth"])
                    if diameter <= 0 or depth <= 0:
                        errors["base"] = "dimensions_invalid"

                # Validation des autres champs
                if not 0 <= ph_current <= 14 or not 0 <= ph_target <= 14:
                    errors["base"] = "ph_invalid"
                elif chlore_current < 0 or chlore_target < 0:
                    errors["base"] = "chlore_invalid"
                elif temperature < 0 or temperature > 50:
                    errors["base"] = "temperature_invalid"
                elif not name:
                    errors["base"] = "name_invalid"
                else:
                    # Stocker les données
                    data = {
                        "name": name,
                        "pool_type": pool_type,
                        "ph_current": ph_current,
                        "ph_target": ph_target,
                        "chlore_current": chlore_current,
                        "chlore_target": chlore_target,
                        "temperature": temperature,
                    }
                    if pool_type == POOL_TYPE_SQUARE:
                        data.update({"length": length, "width": width, "depth": depth})
                    else:
                        data.update({"diameter": diameter, "depth": depth})
                    return self.async_create_entry(title=f"Piscinexa {name}", data=data)
            except ValueError:
                errors["base"] = "invalid_number"

        # Formulaire
        schema = {
            vol.Required("name", default="piscine"): str,
            vol.Required("pool_type", default=POOL_TYPE_SQUARE): vol.In([POOL_TYPE_SQUARE, POOL_TYPE_ROUND]),
            vol.Required("ph_current", default=7.0): float,
            vol.Required("ph_target", default=7.4): float,
            vol.Required("chlore_current", default=1.0): float,
            vol.Required("chlore_target", default=2.0): float,
            vol.Optional("temperature", default=20.0): float,
        }
        if user_input and user_input.get("pool_type") == POOL_TYPE_ROUND:
            schema.update({
                vol.Required("diameter", default=4.0): float,
                vol.Required("depth", default=1.5): float,
            })
        else:
            schema.update({
                vol.Required("length", default=5.0): float,
                vol.Required("width", default=4.0): float,
                vol.Required("depth", default=1.5): float,
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
