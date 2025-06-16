from dataclasses import dataclass
from typing import Tuple
import json

# ============================================================================
# 遊戲設定
# ============================================================================

@dataclass
class GameSettings:
    """遊戲設定"""
    master_volume: float = 0.7
    music_volume: float = 0.5
    sfx_volume: float = 0.8
    fullscreen: bool = False
    resolution: Tuple[int, int] = (1280, 720)
    auto_pickup: bool = True
    show_damage_numbers: bool = True
    show_minimap: bool = True
    show_enemy_health: bool = True
    show_tooltips: bool = True
    difficulty: str = "normal"
    particle_density: str = "high"
    vsync: bool = True
    antialiasing: bool = True
    
    def save(self):
        """保存設定"""
        try:
            with open("settings.json", "w") as f:
                json.dump(self.__dict__, f)
        except:
            pass
    
    def load(self):
        """載入設定"""
        try:
            with open("settings.json", "r") as f:
                data = json.load(f)
                for key, value in data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
        except:
            pass
