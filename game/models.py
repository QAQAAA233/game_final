from dataclasses import dataclass
import math
from .enums import ItemType, SkillType, MessageType

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
