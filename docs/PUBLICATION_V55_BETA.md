# Publication et essai de la v55 bêta

## 1. Publier le code de beta.1

1. Copier les fichiers v55 dans le dépôt local Abisses.
2. Ouvrir GitHub Desktop et vérifier que les données métier n'apparaissent pas.
3. Commiter avec le message :

   ```text
   v0.55.0-beta.1 — installation et mise à jour intégrées
   ```

4. Faire **Push origin**.
5. Attendre que le workflow **Validation Abisses** soit vert.

## 2. Créer la Release beta.1

Depuis un terminal dans le dépôt :

```powershell
py publier_mise_a_jour.py
```

Répondre `PUBLIER`, laisser le message vide si le commit est déjà fait, puis
saisir `0.55.0-beta.1` lorsque le script demande la version de la Release.

Le script peut créer le tag même si le commit a déjà été fait dans GitHub
Desktop. Il retire aussi de Git l'ancien journal
`lancement_gestion_bisses.log`, tout en conservant sa copie locale. Le workflow
**Construire et publier Abisses** produit ensuite le `.exe`, le `.deb` et
`SHA256SUMS`.

## 3. Premier essai sur les deux ordinateurs

Avant l'installation, lancer une fois la nouvelle copie source sur l'ordinateur
de développement permet de copier automatiquement l'ancien
`settings.local.json` vers son nouvel emplacement. Sinon, Abisses demandera
simplement de sélectionner l'ancien `Gestion_Bisses_Data` au premier lancement.

Contrôler sur Windows et Ubuntu :

- installation depuis le fichier téléchargé;
- apparition de l'icône Abisses;
- ouverture maximisée;
- version `v0.55.0-beta.1` dans le titre;
- présence des projets et catégories existants;
- onglet **Paramètres → Mises à jour**;
- absence de modification dans le dépôt Git après utilisation.

## 4. Vérifier réellement l'auto-mise à jour

Après validation de beta.1, publier `0.55.0-beta.2`. Sur les deux ordinateurs :

1. ouvrir **Paramètres → Mises à jour**;
2. cliquer sur **Rechercher une mise à jour**;
3. télécharger et installer beta.2;
4. vérifier que les réglages et données sont conservés.

La version stable `0.55.0` ne sera publiée qu'après cet essai complet.
