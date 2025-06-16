from enum import Enum

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
