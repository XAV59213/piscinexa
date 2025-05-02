# 💧 Intégration Piscine pour Home Assistant

![Logo](https://github.com/XAV59213/piscine/blob/main/images/logo.png)

Ce composant personnalisé Home Assistant vous permet de gérer la **qualité de l’eau de votre piscine** (pH, chlore, température, volume) ainsi que la **filtration**, les **recommandations de traitement**, et d'ajouter des **automatisations personnalisées**.

---

### ⚙️ Installation

[![](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=piscine)

1. Copiez le dossier `custom_components/piscine` dans le répertoire `config/custom_components/` de votre Home Assistant.
2. Redémarrez Home Assistant.
3. Allez dans **Paramètres → Appareils & services → Ajouter une intégration**.
4. Recherchez **Piscine**, suivez les étapes de configuration.
5. Configurez les dimensions, le pH/chlore actuels et cibles.

---

### 🧪 Fonctionnalités

- Calcul du volume d’eau
- Temps de filtration recommandé
- Quantité de pH et chlore à ajouter
- Capteur de log intégré (`sensor.piscine_log`)
- Entrées numériques ajustables via l’UI
- Services personnalisés :
  - `piscine.test_calcul`
  - `piscine.reset_valeurs`
- Boutons dans l’intégration : tester, réinitialiser

---

### 🧰 Entités créées

| Entité | Description |
|--------|-------------|
| `sensor.piscine_volume_eau` | Volume calculé (m³) |
| `sensor.piscine_temps_filtration` | Temps de filtration recommandé |
| `sensor.piscine_ph_a_ajouter` | Dose à ajouter |
| `sensor.piscine_chlore_a_ajouter` | Dose à ajouter |
| `sensor.piscine_log` | Journal des actions |
| `input_number.*` | Entrées pour dimensions, pH, chlore |

---

### 📊 Exemple de tableau de bord

Un fichier YAML est fourni ici : [`piscine_dashboard_custom_component.yaml`](./piscine_dashboard_custom_component.yaml)

![Dashboard piscine](./images/screenshot_dashboard.png)

---

### 🧪 Automatisations possibles

```yaml
automation:
  - alias: "Filtration matinale"
    trigger:
      platform: time
      at: "07:00:00"
    action:
      service: switch.turn_on
      entity_id: switch.pompe_piscine
