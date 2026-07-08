# Architecture des données

## GitHub

GitHub est la référence du code de l'application.

Il permet :
- de versionner les modifications;
- de distribuer la même version aux différents ordinateurs;
- de revenir à une ancienne version;
- de valider automatiquement la syntaxe Python;
- de publier des Releases.

## Gestion_Bisses_Data

`Gestion_Bisses_Data` reste local à chaque ordinateur et est ignoré par Git.
Il contient notamment :
- les projets connus;
- les liens vers les dossiers des bisses;
- la bibliothèque;
- le référentiel global des catégories;
- les sauvegardes et manifests.

Il doit être sauvegardé séparément vers le NAS.

## Dossiers des bisses

Les dossiers des bisses restent sur le NAS pour les postes institutionnels en
mode réseau direct. Les ordinateurs privés peuvent utiliser une copie locale
synchronisée avec le NAS.

## Export_Platform

`Export_Platform` est généré à partir des catalogues et sources. Il n'est pas
versionné dans GitHub.
