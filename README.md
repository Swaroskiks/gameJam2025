<<<<<<< HEAD
# -gameJam2025

Mécanique du cheval :

Endurance : le cheval peut aller au pas, trot, galop baisse plus au moins l’endurance, endurance basse = vitesse réduite

Combats : le cheval doit se déplacer dans certaines zone pour que le chevalier puisse mettre un coup, pareil avec des zones d’esquives 
En fonction de l’allure du cheval des attaques différentes sont disponibles pour le héro 

Lien de confiance : Il y a un lien de confiance entre le chevalier et son destrier, un lien de confiance bas apporte des effets négatifs. Un coup reçu par un ennemi une mauvaise décision peut dégrader le lien de confiance, au contraire une victoire/ un événement positif peut améliorer le lien.


 Ennemis & pièges :

Piquiers (dangereux de face si tu charges mal),

Archers (créent de la peur si tu restes dans leur cône),

Fantassins boucliers (nécessitent saut ou esquive pour exposer flanc),

Loups / chiens (plutôt dans les scènes sans chevalier),

Pièges : pieux, boue (ralentit), feu (peur), ponts branlants






## Installation et lancement (Windows / PowerShell)

1. Installe Python 3.11+ depuis le site officiel.
2. Dans le dossier du projet, crée un environnement virtuel et installe les dépendances :

```powershell
python -m venv .venv
.# Active l'environnement (PowerShell)
\.venv\Scripts\Activate.ps1

# Mets pip à jour et installe les libs
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si PowerShell bloque l'activation, exécute d'abord :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

3. Lance le jeu :

```powershell
python -m src.main
```

Quitter : touche `Échap` ou fermer la fenêtre.


## Structure du projet

```
-gameJam2025/
├─ src/
│  ├─ __init__.py
│  ├─ main.py         # Point d'entrée (boucle de jeu, rendu, events)
│  └─ settings.py     # Constantes (taille fenêtre, FPS, couleurs)
├─ assets/
│  ├─ images/
│  ├─ sounds/
│  └─ fonts/
├─ requirements.txt   # Dépendances (pygame)
├─ .gitignore         # Fichiers à exclure du repo
└─ README.md
```


## Développement

- **Lancer en mode dev**: `python -m src.main`
- **FPS affiché** en haut à gauche pour vérifier les perfs.
- Ajoute tes assets dans `assets/` et importe-les via Pygame.


## Dépendances

- `pygame==2.6.1`

Pitch du jeu
GameJam 2025



Réalisé par 
Tom WAMBEKE -Yohan LI - Auguste SAGAERT - Mouad MOUSTARZAK - Loïc DEBUCHY




Description
Le joueur incarne le destrier d’un chevalier et l’accompagne tout au long de son aventure. Le gameplay repose sur des actions spécifiques au cheval (déplacements, soutien, esquives, transport), permettant d’influencer indirectement l’histoire sans en être le héros principal.

Environnement technique
Le jeu sera développé en Python avec la librairie Pygame pour la gestion graphique et des événements, et l’ensemble du code sera versionné et collaborativement géré via GitHub

Challenges pressenties
Créer un gameplay intéressant pour le destrier sans éclipser le chevalier.
Gérer les animations et interactions techniques avec Pygame
Intégrer l’histoire du chevalier de manière crédible et cohérente.
Respect du thème
Le jeu respecte le thème car le joueur incarne un personnage secondaire : le destrier. Il contribue à l’aventure du chevalier sans être au centre du récit, renforçant l’idée de participer à une histoire dont il n’est pas le protagoniste.



=======
>>>>>>> e490363acc787a1071f9a6f36edb78db637d6145

