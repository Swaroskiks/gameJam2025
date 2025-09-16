#!/usr/bin/env python3
"""
Outil de vérification des assets pour A Day at the Office.
Vérifie que tous les assets du manifest existent et affiche un rapport.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Ajouter le dossier racine au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.settings import ASSETS_PATH, ALT_ASSETS_PATH, DATA_PATH


class AssetChecker:
    """Vérificateur d'assets."""
    
    def __init__(self):
        self.manifest: Dict[str, Any] = {}
        self.missing_assets: List[Tuple[str, str]] = []  # (clé, chemin)
        self.found_assets: List[Tuple[str, str, Path]] = []  # (clé, chemin, chemin_réel)
        self.alt_path_assets: List[Tuple[str, str, Path]] = []  # Assets trouvés dans aassets/
    
    def load_manifest(self, manifest_path: Path = None) -> bool:
        """
        Charge le manifest des assets.
        
        Args:
            manifest_path: Chemin vers le manifest
            
        Returns:
            True si le chargement a réussi
        """
        if manifest_path is None:
            manifest_path = DATA_PATH / "assets_manifest.json"
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                self.manifest = json.load(f)
            print(f"✓ Manifest chargé depuis {manifest_path}")
            return True
        except FileNotFoundError:
            print(f"✗ Manifest non trouvé : {manifest_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"✗ Erreur JSON dans le manifest : {e}")
            return False
        except Exception as e:
            print(f"✗ Erreur lors du chargement : {e}")
            return False
    
    def check_assets(self) -> None:
        """Vérifie tous les assets du manifest."""
        self.missing_assets.clear()
        self.found_assets.clear()
        self.alt_path_assets.clear()
        
        print("\n🔍 Vérification des assets...")
        
        # Parcourir toutes les sections
        for section_name, section in self.manifest.items():
            if section_name in ["version", "description"] or not isinstance(section, dict):
                continue
            
            print(f"\n📁 Section: {section_name}")
            
            if section_name == "audio":
                # Gérer les sous-sections audio
                for subsection_name, subsection in section.items():
                    if isinstance(subsection, dict):
                        print(f"  📁 Sous-section: {subsection_name}")
                        for key, asset_info in subsection.items():
                            if isinstance(asset_info, dict) and "path" in asset_info:
                                self._check_single_asset(f"{subsection_name}_{key}", asset_info["path"])
            else:
                for key, asset_info in section.items():
                    if isinstance(asset_info, dict) and "path" in asset_info:
                        self._check_single_asset(key, asset_info["path"])
    
    def _check_single_asset(self, key: str, relative_path: str) -> None:
        """
        Vérifie un seul asset.
        
        Args:
            key: Clé de l'asset
            relative_path: Chemin relatif
        """
        # Essayer assets/
        full_path = ASSETS_PATH / relative_path
        if full_path.exists():
            self.found_assets.append((key, relative_path, full_path))
            print(f"  ✓ {key} -> {relative_path}")
            return
        
        # Essayer aassets/
        if ALT_ASSETS_PATH.exists():
            alt_full_path = ALT_ASSETS_PATH / relative_path
            if alt_full_path.exists():
                self.alt_path_assets.append((key, relative_path, alt_full_path))
                print(f"  ⚠ {key} -> {relative_path} (trouvé dans aassets/)")
                return
        
        # Asset manquant
        self.missing_assets.append((key, relative_path))
        print(f"  ✗ {key} -> {relative_path} (MANQUANT)")
    
    def print_summary(self) -> None:
        """Affiche un résumé de la vérification."""
        total_assets = len(self.found_assets) + len(self.alt_path_assets) + len(self.missing_assets)
        found_count = len(self.found_assets)
        alt_count = len(self.alt_path_assets)
        missing_count = len(self.missing_assets)
        
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DE LA VÉRIFICATION")
        print("="*60)
        
        print(f"Total des assets    : {total_assets}")
        print(f"Trouvés (assets/)   : {found_count}")
        print(f"Trouvés (aassets/)  : {alt_count}")
        print(f"Manquants           : {missing_count}")
        
        if missing_count == 0:
            print("\n🎉 Tous les assets sont présents !")
        else:
            print(f"\n⚠️  {missing_count} asset(s) manquant(s)")
        
        # Détail des assets manquants
        if self.missing_assets:
            print("\n❌ Assets manquants :")
            for key, path in self.missing_assets:
                print(f"  - {key} : {path}")
        
        # Assets dans aassets/
        if self.alt_path_assets:
            print(f"\n📁 Assets trouvés dans aassets/ ({len(self.alt_path_assets)}) :")
            for key, path, real_path in self.alt_path_assets:
                print(f"  - {key} : {path}")
        
        print("\n" + "="*60)
    
    def generate_report(self, output_file: Path = None) -> None:
        """
        Génère un rapport détaillé.
        
        Args:
            output_file: Fichier de sortie (par défaut: asset_report.txt)
        """
        if output_file is None:
            output_file = Path("asset_report.txt")
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("RAPPORT DE VÉRIFICATION DES ASSETS\n")
                f.write("A Day at the Office\n")
                f.write("="*50 + "\n\n")
                
                # Statistiques
                total = len(self.found_assets) + len(self.alt_path_assets) + len(self.missing_assets)
                f.write(f"Total des assets: {total}\n")
                f.write(f"Trouvés: {len(self.found_assets)}\n")
                f.write(f"Trouvés (alt): {len(self.alt_path_assets)}\n")
                f.write(f"Manquants: {len(self.missing_assets)}\n\n")
                
                # Assets trouvés
                f.write("ASSETS TROUVÉS (assets/):\n")
                f.write("-" * 30 + "\n")
                for key, path, real_path in self.found_assets:
                    f.write(f"{key:30} -> {path}\n")
                
                # Assets alternatifs
                if self.alt_path_assets:
                    f.write(f"\nASSETS TROUVÉS (aassets/):\n")
                    f.write("-" * 30 + "\n")
                    for key, path, real_path in self.alt_path_assets:
                        f.write(f"{key:30} -> {path}\n")
                
                # Assets manquants
                if self.missing_assets:
                    f.write(f"\nASSETS MANQUANTS:\n")
                    f.write("-" * 20 + "\n")
                    for key, path in self.missing_assets:
                        f.write(f"{key:30} -> {path}\n")
            
            print(f"📄 Rapport généré : {output_file}")
            
        except Exception as e:
            print(f"✗ Erreur lors de la génération du rapport : {e}")


def main():
    """Fonction principale."""
    print("🎨 Asset Checker - A Day at the Office")
    print("="*50)
    
    checker = AssetChecker()
    
    # Charger le manifest
    if not checker.load_manifest():
        sys.exit(1)
    
    # Vérifier les assets
    checker.check_assets()
    
    # Afficher le résumé
    checker.print_summary()
    
    # Générer un rapport si demandé
    if "--report" in sys.argv:
        checker.generate_report()
    
    # Code de sortie
    if checker.missing_assets:
        print(f"\n💡 Conseil : Exécutez avec --report pour générer un rapport détaillé")
        sys.exit(1)  # Échec si des assets sont manquants
    else:
        sys.exit(0)  # Succès


if __name__ == "__main__":
    main()
