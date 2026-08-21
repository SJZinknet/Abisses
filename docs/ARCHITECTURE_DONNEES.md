# Architecture des données

## GitHub

GitHub est la référence du code de l'application.

Il permet :
- de versionner les modifications;
- de distribuer la même version aux différents ordinateurs;
- de revenir à une ancienne version;
- de valider automatiquement la syntaxe Python;
- de publier des Releases.

Les ordinateurs qui utilisent l'application installée ne font pas de
`git pull`. Ils récupèrent les installateurs contrôlés par leur empreinte
SHA256 depuis les Releases. Le dépôt Git reste réservé au développement.

## Installation locale

Le dossier d'installation contient uniquement le programme et ses
dépendances. Il peut donc être remplacé ou désinstallé sans toucher aux données
des bisses.

Les fichiers propres à chaque ordinateur sont placés dans le profil
utilisateur :

- réglages : `%LOCALAPPDATA%\Abisses` sous Windows ou `~/.config/Abisses`
  sous Linux;
- journaux : dossier local de journaux Abisses;
- cache : dossier local utilisé temporairement pour les installateurs.

Une ancienne configuration placée près de `gestion_bisses.py` est copiée au
premier lancement, sans suppression de l'original.

## Gestion_Bisses_Data

`Gestion_Bisses_Data` reste local à chaque ordinateur ou relié au NAS et est
ignoré par Git.
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
