# Guide de Contrôle des Sprites - A Day at the Office

## 🎯 Vue d'ensemble

Ce guide vous explique comment contrôler précisément la **taille**, **position** et **apparence** de tous les sprites dans votre jeu multi-étages.

## 📏 Dimensionnement des Sprites

### 1. Fichier Principal : `src/data/assets_manifest.json`

Toutes les tailles sont définies ici. Modifiez les valeurs `frame_w` et `frame_h` :

```json
{
  "images": {
    "player_idle": {
      "path": "sprites/player_idle.png",
      "frame_w": 32,  ← Largeur finale du joueur
      "frame_h": 48,  ← Hauteur finale du joueur
      "description": "Joueur au repos"
    },
    "elevator": {
      "path": "sprites/elevator.png", 
      "frame_w": 80,  ← Largeur de l'ascenseur
      "frame_h": 140, ← Hauteur de l'ascenseur (prend 70% de l'étage)
      "description": "Cabine d'ascenseur"
    }
  }
}
```

### 2. Tailles Recommandées (Vue 3 Étages)

**Dimensions écran :**
- Largeur totale : 1200px
- Hauteur totale : 600px  
- Hauteur par étage : 200px (600÷3)
- Zone de jeu : 1050px de large (1200-150)

**Sprites recommandés :**
```json
"player_idle": {"frame_w": 32, "frame_h": 48},    // Joueur
"npc_generic": {"frame_w": 32, "frame_h": 48},    // NPCs
"elevator": {"frame_w": 80, "frame_h": 140},      // Ascenseur (70% étage)
"interactable_plant": {"frame_w": 24, "frame_h": 32},    // Plante
"interactable_papers": {"frame_w": 16, "frame_h": 16},   // Papiers
"interactable_printer": {"frame_w": 48, "frame_h": 32}   // Imprimante
```

### 3. Redimensionnement Automatique

Le système préserve automatiquement les proportions :
- Vos images sont **redimensionnées** aux tailles du manifest
- Les **proportions** sont conservées (pas de déformation)
- **Ratio intelligent** : utilise le plus petit ratio pour que l'image tienne

## 📍 Positionnement des Objets

### 1. Fichier Principal : `src/data/floors.json`

Contrôlez la position exacte de chaque objet :

```json
{
  "floors": {
    "98": {
      "name": "Direction",
      "bg_key": "floor_98",
      "objects": [
        {
          "id": "plant_98",
          "kind": "plant",
          "x": 500,    ← Position X dans l'étage (0-1050)
          "y": 0,      ← Position Y (toujours 0 = posé au sol)
          "props": {"task_id": "water_plant", "thirst": 0.8}
        }
      ]
    }
  }
}
```

### 2. Système de Coordonnées

**Référentiel par étage :**
- **X=0** : Bord gauche de la zone de jeu
- **X=1050** : Bord droit de la zone de jeu  
- **Y=0** : Objets automatiquement posés au sol
- **Centre étage** : X=525

**Positions typiques :**
```json
// Répartition dans un bureau
{"x": 150, "y": 0}   // Près de la gauche
{"x": 300, "y": 0}   // Gauche-centre  
{"x": 525, "y": 0}   // Centre exact
{"x": 750, "y": 0}   // Droite-centre
{"x": 900, "y": 0}   // Près de la droite
```

### 3. Types d'Objets Supportés

```json
// NPCs
{"kind": "npc", "props": {"name": "Alex", "dialogue_key": "alex_morning"}}

// Objets interactifs
{"kind": "plant", "props": {"task_id": "water_plant", "thirst": 0.8}}
{"kind": "papers", "props": {"task_id": "organize_papers"}}
{"kind": "printer", "props": {"task_id": "fix_printer", "jammed": true}}

// Décorations (pas d'interaction)
{"kind": "decoration", "props": {"sprite": "painting_office"}}
```

## 🎨 Effets Visuels Automatiques

### 1. Effets Selon les Props

**Plantes assoiffées :**
```json
{"kind": "plant", "props": {"thirst": 0.8}}  // > 0.7 = teinte jaune
```

**Imprimantes bloquées :**
```json
{"kind": "printer", "props": {"jammed": true}}  // = teinte rouge
```

**Objets utilisés :**
```json
// Automatiquement grisés après interaction
```

### 2. Mapping des Sprites

Le système mappe automatiquement les `kind` vers les sprites :

```javascript
"plant" → "interactable_plant"
"papers" → "interactable_papers"  
"printer" → "interactable_printer"
"npc" → "npc_generic"
"decoration" → "interactable_plant" (fallback)
```

## 🔧 Workflow de Personnalisation

### 1. Ajuster les Tailles

1. **Ouvrez** `src/data/assets_manifest.json`
2. **Modifiez** `frame_w` et `frame_h` pour l'objet voulu
3. **Sauvegardez** le fichier
4. **Dans le jeu** : Appuyez **F5** pour recharger
5. **Résultat** : Tailles immédiatement mises à jour

### 2. Repositionner les Objets

1. **Ouvrez** `src/data/floors.json`
2. **Modifiez** la valeur `x` de l'objet (0-1050)
3. **Sauvegardez** le fichier  
4. **Relancez** le jeu pour voir les changements
5. **Résultat** : Objets repositionnés précisément

### 3. Ajouter des Objets

```json
{
  "id": "mon_objet",           // ID unique
  "kind": "plant",             // Type d'objet
  "x": 400,                    // Position X (0-1050)
  "y": 0,                      // Position Y (toujours 0)
  "props": {                   // Propriétés spéciales
    "task_id": "ma_tache",
    "thirst": 0.5
  }
}
```

## 🎮 Contrôles de Test

- **F5** : Recharger assets (nouvelles tailles)
- **0-9** : Changer d'étage pour tester
- **T** : Toggle panneau tâches
- **E** : Interagir avec objets

## 📊 Dimensions Exactes Actuelles

**Vue 3 étages :**
- Étage 1 : Y=0-200
- Étage 2 : Y=200-400  
- Étage 3 : Y=400-600

**Zone de jeu :**
- X=120 à X=1170 (1050px de large)
- Ascenseur : X=30 (largeur 80px)

**Sprites actuels :**
- Joueur : 32×48px
- NPCs : 32×48px
- Ascenseur : 80×140px
- Plante : 24×32px
- Papiers : 16×16px
- Imprimante : 48×32px

## 🔄 Rechargement à Chaud

**Pour tester rapidement :**
1. Modifiez `assets_manifest.json` ou `floors.json`
2. Dans le jeu : **F5** (pour assets) ou **redémarrer** (pour positions)
3. Changements immédiatement visibles

## 💡 Conseils

- **Testez sur plusieurs étages** pour voir la cohérence
- **Utilisez X=525** pour centrer un objet
- **Espacez de 100-150px** entre objets pour éviter le chevauchement
- **Gardez les sprites < 50px** pour une vue claire
- **Les fonds d'étage** sont automatiquement étirés à 1050×190px
