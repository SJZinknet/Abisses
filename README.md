# Gestion Bisses

Application locale de préparation des données des bisses : photos, synchronisation
GPX, atelier de segmentation, catégories globales et export vers la plateforme
statique.

## Principe d'architecture

GitHub contient **le logiciel**, pas les données métier.

- `gestion_bisses.py` : application principale.
- `Gestion_Bisses_Data/` : données locales du logiciel, exclues de Git.
- dossiers des bisses : sources photo, GPX et `catalogue.json`, stockés localement
  ou sur le NAS.
- `Export_Platform/` : produit généré, exclu de Git.

## Installation sur un ordinateur

1. Cloner le dépôt avec GitHub Desktop.
2. Double-cliquer sur `installer_dependances.bat`.
3. Double-cliquer sur `lancer_gestion_bisses.bat`.

Au lancement, le script tente une mise à jour avec `git pull --ff-only`.
En cas d'échec réseau, l'application démarre avec la version locale.

## Mise à jour du logiciel

Sur l'ordinateur de développement :

1. remplacer ou modifier `gestion_bisses.py`;
2. lancer `python publier_mise_a_jour.py`;
3. confirmer avec `PUBLIER`;
4. saisir un message de mise à jour;
5. éventuellement créer un tag de version.

Un tag `v...` déclenche automatiquement une Release GitHub téléchargeable.

## Données à ne jamais mettre dans GitHub

- `Gestion_Bisses_Data/`
- `Photos/`
- `Fichiers GPX/`
- `catalogue.json` des bisses
- `Export_JPG/`
- `Export_Platform/`

Ces données restent locales ou sur le NAS.
