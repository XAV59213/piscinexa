# 💧 Intégration Piscinexa pour Home Assistant (version améliorée)

![Logo](https://github.com/XAV59213/piscinexa/blob/main/images/logo.png)

Ce composant personnalisé Home Assistant vous permet de gérer la **qualité de l’eau de votre piscine** (pH, chlore, température, volume) ainsi que la **filtration**, les **recommandations de traitement**, et d'ajouter des **automatisations personnalisées**.

---

### ⚙️ Installation

1. Copiez le dossier `custom_components/piscinexa` dans le répertoire `config/custom_components/` de votre Home Assistant.
2. Redémarrez Home Assistant.
3. Allez dans **Paramètres → Appareils & services → Ajouter une intégration**.
4. Recherchez **Piscinexa**, suivez les étapes de configuration.
5. Configurez les dimensions, le pH/chlore actuels et cibles.

---

### 🧪 Fonctionnalités

- Calcul du volume d’eau
- Temps de filtration recommandé
- Quantité de pH et chlore à ajouter
- Capteur de log intégré (`sensor.piscinexa_log`)
- Entrées numériques ajustables via l’UI
- Services personnalisés :
  - `piscinexa.test_calcul`
  - `piscinexa.reset_valeurs`
- Boutons intégrés à l’interface
- Tableau de bord YAML prêt à l’emploi

---

### 🔄 Mise à jour

Si vous installez manuellement, remplacez simplement le dossier `custom_components/piscinexa` par la nouvelle version, puis redémarrez Home Assistant.

---

### 📊 Exemple de tableau de bord

Un fichier YAML est fourni ici : `piscine_dashboard_custom_component.yaml`
![Dashboard piscine](./images/screenshot_dashboard.png)

### 📜 Changelog
Consultez le fichier [CHANGELOG.md](CHANGELOG.md) pour voir l'historique des versions et des modifications de l'intégration Piscinexa.
### 📄 Licence
L'intégration Piscinexa est distribuée sous la [licence MIT](LICENSE). Consultez le fichier LICENSE pour plus de détails.

## [Unreleased]
### Added
- (Liste des fonctionnalités en cours de développement)
