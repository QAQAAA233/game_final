from game.core import *
from game.resources import AssetManager, MessageLog
from game.particles import ParticleSystem

# ============================================================================
# 實體類別
# ============================================================================

class Entity:
    """遊戲實體基類"""
    
    def __init__(self, position: Position, image_key: str, name: str = ""):
        self.position = position
        self.image_key = image_key
        self.name = name
        self.active = True
        self.blocking = True
        self.visible = True
        self.animation_offset = 0
        self.animation_time = 0
    
    def update(self, dt: float):
        """更新實體"""
        # 動畫效果
        self.animation_time += dt
        self.animation_offset = math.sin(self.animation_time * 3) * 2
    
    def render(self, screen, camera_offset: Position, asset_manager: AssetManager):
        """渲染實體"""
        if not self.active or not self.visible:
            return
            
        image = asset_manager.get_image(self.image_key)
        if image:
            screen_x = (self.position.x * TILE_SIZE) - camera_offset.x
            screen_y = (self.position.y * TILE_SIZE) - camera_offset.y + int(self.animation_offset)
            screen.blit(image, (screen_x, screen_y))

class Player(Entity):
    """玩家角色"""
    # 召喚骷髏屬性繼承配置表
    # 格式：[等級1, 等級2, 等級3, 等級4, 等級5]
    SUMMON_STAT_CONFIG = {
        'hp_percent': [50, 75, 100, 125, 150],        # HP繼承百分比
        'attack_percent': [60, 80, 100, 120, 150],    # 攻擊力繼承百分比
        'defense_percent': [40, 60, 80, 100, 120],    # 防禦力繼承百分比
        'move_speed': [250, 275, 300, 325, 350],      # 移動速度（固定值）
        'duration_base': 15,                           # 基礎持續時間（秒）
        'duration_per_level': 5,                      # 每級增加的持續時間
        'summon_count': [1, 2, 2, 3, 3],              # 召喚數量
        'names': [                                     # 召喚物名稱
            "骷髏戰士",
            "強化骷髏戰士", 
            "精英骷髏戰士",
            "骷髏隊長",
            "骷髏統領"
        ]
    }
    

    def __init__(self, position: Position):
        super().__init__(position, 'player', "勇敢的冒險者")
        self.stats = Stats(
            hp=100, max_hp=100, mp=50, max_mp=50, 
            attack=10, defense=5, crit_chance=0.1, crit_damage=2.0,
            move_speed=200.0  
        )
        self.inventory = []
        self.equipment = {
            'weapon': None,
            'armor': None,
            'shield': None,
            'helmet': None,
            'boots': None,  
            'ring': None,
            'amulet': None
        }
        self.gold = 100
        self.max_inventory = 30
        self.identified_items = set()
        self.temp_buffs = {}
        self.skills = self._init_skills()
        self.shield_active = False
        self.shield_duration = 0
        self.velocity = Position(0, 0)  
        self.move_cooldown = 0  
        self.facing_direction = Direction.RIGHT  
        self.is_moving = False  
        self.fractional_position = Position(float(position.x), float(position.y))  
        self.attack_cooldown = 0  
        self.attack_speed = 1.0  
        self.mana_regen_accumulator = 0.0  # 新增：魔力恢復累積器

    def _init_skills(self):
        """初始化技能系統"""
        # 所有可學習的技能
        self.all_skills = SkillDatabase.get_all_skills()
        
        # 已裝備的技能（4個快捷欄）
        self.equipped_skills = [None, None, None, None]
        
        # 預設學習基礎技能
        self.all_skills['slash'].current_level = 1
        self.all_skills['slash'].slot_index = 0
        self.equipped_skills[0] = self.all_skills['slash']
        
        # 返回裝備的技能列表（兼容舊代碼）
        return self.equipped_skills
    
    def learn_skill(self, skill_id: str) -> bool:
        """學習技能（提升到1級）"""
        if skill_id not in self.all_skills:
            return False
        
        skill = self.all_skills[skill_id]
        if skill.current_level == 0:
            skill.current_level = 1
            return True
        return False
    
    def upgrade_skill(self, skill_id: str) -> tuple:
        """升級技能，返回 (成功與否, 消耗的卷軸數, 消耗的金幣)"""
        if skill_id not in self.all_skills:
            return (False, 0, 0)
        
        skill = self.all_skills[skill_id]
        if skill.is_max_level:
            return (False, 0, 0)
        
        scrolls_needed, gold_needed = skill.get_upgrade_cost()
        
        # 檢查資源是否足夠（這裡簡化處理，實際應該檢查對應的卷軸數量）
        if self.gold < gold_needed:
            return (False, 0, 0)
        
        # 扣除資源並升級
        self.gold -= gold_needed
        skill.current_level += 1
        
        return (True, scrolls_needed, gold_needed)
    
    def equip_skill(self, skill_id: str, slot_index: int) -> bool:
        """裝備技能到快捷欄"""
        if skill_id not in self.all_skills or slot_index < 0 or slot_index > 3:
            return False
        
        skill = self.all_skills[skill_id]
        if not skill.is_learned:
            return False
        
        # 如果技能已經裝備在其他位置，先卸下
        if skill.slot_index != -1:
            self.equipped_skills[skill.slot_index] = None
        
        # 如果目標位置有技能，卸下它
        if self.equipped_skills[slot_index]:
            self.equipped_skills[slot_index].slot_index = -1
        
        # 裝備新技能
        skill.slot_index = slot_index
        self.equipped_skills[slot_index] = skill
        return True
    
    def unequip_skill(self, slot_index: int) -> bool:
        """卸下快捷欄的技能"""
        if slot_index < 0 or slot_index > 3:
            return False
        
        if self.equipped_skills[slot_index]:
            self.equipped_skills[slot_index].slot_index = -1
            self.equipped_skills[slot_index] = None
            return True
        return False
    
    def get_learned_skills(self) -> list:
        """獲取所有已學習的技能"""
        return [skill for skill in self.all_skills.values() if skill.is_learned]
    
    def count_skill_scrolls(self, skill_id: str) -> int:
        """計算擁有的對應技能卷軸數量"""
        count = 0
        skill_to_scroll = {
            'slash': '劍刃斬卷軸',
            'fireball': '火球術卷軸',
            'heal': '治癒術卷軸',
            'shield': '護盾術卷軸',
            'lightning': '閃電鏈卷軸',
            'ice_spike': '冰錐術卷軸',
            'summon': '召喚術卷軸'
        }
        
        if skill_id in skill_to_scroll:
            target_name = skill_to_scroll[skill_id]
            for item in self.inventory:
                if item.item_type == ItemType.SCROLL and item.true_name == target_name:
                    count += 1
        return count
    
    def consume_skill_scrolls(self, skill_id: str, amount: int) -> bool:
        """消耗指定數量的技能卷軸"""
        skill_to_scroll = {
            'slash': '劍刃斬卷軸',
            'fireball': '火球術卷軸',
            'heal': '治癒術卷軸',
            'shield': '護盾術卷軸',
            'lightning': '閃電鏈卷軸',
            'ice_spike': '冰錐術卷軸',
            'summon': '召喚術卷軸'
        }
        
        if skill_id not in skill_to_scroll:
            return False
        
        target_name = skill_to_scroll[skill_id]
        consumed = 0
        
        for item in self.inventory[:]:
            if consumed >= amount:
                break
            if item.item_type == ItemType.SCROLL and item.true_name == target_name:
                self.inventory.remove(item)
                consumed += 1
        
        return consumed == amount
      
    def take_damage(self, damage: int):
        """受到傷害"""
        total_defense = self.stats.defense
        for item in self.equipment.values():
            if item:
                total_defense += item.defense_bonus
        
        # 護盾減傷
        if self.shield_active:
            damage = int(damage * 0.5)
        
        actual_damage = max(1, damage - total_defense)
        self.stats.hp = max(0, self.stats.hp - actual_damage)
        return actual_damage
    
    def heal(self, amount: int):
        """治療"""
        old_hp = self.stats.hp
        self.stats.hp = min(self.stats.max_hp, self.stats.hp + amount)
        return self.stats.hp - old_hp
    
    def restore_mana(self, amount: int):
        """恢復魔力"""
        old_mp = self.stats.mp
        self.stats.mp = min(self.stats.max_mp, self.stats.mp + amount)
        return self.stats.mp - old_mp
    
    def gain_exp(self, exp: int, message_log: MessageLog):
        """獲得經驗值"""
        self.stats.exp += exp
        while self.stats.exp >= self.stats.exp_to_next:
            self.level_up(message_log)
    
    def level_up(self, message_log: MessageLog):
        """升級"""
        self.stats.exp -= self.stats.exp_to_next
        self.stats.level += 1
        
        # 提升屬性
        hp_gain = random.randint(15, 25)
        mp_gain = random.randint(5, 10)
        attack_gain = random.randint(2, 4)
        defense_gain = random.randint(1, 3)
        
        self.stats.max_hp += hp_gain
        self.stats.max_mp += mp_gain
        self.stats.hp = self.stats.max_hp
        self.stats.mp = self.stats.max_mp
        self.stats.attack += attack_gain
        self.stats.defense += defense_gain
        self.stats.exp_to_next = int(self.stats.exp_to_next * 1.3)
        
        # 提升暴擊率
        if self.stats.level % 5 == 0:
            self.stats.crit_chance = min(0.5, self.stats.crit_chance + 0.05)
        
        message_log.add_message(
            GameTexts.COMBAT_LEVEL_UP.format(level=self.stats.level),
            MessageType.LEVEL_UP
        )
    
    def get_total_attack(self):
        """獲取總攻擊力"""
        total = self.stats.attack
        if self.equipment['weapon']:
            total += self.equipment['weapon'].attack_bonus
        # 臨時增益
        if 'strength' in self.temp_buffs:
            total += self.temp_buffs['strength']
        return total
    
    def get_total_defense(self):
        """獲取總防禦力"""
        total = self.stats.defense
        for item in self.equipment.values():
            if item:
                total += item.defense_bonus
        return total
    
    def add_item(self, item: Item, message_log: MessageLog, auto=False):
        if len(self.inventory) < self.max_inventory:
            # 如果是藥水，檢查是否已經鑑定過同類型
            if item.item_type == ItemType.POTION and not item.identified:
                if item.icon in self.identified_items:
                    item.identified = True
                    item.name = item.true_name
                    # 更新描述
                    if item.heal_amount > 0:
                        item.description = f"恢復{item.heal_amount}點生命值的治療藥水"
                    elif item.heal_amount < 0:
                        item.description = f"造成{-item.heal_amount}點傷害的毒藥"
                    elif item.mana_amount > 0:
                        item.description = f"恢復{item.mana_amount}點魔力值的魔力藥水"
                    elif item.special_effect == 'move_speed':
                        item.description = "暫時提升20%移動速度的疾風藥水（持續30秒）"
                    elif item.special_effect == 'strength':
                        bonus = item.attack_bonus if hasattr(item, 'attack_bonus') and item.attack_bonus > 0 else 5
                        item.description = f"暫時提升{bonus}點攻擊力的力量藥水"
            
            if item.item_type == ItemType.GOLD:
                self.gold += item.value
                message_type = GameTexts.ITEM_AUTO_PICKUP if auto else GameTexts.ITEM_PICKUP
                message_log.add_message(
                    message_type.format(item=item.name),
                    MessageType.ITEM
                )
            else:
                self.inventory.append(item)
                message_type = GameTexts.ITEM_AUTO_PICKUP if auto else GameTexts.ITEM_PICKUP
                message_log.add_message(
                    message_type.format(item=item.name),
                    MessageType.ITEM
                )
            return True
        else:
            if not auto:
                message_log.add_message(
                    GameTexts.ITEM_INVENTORY_FULL,
                    MessageType.WARNING
                )
            return False
        
    def use_item(self, item: Item, asset_manager: AssetManager, message_log: MessageLog, particle_system: ParticleSystem):
        if item.item_type == ItemType.POTION:
            return self._use_potion(item, asset_manager, message_log, particle_system)
        elif item.item_type == ItemType.SCROLL:
            return self._use_scroll(item, asset_manager, message_log, particle_system)
        elif item.item_type in [ItemType.WEAPON, ItemType.ARMOR, ItemType.SHIELD, ItemType.HELMET, ItemType.BOOTS, ItemType.RING, ItemType.AMULET]:
            return self._equip_item(item, message_log)
        return False

    def _use_potion(self, potion: Item, asset_manager: AssetManager, message_log: MessageLog, particle_system: ParticleSystem):
        # 如果藥水未鑑定，只進行鑑定，不使用
        if not potion.identified:
            potion.identified = True
            potion.name = potion.true_name
            self.identified_items.add(potion.icon)  # 使用icon作為識別標記
            
            message_log.add_message(
                GameTexts.ITEM_IDENTIFIED.format(item=potion.true_name),
                MessageType.ITEM
            )
            
            # 顯示鑑定後的效果說明
            if potion.heal_amount > 0:
                message_log.add_message(f"這是一瓶恢復{potion.heal_amount}點生命值的治療藥水！", MessageType.ITEM)
            elif potion.heal_amount < 0:
                message_log.add_message(f"這是一瓶會造成{-potion.heal_amount}點傷害的毒藥！", MessageType.WARNING)
            elif potion.mana_amount > 0:
                message_log.add_message(f"這是一瓶恢復{potion.mana_amount}點魔力值的魔力藥水！", MessageType.ITEM)
            elif potion.special_effect == 'move_speed':
                message_log.add_message("這是一瓶能提升20%移動速度的疾風藥水（持續30秒）！", MessageType.ITEM)
            elif potion.special_effect == 'strength':
                bonus = potion.attack_bonus if hasattr(potion, 'attack_bonus') and potion.attack_bonus > 0 else 5
                message_log.add_message(f"這是一瓶能提升{bonus}點攻擊力的力量藥水！", MessageType.ITEM)
            
            # 同步鑑定所有同類型的藥水
            self._identify_all_same_potions(potion.icon)
            
            # 只鑑定不使用，返回False表示物品未被消耗
            return False
        
        # 已鑑定的藥水才會真正使用
        effect_text = ""
        
        # 處理治療/傷害效果
        if potion.heal_amount != 0:
            if potion.heal_amount > 0:
                actual_heal = self.heal(potion.heal_amount)
                effect_text = GameTexts.EFFECT_HEAL.format(amount=actual_heal)
                particle_system.add_heal_text(self.position, actual_heal)
            else:
                actual_damage = self.take_damage(-potion.heal_amount)
                effect_text = GameTexts.EFFECT_POISON
                particle_system.add_damage_text(self.position, actual_damage, Colors.POISON_GREEN)
        
        # 處理魔力恢復
        if potion.mana_amount > 0:
            actual_mana = self.restore_mana(potion.mana_amount)
            effect_text = GameTexts.EFFECT_MANA.format(amount=actual_mana)
        
        # 處理特殊效果
        if potion.special_effect:
            if potion.special_effect == 'move_speed':
                # 增加20%移動速度，持續30秒
                self.temp_buffs['move_speed'] = {
                    'value': 1.2,  # 120%速度
                    'duration': 30.0,
                    'timer': 30.0
                }
                effect_text = "你感到腳步變得輕盈，移動速度提升了20%！"
                particle_system.add_pickup_effect(self.position, "potion")
            elif potion.special_effect == 'strength':
                # 增加5點攻擊力，但黃藥水用attack_bonus值
                strength_bonus = potion.attack_bonus if hasattr(potion, 'attack_bonus') and potion.attack_bonus > 0 else 5
                self.temp_buffs['strength'] = strength_bonus
                effect_text = GameTexts.EFFECT_STRENGTH
        
        message_log.add_message(
            GameTexts.ITEM_USE_POTION.format(potion=potion.name, effect=effect_text),
            MessageType.ITEM
        )
        
        self.inventory.remove(potion)
        asset_manager.play_sound('pickup_sound')
        return True

    def _identify_all_same_potions(self, potion_icon: str):
        """鑑定背包中所有同類型的藥水"""
        for item in self.inventory:
            if item.item_type == ItemType.POTION and item.icon == potion_icon and not item.identified:
                item.identified = True
                item.name = item.true_name
                # 更新描述
                if item.heal_amount > 0:
                    item.description = f"恢復{item.heal_amount}點生命值的治療藥水"
                elif item.heal_amount < 0:
                    item.description = f"造成{-item.heal_amount}點傷害的毒藥"
                elif item.mana_amount > 0:
                    item.description = f"恢復{item.mana_amount}點魔力值的魔力藥水"
                elif item.special_effect == 'move_speed':
                    item.description = "暫時提升20%移動速度的疾風藥水（持續30秒）"
                elif item.special_effect == 'strength':
                    bonus = item.attack_bonus if hasattr(item, 'attack_bonus') and item.attack_bonus > 0 else 5
                    item.description = f"暫時提升{bonus}點攻擊力的力量藥水"

    def _use_scroll(self, scroll: Item, asset_manager: AssetManager, message_log: MessageLog, particle_system: ParticleSystem):
        """使用卷軸學習或升級技能"""
        if not scroll.identified:
            scroll.identified = True
            scroll.name = scroll.true_name
            
            # 如果有儲存的圖標信息，更新圖標
            if hasattr(scroll, '_identified_icon'):
                scroll.icon = scroll._identified_icon
            
            self.identified_items.add(scroll.icon)
            message_log.add_message(
                GameTexts.ITEM_IDENTIFIED.format(item=scroll.true_name),
                MessageType.ITEM
            )
        
        # 獲取對應的技能
        skill_id = SkillDatabase.get_skill_by_scroll(scroll.special_effect)
        
        if skill_id and skill_id in self.all_skills:
            skill = self.all_skills[skill_id]
            
            if not skill.is_learned:
                # 學習新技能
                if self.learn_skill(skill_id):
                    message_log.add_message(
                        f"你學會了新技能：{skill.name}！",
                        MessageType.LEVEL_UP
                    )
                    particle_system.add_level_up_effect(self.position)
                    
                    # 自動裝備到空的快捷欄
                    for i in range(4):
                        if self.equipped_skills[i] is None:
                            self.equip_skill(skill_id, i)
                            message_log.add_message(
                                f"技能已自動裝備到快捷鍵 {i + 1}",
                                MessageType.ITEM
                            )
                            break
                else:
                    message_log.add_message("學習技能失敗！", MessageType.WARNING)
                    return False
            else:
                # 技能已學會，保留卷軸用於升級
                message_log.add_message(
                    f"你已經學會了{skill.name}，可以在技能界面使用卷軸升級！",
                    MessageType.ITEM
                )
                return False  # 不消耗卷軸
        else:
            # 處理特殊卷軸效果
            effect_text = "卷軸的魔力消散了..."
            message_log.add_message(
                GameTexts.ITEM_USE_SCROLL.format(scroll=scroll.name, effect=effect_text),
                MessageType.ITEM
            )
        
        self.inventory.remove(scroll)
        asset_manager.play_sound('skill_sound')
        return True
    def _equip_item(self, item: Item, message_log: MessageLog):
        """裝備物品"""
        slot_map = {
            ItemType.WEAPON: 'weapon',
            ItemType.ARMOR: 'armor',
            ItemType.SHIELD: 'shield', 
            ItemType.HELMET: 'helmet',
            ItemType.BOOTS: 'boots',  # 新增鞋子映射
            ItemType.RING: 'ring',
            ItemType.AMULET: 'amulet'
        }
        
        slot = slot_map.get(item.item_type)
        if slot:
            # 如果已有裝備，先卸下
            if self.equipment[slot]:
                old_item = self.equipment[slot]
                self.inventory.append(old_item)
                message_log.add_message(
                    GameTexts.ITEM_UNEQUIP.format(item=old_item.name),
                    MessageType.ITEM
                )
            
            # 裝備新物品
            self.equipment[slot] = item
            self.inventory.remove(item)
            message_log.add_message(
                GameTexts.ITEM_EQUIP.format(item=item.name),
                MessageType.ITEM
            )
            return True
        return False

    def use_skill(self, skill_index: int, target_pos: Position, asset_manager: AssetManager, 
                  message_log: MessageLog, particle_system: ParticleSystem, enemies: list, dungeon_map=None):
        if skill_index < 0 or skill_index >= 4:
            return False
        skill = self.equipped_skills[skill_index]
        if dungeon_map:
            self.dungeon_map = dungeon_map
        if skill is None:
            message_log.add_message("這個快捷鍵沒有技能！", MessageType.WARNING)
            return False
        if not skill.is_learned:
            message_log.add_message("你還沒有學會這個技能！", MessageType.WARNING)
            return False
        if skill.current_cooldown > 0:
            message_log.add_message(f"{skill.name}還在冷卻中！({int(skill.current_cooldown)}秒)", MessageType.WARNING)
            return False
        if self.stats.mp < skill.mp_cost:
            message_log.add_message("魔力不足！", MessageType.WARNING)
            return False
        self.stats.mp -= skill.mp_cost
        skill.current_cooldown = skill.cooldown
        message_log.add_message(
            GameTexts.COMBAT_SKILL_USED.format(skill=skill.name),
            MessageType.COMBAT
        )
        asset_manager.play_sound('skill_sound')
        def handle_enemy_death(enemy, skill_damage_type="技能"):
            if not enemy.active and not hasattr(enemy, '_death_handled'):
                enemy._death_handled = True  
                if hasattr(self, 'dungeon_level'):
                    dungeon_level = self.dungeon_level
                else:
                    dungeon_level = 1
                exp_gained = 20 + (dungeon_level - 1) * 10
                if hasattr(enemy, 'is_boss') and enemy.is_boss:
                    exp_gained *= 5
                gold_gained = random.randint(20, 50) + (dungeon_level - 1) * 5
                if hasattr(enemy, 'is_boss') and enemy.is_boss:
                    gold_gained *= 3
                self.gain_exp(exp_gained, message_log)
                self.gold += gold_gained
                message_log.add_message(
                    f"你用{skill_damage_type}擊敗了{enemy.name}！獲得{exp_gained}經驗值和{gold_gained}金幣！",
                    MessageType.COMBAT
                )
                particle_system.add_exp_text(enemy.position, exp_gained)
                particle_system.add_pickup_effect(enemy.position, "gold")
                asset_manager.play_sound('level_up_sound', 0.7)
                if hasattr(self, 'game_stats'):
                    self.game_stats.total_kills += 1
                    self.game_stats.total_gold_collected += gold_gained
                if hasattr(self, 'achievement_system'):
                    if self.game_stats.total_kills == 1:
                        self.achievement_system.unlock("first_kill", message_log, particle_system, self.position)
                    if enemy.image_key == 'dragon':
                        self.achievement_system.unlock("dragon_slayer", message_log, particle_system, self.position)
                if random.random() < 0.3 + (0.1 if hasattr(enemy, 'is_boss') and enemy.is_boss else 0):
                    if hasattr(self, '_enemy_drop_item'):
                        self._enemy_drop_item(enemy.position)
        if skill.damage_percent > 0:
            base_attack = self.get_total_attack()
            base_damage = int(base_attack * skill.damage_percent / 100)
            total_damage_dealt = 0  # 新增：追蹤總傷害
            
            if skill.id == 'slash':
                hit_count = 0
                hit_enemies = []  # 新增：記錄被擊中的敵人
                for enemy in enemies:
                    if enemy.active and enemy.position.distance_to(self.position) <= skill.range:
                        actual_damage = enemy.take_damage(base_damage, self.name, message_log)
                        particle_system.add_damage_text(enemy.position, actual_damage)
                        particle_system.add_hit_effect(enemy.position)
                        hit_count += 1
                        hit_enemies.append((enemy.name, actual_damage))  # 記錄敵人和傷害
                        total_damage_dealt += actual_damage
                        
                        # 詳細的傷害訊息
                        message_log.add_message(
                            f"[技能] {skill.name}對{enemy.name}造成了{actual_damage}點傷害！",
                            MessageType.COMBAT
                        )
                        
                        if not enemy.active:
                            handle_enemy_death(enemy, f"{skill.name}")
                        if skill.current_level >= 3:
                            dx = enemy.position.x - self.position.x
                            dy = enemy.position.y - self.position.y
                            if dx != 0 or dy != 0:
                                message_log.add_message(f"[效果] {enemy.name}被擊退了！", MessageType.COMBAT)
                        if skill.current_level >= 4 and enemy.active:
                            message_log.add_message(f"[效果] {enemy.name}開始流血！", MessageType.COMBAT)
                        if skill.current_level >= 5 and enemy.active:
                            message_log.add_message(f"[效果] {enemy.name}被眩暈了！", MessageType.COMBAT)
                
                # 總結訊息
                if hit_count == 0:
                    message_log.add_message("沒有擊中任何敵人！", MessageType.COMBAT)
                else:
                    message_log.add_message(
                        f"[總結] {skill.name}擊中了{hit_count}個敵人，總計造成{total_damage_dealt}點傷害！",
                        MessageType.LEVEL_UP
                    )
                    
            elif skill.id == 'fireball':
                particle_system.add_skill_effect(target_pos, 'fireball')
                hit_count = 0
                hit_enemies = []
                explosion_range = 2
                if skill.current_level >= 3:
                    explosion_range = 3
                if skill.current_level >= 5:
                    explosion_range = 4
                
                message_log.add_message(
                    f"[技能] {skill.name}在目標區域爆炸！（範圍：{explosion_range}格）",
                    MessageType.COMBAT
                )
                
                for enemy in enemies:
                    if enemy.active and enemy.position.distance_to(target_pos) <= explosion_range:
                        actual_damage = enemy.take_damage(base_damage, self.name, message_log)
                        particle_system.add_damage_text(enemy.position, actual_damage, Colors.NEON_ORANGE)
                        hit_count += 1
                        hit_enemies.append((enemy.name, actual_damage))
                        total_damage_dealt += actual_damage
                        
                        # 詳細的傷害訊息
                        message_log.add_message(
                            f"[爆炸] {enemy.name}受到了{actual_damage}點火焰傷害！",
                            MessageType.COMBAT
                        )
                        
                        if not enemy.active:
                            handle_enemy_death(enemy, f"{skill.name}")
                        if skill.current_level >= 4 and enemy.active:
                            message_log.add_message(f"[效果] {enemy.name}被點燃了！", MessageType.COMBAT)
                
                # 總結訊息
                if hit_count > 0:
                    message_log.add_message(
                        f"[總結] {skill.name}擊中了{hit_count}個敵人，總計造成{total_damage_dealt}點傷害！",
                        MessageType.LEVEL_UP
                    )
                else:
                    message_log.add_message("火球沒有擊中任何敵人！", MessageType.WARNING)
                    
            elif skill.id == 'lightning':
                particle_system.add_skill_effect(target_pos, 'lightning')
                max_bounces = 2
                if skill.current_level == 2:
                    max_bounces = 3
                elif skill.current_level == 3:
                    max_bounces = 4
                elif skill.current_level == 4:
                    max_bounces = 5
                elif skill.current_level == 5:
                    max_bounces = 6
                first_target = None
                min_distance = float('inf')
                for enemy in enemies:
                    if enemy.active:
                        dist = enemy.position.distance_to(self.position)
                        if dist <= skill.range and dist < min_distance:
                            min_distance = dist
                            first_target = enemy
                if first_target:
                    hit_enemies = []
                    current_target = first_target
                    chain_damage_total = 0
                    
                    message_log.add_message(
                        f"[技能] {skill.name}釋放！（最多彈跳{max_bounces}次）",
                        MessageType.COMBAT
                    )
                    
                    for bounce in range(max_bounces):
                        if current_target and current_target not in hit_enemies:
                            bounce_damage = int(base_damage * (0.8 ** bounce))
                            actual_damage = current_target.take_damage(bounce_damage, self.name, message_log)
                            particle_system.add_damage_text(current_target.position, actual_damage, Colors.NEON_CYAN)
                            hit_enemies.append(current_target)
                            chain_damage_total += actual_damage
                            
                            # 詳細的彈跳訊息
                            bounce_text = f"第{bounce + 1}次彈跳" if bounce > 0 else "初始打擊"
                            message_log.add_message(
                                f"[{bounce_text}] 閃電擊中{current_target.name}，造成{actual_damage}點傷害！",
                                MessageType.COMBAT
                            )
                            
                            if not current_target.active:
                                handle_enemy_death(current_target, f"{skill.name}")
                            if skill.current_level >= 4 and current_target.active:
                                message_log.add_message(f"[效果] {current_target.name}被麻痺了！", MessageType.COMBAT)
                            next_target = None
                            min_next_dist = float('inf')
                            for enemy in enemies:
                                if enemy.active and enemy not in hit_enemies:
                                    dist = enemy.position.distance_to(current_target.position)
                                    if dist <= 5 and dist < min_next_dist:
                                        min_next_dist = dist
                                        next_target = enemy
                            current_target = next_target
                        else:
                            break
                    
                    # 總結訊息
                    message_log.add_message(
                        f"[總結] {skill.name}擊中了{len(hit_enemies)}個敵人，總計造成{chain_damage_total}點傷害！",
                        MessageType.LEVEL_UP
                    )
                else:
                    message_log.add_message("沒有找到有效的目標！", MessageType.WARNING)
                    
            elif skill.id == 'ice_spike':
                particle_system.add_skill_effect(target_pos, 'ice')
                hit_count = 0
                hit_enemies = []
                
                message_log.add_message(
                    f"[技能] {skill.name}從地面刺出！（範圍：{skill.range}格）",
                    MessageType.COMBAT
                )
                
                for enemy in enemies:
                    if enemy.active and enemy.position.distance_to(self.position) <= skill.range:
                        actual_damage = enemy.take_damage(base_damage, self.name, message_log)
                        particle_system.add_damage_text(enemy.position, actual_damage, Colors.NEON_CYAN)
                        hit_count += 1
                        hit_enemies.append((enemy.name, actual_damage))
                        total_damage_dealt += actual_damage
                        
                        # 詳細的傷害訊息
                        message_log.add_message(
                            f"[冰錐] {enemy.name}受到了{actual_damage}點冰霜傷害！",
                            MessageType.COMBAT
                        )
                        
                        if not enemy.active:
                            handle_enemy_death(enemy, f"{skill.name}")
                        else:
                            slow_percent = 30 + (skill.current_level - 1) * 10
                            message_log.add_message(f"[效果] {enemy.name}被減速{slow_percent}%！", MessageType.COMBAT)
                            if skill.current_level >= 3:
                                freeze_chance = 0.2 + (skill.current_level - 3) * 0.2
                                if random.random() < freeze_chance:
                                    message_log.add_message(f"[效果] {enemy.name}被冰凍了！", MessageType.COMBAT)
                
                # 總結訊息
                if hit_count > 0:
                    message_log.add_message(
                        f"[總結] {skill.name}擊中了{hit_count}個敵人，總計造成{total_damage_dealt}點傷害！",
                        MessageType.LEVEL_UP
                    )
                else:
                    message_log.add_message("冰錐沒有擊中任何敵人！", MessageType.WARNING)
                    
        elif skill.heal_percent > 0:
            heal_amount = int(self.stats.max_hp * skill.heal_percent / 100)
            actual_heal = self.heal(heal_amount)
            particle_system.add_heal_text(self.position, actual_heal)
            particle_system.add_skill_effect(self.position, 'heal')
            
            # 詳細的治療訊息
            message_log.add_message(
                f"[技能] {skill.name}恢復了{actual_heal}點生命值！（{self.stats.hp}/{self.stats.max_hp}）",
                MessageType.ITEM
            )
            
            if skill.current_level >= 3:
                debuffs_removed = min(skill.current_level - 2, 3)
                message_log.add_message(f"[效果] 清除了{debuffs_removed}個負面效果！", MessageType.ITEM)
            if skill.current_level >= 5:
                message_log.add_message("[效果] 你的護甲得到了修復！", MessageType.ITEM)
                
        elif skill.id == 'shield':
            self.shield_active = True
            durations = [5, 6, 7, 8, 10]
            self.shield_duration = durations[skill.current_level - 1]
            self.shield_reduction = 0.5 + (skill.current_level - 1) * 0.05
            particle_system.add_skill_effect(self.position, 'shield')
            
            # 詳細的護盾訊息
            reduction_percent = int((1 - self.shield_reduction) * 100)
            message_log.add_message(
                f"[技能] {skill.name}啟動！減少{reduction_percent}%傷害，持續{self.shield_duration}秒！",
                MessageType.COMBAT
            )
            
            if skill.current_level >= 4:
                message_log.add_message("[效果] 護盾獲得反彈效果！", MessageType.COMBAT)
                
        elif skill.id == 'summon':
            particle_system.add_skill_effect(self.position, 'summon')
            level_index = skill.current_level - 1
            summon_count = self.SUMMON_STAT_CONFIG['summon_count'][level_index]
            summon_type = self.SUMMON_STAT_CONFIG['names'][level_index]
            summon_duration = self.SUMMON_STAT_CONFIG['duration_base'] + self.SUMMON_STAT_CONFIG['duration_per_level'] * skill.current_level
            hp_percent = self.SUMMON_STAT_CONFIG['hp_percent'][level_index] / 100.0
            attack_percent = self.SUMMON_STAT_CONFIG['attack_percent'][level_index] / 100.0
            defense_percent = self.SUMMON_STAT_CONFIG['defense_percent'][level_index] / 100.0
            move_speed = self.SUMMON_STAT_CONFIG['move_speed'][level_index]
            
            # 召喚詳細訊息
            message_log.add_message(
                f"[技能] {skill.name}！準備召喚{summon_count}個{summon_type}！",
                MessageType.COMBAT
            )
            
            summoned = 0
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if summoned >= summon_count:
                        break
                    if dx == 0 and dy == 0:
                        continue
                    summon_pos = Position(self.position.x + dx, self.position.y + dy)
                    if not self._is_position_available_for_summon(summon_pos, enemies):
                        continue
                    skeleton_hp = int(self.stats.max_hp * hp_percent)
                    skeleton_attack = int(self.get_total_attack() * attack_percent)
                    skeleton_defense = int(self.get_total_defense() * defense_percent)
                    skeleton_stats = Stats(
                        hp=skeleton_hp,
                        max_hp=skeleton_hp,
                        mp=0,
                        max_mp=0,
                        attack=skeleton_attack,
                        defense=skeleton_defense,
                        level=self.stats.level,
                        move_speed=move_speed
                    )
                    skeleton = Enemy(summon_pos, 'skeleton', f"召喚的{summon_type}", skeleton_stats)
                    skeleton.is_friendly = True
                    skeleton.summon_duration = summon_duration
                    skeleton.summoner = self
                    skeleton.friendly_glow_color = Colors.NEON_GREEN
                    enemies.append(skeleton)
                    summoned += 1
                    particle_system.add_skill_effect(summon_pos, 'summon')
                    
                    # 每個召喚物的詳細訊息
                    message_log.add_message(
                        f"[召喚] {summon_type}出現了！（HP:{skeleton_hp} 攻擊:{skeleton_attack} 防禦:{skeleton_defense}）",
                        MessageType.COMBAT
                    )
                    
            if summoned > 0:
                message_log.add_message(
                    f"[總結] 成功召喚了{summoned}個{summon_type}！(持續{summon_duration}秒)",
                    MessageType.LEVEL_UP
                )
            else:
                message_log.add_message("沒有足夠的空間召喚骷髏！", MessageType.WARNING)
                self.stats.mp += skill.mp_cost
                skill.current_cooldown = 0
                return False
        return True
    
    
    def _is_position_available_for_summon(self, pos: Position, enemies: list) -> bool:
        """檢查位置是否可以召喚"""
        # 檢查地形
        if hasattr(self, 'dungeon_map'):
            if not self.dungeon_map.is_walkable(pos):
                return False
        
        # 檢查是否有其他實體
        for enemy in enemies:
            if enemy.active and enemy.position.x == pos.x and enemy.position.y == pos.y:
                return False
        
        # 檢查玩家位置
        if self.position.x == pos.x and self.position.y == pos.y:
            return False
        
        return True
    
    def update_skills(self, dt):
        """更新技能冷卻"""
        # 更新所有已學技能的冷卻（不管是否裝備）
        for skill in self.all_skills.values():
            if skill.is_learned and skill.current_cooldown > 0:
                skill.current_cooldown = max(0, skill.current_cooldown - dt)
        
        # 更新護盾持續時間
        if self.shield_active:
            self.shield_duration -= dt
            if self.shield_duration <= 0:
                self.shield_active = False

    def update_buffs(self, dt):
        # 更新所有臨時增益的持續時間
        buffs_to_remove = []
        
        for buff_name, buff_data in self.temp_buffs.items():
            if isinstance(buff_data, dict) and 'timer' in buff_data:
                buff_data['timer'] -= dt
                if buff_data['timer'] <= 0:
                    buffs_to_remove.append(buff_name)
        
        # 移除過期的增益
        for buff_name in buffs_to_remove:
            del self.temp_buffs[buff_name]
            if buff_name == 'move_speed':
                if hasattr(self, 'message_log'):
                    self.message_log.add_message("疾風效果消失了", MessageType.NORMAL)

    def update_mana_regeneration(self, dt: float):
        if self.stats.mp < self.stats.max_mp:
            # 每秒恢復最大魔力值的3%
            regen_per_second = self.stats.max_mp * 0.03
            regen_amount = regen_per_second * dt
            
            # 累積恢復量
            self.mana_regen_accumulator += regen_amount
            
            # 當累積量超過1時，恢復整數點魔力
            if self.mana_regen_accumulator >= 1.0:
                # 計算要恢復的整數點數
                points_to_restore = int(self.mana_regen_accumulator)
                
                # 確保不會超過最大魔力值
                actual_restore = min(points_to_restore, self.stats.max_mp - self.stats.mp)
                
                # 恢復魔力（整數）
                self.stats.mp += actual_restore
                
                # 減去已恢復的部分，保留小數部分
                self.mana_regen_accumulator -= points_to_restore

    def update_movement(self, dt: float, dungeon_map):
        """更新即時移動（每幀調用）"""
        # 移除移動冷卻檢查，讓移動更流暢
        # 舊的冷卻機制會導致快速按鍵時的延遲
            
        if self.velocity.x != 0 or self.velocity.y != 0:
            self.is_moving = True
            
            # 計算實際移動速度（格子/秒）
            actual_speed = self.get_total_move_speed() / TILE_SIZE
            
            # 計算移動距離（格子）
            move_distance = actual_speed * dt
            
            # 更新精確位置
            new_x = self.fractional_position.x + self.velocity.x * move_distance
            new_y = self.fractional_position.y + self.velocity.y * move_distance
            
            # 檢查碰撞並移動
            target_pos = Position(int(new_x), int(new_y))
            
            # 分別檢查X和Y方向的碰撞
            can_move_x = True
            can_move_y = True
            
            # 檢查X方向
            if abs(new_x - self.fractional_position.x) > 0.01:
                x_check = new_x
                y_check = self.fractional_position.y
                x_pos = Position(int(x_check), int(y_check))
                
                if x_pos.x != self.position.x:
                    if not dungeon_map.is_walkable(x_pos) or dungeon_map.get_blocking_entity(x_pos):
                        can_move_x = False
                        new_x = self.position.x + (0.49 if self.velocity.x > 0 else 0.51)
            
            # 檢查Y方向
            if abs(new_y - self.fractional_position.y) > 0.01:
                x_check = self.fractional_position.x
                y_check = new_y
                y_pos = Position(int(x_check), int(y_check))
                
                if y_pos.y != self.position.y:
                    if not dungeon_map.is_walkable(y_pos) or dungeon_map.get_blocking_entity(y_pos):
                        can_move_y = False
                        new_y = self.position.y + (0.49 if self.velocity.y > 0 else 0.51)
            
            # 應用移動
            if can_move_x:
                self.fractional_position.x = new_x
            if can_move_y:
                self.fractional_position.y = new_y
            
            # 更新整數位置
            old_pos = Position(self.position.x, self.position.y)
            self.position.x = int(self.fractional_position.x)
            self.position.y = int(self.fractional_position.y)
            
            # 確保位置在地圖範圍內
            self.position.x = max(0, min(dungeon_map.width - 1, self.position.x))
            self.position.y = max(0, min(dungeon_map.height - 1, self.position.y))
            
            # 如果位置改變了，更新視野
            if self.position.x != old_pos.x or self.position.y != old_pos.y:
                dungeon_map.update_fov(self.position)
                # 移除移動冷卻設置，讓移動更流暢
        else:
            self.is_moving = False

    def update_combat(self, dt: float, enemies: list, message_log, particle_system, asset_manager, game_stats):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        
        if self.attack_cooldown > 0:
            return
        
        # 尋找可攻擊的敵人
        for enemy in enemies:
            if not enemy.active:
                continue
            
            # 跳過友方單位
            if hasattr(enemy, 'is_friendly') and enemy.is_friendly:
                continue
            
            dx = abs(enemy.position.x - self.position.x)
            dy = abs(enemy.position.y - self.position.y)
            
            if dx <= 1 and dy <= 1:
                self.attack_enemy(enemy, message_log, particle_system, asset_manager, game_stats)
                self.attack_cooldown = 1.0 / self.attack_speed
                break

    def attack_enemy(self, enemy, message_log, particle_system, asset_manager, game_stats):
        # 檢查是否為友方單位
        if hasattr(enemy, 'is_friendly') and enemy.is_friendly:
            message_log.add_message(
                f"你不能攻擊友方的{enemy.name}！",
                MessageType.WARNING
            )
            return
        
        is_critical = random.random() < self.stats.crit_chance
        damage = self.get_total_attack()
        if is_critical:
            damage = int(damage * self.stats.crit_damage)
            game_stats.total_critical_hits += 1
        
        hit_chance = 0.9
        if random.random() < hit_chance:
            actual_damage = enemy.take_damage(damage, self.name, message_log)
            weapon_name = self.equipment['weapon'].name if self.equipment['weapon'] else "拳頭"
            
            if self.equipment['weapon']:
                message_log.add_message(
                    GameTexts.COMBAT_PLAYER_ATTACK.format(weapon=weapon_name, enemy=enemy.name, damage=actual_damage),
                    MessageType.COMBAT
                )
            else:
                message_log.add_message(
                    GameTexts.COMBAT_PLAYER_ATTACK_BARE.format(enemy=enemy.name, damage=actual_damage),
                    MessageType.COMBAT
                )
            
            particle_system.add_damage_text(enemy.position, actual_damage, critical=is_critical)
            particle_system.add_hit_effect(enemy.position, critical=is_critical)
            
            if is_critical:
                asset_manager.play_sound('critical_sound')
            else:
                asset_manager.play_sound('hit_sound')
            
            game_stats.total_damage_dealt += actual_damage
            
            if is_critical:
                message_log.add_message(
                    GameTexts.COMBAT_CRITICAL_HIT.format(damage=actual_damage),
                    MessageType.COMBAT
                )
            
            if not enemy.active:
                exp_gained = 20 + (enemy.stats.level - 1) * 10 if hasattr(enemy.stats, 'level') else 20
                if enemy.is_boss:
                    exp_gained *= 5
                
                gold_gained = random.randint(20, 50) + 5
                if enemy.is_boss:
                    gold_gained *= 3
                
                self.gain_exp(exp_gained, message_log)
                self.gold += gold_gained
                
                message_log.add_message(
                    GameTexts.COMBAT_ENEMY_DEFEATED.format(
                        enemy=enemy.name, exp=exp_gained, gold=gold_gained
                    ),
                    MessageType.COMBAT
                )
                
                particle_system.add_exp_text(enemy.position, exp_gained)
                particle_system.add_pickup_effect(enemy.position, "gold")
                asset_manager.play_sound('level_up_sound', 0.7)
                
                game_stats.total_kills += 1
                game_stats.total_gold_collected += gold_gained
        else:
            message_log.add_message(
                GameTexts.COMBAT_MISS.format(attacker="你", target=enemy.name),
                MessageType.COMBAT
            )

    def set_velocity(self, dx: float, dy: float):
        """設置移動速度向量"""
        # 正規化速度向量
        if dx != 0 or dy != 0:
            length = math.sqrt(dx * dx + dy * dy)
            self.velocity.x = dx / length
            self.velocity.y = dy / length
            
            # 更新面向方向
            if abs(dx) > abs(dy):
                self.facing_direction = Direction.RIGHT if dx > 0 else Direction.LEFT
            else:
                self.facing_direction = Direction.DOWN if dy > 0 else Direction.UP
        else:
            self.velocity.x = 0
            self.velocity.y = 0
    
    def get_total_move_speed(self):
        base_speed = self.stats.move_speed
        
        # 鞋子加成
        if self.equipment['boots']:
            base_speed += self.equipment['boots'].move_speed_bonus
        
        # 等級加成
        level_bonus = 1 + (self.stats.level - 1) * 0.02
        
        # 藥水增益
        speed_multiplier = 1.0
        if 'move_speed' in self.temp_buffs and isinstance(self.temp_buffs['move_speed'], dict):
            speed_multiplier = self.temp_buffs['move_speed']['value']
        
        return base_speed * level_bonus * speed_multiplier
    
    def rest(self, message_log: MessageLog):
        """休息恢復體力"""
        if self.stats.hp >= self.stats.max_hp:
            message_log.add_message(GameTexts.REST_FULL_HP, MessageType.NORMAL)
            return False
        
        heal_amount = min(20, self.stats.max_hp - self.stats.hp)
        self.stats.hp += heal_amount
        
        # 恢復少量魔力
        mana_amount = min(10, self.stats.max_mp - self.stats.mp)
        self.stats.mp += mana_amount
        
        message_log.add_message(GameTexts.REST_SUCCESS, MessageType.ITEM)
        return True

    def debug_move_speed(self, message_log):
        """調試移動速度計算"""
        base_speed = self.stats.move_speed
        boots_bonus = 0
        if self.equipment['boots']:
            boots_bonus = self.equipment['boots'].move_speed_bonus
            boots_name = self.equipment['boots'].name
            boots_effect = self.equipment['boots'].special_effect
        else:
            boots_name = "無"
            boots_effect = ""
            
        level_bonus = 1 + (self.stats.level - 1) * 0.02
        total = self.get_total_move_speed()
        
        message_log.add_message(f"[調試] 基礎速度: {base_speed}", MessageType.NORMAL)
        message_log.add_message(f"[調試] 鞋子: {boots_name}", MessageType.NORMAL)
        message_log.add_message(f"[調試] 鞋子加成: {boots_bonus}", MessageType.NORMAL)
        message_log.add_message(f"[調試] 鞋子效果: {boots_effect}", MessageType.NORMAL)
        message_log.add_message(f"[調試] 等級加成: x{level_bonus:.2f}", MessageType.NORMAL)
        message_log.add_message(f"[調試] 總移速: {total}", MessageType.NORMAL)

class Enemy(Entity):
    """敵人基類"""
    
    def __init__(self, position: Position, image_key: str, name: str, stats: Stats):
        super().__init__(position, image_key, name)
        self.stats = stats
        self.original_stats = Stats(**stats.__dict__)
        self.target = None
        self.ai_state = "patrol"
        self.detection_range = 8
        self.chase_range = 15
        self.attack_animation = 0
        self.is_boss = False
        
        # 友方單位相關屬性
        self.is_friendly = False  # 是否為友方單位
        self.summon_duration = 0  # 召喚持續時間
        self.summoner = None      # 召喚者（玩家）
        self.friendly_glow_color = Colors.NEON_GREEN  # 友方單位的光暈顏色
        
        # 即時移動相關
        self.move_cooldown = 0
        self.attack_cooldown = 0
        self.velocity = Position(0, 0)
        self.fractional_position = Position(float(position.x), float(position.y))
        
        # 不同敵人類型的基礎移速（像素/秒）- 統一單位
        enemy_speeds = {
            'skeleton': 200.0,   # 骷髏：較慢
            'orc': 180.0,        # 獸人：最慢（坦克）
            'goblin': 350.0,    # 哥布林：快速
            'demon': 240.0,      # 惡魔：中速
            'lich': 250.0,       # 巫妖：中速
            'dragon': 240.0      # 龍：較慢但強大
        }
        # 只設置一次，使用像素/秒為單位
        self.base_move_speed = enemy_speeds.get(image_key, 60.0)

    def can_attack(self, target_pos: Position) -> bool:
        """檢查是否可以攻擊目標"""
        dx = abs(self.position.x - target_pos.x)
        dy = abs(self.position.y - target_pos.y)
        return dx <= 1 and dy <= 1 and self.attack_cooldown <= 0

    def should_attack(self, target) -> bool:
        """判斷是否應該攻擊目標"""
        if not self.active:
            return False
            
        # 友方單位的攻擊邏輯
        if self.is_friendly:
            # 不能攻擊玩家
            if hasattr(target, 'equipment'):  # Player 有 equipment 屬性
                return False
            # 不能攻擊其他友方單位
            if hasattr(target, 'is_friendly') and target.is_friendly:
                return False
            # 只能攻擊敵對的 Enemy
            return isinstance(target, Enemy) and not target.is_friendly
        else:
            # 敵對單位不能攻擊其他敵對單位
            if isinstance(target, Enemy) and not target.is_friendly:
                return False
            return True

    def update(self, player: Player, game_map, dt: float):
        super().update(dt)
        
        if not self.active:
            return
        
        # 更新冷卻時間
        if self.move_cooldown > 0:
            self.move_cooldown -= dt
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        if self.attack_animation > 0:
            self.attack_animation -= dt
        
        # 友方生物的持續時間檢查
        if self.is_friendly and self.summon_duration > 0:
            self.summon_duration -= dt
            if self.summon_duration <= 0:
                self.active = False
                return
        
        # 友方生物 AI
        if self.is_friendly:
            nearest_enemy = None
            min_distance = float('inf')
            
            # 尋找最近的敵對目標
            for enemy in game_map.enemies:
                if enemy.active and not enemy.is_friendly and enemy != self:
                    distance = self.position.distance_to(enemy.position)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_enemy = enemy
            
            if nearest_enemy:
                distance_to_enemy = min_distance
                if distance_to_enemy <= 1.5:
                    self.ai_state = "attack"
                    self.target = nearest_enemy
                elif distance_to_enemy <= self.detection_range:
                    self.ai_state = "chase"
                    self.target = nearest_enemy
                else:
                    self.ai_state = "follow"
                    self.target = player
            else:
                self.ai_state = "follow"
                self.target = player
        else:
            # 敵對生物 AI - 修改為可以攻擊友方骷髏
            potential_targets = []
            
            # 添加玩家作為潛在目標
            distance_to_player = self.position.distance_to(player.position)
            potential_targets.append({
                'target': player,
                'distance': distance_to_player,
                'priority': 1.0  # 玩家優先級較高
            })
            
            # 添加友方骷髏作為潛在目標
            for enemy in game_map.enemies:
                if enemy.active and enemy.is_friendly and enemy != self:
                    distance = self.position.distance_to(enemy.position)
                    potential_targets.append({
                        'target': enemy,
                        'distance': distance,
                        'priority': 1.5  # 骷髏優先級較低
                    })
            
            # 選擇最近的目標（考慮優先級）
            best_target = None
            best_score = float('inf')
            
            for target_info in potential_targets:
                # 分數 = 距離 * 優先級（越小越好）
                score = target_info['distance'] * target_info['priority']
                if score < best_score:
                    best_score = score
                    best_target = target_info
            
            if best_target:
                if best_target['distance'] <= 1.5:
                    self.ai_state = "attack"
                    self.target = best_target['target']
                elif best_target['distance'] <= self.detection_range:
                    self.ai_state = "chase"
                    self.target = best_target['target']
                elif best_target['distance'] > self.chase_range:
                    self.ai_state = "patrol"
                    self.target = None
            else:
                self.ai_state = "patrol"
                self.target = None
        
        # 根據 AI 狀態執行行動
        if self.ai_state == "attack":
            if self.is_friendly and self.target == player:
                self.ai_state = "follow"
            elif self.attack_cooldown <= 0:
                self.attack_animation = 0.5
        elif self.ai_state in ["chase", "follow"] and self.move_cooldown <= 0 and self.target:
            # 追逐目標
            dx = self.target.position.x - self.position.x
            dy = self.target.position.y - self.position.y
            
            # 如果是跟隨玩家，保持一定距離
            if self.ai_state == "follow" and abs(dx) <= 3 and abs(dy) <= 3:
                return  # 距離夠近了，不需要移動
            
            if dx != 0 or dy != 0:
                # 正規化方向
                length = math.sqrt(dx * dx + dy * dy)
                self.velocity.x = dx / length
                self.velocity.y = dy / length
                
                # 移動 - 使用像素/秒，需要除以TILE_SIZE轉換為格子/秒
                move_speed_in_tiles = self.base_move_speed / TILE_SIZE
                move_distance = move_speed_in_tiles * dt
                new_x = self.fractional_position.x + self.velocity.x * move_distance
                new_y = self.fractional_position.y + self.velocity.y * move_distance
                
                # 檢查碰撞
                target_pos = Position(int(new_x), int(new_y))
                
                can_move = True
                if target_pos.x != self.position.x or target_pos.y != self.position.y:
                    if not game_map.is_walkable(target_pos):
                        can_move = False
                    else:
                        # 檢查是否有其他實體
                        for other_enemy in game_map.enemies:
                            if other_enemy != self and other_enemy.active:
                                if other_enemy.position.x == target_pos.x and other_enemy.position.y == target_pos.y:
                                    can_move = False
                                    break
                        
                        # 檢查玩家位置（友方單位不應該與玩家碰撞）
                        if not self.is_friendly and player.position.x == target_pos.x and player.position.y == target_pos.y:
                            can_move = False
                
                if can_move:
                    self.fractional_position.x = new_x
                    self.fractional_position.y = new_y
                    self.position.x = int(self.fractional_position.x)
                    self.position.y = int(self.fractional_position.y)
                    self.move_cooldown = 0.1  # 減少移動冷卻時間
        
        elif self.ai_state == "patrol":
            # 巡邏行為
            if self.move_cooldown <= 0 and random.random() < 0.3:  # 30%機率移動
                # 隨機選擇方向
                self.velocity.x = random.choice([-1, 0, 1])
                self.velocity.y = random.choice([-1, 0, 1])
                
                if self.velocity.x != 0 or self.velocity.y != 0:
                    # 正規化
                    length = math.sqrt(self.velocity.x ** 2 + self.velocity.y ** 2)
                    self.velocity.x /= length
                    self.velocity.y /= length
                    
                    # 巡邏時速度減半
                    patrol_speed = self.base_move_speed * 0.5 / TILE_SIZE
                    move_distance = patrol_speed * dt
                    new_x = self.fractional_position.x + self.velocity.x * move_distance
                    new_y = self.fractional_position.y + self.velocity.y * move_distance
                    
                    # 檢查碰撞
                    target_pos = Position(int(new_x), int(new_y))
                    
                    if (0 <= target_pos.x < game_map.width and 
                        0 <= target_pos.y < game_map.height and
                        game_map.is_walkable(target_pos)):
                        
                        # 檢查其他實體
                        can_move = True
                        for other_enemy in game_map.enemies:
                            if other_enemy != self and other_enemy.active:
                                if other_enemy.position.x == target_pos.x and other_enemy.position.y == target_pos.y:
                                    can_move = False
                                    break
                        
                        if can_move:
                            self.fractional_position.x = new_x
                            self.fractional_position.y = new_y
                            self.position.x = int(self.fractional_position.x)
                            self.position.y = int(self.fractional_position.y)
                    
                    self.move_cooldown = 0.5  # 巡邏時冷卻更長

    def attack(self, target, asset_manager: AssetManager, message_log: MessageLog, 
               particle_system: ParticleSystem, game_stats: GameStats):
        # 添加額外的安全檢查
        if not self.should_attack(target):
            return 0

        if self.position.distance_to(target.position) <= 1.5:
            hit_chance = 0.8
            if random.random() < hit_chance:
                # 判斷目標是否為 Enemy 類型
                if isinstance(target, Enemy):
                    # 如果是敵人對敵人，需要提供 attacker_name 和 message_log
                    damage = target.take_damage(self.stats.attack, self.name, message_log)
                else:
                    # 如果是對玩家的攻擊
                    damage = target.take_damage(self.stats.attack)
                
                asset_manager.play_sound('hit_sound')
                
                # 處理訊息顯示
                if hasattr(target, 'name'):
                    if self.is_friendly:
                        message_log.add_message(
                            f"你的{self.name}對{target.name}造成了{damage}點傷害！",
                            MessageType.COMBAT
                        )
                    else:
                        message_log.add_message(
                            GameTexts.COMBAT_ENEMY_ATTACK.format(enemy=self.name, damage=damage),
                            MessageType.COMBAT
                        )
                
                particle_system.add_hit_effect(target.position)
                return damage
            else:
                target_name = "你" if not hasattr(target, 'name') else target.name
                message_log.add_message(
                    GameTexts.COMBAT_MISS.format(attacker=self.name, target=target_name),
                    MessageType.COMBAT
                )
        return 0
    
    def take_damage(self, damage: int, attacker_name: str, message_log: MessageLog):
        """受到傷害"""
        actual_damage = max(1, damage - self.stats.defense)
        self.stats.hp = max(0, self.stats.hp - actual_damage)
        
        if self.stats.hp <= 0:
            self.active = False
            self.just_died = True  # 標記剛死亡，用於掉落物品
        return actual_damage
    
    def render(self, screen, camera_offset: Position, asset_manager: AssetManager):
        """渲染敵人"""
        if not self.active or not self.visible:
            return
            
        image = asset_manager.get_image(self.image_key)
        if image:
            screen_x = (self.position.x * TILE_SIZE) - camera_offset.x
            screen_y = (self.position.y * TILE_SIZE) - camera_offset.y + int(self.animation_offset)
            
            # 如果是友方單位，添加綠色光暈
            if self.is_friendly:
                # 繪製光暈
                glow_surface = pygame.Surface((TILE_SIZE * 2, TILE_SIZE * 2), pygame.SRCALPHA)
                glow_size = TILE_SIZE + 10
                
                # 脈衝效果
                pulse = abs(math.sin(pygame.time.get_ticks() * 0.003))
                glow_alpha = int(100 + pulse * 50)
                
                pygame.gfxdraw.filled_circle(glow_surface, TILE_SIZE, TILE_SIZE, 
                                            glow_size, (*self.friendly_glow_color, glow_alpha))
                screen.blit(glow_surface, (screen_x - TILE_SIZE//2, screen_y - TILE_SIZE//2))
                
                # 添加綠色邊框
                border_rect = pygame.Rect(screen_x - 2, screen_y - 2, TILE_SIZE + 4, TILE_SIZE + 4)
                pygame.draw.rect(screen, self.friendly_glow_color, border_rect, 2)
            
            # 攻擊動畫效果（減少震動幅度）
            if self.attack_animation > 0:
                offset_x = random.randint(-1, 1)  # 從-2減少到-1
                offset_y = random.randint(-1, 1)  # 從-2減少到-1
                screen.blit(image, (screen_x + offset_x, screen_y + offset_y))
            else:
                screen.blit(image, (screen_x, screen_y))
