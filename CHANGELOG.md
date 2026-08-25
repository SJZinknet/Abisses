# Journal des versions

## v56

- Atelier Photos organisé en trois panneaux indépendants : carte, photo et
  métadonnées ;
- séparateurs visibles et déplaçables, avec des tailles minimales réduites ;
- carte agrandie à l'ouverture et mode « Carte seule » en un clic ;
- menu « Panneaux » pour afficher ou masquer chaque module sans perdre le
  travail en cours ;
- commandes des couches cartographiques regroupées dans un menu compact ;
- version stable courte `v56`, sans suffixe bêta.

## 0.55.0-beta.1

- nom Abisses dans l'application et les nouveaux paquets;
- réglages, journaux et cache déplacés dans le profil utilisateur;
- migration non destructive de l'ancien `settings.local.json`;
- détection des chemins appartenant à un autre système d'exploitation;
- onglet Paramètres → Mises à jour;
- vérification automatique facultative et bouton de vérification manuelle;
- téléchargement des Releases GitHub avec contrôle SHA256;
- installateur Windows 64 bits et paquet Ubuntu/Debian 64 bits;
- construction et publication automatiques par GitHub Actions;
- séparation entre copie de développement Git et application installée.

## 0.54.0

- fusion de la v53 avec la fenêtre principale adaptative;
- ouverture maximisée sous Windows et Ubuntu/Linux;
- taille de repli adaptée aux petits écrans.

## 0.53.0

- utilisation de plusieurs GPX topo/live comme réseau géométrique pour le tri;
- conservation des coordonnées préexistantes lorsqu'une photo est hors des
  plages temporelles GPX.

## 0.49.0

- catégories de segments globales;
- nettoyage et migration assistés des anciennes catégories;
- sauvegardes et manifest avant migration;
- carte photo avec agrégats;
- visionneuse flottante ou intégrée;
- synchronisation photo multi-GPX;
- écriture GPS EXIF dans les JPG;
- garde-fous Data/local et exports sécurisés.
