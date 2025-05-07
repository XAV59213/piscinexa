ChangelogAll notable changes to the Piscinexa Home Assistant integration will be documented in this file.The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.
[1.0.7] - 2025-05-10Added

Added PiscinexaTempsFiltrationSensor to calculate recommended filtration time based on pool temperature.

Fixed

Resolved "PiscinexaTempsFiltrationSensor is not defined" error by adding the missing sensor class.
Fixed "temperature manquant" warning by making temperature input required in config_flow.py.
Improved handling of existing config entries in __init__.py to prevent "Entrée déjà configurée" errors.

[1.0.6] - 2025-05-09Added

Added new sensors for pH+ to add (sensor.piscinexa_piscine_phplusaajouter) and pH- to add (sensor.piscinexa_piscine_phminusaajouter).
Added input number for pH target (input_number.piscine_ph_target) to allow users to adjust the target pH via the UI.
Updated dashboard (piscine_dashboard_custom_component.yaml) to include new pH+ and pH- sensors and pH target input.
Updated translations (fr.json and en.json) to include new entities.
Enhanced pH management by separating pH+ and pH- calculations for better clarity.

[1.0.5] - 2025-05-08Added

Added state change subscriptions to dynamically update sensors (PiscinexaTemperatureSensor, PiscinexaPhSensor, PiscinexaChloreSensor, PiscinexaPoolStateSensor, etc.) when dependent sensors or inputs change.

[1.0.4] - 2025-05-07Added

Added PiscinexaPoolStateSensor to evaluate the overall pool state (temperature, chlorine, pH, filtration time) and indicate if swimming is allowed.

[1.0.3] - 2025-05-06Added

Added issue_tracker field in manifest.json to direct users to GitHub issues.
Added hacs field in hacs.json to specify minimum HACS version.

Fixed

Updated sw_version to 1.0.2 in entity DeviceInfo for consistency with manifest.json.

[1.0.2] - 2025-05-05Added

Added MIT License (LICENSE) to clarify usage terms.

[1.0.1] - 2025-05-04Added

Added English translations (translations/en.json) to support multilingual users.
Added CHANGELOG.md to document versions and changes.

[1.0.0] - 2025-04-01Added

Initial release of the Piscinexa integration for Home Assistant.
Support for managing pool water quality (pH, chlorine, temperature, volume).
Features include:
Calculation of water volume based on pool dimensions.
Recommended filtration time based on temperature.
Calculation of pH and chlorine amounts to add.
Integrated log sensor (sensor.piscinexa_log).
Adjustable input numbers via the UI.
Custom services: piscinexa.test_calcul and piscinexa.reset_valeurs.
Buttons integrated into the interface.
Example dashboard YAML files (piscine_dashboard_custom_component.yaml and piscine_dashboard_multi.yaml).


Configuration flow to set up pool type, dimensions, and sensor or manual inputs for pH, chlorine, temperature, and power.
French translations (translations/fr.json) for configuration and entities.
Support for square and round pools.
Integration with HACS via hacs.json.



