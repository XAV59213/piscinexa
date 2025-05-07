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
        self._ph_config_choice = None
        self._chlore_config_choice = None
        self._temperature_config_choice = None
        self._power_config_choice = None
        self._no_sensor_message = False

    async def async_step_user(self, user_input=None):
        """Step 1 : demander le nom et le type de piscine."""
        errors = {}
        if user_input is not None:
            try:
                name = user_input["name"].strip().lower().replace(" ", "_")
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
        """Step 3 : configuration du pH (choix entre manuel et capteur)."""
        errors = {}
        if user_input is not None:
            if "ph_config_choice" in user_input:
                self._ph_config_choice = user_input["ph_config_choice"]
                if self._ph_config_choice == "manual":
                    self._no_sensor_message = False
                    return await self.async_step_ph_manual()
                else:
                    self._no_sensor_message = False
                    return await self.async_step_ph_sensor()
            else:
                errors["ph_config_choice"] = "required_field"

        schema = vol.Schema({
            vol.Required("ph_config_choice"): vol.In({
                "manual": "Saisir manuellement",
                "sensor": "Choisir un capteur"
            }),
        })

        return self.async_show_form(
            step_id="ph_config",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_ph_manual(self, user_input=None):
        """Step 3 (sous-étape) : saisie manuelle des valeurs pH."""
        errors = {}
        if user_input is not None:
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

            if not errors:
                if "ph_current" not in self._data or self._data["ph_current"] is None:
                    self._data["ph_current"] = 7.0
                self._data["use_ph_sensor"] = False
                self._data["ph_sensor"] = ""
                return await self.async_step_chlore_config()

        description = "Entrez les valeurs du pH pour votre piscine.\n\n- **pH actuel (valeur mesurée)** : La valeur actuelle du pH dans votre piscine, mesurée manuellement (facultatif).\n- **pH cible (valeur idéale)** : La valeur idéale que vous souhaitez atteindre (obligatoire, généralement entre 7.2 et 7.6 pour une piscine)."
        if self._no_sensor_message:
            description = "Piscinexa n'a pas trouvé de capteur pH compatible. Vous devez configurer les valeurs manuellement.\n\n" + description

        schema = vol.Schema({
            vol.Optional("ph_current", default=7.0): vol.Coerce(float),
            vol.Required("ph_target", default=7.4): vol.Coerce(float),
        })

        return self.async_show_form(
            step_id="ph_manual",
            description_placeholders={"description": description},
            data_schema=schema,
            errors=errors,
        )

    async def async_step_ph_sensor(self, user_input=None):
        """Step 3 (sous-étape) : sélection d'un capteur pH."""
        errors = {}
        if user_input is not None:
            ph_sensor = user_input.get("ph_sensor", "")
            try:
                ph_target = user_input.get("ph_target", "")
                if ph_target is None or ph_target == "":
                    errors["ph_target"] = "required_field"
                else:
                    ph_target = str(ph_target).replace(",", ".").strip()
                    ph_target = float(ph_target)
                    if not (0 <= ph_target <= 14):
                        errors["ph_target"] = "ph_invalid"
                    else:
                        self._data["ph_target"] = ph_target
            except ValueError:
                errors["ph_target"] = "invalid_number"

            if not ph_sensor and ("ph_current" not in self._data or self._data["ph_current"] is None):
                return await self.async_step_confirm_ph_sensor()

            if not errors:
                self._data["ph_sensor"] = ph_sensor if ph_sensor else ""
                self._data["use_ph_sensor"] = bool(ph_sensor)
                return await self.async_step_chlore_config()

        ph_sensors = [""]
        ph_sensors_dict = {"": "Aucun capteur"}
        for state in self.hass.states.async_all("sensor"):
            entity_id = state.entity_id
            if entity_id.startswith(f"sensor.{DOMAIN}_"):
                continue
            if "ph_a_ajouter" in entity_id.lower() or "phaajouter" in entity_id.lower():
                continue
            attributes = state.attributes
            unit = attributes.get("unit_of_measurement", "").lower()
            friendly_name = attributes.get("friendly_name", entity_id).lower()
            if unit == "ph" or "ph" in friendly_name or "ph" in entity_id.lower():
                friendly_name = attributes.get("friendly_name", entity_id)
                ph_sensors.append(entity_id)
                ph_sensors_dict[entity_id] = f"{friendly_name} ({entity_id})"

        _LOGGER.debug("Capteurs de pH trouvés : %s", ph_sensors)

        schema = vol.Schema({
            vol.Optional("ph_sensor", default=""): vol.In(ph_sensors_dict),
            vol.Required("ph_target", default=7.4): vol.Coerce(float),
        })

        return self.async_show_form(
            step_id="ph_sensor",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_confirm_ph_sensor(self, user_input=None):
        """Step 3 (sous-étape) : confirmation avant redirection pour pH."""
        errors = {}
        if user_input is not None:
            if "confirm_choice" in user_input:
                choice = user_input["confirm_choice"]
                if choice == "manual":
                    self._no_sensor_message = True
                    return await self.async_step_ph_manual()
                else:
                    return await self.async_step_ph_sensor()
            else:
                errors["confirm_choice"] = "required_field"

        schema = vol.Schema({
            vol.Required("confirm_choice"): vol.In({
                "manual": "Configurer manuellement",
                "retry": "Réessayer"
            }),
        })

        return self.async_show_form(
            step_id="confirm_ph_sensor",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_chlore_config(self, user_input=None):
        """Step 4 : configuration du chlore (choix entre manuel et capteur)."""
        errors = {}
        if user_input is not None:
            if "chlore_config_choice" in user_input:
                self._chlore_config_choice = user_input["chlore_config_choice"]
                if self._chlore_config_choice == "manual":
                    self._no_sensor_message = False
                    return await self.async_step_chlore_manual()
                else:
                    self._no_sensor_message = False
                    return await self.async_step_chlore_sensor()
            else:
                errors["chlore_config_choice"] = "required_field"

        schema = vol.Schema({
            vol.Required("chlore_config_choice"): vol.In({
                "manual": "Saisir manuellement",
                "sensor": "Choisir un capteur"
            }),
        })

        return self.async_show_form(
            step_id="chlore_config",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_chlore_manual(self, user_input=None):
        """Step 4 (sous-étape) : saisie manuelle des valeurs chlore."""
        errors = {}
        if user_input is not None:
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

            if not errors:
                if "chlore_current" not in self._data or self._data["chlore_current"] is None:
                    self._data["chlore_current"] = 1.0
                self._data["use_chlore_sensor"] = False
                self._data["chlore_sensor"] = ""
                return await self.async_step_temperature_config()

        description = "Entrez les valeurs du chlore pour votre piscine.\n\n- **Chlore actuel (valeur mesurée, mg/L)** : La valeur actuelle du chlore dans votre piscine, mesurée manuellement (facultatif).\n- **Chlore cible (valeur idéale, mg/L)** : La valeur idéale que vous souhaitez atteindre (obligatoire, généralement entre 1 et 3 mg/L pour une piscine)."
        if self._no_sensor_message:
            description = "Piscinexa n'a pas trouvé de capteur chlore compatible. Vous devez configurer les valeurs manuellement.\n\n" + description

        schema = vol.Schema({
            vol.Optional("chlore_current", default=1.0): vol.Coerce(float),
            vol.Required("chlore_target", default=2.0): vol.Coerce(float),
        })

        return self.async_show_form(
            step_id="chlore_manual",
            description_placeholders={"description": description},
            data_schema=schema,
            errors=errors,
        )

    async def async_step_chlore_sensor(self, user_input=None):
        """Step 4 (sous-étape) : sélection d'un capteur chlore."""
        errors = {}
        if user_input is not None:
            chlore_sensor = user_input.get("chlore_sensor", "")
            try:
                chlore_target = user_input.get("chlore_target", "")
                if chlore_target is None or chlore_target == "":
                    errors["chlore_target"] = "required_field"
                else:
                    chlore_target = str(chlore_target).replace(",", ".").strip()
                    chlore_target = float(chlore_target)
                    if not (chlore_target >= 0):
                        errors["chlore_target"] = "chlore_invalid"
                    else:
                        self._data["chlore_target"] = chlore_target
            except ValueError:
                errors["chlore_target"] = "invalid_number"

            if not chlore_sensor and ("chlore_current" not in self._data or self._data["chlore_current"] is None):
                return await self.async_step_confirm_chlore_sensor()

            if not errors:
                self._data["chlore_sensor"] = chlore_sensor if chlore_sensor else ""
                self._data["use_chlore_sensor"] = bool(chlore_sensor)
                return await self.async_step_temperature_config()

        chlore_sensors = [""]
        chlore_sensors_dict = {"": "Aucun capteur"}
        for state in self.hass.states.async_all("sensor"):
            entity_id = state.entity_id
            if entity_id.startswith(f"sensor.{DOMAIN}_"):
                continue
            if "chlore_a_ajouter" in entity_id.lower() or "chloreaajouter" in entity_id.lower():
                continue
            attributes = state.attributes
            unit = attributes.get("unit_of_measurement", "").lower()
            if unit in ("mg/l", "ppm", "mg per liter", "parts per million"):
                friendly_name = attributes.get("friendly_name", entity_id)
                chlore_sensors.append(entity_id)
                chlore_sensors_dict[entity_id] = f"{friendly_name} ({entity_id})"

        _LOGGER.debug("Capteurs de chlore trouvés : %s", chlore_sensors)

        schema = vol.Schema({
            vol.Optional("chlore_sensor", default=""): vol.In(chlore_sensors_dict),
            vol.Required("chlore_target", default=2.0): vol.Coerce(float),
        })

        return self.async_show_form(
            step_id="chlore_sensor",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_confirm_chlore_sensor(self, user_input=None):
        """Step 4 (sous-étape) : confirmation avant redirection pour chlore."""
        errors = {}
        if user_input is not None:
            if "confirm_choice" in user_input:
                choice = user_input["confirm_choice"]
                if choice == "manual":
                    self._no_sensor_message = True
                    return await self.async_step_chlore_manual()
                else:
                    return await self.async_step_chlore_sensor()
            else:
                errors["confirm_choice"] = "required_field"

        schema = vol.Schema({
            vol.Required("confirm_choice"): vol.In({
                "manual": "Configurer manuellement",
                "retry": "Réessayer"
            }),
        })

        return self.async_show_form(
            step_id="confirm_chlore_sensor",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_temperature_config(self, user_input=None):
        """Step 5 : configuration de la température (choix entre manuel et capteur)."""
        errors = {}
        if user_input is not None:
            if "temperature_config_choice" in user_input:
                self._temperature_config_choice = user_input["temperature_config_choice"]
                if self._temperature_config_choice == "manual":
                    self._no_sensor_message = False
                    return await self.async_step_temperature_manual()
                else:
                    self._no_sensor_message = False
                    return await self.async_step_temperature_sensor()
            else:
                errors["temperature_config_choice"] = "required_field"

        schema = vol.Schema({
            vol.Required("temperature_config_choice"): vol.In({
                "manual": "Saisir manuellement",
                "sensor": "Choisir un capteur"
            }),
        })

        return self.async_show_form(
            step_id="temperature_config",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_temperature_manual(self, user_input=None):
        """Step 5 (sous-étape) : saisie manuelle de la température."""
        errors = {}
        if user_input is not None:
            numeric_fields = [
                ("temperature", "temperature_invalid", lambda x: 0 <= x <= 50, True),
            ]
            for field, error_key, validator, required in numeric_fields:
                try:
                    value = user_input.get(field)
                    if required and (value is None or value == ""):
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
                self._data["use_temperature_sensor"] = False
                self._data["temperature_sensor"] = ""
                return await self.async_step_power_config()

        description = "Entrez la température actuelle mesurée de votre piscine.\n\n- **Température actuelle (°C)** : La température actuelle de l’eau, mesurée manuellement (obligatoire)."
        if self._no_sensor_message:
            description = "Piscinexa n'a pas trouvé de capteur température compatible. Vous devez configurer les valeurs manuellement.\n\n" + description

        schema = vol.Schema({
            vol.Required("temperature", default=20.0): vol.Coerce(float),
        })

        return self.async_show_form(
            step_id="temperature_manual",
            description_placeholders={"description": description},
            data_schema=schema,
            errors=errors,
        )

    async def async_step_temperature_sensor(self, user_input=None):
        """Step 5 (sous-étape) : sélection d'un capteur température."""
        errors = {}
        if user_input is not None:
            temperature_sensor = user_input.get("temperature_sensor", "")
            if not temperature_sensor and ("temperature" not in self._data or self._data["temperature"] is None):
                return await self.async_step_confirm_temperature_sensor()

            if not errors:
                self._data["temperature_sensor"] = temperature_sensor if temperature_sensor else ""
                self._data["use_temperature_sensor"] = bool(temperature_sensor)
                return await self.async_step_power_config()

        temp_sensors = [""]
        temp_sensors_dict = {"": "Aucun capteur"}
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

        schema = vol.Schema({
            vol.Optional("temperature_sensor", default=""): vol.In(temp_sensors_dict),
        })

        return self.async_show_form(
            step_id="temperature_sensor",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_confirm_temperature_sensor(self, user_input=None):
        """Step 5 (sous-étape) : confirmation avant redirection pour température."""
        errors = {}
        if user_input is not None:
            if "confirm_choice" in user_input:
                choice = user_input["confirm_choice"]
                if choice == "manual":
                    self._no_sensor_message = True
                    return await self.async_step_temperature_manual()
                else:
                    return await self.async_step_temperature_sensor()
            else:
                errors["confirm_choice"] = "required_field"

        schema = vol.Schema({
            vol.Required("confirm_choice"): vol.In({
                "manual": "Configurer manuellement",
                "retry": "Réessayer"
            }),
        })

        return self.async_show_form(
            step_id="confirm_temperature_sensor",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_power_config(self, user_input=None):
        """Step 6 : configuration de la puissance (choix entre manuel et capteur)."""
        errors = {}
        if user_input is not None:
            if "power_config_choice" in user_input:
                self._power_config_choice = user_input["power_config_choice"]
                if self._power_config_choice == "manual":
                    self._no_sensor_message = False
                    return await self.async_step_power_manual()
                else:
                    self._no_sensor_message = False
                    return await self.async_step_power_sensor()
            else:
                errors["power_config_choice"] = "required_field"

        schema = vol.Schema({
            vol.Required("power_config_choice"): vol.In({
                "manual": "Saisir manuellement",
                "sensor": "Choisir un capteur"
            }),
        })

        return self.async_show_form(
            step_id="power_config",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_power_manual(self, user_input=None):
        """Step 6 (sous-étape) : saisie manuelle pour la puissance (vide)."""
        description = "Aucune valeur à saisir pour la puissance. Ce champ sera laissé vide."
        if self._no_sensor_message:
            description = "Piscinexa n'a pas trouvé de capteur puissance compatible. Ce champ sera laissé vide.\n\n" + description

        self._data["use_power_sensor"] = False
        self._data["power_sensor_entity_id"] = ""
        return await self.async_step_treatment_config()

    async def async_step_power_sensor(self, user_input=None):
        """Step 6 (sous-étape) : sélection d'un capteur puissance."""
        errors = {}
        if user_input is not None:
            power_sensor = user_input.get("power_sensor_entity_id", "")
            if not power_sensor:
                return await self.async_step_confirm_power_sensor()

            if not errors:
                self._data["power_sensor_entity_id"] = power_sensor if power_sensor else ""
                self._data["use_power_sensor"] = bool(power_sensor)
                return await self.async_step_treatment_config()

        schema = vol.Schema({
            vol.Optional("power_sensor_entity_id", default=""): str,
        })

        return self.async_show_form(
            step_id="power_sensor",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_confirm_power_sensor(self, user_input=None):
        """Step 6 (sous-étape) : confirmation avant redirection pour puissance."""
        errors = {}
        if user_input is not None:
            if "confirm_choice" in user_input:
                choice = user_input["confirm_choice"]
                if choice == "manual":
                    self._no_sensor_message = True
                    return await self.async_step_power_manual()
                else:
                    return await self.async_step_power_sensor()
            else:
                errors["confirm_choice"] = "required_field"

        schema = vol.Schema({
            vol.Required("confirm_choice"): vol.In({
                "manual": "Configurer manuellement",
                "retry": "Réessayer"
            }),
        })

        return self.async_show_form(
            step_id="confirm_power_sensor",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_treatment_config(self, user_input=None):
        """Step 7 : configuration des types de traitements."""
        errors = {}
        if user_input is not None:
            self._data["ph_plus_treatment"] = user_input.get("ph_plus_treatment", "Liquide")
            self._data["ph_minus_treatment"] = user_input.get("ph_minus_treatment", "Liquide")
            self._data["chlore_treatment"] = user_input.get("chlore_treatment", "Chlore choc (poudre)")
            return await self.async_step_summary()

        schema = vol.Schema({
            vol.Required("ph_plus_treatment", default="Liquide"): vol.In({
                "Liquide": "Liquide",
                "Granulés": "Granulés"
            }),
            vol.Required("ph_minus_treatment", default="Liquide"): vol.In({
                "Liquide": "Liquide",
                "Granulés": "Granulés"
            }),
            vol.Required("chlore_treatment", default="Chlore choc (poudre)"): vol.In({
                "Liquide": "Liquide",
                "Chlore choc (poudre)": "Chlore choc (poudre)",
                "Pastille lente": "Pastille lente"
            }),
        })

        return self.async_show_form(
            step_id="treatment_config",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "description": "Sélectionnez les types de produits chimiques utilisés pour les traitements de votre piscine."
            },
        )

    async def async_step_summary(self, user_input=None):
        """Step 8 : récapitulatif avant validation."""
        if user_input is not None:
            return self.async_create_entry(title=f"Piscinexa {self._data['name']}", data=self._data)

        summary = [
            f"Nom de la piscine: {self._data['name']}",
            f"Type de piscine: {self._data['pool_type']}",
            f"Dimensions: {self._get_dimensions_summary()}",
            f"pH actuel: {self._data.get('ph_current', 'Non défini')}",
            f"pH cible: {self._data['ph_target']}",
            f"Source pH: {'Capteur' if self._data.get('use_ph_sensor', False) else 'Valeur manuelle'} ({self._data.get('ph_sensor', 'Aucune sélection')})",
            f"Traitement pH+: {self._data.get('ph_plus_treatment', 'Liquide')}",
            f"Traitement pH-: {self._data.get('ph_minus_treatment', 'Liquide')}",
            f"Chlore actuel: {self._data.get('chlore_current', 'Non défini')} mg/L",
            f"Chlore cible: {self._data['chlore_target']} mg/L",
            f"Source chlore: {'Capteur' if self._data.get('use_chlore_sensor', False) else 'Valeur manuelle'} ({self._data.get('chlore_sensor', 'Aucune sélection')})",
            f"Traitement Chlore: {self._data.get('chlore_treatment', 'Chlore choc (poudre)')}",
            f"Température: {self._data.get('temperature', 'Non défini')} °C",
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

        temp_sensors = [""]
        temp_sensors_dict = {"": "Aucun capteur (ajoutez un capteur de température)"}
        temp_sensor_entities = []
        for state in self.hass.states.async_all("sensor"):
            entity_id = state.entity_id
            if entity_id.startswith(f"sensor.{DOMAIN}_"):
                continue
            attributes = state.attributes
            unit = attributes.get("unit_of_measurement", "").lower()
            device_class = attributes.get("device_class", "").lower()
            friendly_name = attributes.get("friendly_name", entity_id).lower()
            if (device_class == "temperature" or
                unit in ("°c", "°f", "c", "f", "celsius", "fahrenheit") or
                "temperature" in friendly_name or "temp" in friendly_name):
                friendly_name = attributes.get("friendly_name", entity_id)
                temp_sensors.append(entity_id)
                temp_sensors_dict[entity_id] = f"{friendly_name} ({entity_id})"
                temp_sensor_entities.append((entity_id, unit, device_class, friendly_name))

        if len(temp_sensors) == 1:
            temp_sensors.append("sensor.test_temperature")
            temp_sensors_dict["sensor.test_temperature"] = "Test Temperature Sensor (sensor.test_temperature)"
            temp_sensor_entities.append(("sensor.test_temperature", "°C", "temperature", "Test Temperature Sensor"))

        chlore_sensors = [""]
        chlore_sensors_dict = {"": "Aucun capteur (ajoutez un capteur de chlore)"}
        chlore_sensor_entities = []
        for state in self.hass.states.async_all("sensor"):
            entity_id = state.entity_id
            if entity_id.startswith(f"sensor.{DOMAIN}_"):
                continue
            if "chlore_a_ajouter" in entity_id.lower() or "chloreaajouter" in entity_id.lower():
                continue
            attributes = state.attributes
            unit = attributes.get("unit_of_measurement", "").lower()
            friendly_name = attributes.get("friendly_name", entity_id).lower()
            if unit in ("mg/l", "ppm", "mg per liter", "parts per million") or "chlorine" in friendly_name or "chlore" in friendly_name:
                friendly_name = attributes.get("friendly_name", entity_id)
                chlore_sensors.append(entity_id)
                chlore_sensors_dict[entity_id] = f"{friendly_name} ({entity_id})"
                chlore_sensor_entities.append((entity_id, unit, friendly_name))

        ph_sensors = [""]
        ph_sensors_dict = {"": "Aucun capteur (ajoutez un capteur de pH)"}
        ph_sensor_entities = []
        for state in self.hass.states.async_all("sensor"):
            entity_id = state.entity_id
            if entity_id.startswith(f"sensor.{DOMAIN}_"):
                continue
            if "ph_a_ajouter" in entity_id.lower() or "phaajouter" in entity_id.lower():
                continue
            attributes = state.attributes
            unit = attributes.get("unit_of_measurement", "").lower()
            friendly_name = attributes.get("friendly_name", entity_id).lower()
            if unit == "ph" or "ph" in friendly_name or "ph" in entity_id.lower():
                friendly_name = attributes.get("friendly_name", entity_id)
                ph_sensors.append(entity_id)
                ph_sensors_dict[entity_id] = f"{friendly_name} ({entity_id})"
                ph_sensor_entities.append((entity_id, unit, friendly_name))

        if len(ph_sensors) == 1:
            ph_sensors.append("sensor.test_ph")
            ph_sensors_dict["sensor.test_ph"] = "Test pH Sensor (sensor.test_ph)"
            ph_sensor_entities.append(("sensor.test_ph", "pH", "Test pH Sensor"))

        _LOGGER.debug("Capteurs de température trouvés dans les options : %s", temp_sensors)
        _LOGGER.debug("Détails des capteurs de température : %s", temp_sensor_entities)
        _LOGGER.debug("Capteurs de chlore trouvés dans les options : %s", chlore_sensors)
        _LOGGER.debug("Détails des capteurs de chlore : %s", chlore_sensor_entities)
        _LOGGER.debug("Capteurs de pH trouvés dans les options : %s", ph_sensors)
        _LOGGER.debug("Détails des capteurs de pH : %s", ph_sensor_entities)

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