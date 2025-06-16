from dataclasses import dataclass
import json


# ============================================================================
# 遊戲統計
# ============================================================================

@dataclass
class GameStats:
    """遊戲統計數據"""
    total_kills: int = 0
    total_damage_dealt: int = 0
    total_damage_taken: int = 0
    total_items_collected: int = 0
    total_gold_collected: int = 0
    total_floors_explored: int = 0
    total_deaths: int = 0
    highest_level: int = 1
    deepest_floor: int = 1
    longest_run_turns: int = 0
    current_floor_damage_taken: int = 0
    total_skills_used: int = 0
    total_critical_hits: int = 0
    
    def save(self):
        """保存統計"""
        try:
            with open("stats.json", "w") as f:
                json.dump(self.__dict__, f)
        except:
            pass
    
    def load(self):
        """載入統計"""
        try:
            with open("stats.json", "r") as f:
                data = json.load(f)
                for key, value in data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
        except:
            pass

