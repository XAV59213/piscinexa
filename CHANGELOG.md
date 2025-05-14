### [1.0.14] - 2025-05-14 19:29 CEST

#### Fixed
- **Correction d'une erreur de syntaxe dans `sensor.py`** :
  - Résolu une erreur de syntaxe dans la méthode `native_value` de la classe `PiscinexaChloreSensor`. Une soustraction incorrecte (`self._hass.data - self._hass.data[DOMAIN][self._entry.entry_id]["chlore_current"] = value`) a été remplacée par une affectation correcte (`self._hass.data[DOMAIN][self._entry.entry_id]["chlore_current"] = value`).
  - Cette correction résout l'erreur `SyntaxError: cannot assign to expression here` signalée dans les logs de Home Assistant.

#### Changed
- **Refonte de `PiscinexaPhPlusAjouterSensor` dans `sensor.py`** :
  - La classe `PiscinexaPhPlusAjouterSensor` a été restructurée pour adopter la même logique et structure que `PiscinexaPhMinusAjouterSensor`, avec une condition inversée (`ph_current < ph_target`).
  - Ajout de valeurs par défaut explicites pour `ph_current` (7.0), `ph_target` (7.4), et `volume_val` (30.0) pour une meilleure robustesse.
  - Utilisation des mêmes coefficients que `PiscinexaPhMinusAjouterSensor` (0.012 L/m³ pour "Liquide", 1.2 g/m³ pour "Granulés") pour une cohérence dans les calculs.
  - Retour de `0` au lieu de `None` en cas d'erreur pour éviter l'état "inconnu" dans Home Assistant.

#### Added
- **Complétion des classes manquantes dans `sensor.py`** :
  - Ajout des méthodes et propriétés manquantes pour `PiscinexaPhTreatmentSensor`.
  - Ajout des classes `PiscinexaChloreTreatmentSensor`, `PiscinexaChloreStateSensor`, `PiscinexaPhStateSensor`, et `PiscinexaTemperatureStateSensor` pour compléter le fichier.
- **Mise à jour des tableaux de bord** :
  - Ajout des nouveaux capteurs `etat_chlore`, `etat_ph`, et `etat_temperature` dans `piscine_dashboard_custom_component.yaml` et `piscine_dashboard_multi.yaml`.
- **Amélioration des traductions** :
  - Ajout de la clé `platform_load_error` dans `fr.json` et `en.json` pour résoudre l'erreur de traduction manquante signalée dans `__init__.py`.
  - Ajout de la clé `volume_unavailable_message` dans `fr.json` et `en.json`, utilisée dans `PiscinexaPhPlusAjouterSensor` et `PiscinexaPhMinusAjouterSensor`.
  - Ajout des clés pour les capteurs d'état : `chlore_state_ok`, `chlore_state_adjust`, `ph_state_ok`, `ph_state_adjust`, `temperature_state_wait`, `temperature_state_good`, `temperature_state_relax`.

#### Notes
- Les utilisateurs doivent redémarrer Home Assistant après la mise à jour pour que les nouvelles traductions et corrections soient appliquées.
- Assurez-vous que les fichiers `fr.json` et `en.json` sont correctement placés dans `custom_components/piscinexa/translations/`.

---

### [1.0.13] - 2025-05-13

#### Added
- Added new sensors: `pH Difference`, `pH Treatment`, and `Chlorine Treatment` to provide detailed monitoring of pH and chlorine treatment requirements.
- Updated dashboard configurations (`piscine_dashboard_custom_component.yaml` and `piscine_dashboard_multi.yaml`) to include the new sensors.
- Added translations for new sensors in `translations/en.json` and `translations/fr.json`.

#### Fixed
- Fixed `TypeError: expected str, got NoneType` by removing `null` values in translation files.
- Fixed `KeyError: 'piscinexa'` in `config_flow.py` by removing dynamic translation access.

---

### [1.0.12] - 2025-04-15

#### Changed
- Improved performance of sensor updates.
- Updated documentation for better clarity.

---

### [1.0.11] - 2025-03-10

#### Fixed
- Resolved issue with power sensor initialization.
- Fixed SyntaxError in `sensor.py` caused by invalid string in `PiscinexaTempsFiltrationRecommandeSensor` icon definition.

---

### [1.0.10] - 2025-02-20

#### Changed
- Added unit of measurement `mg/L` to sensors `pH Actuel` and `pH Cible` as per user request.

---

### [1.0.9] - 2025-02-15

#### Fixed
- Fixed translation error causing `TypeError: expected str, got NoneType` by removing `unit_of_measurement: null` from sensors without units in `en.json` and `fr.json`.

---

### [1.0.8] - 2025-02-10

#### Fixed
- Corrected missing or inconsistent units of measurement (`h`, `m³`, `°C`, `mg/L`, `W`, etc.) for all sensors by using `native_unit_of_measurement` and updating translations.

---

### [1.0.7] - 2025-02-05

#### Added
- Added new sensor "Temps de filtration effectué" to track the cumulative time (in hours) when the power sensor exceeds 10 W, indicating active filtration.

---

### [1.0.6] - 2025-02-01

#### Changed
- Renamed "Temps de filtration" sensor to "Temps de filtration recommandé" to better reflect its purpose.

---

### [1.0.5] - 2025-01-28

#### Added
- Added state change subscriptions to dynamically update sensors (`PiscinexaTemperatureSensor`, `PiscinexaPhSensor`, `PiscinexaChloreSensor`, `PiscinexaPoolStateSensor`, etc.) when dependent sensors or inputs change.

---

### [1.0.4] - 2025-01-20

#### Added
- Added `PiscinexaPoolStateSensor` to evaluate the overall pool state (temperature, chlorine, pH, filtration time) and indicate if swimming is allowed.

---

### [1.0.3] - 2025-01-15

#### Added
- Added `issue_tracker` field in `manifest.json` to direct users to GitHub issues.
- Added `hacs` field in `hacs.json` to specify minimum HACS version.

#### Fixed
- Updated `sw_version` to `1.0.2` in entity `DeviceInfo` for consistency with `manifest.json`.

---

### [1.0.2] - 2025-01-10

#### Added
- Added MIT License (`LICENSE`) to clarify usage terms.

---

### [1.0.1] - 2025-01-05

#### Added
- Added English translations (`translations/en.json`) to support multilingual users.
- Added `CHANGELOG.md` to document versions and changes.

---

### [1.0.0] - 2025-04-01

#### Added
- Initial release of the Piscinexa integration for Home Assistant.
- Support for managing pool water quality (pH, chlorine, temperature, volume).
- Features include:
  - Calculation of water volume based on pool dimensions.
  - Recommended filtration time based on temperature.
  - Calculation of pH and chlorine amounts to add.
  - Integrated log sensor (`sensor.piscinexa_log`).
  - Adjustable input numbers via the UI.
  - Custom services: `piscinexa.test_calcul` and `piscinexa.reset_valeurs`.
  - Buttons integrated into the interface.
  - Example dashboard YAML files (`piscine_dashboard_custom_component.yaml` and `piscine_dashboard_multi.yaml`).
- Configuration flow to set up pool type, dimensions, and sensor or manual inputs for pH, chlorine, temperature, and power.
- French translations (`translations/fr.json`) for configuration and entities.
- Support for square and round pools.
- Integration with HACS via `hacs.json`.
