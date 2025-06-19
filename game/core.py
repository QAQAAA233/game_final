# -*- coding: utf-8 -*-
"""
深淵地牢探險記 v3.0 - 超精美視覺增強版（修復版）
修復了粒子系統顏色錯誤和畫面閃爍問題
"""
import freetype
import pygame
import pygame.mixer
import pygame.gfxdraw
import random
import math
import sys
import os
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Set
import json
from pathlib import Path
import pickle
from datetime import datetime
import time
import re # <--- 新增此行

# ============================================================================
# 高解析度設定 - 支援1920x1080及以上
# ============================================================================

# 視窗設定 - 預設Full HD
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
FPS = 60

# 支援的解析度
RESOLUTIONS = [
    (1280, 720),   # HD
    (1600, 900),   # HD+
    (1920, 1080),  # Full HD
    (2560, 1440),  # 2K
    (3840, 2160),  # 4K
]

# 遊戲網格設定
TILE_SIZE = 48  # 提升瓦片大小以適應高解析度
MAP_WIDTH = 60
MAP_HEIGHT = 45

# 小地圖設定
MINIMAP_SIZE = 300
MINIMAP_TILE_SIZE = 5

# 訊息日誌設定
MAX_LOG_MESSAGES = 25
MESSAGE_DISPLAY_TIME = 12000

# ============================================================================
# 現代化配色方案 - 高對比度設計
# ============================================================================

class Colors:
    # 基礎色彩
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    
    # 主題色彩 - 霓虹風格
    NEON_BLUE = (0, 255, 255)
    NEON_PINK = (255, 0, 128)
    NEON_GREEN = (0, 255, 128)
    NEON_YELLOW = (255, 255, 0)
    NEON_PURPLE = (255, 0, 255)
    NEON_ORANGE = (255, 128, 0)
    NEON_CYAN = (0, 255, 255)
    
    # 遊戲色彩
    HEALTH_RED = (255, 60, 90)
    MANA_BLUE = (60, 180, 255)
    EXP_YELLOW = (255, 215, 0)
    POISON_GREEN = (128, 255, 0)
    
    # 地形色彩 - 高對比度
    FLOOR_COLOR = (40, 40, 50)
    WALL_COLOR = (20, 20, 25)
    FLOOR_HIGHLIGHT = (60, 60, 75)
    WALL_HIGHLIGHT = (35, 35, 40)
    STAIRS_COLOR = (255, 200, 50)
    
    # UI色彩
    UI_BG = (15, 15, 20)
    UI_SECONDARY = (25, 25, 35)
    UI_BORDER = (100, 100, 120)
    UI_HIGHLIGHT = (0, 200, 255)
    UI_TEXT = (220, 220, 230)
    UI_TEXT_DARK = (150, 150, 160)
    
    # 特效色彩
    PARTICLE_FIRE = [(255, 100, 0), (255, 150, 0), (255, 200, 0), (255, 255, 100)]
    PARTICLE_ICE = [(100, 200, 255), (150, 220, 255), (200, 240, 255), (255, 255, 255)]
    PARTICLE_HEAL = [(0, 255, 100), (100, 255, 150), (200, 255, 200)]
    
    # 訊息色彩
    MSG_NORMAL = (200, 200, 210)
    MSG_COMBAT = (255, 100, 100)
    MSG_ITEM = (100, 255, 150)
    MSG_LEVEL = (255, 220, 100)
    MSG_STORY = (150, 200, 255)
    MSG_WARNING = (255, 150, 50)

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

# ============================================================================
# 遊戲文字內容
# ============================================================================

class GameTexts:
    """遊戲文字內容管理"""
    
    # 主選單文字
    MENU_TITLE = "深淵地牢探險記"
    MENU_SUBTITLE = "精美視覺增強版 v3.0"
    MENU_START = "開始新的冒險"
    MENU_CONTINUE = "繼續冒險"
    MENU_TUTORIAL = "新手冒險指引"
    MENU_SETTINGS = "遊戲設定"
    MENU_ACHIEVEMENTS = "成就"
    MENU_QUIT = "離開遊戲"
    MENU_HINT = "使用 方向鍵 選擇，按 空白鍵 確認"
    
    # 教學文字
    TUTORIAL_TITLE = "勇者冒險指南"
    TUTORIAL_WELCOME = "歡迎踏入深淵地牢！這是一個充滿危險與寶藏的古老迷宮。"
    
    # 遊戲內提示文字
    CONTROLS_MOVE = "移動: 方向鍵/WASD/滑鼠"
    CONTROLS_INVENTORY = "背包: B 鍵"
    CONTROLS_EXAMINE = "查看: X 鍵"
    CONTROLS_REST = "休息: R 鍵"
    CONTROLS_PAUSE = "選單: ESC 鍵"
    CONTROLS_PICKUP = "拾取: F 鍵"
    CONTROLS_USE = "使用: U 鍵"
    CONTROLS_SKILL = "技能: 1-4 鍵"
    CONTROLS_SAVE = "快速保存: F5"
    CONTROLS_LOAD = "快速載入: F9"
    
    # 狀態文字
    STATUS_HP = "生命值"
    STATUS_MP = "魔力值"
    STATUS_EXP = "經驗值"
    STATUS_LEVEL = "等級"
    STATUS_ATTACK = "攻擊力"
    STATUS_DEFENSE = "防禦力"
    STATUS_GOLD = "金幣"
    STATUS_FLOOR = "地牢第 {} 層"
    STATUS_TURN = "回合: {}"
    
    # 武器名稱
    WEAPON_DAGGER = "銳利匕首"
    WEAPON_SWORD = "精鋼長劍"
    WEAPON_AXE = "戰斧"
    WEAPON_MACE = "戰錘"
    WEAPON_BOW = "長弓"
    WEAPON_LEGENDARY_SWORD = "傳說之劍"
    
    # 護甲名稱  
    ARMOR_LEATHER = "皮甲"
    ARMOR_CHAIN = "鎖甲"
    ARMOR_PLATE = "板甲"
    ARMOR_SHIELD = "盾牌"
    ARMOR_HELMET = "頭盔"
    ARMOR_LEGENDARY = "龍鱗甲"
    
    # 藥水名稱（未識別）
    POTION_RED = "紅色藥水"
    POTION_BLUE = "藍色藥水"
    POTION_GREEN = "綠色藥水"
    POTION_YELLOW = "黃色藥水"
    
    # 藥水名稱（已識別）
    POTION_HEALING = "治療藥水"
    POTION_MANA = "魔力藥水"
    POTION_POISON = "毒藥"
    POTION_STRENGTH = "力量藥水"
    
    # 卷軸名稱（未識別）
    SCROLL_ANCIENT = "古老卷軸"
    SCROLL_MYSTIC = "神秘卷軸"
    # 刪除了 SCROLL_RUNIC
    
    # 卷軸名稱（已識別）
    SCROLL_FIREBALL = "火球術卷軸"
    SCROLL_HEAL = "治療術卷軸"
    # 刪除了 SCROLL_TELEPORT
    
    # 飾品名稱
    RING_POWER = "力量戒指"
    RING_AGILITY = "敏捷戒指"
    RING_MAGIC = "魔法戒指"
    RING_FIRE = "火焰戒指"
    RING_ICE = "寒冰戒指"
    RING_WISDOM = "智慧戒指"
    RING_VITALITY = "活力戒指"
    AMULET_PROTECTION = "護身符"
    AMULET_LIFE = "生命護符"
    AMULET_MIGHT = "力量護符"
    AMULET_SPEED = "速度護符"
    AMULET_SHADOW = "暗影護符"
    GEM_MAGIC = "魔法寶石"
    GOLD_COIN = "金幣"
    
    # 敵人名稱
    ENEMY_SKELETON = "骷髏戰士"
    ENEMY_ORC = "獸人勇士"
    ENEMY_GOBLIN = "哥布林盜賊"
    ENEMY_DRAGON = "古老巨龍"
    ENEMY_DEMON = "深淵惡魔"
    ENEMY_LICH = "巫妖王"
    
    # 技能名稱
    SKILL_SLASH = "劍刃斬"
    SKILL_FIREBALL = "火球術"
    SKILL_HEAL = "治癒術"
    SKILL_SHIELD = "護盾術"
    
# 戰鬥訊息（修改版 - 使用文字標記）
    COMBAT_PLAYER_ATTACK = "[劍] 你用{weapon}對{enemy}造成了{damage}點傷害！"
    COMBAT_PLAYER_ATTACK_BARE = "[拳] 你對{enemy}造成了{damage}點傷害！"
    COMBAT_CRITICAL_HIT = "[爆] 暴擊！造成{damage}點傷害！"
    COMBAT_ENEMY_ATTACK = "[刃] {enemy}對你造成了{damage}點傷害！"
    COMBAT_ENEMY_DEFEATED = "[勝] 你擊倒了{enemy}！獲得{exp}經驗值和{gold}金幣！"
    COMBAT_LEVEL_UP = "[升] 恭喜！你提升到了第{level}級！所有能力都獲得了提升！"
    COMBAT_MISS = "[失] {attacker}的攻擊沒有命中{target}！"
    COMBAT_SKILL_USED = "[技] 你使用了{skill}！"
    
    # 物品訊息（修改版 - 使用文字標記）
    ITEM_PICKUP = "[得] 你撿起了{item}"
    ITEM_AUTO_PICKUP = "[自] 自動撿起了{item}"
    ITEM_USE_POTION = "[藥] 你喝下了{potion}，{effect}"
    ITEM_USE_SCROLL = "[卷] 你閱讀了{scroll}，{effect}"
    ITEM_EQUIP = "[裝] 你裝備了{item}"
    ITEM_UNEQUIP = "[卸] 你卸下了{item}"
    ITEM_INVENTORY_FULL = "[滿] 背包已滿！你無法撿起更多物品"
    ITEM_IDENTIFIED = "[鑑] 你識別出這是{item}！"
    
    # 藥水效果
    EFFECT_HEAL = "恢復了{amount}點生命值"
    EFFECT_MANA = "恢復了{amount}點魔力值"
    EFFECT_POISON = "你感到身體不適..."
    EFFECT_STRENGTH = "你感到力量大增！"
    
    # 探索訊息
    EXPLORE_ENTER_FLOOR = "你踏入了地牢的第{floor}層，這裡的空氣更加陰冷..."
    EXPLORE_FIND_STAIRS = "你發現了通往更深層的階梯"
    EXPLORE_ROOM_EMPTY = "這個房間空蕩蕩的"
    EXPLORE_ROOM_TREASURE = "你發現了一些有價值的物品！"
    EXPLORE_ROOM_DANGER = "你感受到強烈的危險氣息..."
    EXPLORE_TURN_COUNT = "你已經在地牢中度過了{turns}個回合"
    
    # 休息訊息
    REST_SUCCESS = "你休息了一會兒，恢復了一些體力"
    REST_INTERRUPTED = "有敵人靠近，你無法安心休息！"
    REST_FULL_HP = "你已經完全恢復，不需要休息"
    
    # 遊戲結束訊息
    GAME_OVER_TITLE = "冒險終結"
    GAME_OVER_DEFEAT = "你在地牢的深處倒下了...但你的勇敢精神將被永遠銘記"
    GAME_OVER_VICTORY = "恭喜！你成功征服了深淵地牢，成為了傳說中的英雄！"
    GAME_OVER_RESTART = "按 R 重新開始冒險"
    GAME_OVER_MENU = "按 ESC 回到主選單"
    
    # 暫停訊息
    PAUSE_TITLE = "遊戲暫停"
    PAUSE_HINT = "按 ESC 繼續冒險"
    PAUSE_RESUME = "繼續遊戲"
    PAUSE_SAVE = "保存遊戲"
    PAUSE_MENU = "回到主選單"
    
    # 背包訊息
    INVENTORY_TITLE = "冒險者背包"
    INVENTORY_EMPTY = "背包是空的"
    INVENTORY_HELP = "方向鍵選擇，空白鍵使用，D丟棄，B關閉"
    INVENTORY_WEIGHT = "負重: {current}/{max}"
    INVENTORY_EQUIPPED = "已裝備"
    
    # 裝備訊息
    EQUIPMENT_WEAPON = "武器: {weapon}"
    EQUIPMENT_ARMOR = "護甲: {armor}"
    EQUIPMENT_SHIELD = "盾牌: {shield}"
    EQUIPMENT_HELMET = "頭盔: {helmet}"
    EQUIPMENT_BOOTS = "鞋子: {boots}"  # 新增
    EQUIPMENT_RING = "戒指: {ring}"
    EQUIPMENT_AMULET = "護身符: {amulet}"
    
    # 識別系統訊息
    IDENTIFY_SUCCESS = "你仔細檢視了{item}，發現它是{true_name}！"
    IDENTIFY_FAIL = "你無法確定{item}的真正性質"
    IDENTIFY_ALREADY = "你已經知道{item}是什麼了"
    
    # 設定選單
    SETTINGS_TITLE = "遊戲設定"
    SETTINGS_VOLUME = "音量設定"
    SETTINGS_GRAPHICS = "圖像設定"
    SETTINGS_GAMEPLAY = "遊戲設定"
    SETTINGS_APPLY = "套用設定"
    SETTINGS_CANCEL = "取消"
    
    # 工具提示
    TOOLTIP_COMPARE = "與當前裝備比較："
    TOOLTIP_BETTER = "↑ 較好"
    TOOLTIP_WORSE = "↓ 較差"
    TOOLTIP_SAME = "= 相同"

# ============================================================================
# 遊戲狀態枚舉
# ============================================================================

class GameState(Enum):
    MENU = "menu"
    TUTORIAL = "tutorial"
    PLAYING = "playing"
    INVENTORY = "inventory"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    VICTORY = "victory"
    EXAMINING = "examining"
    SETTINGS = "settings"
    ACHIEVEMENTS = "achievements"
    SKILL_SELECT = "skill_select"

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    UP_LEFT = (-1, -1)
    UP_RIGHT = (1, -1)
    DOWN_LEFT = (-1, 1)
    DOWN_RIGHT = (1, 1)

class MessageType(Enum):
    NORMAL = "normal"
    COMBAT = "combat"
    ITEM = "item"
    LEVEL_UP = "level_up"
    STORY = "story"
    WARNING = "warning"

class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    SHIELD = "shield"
    HELMET = "helmet"
    BOOTS = "boots"  # 新增：鞋子類型
    POTION = "potion"
    SCROLL = "scroll"
    RING = "ring"
    AMULET = "amulet"
    MISC = "misc"
    GOLD = "gold"

class SkillType(Enum):
    ACTIVE = "active"
    PASSIVE = "passive"

# ============================================================================
# 資料類別定義
# ============================================================================

@dataclass
class Position:
    x: int
    y: int    
    def distance_to(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    

@dataclass
class Stats:
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    attack: int
    defense: int
    level: int = 1
    exp: int = 0
    exp_to_next: int = 100
    crit_chance: float = 0.1
    crit_damage: float = 2.0
    move_speed: float = 2.0  # 修改為5格/秒（從200像素/秒改為合理的格子速度）

@dataclass
class Item:
    name: str
    item_type: ItemType
    icon: str = ""
    identified: bool = False
    true_name: str = ""
    description: str = ""
    value: int = 0
    # 武器/護甲屬性
    attack_bonus: int = 0
    defense_bonus: int = 0
    # 藥水/卷軸效果
    heal_amount: int = 0
    mana_amount: int = 0
    special_effect: str = ""
    # 其他屬性
    weight: int = 1
    durability: int = 100
    cursed: bool = False
    rarity: str = "common"
    # 新增：直接存儲移速加成
    _move_speed_bonus: int = 0  # 直接存儲移速值
    
    @property
    def move_speed_bonus(self) -> int:
        """獲取移速加成"""
        # 優先使用直接存儲的值
        if self._move_speed_bonus != 0:
            return self._move_speed_bonus
        # 兼容舊的special_effect方式
        if self.item_type == ItemType.BOOTS and self.special_effect.startswith("move_speed:"):
            try:
                return int(float(self.special_effect.split(":")[1]))
            except:
                return 0
        return 0

@dataclass
class Skill:
    """技能類別（支援等級系統）"""
    id: str  # 技能唯一標識
    name: str
    description: str
    icon: str
    skill_type: SkillType
    max_level: int = 5
    current_level: int = 0  # 0表示未學習
    
    # 每級數據（索引0-4對應1-5級）
    mp_cost_per_level: list = None
    cooldown_per_level: list = None
    damage_percent_per_level: list = None  # 改為傷害百分比
    heal_percent_per_level: list = None    # 改為治療百分比
    range_per_level: list = None
    effect_per_level: list = None
    
    # 當前狀態
    current_cooldown: float = 0
    slot_index: int = -1  # -1表示未裝備，0-3表示快捷欄位置
    
    def __post_init__(self):
        """初始化每級數據"""
        if self.mp_cost_per_level is None:
            self.mp_cost_per_level = [10, 12, 15, 18, 20]
        if self.cooldown_per_level is None:
            self.cooldown_per_level = [5, 4.5, 4, 3.5, 3]
        if self.damage_percent_per_level is None:
            self.damage_percent_per_level = [100, 150, 200, 250, 300]  # 百分比
        if self.heal_percent_per_level is None:
            self.heal_percent_per_level = [30, 40, 50, 60, 70]  # 百分比
        if self.range_per_level is None:
            self.range_per_level = [1, 1, 2, 2, 3]
        if self.effect_per_level is None:
            self.effect_per_level = ["", "", "", "", ""]
    
    @property
    def is_learned(self) -> bool:
        """是否已學習"""
        return self.current_level > 0
    
    @property
    def is_max_level(self) -> bool:
        """是否達到最高等級"""
        return self.current_level >= self.max_level
    
    @property
    def mp_cost(self) -> int:
        """當前等級的MP消耗"""
        if self.current_level > 0:
            return self.mp_cost_per_level[self.current_level - 1]
        return self.mp_cost_per_level[0]
    
    @property
    def cooldown(self) -> float:
        """當前等級的冷卻時間"""
        if self.current_level > 0:
            return self.cooldown_per_level[self.current_level - 1]
        return self.cooldown_per_level[0]
    
    @property
    def damage_percent(self) -> int:
        """當前等級的傷害百分比"""
        if self.current_level > 0:
            return self.damage_percent_per_level[self.current_level - 1]
        return self.damage_percent_per_level[0]
    
    @property
    def heal_percent(self) -> int:
        """當前等級的治療百分比"""
        if self.current_level > 0:
            return self.heal_percent_per_level[self.current_level - 1]
        return self.heal_percent_per_level[0]
    
    @property
    def range(self) -> int:
        """當前等級的範圍"""
        if self.current_level > 0:
            return self.range_per_level[self.current_level - 1]
        return self.range_per_level[0]
    
    @property
    def effect(self) -> str:
        """當前等級的特殊效果"""
        if self.current_level > 0:
            return self.effect_per_level[self.current_level - 1]
        return self.effect_per_level[0]
    
    def get_upgrade_cost(self) -> tuple:
        """獲取升級所需資源 (卷軸數量, 金幣數量)"""
        if self.is_max_level:
            return (0, 0)
        
        # 學習技能只需要1個卷軸
        if self.current_level == 0:
            return (1, 0)
        
        # 升級需要卷軸和金幣
        scrolls_needed = self.current_level  # 2級需1卷，3級需2卷...
        gold_needed = self.current_level * 200  # 2級需200金，3級需400金...
        
        return (scrolls_needed, gold_needed)
    
    def get_level_description(self, level: int) -> str:
        """獲取指定等級的描述"""
        if level < 1 or level > self.max_level:
            return ""
        
        idx = level - 1
        parts = []
        
        if self.damage_percent_per_level[idx] > 0:
            parts.append(f"傷害: {self.damage_percent_per_level[idx]}%攻擊力")
        if self.heal_percent_per_level[idx] > 0:
            parts.append(f"治療: {self.heal_percent_per_level[idx]}%最大生命")
        
        parts.append(f"MP消耗: {self.mp_cost_per_level[idx]}")
        parts.append(f"冷卻: {self.cooldown_per_level[idx]}秒")
        
        if self.range_per_level[idx] > 0:
            parts.append(f"範圍: {self.range_per_level[idx]}")
        
        if self.effect_per_level[idx]:
            parts.append(f"特效: {self.effect_per_level[idx]}")
        
        return " | ".join(parts)
      
@dataclass
class GameMessage:
    text: str
    msg_type: MessageType
    timestamp: int
    fade_alpha: int = 255

# ============================================================================
# 物品資料庫
# ============================================================================

class ItemDatabase:
    """物品資料庫，管理所有物品的生成和識別"""
    
    def __init__(self):
        self.weapon_data = {
            'dagger': {'name': GameTexts.WEAPON_DAGGER, 'attack': 3, 'value': 50, 'rarity': 'common'},
            'sword': {'name': GameTexts.WEAPON_SWORD, 'attack': 6, 'value': 150, 'rarity': 'uncommon'},
            'axe': {'name': GameTexts.WEAPON_AXE, 'attack': 8, 'value': 200, 'rarity': 'uncommon'},
            'mace': {'name': GameTexts.WEAPON_MACE, 'attack': 7, 'value': 180, 'rarity': 'uncommon'},
            'bow': {'name': GameTexts.WEAPON_BOW, 'attack': 5, 'value': 120, 'rarity': 'common'},
            'legendary_sword': {'name': GameTexts.WEAPON_LEGENDARY_SWORD, 'attack': 15, 'value': 1000, 'rarity': 'legendary'}
        }
        
        self.armor_data = {
            'leather_armor': {'name': GameTexts.ARMOR_LEATHER, 'defense': 2, 'value': 80, 'rarity': 'common'},
            'chain_mail': {'name': GameTexts.ARMOR_CHAIN, 'defense': 4, 'value': 200, 'rarity': 'uncommon'},
            'plate_armor': {'name': GameTexts.ARMOR_PLATE, 'defense': 6, 'value': 400, 'rarity': 'rare'},
            'shield': {'name': GameTexts.ARMOR_SHIELD, 'defense': 3, 'value': 100, 'rarity': 'common'},
            'helmet': {'name': GameTexts.ARMOR_HELMET, 'defense': 2, 'value': 60, 'rarity': 'common'},
            'legendary_armor': {'name': GameTexts.ARMOR_LEGENDARY, 'defense': 10, 'value': 1500, 'rarity': 'legendary'}
        }
        
        # 固定的藥水效果映射（不再隨機化）
        self.potion_data = {
            'red_potion': {
                'unid_name': GameTexts.POTION_RED, 
                'true_name': GameTexts.POTION_HEALING, 
                'heal': 50,
                'effect': '',
                'rarity': 'common'
            },
            'blue_potion': {
                'unid_name': GameTexts.POTION_BLUE, 
                'true_name': GameTexts.POTION_MANA, 
                'mana': 40,
                'effect': '',
                'rarity': 'common'
            },
            'green_potion': {
                'unid_name': GameTexts.POTION_GREEN, 
                'true_name': '疾風藥水',
                'heal': 0,
                'mana': 0,
                'effect': 'move_speed',
                'rarity': 'common'
            },
            'yellow_potion': {
                'unid_name': GameTexts.POTION_YELLOW, 
                'true_name': GameTexts.POTION_STRENGTH,
                'heal': 0,
                'mana': 0,
                'effect': 'strength',
                'attack': 5,
                'rarity': 'uncommon'
            }
        }
        
        # 初始化已鑑定的藥水類型集合（需要從Player獲取）
        self.identified_potion_types = set()
        
        # 卷軸數據 - 統一未鑑定圖標，包含所有技能
        self.scroll_data = {
            'scroll_slash': {
                'unid_name': '神秘卷軸', 
                'true_name': '劍刃斬卷軸', 
                'effect': 'slash',
                'icon': 'scroll_unidentified',  # 未鑑定時的統一圖標
                'identified_icon': 'scroll_slash',  # 鑑定後的圖標
                'rarity': 'common'
            },
            'scroll_fireball': {
                'unid_name': '神秘卷軸', 
                'true_name': '火球術卷軸', 
                'effect': 'fireball',
                'icon': 'scroll_unidentified',
                'identified_icon': 'scroll_fireball',
                'rarity': 'uncommon'
            },
            'scroll_heal': {
                'unid_name': '神秘卷軸', 
                'true_name': '治癒術卷軸', 
                'effect': 'heal',
                'icon': 'scroll_unidentified',
                'identified_icon': 'scroll_heal',
                'rarity': 'uncommon'
            },
            'scroll_shield': {
                'unid_name': '神秘卷軸', 
                'true_name': '護盾術卷軸', 
                'effect': 'shield',
                'icon': 'scroll_unidentified',
                'identified_icon': 'scroll_shield',
                'rarity': 'uncommon'
            },
            'scroll_lightning': {
                'unid_name': '神秘卷軸', 
                'true_name': '閃電鏈卷軸', 
                'effect': 'lightning',
                'icon': 'scroll_unidentified',
                'identified_icon': 'scroll_lightning',
                'rarity': 'rare'
            },
            'scroll_ice': {
                'unid_name': '神秘卷軸', 
                'true_name': '冰錐術卷軸', 
                'effect': 'ice_spike',
                'icon': 'scroll_unidentified',
                'identified_icon': 'scroll_ice',
                'rarity': 'rare'
            },
            'scroll_summon': {
                'unid_name': '神秘卷軸', 
                'true_name': '召喚術卷軸', 
                'effect': 'summon',
                'icon': 'scroll_unidentified',
                'identified_icon': 'scroll_summon',
                'rarity': 'rare'
            }
        }
        
        self.boots_data = {
            'leather_boots': {'name': '皮靴', 'defense': 1, 'move_speed': 50, 'value': 50, 'rarity': 'common'},
            'speed_boots': {'name': '疾風之靴', 'defense': 2, 'move_speed': 200, 'value': 200, 'rarity': 'uncommon'},
            'mage_boots': {'name': '法師長靴', 'defense': 1, 'move_speed': 100, 'mp': 10, 'value': 180, 'rarity': 'uncommon'},
            'warrior_boots': {'name': '戰士重靴', 'defense': 4, 'move_speed': -50, 'value': 150, 'rarity': 'uncommon'},
            'heavy_boots': {'name': '重鐵靴', 'defense': 5, 'move_speed': -100, 'value': 200, 'rarity': 'uncommon'},
            'swift_boots': {'name': '迅捷之靴', 'defense': 1, 'move_speed': 150, 'value': 220, 'rarity': 'uncommon'},
            'legendary_boots': {'name': '神行靴', 'defense': 3, 'move_speed': 300, 'value': 1000, 'rarity': 'legendary'}
        }

        self.ring_data = {
            'ring_power': {'name': GameTexts.RING_POWER, 'attack': 2, 'value': 150, 'rarity': 'uncommon'},
            'ring_agility': {'name': GameTexts.RING_AGILITY, 'move_speed': 100, 'value': 150, 'rarity': 'uncommon'},
            'ring_magic': {'name': GameTexts.RING_MAGIC, 'mana': 20, 'value': 200, 'rarity': 'rare'},
            'ring_fire': {'name': GameTexts.RING_FIRE, 'attack': 3, 'special_effect': 'fire_resist', 'value': 250, 'rarity': 'rare'},
            'ring_ice': {'name': GameTexts.RING_ICE, 'defense': 1, 'special_effect': 'ice_resist', 'value': 250, 'rarity': 'rare'},
            'ring_wisdom': {'name': GameTexts.RING_WISDOM, 'mana': 30, 'value': 220, 'rarity': 'uncommon'},
            'ring_vitality': {'name': GameTexts.RING_VITALITY, 'hp': 30, 'defense': 1, 'value': 220, 'rarity': 'uncommon'},
            'ring_fortune': {'name': '幸運戒指', 'value': 300, 'rarity': 'rare'}
        }

        self.amulet_data = {
            'amulet_protection': {'name': GameTexts.AMULET_PROTECTION, 'defense': 2, 'value': 120, 'rarity': 'uncommon'},
            'amulet_life': {'name': GameTexts.AMULET_LIFE, 'hp': 20, 'value': 200, 'rarity': 'rare'},
            'amulet_might': {'name': GameTexts.AMULET_MIGHT, 'attack': 3, 'value': 200, 'rarity': 'rare'},
            'amulet_speed': {'name': GameTexts.AMULET_SPEED, 'move_speed': 150, 'value': 180, 'rarity': 'uncommon'},
            'amulet_shadow': {'name': GameTexts.AMULET_SHADOW, 'special_effect': 'stealth', 'value': 250, 'rarity': 'rare'}
        }
    
    def create_weapon(self, weapon_key: str) -> Item:
        """創建武器"""
        data = self.weapon_data[weapon_key]
        return Item(
            name=data['name'],
            item_type=ItemType.WEAPON,
            icon=weapon_key,
            identified=True,
            true_name=data['name'],
            attack_bonus=data['attack'],
            value=data['value'],
            rarity=data['rarity'],
            description=f"一把優質的{data['name']}，攻擊力+{data['attack']}"
        )
    
    def create_armor(self, armor_key: str) -> Item:
        """創建護甲"""
        data = self.armor_data[armor_key]
        item_type = ItemType.ARMOR
        if armor_key == 'shield':
            item_type = ItemType.SHIELD
        elif armor_key == 'helmet':
            item_type = ItemType.HELMET
            
        return Item(
            name=data['name'],
            item_type=item_type,
            icon=armor_key,
            identified=True,
            true_name=data['name'],
            defense_bonus=data['defense'],
            value=data['value'],
            rarity=data['rarity'],
            description=f"堅固的{data['name']}，防禦力+{data['defense']}"
        )
    
    def create_potion(self, potion_key: str) -> Item:
        if potion_key not in self.potion_data:
            print(f"警告：未知的藥水類型 {potion_key}")
            potion_key = 'red_potion'
        
        data = self.potion_data[potion_key]
        
        # 創建一個臨時的Player實例來檢查identified_items（如果可能的話）
        # 或者從全局遊戲狀態獲取
        is_identified = False
        
        item = Item(
            name=data['unid_name'],  # 默認使用未鑑定名稱
            item_type=ItemType.POTION,
            icon=potion_key,
            identified=False,  # 默認未鑑定
            true_name=data['true_name'],
            heal_amount=data.get('heal', 0),
            mana_amount=data.get('mana', 0),
            special_effect=data.get('effect', ''),
            attack_bonus=data.get('attack', 0),  # 添加攻擊加成
            value=30,
            rarity=data['rarity'],
            description="一瓶神秘的藥水，不知道會有什麼效果..."
        )
        
        return item
      
    def _get_potion_description(self, data: dict, is_identified: bool) -> str:
        if not is_identified:
            return "一瓶神秘的藥水，不知道會有什麼效果..."
        
        # 根據藥水效果生成描述
        if data.get('heal', 0) > 0:
            return f"恢復{data['heal']}點生命值的治療藥水"
        elif data.get('heal', 0) < 0:
            return f"造成{-data['heal']}點傷害的毒藥"
        elif data.get('mana', 0) > 0:
            return f"恢復{data['mana']}點魔力值的魔力藥水"
        elif data.get('effect') == 'move_speed':
            return "暫時提升20%移動速度的疾風藥水"
        elif data.get('effect') == 'strength':
            return "暫時提升5點攻擊力的力量藥水"
        else:
            return "未知效果的神秘藥水"
           
    def create_scroll(self, scroll_key: str = None) -> Item:
        if scroll_key is None:
            # 隨機選擇一個卷軸類型
            scroll_weights = {
                'scroll_slash': 15,      
                'scroll_fireball': 10,   
                'scroll_heal': 10,       
                'scroll_shield': 8,      
                'scroll_lightning': 5,   
                'scroll_ice': 5,         
                'scroll_summon': 3       
            }
            scroll_keys = list(scroll_weights.keys())
            weights = list(scroll_weights.values())
            scroll_key = random.choices(scroll_keys, weights=weights, k=1)[0]
        
        # 處理舊的卷軸類型映射
        legacy_scroll_map = {
            'scroll_1': 'scroll_slash',
            'scroll_2': 'scroll_fireball', 
            'scroll_3': 'scroll_heal'
        }
        
        # 如果是舊的卷軸類型，轉換為新的
        if scroll_key in legacy_scroll_map:
            scroll_key = legacy_scroll_map[scroll_key]
        
        if scroll_key not in self.scroll_data:
            print(f"警告：未知的卷軸類型 {scroll_key}，使用預設值")
            scroll_key = 'scroll_slash'
        
        data = self.scroll_data[scroll_key]
        item = Item(
            name=data['unid_name'],
            item_type=ItemType.SCROLL,
            icon=data['icon'],  
            identified=False,
            true_name=data['true_name'],
            special_effect=data['effect'],
            value=50,
            rarity=data['rarity'],
            description="一張古老的魔法卷軸，上面寫著神秘的文字..."
        )
        
        # 保存卷軸類型和識別後的圖標
        item._scroll_type = scroll_key
        item._identified_icon = data['identified_icon']
        
        return item
          
    def create_gold(self, amount: int = None) -> Item:
        """創建金幣"""
        if amount is None:
            amount = random.randint(20, 100)
        return Item(
            name=f"{amount} {GameTexts.GOLD_COIN}",
            item_type=ItemType.GOLD,
            icon='coin',
            identified=True,
            value=amount,
            rarity='common',
            description=f"閃閃發光的金幣，價值{amount}"
        )

    def create_boots(self, boots_key: str) -> Item:
        """創建鞋子"""
        data = self.boots_data[boots_key]
        move_speed = data.get('move_speed', 0)
        
        item = Item(
            name=data['name'],
            item_type=ItemType.BOOTS,
            icon=boots_key,
            identified=True,
            true_name=data['name'],
            defense_bonus=data.get('defense', 0),
            value=data['value'],
            rarity=data['rarity'],
            description=f"一雙{data['name']}，防禦力+{data.get('defense', 0)}，移動速度+{move_speed}",
            special_effect=f"move_speed:{move_speed}",
            _move_speed_bonus=move_speed
        )
        
        if boots_key == 'mage_boots' and 'mp' in data:
            item.description += f"，魔力+{data['mp']}"

        return item

    def create_ring(self, ring_key: str) -> Item:
        """創建戒指"""
        data = self.ring_data[ring_key]
        move_speed = data.get('move_speed', 0)
        item = Item(
            name=data['name'],
            item_type=ItemType.RING,
            icon=ring_key,
            identified=True,
            true_name=data['name'],
            attack_bonus=data.get('attack', 0),
            defense_bonus=data.get('defense', 0),
            value=data['value'],
            rarity=data['rarity'],
            description=f"一枚{data['name']}",
            special_effect=data.get('special_effect', ''),
            _move_speed_bonus=move_speed
        )
        return item

    def create_amulet(self, amulet_key: str) -> Item:
        """創建護身符"""
        data = self.amulet_data[amulet_key]
        item = Item(
            name=data['name'],
            item_type=ItemType.AMULET,
            icon=amulet_key,
            identified=True,
            true_name=data['name'],
            attack_bonus=data.get('attack', 0),
            defense_bonus=data.get('defense', 0),
            value=data['value'],
            rarity=data['rarity'],
            description=f"一個{data['name']}",
            special_effect=data.get('special_effect', '')
        )
        return item
       
class SkillDatabase:
    """技能資料庫"""
    
    @staticmethod
    def get_all_skills():
        """獲取所有技能定義"""
        skills = {
            'slash': Skill(
                id='slash',
                name=GameTexts.SKILL_SLASH,
                description="對前方敵人造成物理傷害，高級可以擴大範圍",
                icon='skill_slash',
                skill_type=SkillType.ACTIVE,
                mp_cost_per_level=[10, 12, 15, 18, 20],
                cooldown_per_level=[3.0, 2.8, 2.5, 2.2, 2.0],
                damage_percent_per_level=[150, 200, 250, 300, 350],  # 攻擊力的百分比
                heal_percent_per_level=[0, 0, 0, 0, 0],
                range_per_level=[1, 1, 2, 2, 3],
                effect_per_level=["", "", "擊退", "擊退+流血", "擊退+流血+眩暈"]
            ),
            'fireball': Skill(
                id='fireball',
                name=GameTexts.SKILL_FIREBALL,
                description="發射火球造成範圍魔法傷害，高級增加爆炸範圍",
                icon='skill_fireball',
                skill_type=SkillType.ACTIVE,
                mp_cost_per_level=[20, 25, 30, 35, 40],
                cooldown_per_level=[5.0, 4.5, 4.0, 3.5, 3.0],
                damage_percent_per_level=[350, 500, 750, 1100, 1500],  # 攻擊力的百分比
                heal_percent_per_level=[0, 0, 0, 0, 0],
                range_per_level=[5, 6, 7, 8, 10],
                effect_per_level=["爆炸範圍2", "爆炸範圍2", "爆炸範圍3", "爆炸範圍3+燃燒", "爆炸範圍4+燃燒"]
            ),
            'heal': Skill(
                id='heal',
                name=GameTexts.SKILL_HEAL,
                description="恢復自身生命值，高級可以清除負面效果",
                icon='skill_heal',
                skill_type=SkillType.ACTIVE,
                mp_cost_per_level=[15, 18, 22, 26, 30],
                cooldown_per_level=[8.0, 7.0, 6.0, 5.0, 4.0],
                damage_percent_per_level=[0, 0, 0, 0, 0],
                heal_percent_per_level=[30, 40, 50, 60, 70],  # 最大生命值的百分比
                range_per_level=[0, 0, 0, 0, 0],
                effect_per_level=["", "", "清除1個負面", "清除2個負面", "清除所有負面+回復護甲"]
            ),
            'shield': Skill(
                id='shield',
                name=GameTexts.SKILL_SHIELD,
                description="召喚護盾減少受到的傷害，高級增加持續時間",
                icon='skill_shield',
                skill_type=SkillType.ACTIVE,
                mp_cost_per_level=[25, 30, 35, 40, 45],
                cooldown_per_level=[10.0, 9.0, 8.0, 7.0, 6.0],
                damage_percent_per_level=[0, 0, 0, 0, 0],
                heal_percent_per_level=[0, 0, 0, 0, 0],
                range_per_level=[0, 0, 0, 0, 0],
                effect_per_level=["減傷50% 5秒", "減傷55% 6秒", "減傷60% 7秒", "減傷65% 8秒+反彈", "減傷70% 10秒+反彈"]
            ),
            'lightning': Skill(
                id='lightning',
                name="閃電鏈",
                description="釋放閃電鏈攻擊多個敵人",
                icon='skill_lightning',
                skill_type=SkillType.ACTIVE,
                mp_cost_per_level=[30, 35, 40, 45, 50],
                cooldown_per_level=[6.0, 5.5, 5.0, 4.5, 4.0],
                damage_percent_per_level=[120, 150, 180, 210, 250],  # 攻擊力的百分比
                heal_percent_per_level=[0, 0, 0, 0, 0],
                range_per_level=[6, 7, 8, 9, 10],
                effect_per_level=["彈跳2次", "彈跳3次", "彈跳4次", "彈跳5次+麻痺", "彈跳6次+麻痺"]
            ),
            'ice_spike': Skill(
                id='ice_spike',
                name="冰錐術",
                description="召喚冰錐從地面刺出，造成傷害並減速",
                icon='skill_ice',
                skill_type=SkillType.ACTIVE,
                mp_cost_per_level=[15, 18, 22, 26, 30],
                cooldown_per_level=[4.0, 3.8, 3.5, 3.2, 3.0],
                damage_percent_per_level=[180, 220, 260, 300, 350],  # 攻擊力的百分比
                heal_percent_per_level=[0, 0, 0, 0, 0],
                range_per_level=[3, 3, 4, 4, 5],
                effect_per_level=["減速30%", "減速40%", "減速50%+冰凍機率20%", "減速60%+冰凍機率40%", "減速70%+冰凍機率60%"]
            ),
            'summon': Skill(
                id='summon',
                name="召喚術",
                description="召喚骷髏戰士協助戰鬥",
                icon='skill_summon',
                skill_type=SkillType.ACTIVE,
                mp_cost_per_level=[40, 45, 50, 55, 60],
                cooldown_per_level=[20.0, 18.0, 16.0, 14.0, 12.0],
                damage_percent_per_level=[0, 0, 0, 0, 0],
                heal_percent_per_level=[0, 0, 0, 0, 0],
                range_per_level=[0, 0, 0, 0, 0],
                effect_per_level=["召喚1個骷髏", "召喚2個骷髏", "召喚2個強化骷髏", "召喚3個強化骷髏", "召喚3個精英骷髏"]
            )
        }
        
        return skills
    
    @staticmethod
    def get_skill_by_scroll(scroll_effect: str) -> str:
        """根據卷軸效果獲取對應的技能ID"""
        scroll_to_skill = {
            'slash': 'slash',
            'fireball': 'fireball',
            'heal': 'heal',
            'shield': 'shield',
            'lightning': 'lightning',
            'ice_spike': 'ice_spike',
            'summon': 'summon'
        }
        return scroll_to_skill.get(scroll_effect, None)
# ============================================================================
# 核心遊戲類別
# ============================================================================
