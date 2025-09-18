"""
Système de gestion des assets avec fallbacks et asset discovery.
Charge le manifest, génère des placeholders pour les assets manquants,
et recherche automatiquement dans assets/ puis aassets/.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union
import pygame
from src.settings import (
    ASSETS_PATH, ALT_ASSETS_PATH, DATA_PATH, 
    FALLBACK_FONT_SIZE, ASSET_SCALE, DEV_MODE
)

logger = logging.getLogger(__name__)


class AssetManager:
    """
    Gestionnaire d'assets avec fallbacks automatiques et asset discovery.
    """
    
    def __init__(self):
        self.manifest: Dict[str, Any] = {}
        self.cache: Dict[str, Any] = {}
        self.missing_assets: set = set()
        self.discovered_assets: Dict[str, Path] = {}
        
        # Initialiser pygame.mixer si pas déjà fait
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except pygame.error as e:
                logger.warning(f"Could not initialize mixer: {e}")
    
    def load_manifest(self, manifest_path: Optional[Path] = None) -> bool:
        """
        Charge le manifest des assets.
        
        Args:
            manifest_path: Chemin vers le manifest, ou None pour le chemin par défaut
            
        Returns:
            True si le chargement a réussi
        """
        if manifest_path is None:
            manifest_path = DATA_PATH / "assets_manifest.json"
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                self.manifest = json.load(f)
            logger.info(f"Manifest loaded from {manifest_path}")
            
            # Valider le manifest si possible
            self._validate_manifest()
            
            # Découvrir les assets existants
            self._discover_assets()
            
            return True
            
        except FileNotFoundError:
            logger.error(f"Manifest not found: {manifest_path}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in manifest: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading manifest: {e}")
            return False
    
    def _validate_manifest(self) -> None:
        """Valide la structure basique du manifest."""
        if "version" not in self.manifest:
            logger.warning("Manifest missing version field")
        
        expected_sections = ["images", "spritesheets", "tilesets", "backgrounds", "fonts", "audio"]
        for section in expected_sections:
            if section not in self.manifest:
                logger.debug(f"Manifest missing optional section: {section}")
    
    def _discover_assets(self) -> None:
        """
        Découvre les assets existants dans assets/ et aassets/.
        Crée un mapping clé -> chemin_réel pour les assets trouvés.
        """
        self.discovered_assets.clear()
        
        # Parcourir toutes les clés du manifest
        for section_name, section in self.manifest.items():
            if section_name in ["version", "description"] or not isinstance(section, dict):
                continue
            
            # Gérer les sous-sections audio
            if section_name == "audio":
                for subsection_name, subsection in section.items():
                    if isinstance(subsection, dict):
                        for key, asset_info in subsection.items():
                            if isinstance(asset_info, dict) and "path" in asset_info:
                                self._discover_single_asset(f"{subsection_name}_{key}", asset_info["path"])
            else:
                for key, asset_info in section.items():
                    if isinstance(asset_info, dict) and "path" in asset_info:
                        self._discover_single_asset(key, asset_info["path"])
    
    def _discover_single_asset(self, key: str, relative_path: str) -> None:
        """
        Découvre un seul asset en cherchant dans assets/ puis aassets/.
        
        Args:
            key: Clé de l'asset dans le manifest
            relative_path: Chemin relatif depuis le dossier assets
        """
        # Essayer d'abord assets/
        full_path = ASSETS_PATH / relative_path
        if full_path.exists():
            self.discovered_assets[key] = full_path
            logger.debug(f"Asset found: {key} -> {full_path}")
            return
        
        # Essayer ensuite aassets/ si il existe
        if ALT_ASSETS_PATH.exists():
            alt_full_path = ALT_ASSETS_PATH / relative_path
            if alt_full_path.exists():
                self.discovered_assets[key] = alt_full_path
                logger.info(f"Asset found in alt path: {key} -> {alt_full_path}")
                return
        
        # Asset manquant
        self.missing_assets.add(key)
        logger.warning(f"Asset not found: {key} (expected: {relative_path})")
    
    def _get_asset_info(self, section: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'un asset depuis le manifest.
        
        Args:
            section: Section du manifest (images, fonts, etc.)
            key: Clé de l'asset
            
        Returns:
            Dictionnaire des infos de l'asset ou None
        """
        section_data = self.manifest.get(section, {})
        
        # Gérer les sous-sections audio
        if section == "audio":
            for subsection in section_data.values():
                if isinstance(subsection, dict) and key in subsection:
                    return subsection[key]
            return None
        
        return section_data.get(key)
    
    def _create_placeholder_surface(self, width: int, height: int, text: str) -> pygame.Surface:
        """
        Crée une surface placeholder avec motif damier et texte.
        
        Args:
            width: Largeur de la surface
            height: Hauteur de la surface
            text: Texte à afficher au centre
            
        Returns:
            Surface pygame avec placeholder
        """
        surface = pygame.Surface((width, height))
        
        # Motif damier gris
        tile_size = 8
        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                color = (200, 200, 200) if (x // tile_size + y // tile_size) % 2 else (150, 150, 150)
                rect = pygame.Rect(x, y, min(tile_size, width - x), min(tile_size, height - y))
                surface.fill(color, rect)
        
        # Bordure
        pygame.draw.rect(surface, (255, 0, 0), surface.get_rect(), 2)
        
        # Texte centré
        try:
            font = pygame.font.SysFont(None, min(24, width // 8))
            text_surface = font.render(text, True, (255, 0, 0))
            text_rect = text_surface.get_rect(center=(width // 2, height // 2))
            surface.blit(text_surface, text_rect)
        except Exception as e:
            logger.debug(f"Could not render placeholder text: {e}")
        
        return surface
    
    def get_image(self, key: str) -> pygame.Surface:
        """
        Récupère une image, avec fallback vers placeholder si manquante.
        
        Args:
            key: Clé de l'image dans le manifest
            
        Returns:
            Surface pygame (image ou placeholder)
        """
        cache_key = f"image_{key}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Essayer de charger depuis asset découvert
        if key in self.discovered_assets:
            try:
                surface = pygame.image.load(self.discovered_assets[key]).convert_alpha()
                
                # Redimensionner selon le manifest en préservant les proportions
                asset_info = self._get_asset_info("images", key)
                if asset_info and ("frame_w" in asset_info and "frame_h" in asset_info):
                    # Tailles cibles depuis le manifest
                    target_w = asset_info["frame_w"]
                    target_h = asset_info["frame_h"]
                    
                    # Calculer le ratio pour préserver les proportions
                    original_w, original_h = surface.get_size()
                    ratio_w = target_w / original_w
                    ratio_h = target_h / original_h
                    
                    # Utiliser le plus petit ratio pour que l'image tienne dans les dimensions cibles
                    ratio = min(ratio_w, ratio_h)
                    
                    # Calculer les nouvelles dimensions proportionnelles
                    new_w = int(original_w * ratio)
                    new_h = int(original_h * ratio)
                    
                    # Redimensionner en préservant les proportions
                    surface = pygame.transform.scale(surface, (new_w, new_h))
                elif ASSET_SCALE != 1:
                    # Appliquer seulement le facteur d'échelle si pas de taille spécifiée
                    width = surface.get_width() * ASSET_SCALE
                    height = surface.get_height() * ASSET_SCALE
                    surface = pygame.transform.scale(surface, (width, height))
                
                self.cache[cache_key] = surface
                return surface
                
            except Exception as e:
                logger.error(f"Error loading image {key}: {e}")
        
        # Créer placeholder
        asset_info = self._get_asset_info("images", key)
        if asset_info:
            width = asset_info.get("frame_w", 64) * ASSET_SCALE
            height = asset_info.get("frame_h", 64) * ASSET_SCALE
        else:
            width = height = 64 * ASSET_SCALE
        
        surface = self._create_placeholder_surface(width, height, key)
        self.cache[cache_key] = surface
        
        if DEV_MODE:
            logger.debug(f"Created placeholder for image: {key}")
        
        return surface
    
    def get_background(self, key: str) -> pygame.Surface:
        """
        Récupère un fond d'écran, identique à get_image mais sémantiquement différent.
        
        Args:
            key: Clé du fond dans le manifest
            
        Returns:
            Surface pygame (fond ou placeholder)
        """
        return self.get_image(key)
    
    def get_spritesheet(self, key: str) -> Tuple[pygame.Surface, Dict[str, Any]]:
        """
        Récupère une spritesheet avec ses métadonnées.
        
        Args:
            key: Clé de la spritesheet
            
        Returns:
            Tuple (surface, metadata_dict)
        """
        cache_key = f"spritesheet_{key}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Essayer de charger depuis asset découvert
        if key in self.discovered_assets:
            try:
                surface = pygame.image.load(self.discovered_assets[key]).convert_alpha()
                asset_info = self._get_asset_info("spritesheets", key) or {}
                
                # Redimensionner selon le manifest en préservant les proportions
                if asset_info and ("frame_w" in asset_info and "frame_h" in asset_info):
                    # Calculer la taille cible d'une frame (utiliser les valeurs du manifest directement)
                    target_frame_w = asset_info["frame_w"]
                    target_frame_h = asset_info["frame_h"]
                    frames = asset_info.get("frames", 1)
                    
                    # Calculer les dimensions originales d'une frame
                    original_w, original_h = surface.get_size()
                    original_frame_w = original_w // frames  # Assumer disposition horizontale
                    original_frame_h = original_h
                    
                    # Calculer le ratio pour préserver les proportions
                    ratio_w = target_frame_w / original_frame_w
                    ratio_h = target_frame_h / original_frame_h
                    ratio = min(ratio_w, ratio_h)
                    
                    # Appliquer le ratio à toute la spritesheet
                    new_w = int(original_w * ratio)
                    new_h = int(original_h * ratio)
                    surface = pygame.transform.scale(surface, (new_w, new_h))
                    
                    # Mettre à jour les dimensions réelles des frames dans asset_info
                    asset_info = asset_info.copy()
                    asset_info["frame_w"] = new_w // frames
                    asset_info["frame_h"] = new_h
                elif ASSET_SCALE != 1:
                    # Appliquer seulement le facteur d'échelle si pas de taille spécifiée
                    width = surface.get_width() * ASSET_SCALE
                    height = surface.get_height() * ASSET_SCALE
                    surface = pygame.transform.scale(surface, (width, height))
                    
                    # Ajuster les dimensions des frames
                    asset_info = asset_info.copy()
                    if "frame_w" in asset_info:
                        asset_info["frame_w"] *= ASSET_SCALE
                    if "frame_h" in asset_info:
                        asset_info["frame_h"] *= ASSET_SCALE
                
                result = (surface, asset_info)
                self.cache[cache_key] = result
                return result
                
            except Exception as e:
                logger.error(f"Error loading spritesheet {key}: {e}")
        
        # Créer placeholder avec plusieurs frames
        asset_info = self._get_asset_info("spritesheets", key) or {}
        frame_w = asset_info.get("frame_w", 32) * ASSET_SCALE
        frame_h = asset_info.get("frame_h", 32) * ASSET_SCALE
        frames = asset_info.get("frames", 2)
        
        # Créer une spritesheet horizontale avec variations de couleur
        total_width = frame_w * frames
        surface = pygame.Surface((total_width, frame_h))
        
        for i in range(frames):
            x = i * frame_w
            # Varier la couleur pour distinguer les frames
            hue = (i * 60) % 360
            color = pygame.Color(0)
            color.hsla = (hue, 50, 75, 100)
            
            frame_surface = self._create_placeholder_surface(frame_w, frame_h, f"{key}_{i}")
            # Teinter légèrement
            frame_surface.fill((*color[:3], 50), special_flags=pygame.BLEND_ADD)
            surface.blit(frame_surface, (x, 0))
        
        result = (surface, asset_info)
        self.cache[cache_key] = result
        
        if DEV_MODE:
            logger.debug(f"Created placeholder spritesheet: {key}")
        
        return result
    
    def get_font(self, key: str) -> pygame.font.Font:
        """
        Récupère une police, avec fallback vers police système si manquante.
        
        Args:
            key: Clé de la police
            
        Returns:
            Objet Font pygame
        """
        cache_key = f"font_{key}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        asset_info = self._get_asset_info("fonts", key)
        size = asset_info.get("size", FALLBACK_FONT_SIZE) if asset_info else FALLBACK_FONT_SIZE
        
        # Essayer de charger depuis asset découvert
        if key in self.discovered_assets:
            try:
                font = pygame.font.Font(str(self.discovered_assets[key]), size)
                self.cache[cache_key] = font
                return font
            except Exception as e:
                logger.error(f"Error loading font {key}: {e}")
        
        # Fallback vers police système
        font = pygame.font.SysFont(None, size)
        self.cache[cache_key] = font
        
        if DEV_MODE:
            logger.debug(f"Using system font fallback for: {key}")
        
        return font
    
    def get_sound(self, key: str) -> Optional[pygame.mixer.Sound]:
        """
        Récupère un effet sonore, avec fallback vers None si manquant.
        
        Args:
            key: Clé du son (sans préfixe sfx_)
            
        Returns:
            Sound pygame ou None
        """
        full_key = f"sfx_{key}"
        cache_key = f"sound_{full_key}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Essayer de charger depuis asset découvert
        if full_key in self.discovered_assets:
            try:
                sound = pygame.mixer.Sound(str(self.discovered_assets[full_key]))
                
                # Appliquer le volume par défaut si spécifié
                asset_info = self._get_asset_info("audio", key)
                if asset_info and "volume" in asset_info:
                    sound.set_volume(asset_info["volume"])
                else:
                    sound.set_volume(0.7)  # Volume par défaut
                
                self.cache[cache_key] = sound
                logger.info(f"Sound loaded successfully: {key}")
                return sound
                
            except Exception as e:
                logger.error(f"Error loading sound {key}: {e}")
        
        # Debug : afficher les sons disponibles
        if DEV_MODE:
            available_sounds = [k for k in self.discovered_assets.keys() if k.startswith("sfx_")]
            logger.debug(f"Sound not available: {key} (full_key: {full_key})")
            logger.debug(f"Available sounds: {available_sounds}")
        
        # Pas de fallback pour les sons - retourner None
        self.cache[cache_key] = None
        return None
    
    def get_music_path(self, key: str) -> Optional[str]:
        """
        Récupère le chemin d'un fichier musique.
        
        Args:
            key: Clé de la musique (sans préfixe music_)
            
        Returns:
            Chemin vers le fichier ou None
        """
        full_key = f"music_{key}"
        
        if full_key in self.discovered_assets:
            return str(self.discovered_assets[full_key])
        
        if DEV_MODE:
            logger.debug(f"Music not available: {key}")
        
        return None
    
    def clear_cache(self) -> None:
        """Vide le cache des assets (utile pour hot-reload)."""
        self.cache.clear()
        logger.info("Asset cache cleared")
    
    def reload_manifest(self) -> bool:
        """
        Recharge le manifest et vide le cache (hot-reload).
        
        Returns:
            True si le rechargement a réussi
        """
        self.clear_cache()
        self.missing_assets.clear()
        return self.load_manifest()
    
    def get_missing_assets(self) -> set:
        """Retourne l'ensemble des clés d'assets manquants."""
        return self.missing_assets.copy()
    
    def get_manifest_section(self, section: str) -> Optional[Dict]:
        """
        Récupère une section du manifest.
        
        Args:
            section: Nom de la section (images, spritesheets, sfx, music, etc.)
            
        Returns:
            Dictionnaire de la section ou None si non trouvée
        """
        return self.manifest.get(section)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne des statistiques sur les assets.
        
        Returns:
            Dictionnaire avec les stats
        """
        total_assets = len(self.discovered_assets) + len(self.missing_assets)
        
        return {
            "total_assets": total_assets,
            "found_assets": len(self.discovered_assets),
            "missing_assets": len(self.missing_assets),
            "cached_assets": len(self.cache),
            "cache_hit_ratio": 0.0 if total_assets == 0 else len(self.cache) / total_assets
        }


# Instance globale
asset_manager = AssetManager()
