💧 Intégration Piscinexa pour Home Assistant (version 1.0.5)

Ce composant personnalisé Home Assistant vous permet de gérer la qualité de l’eau de votre piscine (pH, chlore, température, volume) ainsi que la filtration, les recommandations de traitement, et d'ajouter des automatisations personnalisées.

🌍 Langues supportéesL'intégration Piscinexa prend en charge plusieurs langues : français et anglais. Les chaînes visibles dans l'interface utilisateur sont traduites en fonction de la langue configurée dans Home Assistant.

⚙️ Installation
Copiez le dossier custom_components/piscinexa dans le répertoire config/custom_components/ de votre Home Assistant.Redémarrez Home Assistant.Allez dans Paramètres → Appareils & services → Ajouter une intégration.Recherchez Piscinexa, suivez les étapes de configuration.Configurez les dimensions, le pH/chlore actuels et cibles.

🧪 Fonctionnalités
Calcul du volume d’eauTemps de filtration recommandéQuantité de pH et chlore à ajouterCapteur de log intégré (sensor.piscinexa_log)Entrées numériques ajustables via l’UIServices personnalisés :piscinexa.test_calculpiscinexa.reset_valeurs  
Boutons intégrés à l’interfaceTableau de bord YAML prêt à l’emploi

🔄 Mise à jourSi vous installez manuellement, remplacez simplement le dossier custom_components/piscinexa par la nouvelle version, puis redémarrez Home Assistant.

📊 Exemple de tableau de bordUn fichier YAML est fourni ici : piscine_dashboard_custom_component.yaml

📜 ChangelogConsultez le fichier CHANGELOG.md pour voir l'historique des versions et des modifications de l'intégration Piscinexa.

📄 LicenceL'intégration Piscinexa est distribuée sous la licence MIT. Consultez le fichier LICENSE pour plus de détails.

🐞 Signaler un problèmeSi vous rencontrez des bugs ou avez des suggestions, veuillez ouvrir une issue sur GitHub.
