# Abisses

Application locale de préparation des données des bisses : photos, métadonnées,
synchronisation GPX, atelier de segmentation, catégories globales et export
vers la plateforme statique.

## Installation pour utiliser Abisses

Les Releases GitHub fournissent deux installations autonomes :

- `Abisses-Setup-v…-Windows-x64.exe` pour Windows 64 bits ;
- `abisses_…_amd64.deb` pour Ubuntu/Debian 64 bits.

Python, `pip` et les bibliothèques ne doivent pas être installés manuellement.
L'installation crée l'icône Abisses et conserve les données lors des mises à
jour ou de la désinstallation.

## Mise à jour sans manipuler le code

Dans Abisses :

```text
Paramètres → Mises à jour → Rechercher une mise à jour
```

Abisses télécharge l'installateur correspondant au système depuis une Release
GitHub, vérifie son empreinte SHA256, puis l'ouvre. Une vérification automatique
quotidienne peut être activée ou désactivée.

Une version stable ne propose que les Releases stables. Une version bêta
continue de recevoir les Releases bêta afin de permettre les essais.

## Développement

Le dépôt Git reste séparé de l'application installée. Pour modifier le code :

1. cloner le dépôt ;
2. créer un environnement Python ;
3. installer `requirements.txt` ;
4. lancer `lancer_gestion_bisses.py`.

Le lanceur de développement peut encore effectuer un `git pull --ff-only`
lorsque le dépôt est propre. L'application installée, elle, ne dépend ni de Git
ni de GitHub Desktop.

## Emplacement des fichiers locaux

| Élément | Windows | Ubuntu/Linux |
| --- | --- | --- |
| Réglages | `%LOCALAPPDATA%\Abisses\settings.local.json` | `~/.config/Abisses/settings.local.json` |
| Journaux | `%LOCALAPPDATA%\Abisses\logs` | `~/.local/state/Abisses/logs` |
| Cache des mises à jour | `%LOCALAPPDATA%\Abisses\cache\updates` | `~/.cache/Abisses/updates` |

Au premier lancement de la v55 depuis une ancienne copie, le
`settings.local.json` placé près du code est copié sans être supprimé.
`Gestion_Bisses_Data` reste local, sur le NAS ou à l'emplacement choisi par
l'utilisateur.

## Publication d'une version

1. mettre à jour `VERSION` ;
2. valider et pousser le code ;
3. créer un tag identique préfixé par `v`, par exemple
   `v0.55.0-beta.1` ;
4. pousser le tag.

GitHub Actions valide alors le code, construit les installateurs Windows et
Ubuntu, génère `SHA256SUMS` et publie la Release. Les binaires ne sont pas
committés dans le dépôt.

## Principe des données

GitHub contient le logiciel, jamais les données métier :

- `Gestion_Bisses_Data/` reste local ou sur le NAS ;
- les dossiers des bisses contiennent photos, GPX et catalogues ;
- `Export_Platform/` est un produit généré ;
- les réglages propres à un ordinateur ne sont pas versionnés.
