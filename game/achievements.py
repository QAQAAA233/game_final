from datetime import datetime
import json
from .enums import MessageType

# ============================================================================
# 成就系統
# ============================================================================

class Achievement:
    """成就類別"""
    def __init__(self, id: str, name: str, description: str, icon: str = ""):
        self.id = id
        self.name = name
        self.description = description
        self.icon = icon
        self.unlocked = False
        self.unlock_time = None

class AchievementSystem:
    """成就系統"""
    
    def __init__(self):
        self.achievements = self._init_achievements()
        self.load()
    
    def _init_achievements(self):
        """初始化成就列表"""
        return {
            "first_kill": Achievement("first_kill", "初次擊殺", "擊敗你的第一個敵人"),
            "level_5": Achievement("level_5", "新手冒險者", "達到等級5"),
            "level_10": Achievement("level_10", "經驗豐富", "達到等級10"),
            "floor_5": Achievement("floor_5", "深入地牢", "到達地下5層"),
            "floor_10": Achievement("floor_10", "深淵探索者", "到達地下10層"),
            "gold_1000": Achievement("gold_1000", "小富翁", "累積1000金幣"),
            "gold_5000": Achievement("gold_5000", "富豪", "累積5000金幣"),
            "no_damage_floor": Achievement("no_damage_floor", "完美通關", "在一層中不受任何傷害"),
            "full_equipment": Achievement("full_equipment", "全副武裝", "裝備所有部位"),
            "dragon_slayer": Achievement("dragon_slayer", "屠龍者", "擊敗古老巨龍"),
        }
    
    def unlock(self, achievement_id: str, message_log=None, particle_system=None, player_pos=None):
            """解鎖成就"""
            if achievement_id in self.achievements and not self.achievements[achievement_id].unlocked:
                self.achievements[achievement_id].unlocked = True
                self.achievements[achievement_id].unlock_time = datetime.now()
                self.save()
                
                if message_log:
                    # 使用文字標記代替emoji
                    achievement_name = self.achievements[achievement_id].name
                    message_log.add_message(
                        f"[獎] 成就解鎖：{achievement_name}！",
                        MessageType.LEVEL_UP
                    )
                
                if particle_system and player_pos:
                    particle_system.add_achievement_effect(player_pos)
                
                return True
            return False

    def check_achievements(self, player, dungeon_level, game_stats):
        """檢查成就條件"""
        unlocked = []
        
        # 等級成就
        if player.stats.level >= 5:
            if self.unlock("level_5"):
                unlocked.append("level_5")
        if player.stats.level >= 10:
            if self.unlock("level_10"):
                unlocked.append("level_10")
        
        # 樓層成就
        if dungeon_level >= 5:
            if self.unlock("floor_5"):
                unlocked.append("floor_5")
        if dungeon_level >= 10:
            if self.unlock("floor_10"):
                unlocked.append("floor_10")
        
        # 金幣成就
        if player.gold >= 1000:
            if self.unlock("gold_1000"):
                unlocked.append("gold_1000")
        if player.gold >= 5000:
            if self.unlock("gold_5000"):
                unlocked.append("gold_5000")
        
        # 裝備成就
        if all(player.equipment.values()):
            if self.unlock("full_equipment"):
                unlocked.append("full_equipment")
        
        return unlocked
    
    def save(self):
        """保存成就進度"""
        try:
            data = {}
            for id, ach in self.achievements.items():
                data[id] = {
                    "unlocked": ach.unlocked,
                    "unlock_time": ach.unlock_time.isoformat() if ach.unlock_time else None
                }
            with open("achievements.json", "w") as f:
                json.dump(data, f)
        except:
            pass
    
    def load(self):
        """載入成就進度"""
        try:
            with open("achievements.json", "r") as f:
                data = json.load(f)
                for id, info in data.items():
                    if id in self.achievements:
                        self.achievements[id].unlocked = info["unlocked"]
                        if info["unlock_time"]:
                            self.achievements[id].unlock_time = datetime.fromisoformat(info["unlock_time"])
        except:
            pass
