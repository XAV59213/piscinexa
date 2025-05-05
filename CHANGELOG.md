Changelog
All notable changes to the Piscinexa Home Assistant integration will be documented in this file.
The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.
[1.0.5] - 2025-05-08
Added

Added state change subscriptions to dynamically update sensors (PiscinexaTemperatureSensor, PiscinexaPhSensor, PiscinexaChloreSensor, PiscinexaPoolStateSensor, etc.) when dependent sensors or inputs change.

[1.0.4] - 2025-05-07
Added

Added PiscinexaPoolStateSensor to evaluate the overall pool state (temperature, chlorine, pH, filtration time) and indicate if swimming is allowed.

[1.0.3] - 2025-05-06
Added

Added issue_tracker field in manifest.json to direct users to GitHub issues.
Added hacs field in hacs.json to specify minimum HACS version.

Fixed

Updated sw_version to 1.0.2 in entity DeviceInfo for consistency with manifest.json.

[1.0.2] - 2025-05-05
Added

Added MIT License (LICENSE) to clarify usage terms.

[1.0.1] - 2025-05-04
Added

Added English translations (translations/en.json) to support multilingual users.
Added CHANGELOG.md to document versions and changes.

[1.0.0] - 2025-04-01
Added

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


