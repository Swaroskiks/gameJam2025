#!/usr/bin/env python3
"""
Testeur d'interactions pour vérifier le placement et les dialogues.
"""

import sys
from pathlib import Path

# Ajouter le dossier racine au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pygame
import json
from src.core.assets import asset_manager

def main():
    """Test des interactions et dialogues."""
    pygame.init()
    screen = pygame.display.set_mode((1200, 600))
    pygame.display.set_caption("Test Interactions - A Day at the Office")
    
    print("🎮 Test des Interactions")
    print("========================")
    
    # Charger les données
    try:
        with open("src/data/floors.json", 'r', encoding='utf-8') as f:
            floors_data = json.load(f)
        
        with open("src/data/strings_fr.json", 'r', encoding='utf-8') as f:
            strings_data = json.load(f)
        
        print("✅ Données chargées")
    except Exception as e:
        print(f"❌ Erreur chargement: {e}")
        return
    
    # Analyser les objets et dialogues
    print("\n📋 Objets par étage :")
    floors = floors_data.get('floors', {})
    
    for floor_num, floor_data in floors.items():
        objects = floor_data.get('objects', [])
        print(f"\n🏢 Étage {floor_num} - {floor_data.get('name', 'Sans nom')} :")
        
        for obj in objects:
            kind = obj.get('kind', 'unknown')
            obj_id = obj.get('id', 'unknown')
            x = obj.get('x', 0)
            props = obj.get('props', {})
            
            if kind == "npc":
                name = props.get('name', 'Inconnu')
                dialogue_key = props.get('dialogue_key', 'Aucun')
                
                # Vérifier si le dialogue existe
                dialogues = strings_data.get('dialogues', {})
                dialogue_exists = dialogue_key in dialogues
                dialogue_status = "✅" if dialogue_exists else "❌"
                
                print(f"  👤 {name} (x={x}) - Dialogue: {dialogue_key} {dialogue_status}")
                
                if dialogue_exists:
                    dialogue_lines = dialogues[dialogue_key]
                    print(f"     💬 \"{dialogue_lines[0] if dialogue_lines else 'Vide'}\"")
            else:
                task_id = props.get('task_id', 'Aucune')
                print(f"  📦 {kind} (x={x}) - Tâche: {task_id}")
    
    print("\n🎯 Conseils de placement :")
    print("  - Zone de jeu : X=0 à X=1050")
    print("  - Espacement recommandé : 100-150px entre objets")
    print("  - Position ascenseur : X=70 (centre)")
    print("  - Distance interaction : 80px")
    
    print("\n🔧 Pour corriger les interactions :")
    print("  1. Vérifiez que les objets sont espacés de 80+ pixels")
    print("  2. Assurez-vous que les dialogue_key existent dans strings_fr.json")
    print("  3. Testez en jeu avec la touche E près des objets")
    
    pygame.quit()

if __name__ == "__main__":
    main()
