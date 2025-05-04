Changelog
All notable changes to the Piscinexa Home Assistant integration will be documented in this file.
The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.
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

