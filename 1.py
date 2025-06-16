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
from game.constants import *
from game.settings import GameSettings
from game.achievements import Achievement, AchievementSystem
from game.stats import GameStats
from game.texts import GameTexts
from game.enums import GameState, Direction, MessageType, ItemType, SkillType
from game.models import Position, Stats, Item, Skill, GameMessage




# ============================================================================

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
            'legendary_boots': {'name': '神行靴', 'defense': 3, 'move_speed': 300, 'value': 1000, 'rarity': 'legendary'}
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

class FontManager:
    """字體管理器 - 解決中文和Emoji顯示問題"""
    
    def __init__(self):
        pygame.font.init()
        self.fonts = {}
        self.emoji_fonts = {}
        self.emoji_supported = False
        self._load_fonts()
    
    def _load_fonts(self):
        """載入支援中文和Emoji的字體"""
        # Windows 系統 emoji 字體優先級
        windows_emoji_fonts = [
            "Segoe UI Emoji",
            "Segoe UI Symbol",
            "Segoe UI",
        ]
        
        # macOS 系統 emoji 字體
        mac_emoji_fonts = [
            "Apple Color Emoji",
            "Apple Symbols",
        ]
        
        # Linux 系統 emoji 字體
        linux_emoji_fonts = [
            "Noto Color Emoji",
            "Noto Emoji",
            "Symbola",
            "EmojiOne Color",
            "Twitter Color Emoji"
        ]
        
        # 中文字體列表
        chinese_fonts = [
            "Microsoft JhengHei",
            "Microsoft YaHei",
            "PingFang TC",
            "PingFang SC",
            "Noto Sans CJK TC",
            "SimHei",
            "Arial Unicode MS",
            "微軟正黑體",
            "微软雅黑",
            "標楷體"
        ]
        
        # 檢測系統類型
        import platform
        system = platform.system()
        
        if system == "Windows":
            emoji_font_list = windows_emoji_fonts + mac_emoji_fonts + linux_emoji_fonts
        elif system == "Darwin":  # macOS
            emoji_font_list = mac_emoji_fonts + windows_emoji_fonts + linux_emoji_fonts
        else:  # Linux
            emoji_font_list = linux_emoji_fonts + windows_emoji_fonts + mac_emoji_fonts
        
        # 嘗試載入Emoji字體
        emoji_font_loaded = None
        for font_name in emoji_font_list:
            try:
                # 測試是否能載入並渲染emoji
                test_font = pygame.font.SysFont(font_name, 24)
                # 測試多個emoji確保支援
                test_emojis = ["😀", "⚔️", "🛡️", "💎", "🧪"]
                success = True
                for emoji in test_emojis:
                    try:
                        test_surface = test_font.render(emoji, True, (255, 255, 255))
                        # 檢查是否真的渲染了內容（不是空白）
                        if test_surface.get_width() <= 0 or test_surface.get_height() <= 0:
                            success = False
                            break
                        # 檢查是否只是渲染了方塊
                        pixels = pygame.PixelArray(test_surface)
                        has_content = False
                        for x in range(min(test_surface.get_width(), 10)):
                            for y in range(min(test_surface.get_height(), 10)):
                                if pixels[x, y] != 0:
                                    has_content = True
                                    break
                            if has_content:
                                break
                        del pixels
                        if not has_content:
                            success = False
                            break
                    except Exception as e:
                        print(f"測試emoji失敗 {font_name}: {e}")
                        success = False
                        break
                
                if success:
                    emoji_font_loaded = font_name
                    self.emoji_supported = True
                    print(f"成功載入 Emoji 字體: {font_name}")
                    break
            except Exception as e:
                print(f"載入字體失敗 {font_name}: {e}")
                continue
        
        if not emoji_font_loaded:
            print("警告：無法找到支援 Emoji 的字體，將使用備用圖形")
            self.emoji_supported = False
        
        # 載入中文字體
        chinese_font_loaded = None
        for font_name in chinese_fonts:
            try:
                test_font = pygame.font.SysFont(font_name, 24)
                test_surface = test_font.render("測試中文", True, (255, 255, 255))
                if test_surface.get_width() > 0:
                    chinese_font_loaded = font_name
                    print(f"成功載入中文字體: {font_name}")
                    break
            except:
                continue
        
        if not chinese_font_loaded:
            chinese_font_loaded = pygame.font.get_default_font()
            print("使用預設字體")
        
        # 載入不同大小的字體
        sizes = [12, 14, 16, 18, 20, 24, 28, 32, 36, 42, 48, 56, 64, 72]
        for size in sizes:
            # 中文字體
            try:
                if chinese_font_loaded == pygame.font.get_default_font():
                    self.fonts[size] = pygame.font.Font(None, size)
                else:
                    self.fonts[size] = pygame.font.SysFont(chinese_font_loaded, size)
            except:
                self.fonts[size] = pygame.font.Font(None, size)
            
            # Emoji字體
            if emoji_font_loaded:
                try:
                    self.emoji_fonts[size] = pygame.font.SysFont(emoji_font_loaded, size)
                except:
                    self.emoji_fonts[size] = self.fonts[size]
            else:
                self.emoji_fonts[size] = self.fonts[size]
    
    def get_font(self, size: int):
        """獲取指定大小的字體"""
        return self.fonts.get(size, self.fonts[24])
    
    def get_emoji_font(self, size: int):
        """獲取emoji字體"""
        return self.emoji_fonts.get(size, self.fonts.get(size, self.fonts[24]))
    
    # 檔案: 1.py, 類別: FontManager

    # +++ 請用這段全新的函式，完整取代舊的 render_text 函式 +++
    def render_text(self, text: str, size: int, color, antialias=True):
        """
        渲染文字（智慧分段版），自動處理中文字、英文和Emoji/符號的字體切換。
        """
        try:
            segments = []
            current_text = ""
            current_is_special = None

            def is_symbol_or_emoji(char):
                code = ord(char)
                # U+25A0-U+26FF: 幾何圖形 (包含 ▶)
                # U+2600-U+26FF: 雜項符號
                # U+1F000 以上: 大部分的 Emoji
                return (0x25A0 <= code <= 0x26FF) or (code > 0x1F000)

            # 1. 根據字體類型（普通 vs 特殊/Emoji）將字串分段
            for char in text:
                char_is_special = is_symbol_or_emoji(char) and self.emoji_supported
                if current_is_special is None:
                    current_is_special = char_is_special
                
                if char_is_special != current_is_special:
                    segments.append((current_text, current_is_special))
                    current_text = ""
                    current_is_special = char_is_special
                
                current_text += char
            
            if current_text:
                segments.append((current_text, current_is_special))

            # 2. 分別渲染每一個分段
            rendered_surfaces = []
            total_width = 0
            max_height = 0
            for segment_text, use_special_font in segments:
                if use_special_font:
                    font = self.get_emoji_font(size)
                else:
                    font = self.get_font(size)
                
                surface = font.render(segment_text, antialias, color)
                rendered_surfaces.append(surface)
                total_width += surface.get_width()
                if surface.get_height() > max_height:
                    max_height = surface.get_height()

            # 3. 將所有分段表面拼接成一個最終表面
            final_surface = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
            current_x = 0
            for surface in rendered_surfaces:
                # 垂直對齊（例如，底部對齊）
                y_pos = max_height - surface.get_height()
                final_surface.blit(surface, (current_x, y_pos))
                current_x += surface.get_width()
                
            return final_surface

        except Exception as e:
            print(f"渲染文字失敗: {text}, 錯誤: {e}")
            # 使用基本字體作為後備
            font = self.get_font(size)
            return font.render("?", antialias, color)
      
    def can_render_emoji(self):
        """檢查是否能渲染emoji"""
        return self.emoji_supported

class EmojiManager:
    """Emoji管理器 - 支援多種渲染方式"""
    
    def __init__(self):
        self.freetype_available = False
        self.emoji_font = None
        self.pygame_emojis = {}
        self._init_emoji_system()
    
    def _init_emoji_system(self):
        """初始化emoji系統"""
        # 嘗試載入freetype
        try:
            import freetype
            self.freetype_available = True
            
            # 嘗試載入彩色emoji字體
            emoji_fonts = [
                "AppleColorEmoji.ttf",
                "NotoColorEmoji.ttf",
                "TwitterColorEmoji.ttf",
                "seguiemj.ttf",  # Windows 10 emoji font
            ]
            
            for font_name in emoji_fonts:
                try:
                    # 嘗試從系統路徑載入
                    import os
                    system_paths = [
                        "C:/Windows/Fonts/",
                        "/System/Library/Fonts/",
                        "/usr/share/fonts/",
                        "./assets/fonts/",  # 本地資源目錄
                    ]
                    
                    for path in system_paths:
                        font_path = os.path.join(path, font_name)
                        if os.path.exists(font_path):
                            self.emoji_font = freetype.Face(font_path)
                            self.emoji_font.set_char_size(int(self.emoji_font.available_sizes[-1].size))
                            print(f"成功載入彩色emoji字體: {font_path}")
                            return
                except Exception as e:
                    continue
            
            # 如果沒有找到彩色emoji字體，禁用freetype
            if not self.emoji_font:
                self.freetype_available = False
                print("未找到彩色emoji字體，使用圖形化備用方案")
                
        except ImportError:
            print("freetype-py未安裝，使用圖形化備用方案")
            self.freetype_available = False
    
    def render_emoji(self, emoji_char: str, size: int) -> pygame.Surface:
        """渲染emoji（嘗試多種方式）"""
        # 方法1：使用freetype渲染彩色emoji（修復版）
        if self.freetype_available and self.emoji_font:
            try:
                import freetype
                import numpy as np
                
                # 檢查 emoji_font 是否有效
                if not self.emoji_font:
                    raise ValueError("Emoji font not loaded")
                
                # 設置字體大小
                self.emoji_font.set_char_size(size * 64)
                
                # 處理字符編碼（修復 'str' object has no attribute 'decode' 錯誤）
                # Python 3 中字串已經是 Unicode，不需要 decode
                if isinstance(emoji_char, str):
                    # 對於某些 emoji，可能需要獲取正確的字符碼
                    char_code = ord(emoji_char[0]) if emoji_char else 0
                else:
                    char_code = emoji_char
                
                # 載入彩色emoji（使用字符碼而不是字串）
                try:
                    self.emoji_font.load_char(char_code, freetype.FT_LOAD_COLOR)
                except Exception as e:
                    # 如果載入失敗，跳過 freetype 方法
                    raise ValueError(f"Failed to load char: {e}")
                
                bitmap = self.emoji_font.glyph.bitmap
                
                if bitmap.width > 0 and bitmap.rows > 0:
                    # 檢查 bitmap.buffer 是否有效
                    if not bitmap.buffer:
                        raise ValueError("Invalid bitmap buffer")
                    
                    # 轉換為pygame surface
                    bitmap_array = np.array(bitmap.buffer, dtype=np.uint8).reshape((bitmap.rows, bitmap.width, 4))
                    # 交換紅藍通道（BGRA -> RGBA）
                    bitmap_array[:, :, [0, 2]] = bitmap_array[:, :, [2, 0]]
                    
                    surface = pygame.image.frombuffer(
                        bitmap_array.flatten(), 
                        (bitmap.width, bitmap.rows), 
                        'RGBA'
                    )
                    
                    # 縮放到目標大小
                    if surface.get_width() != size or surface.get_height() != size:
                        surface = pygame.transform.smoothscale(surface, (size, size))
                    
                    return surface
            except Exception as e:
                # 如果出現任何錯誤，靜默失敗並使用其他方法
                # 不再打印錯誤訊息，避免干擾
                pass
        
        # 方法2：使用pygame的內建emoji支援（如果可用）
        try:
            # 檢查pygame版本是否支援UCS4
            if hasattr(pygame.font, "UCS4"):
                font = pygame.font.SysFont("Segoe UI Emoji", size)
                test_surface = font.render(emoji_char, True, Colors.WHITE)
                
                # 檢查是否真的渲染了內容
                if test_surface.get_width() > 0 and test_surface.get_height() > 0:
                    # 創建透明背景的surface
                    emoji_surface = pygame.Surface((size, size), pygame.SRCALPHA)
                    emoji_surface.fill((0, 0, 0, 0))
                    
                    # 居中繪製
                    rect = test_surface.get_rect(center=(size // 2, size // 2))
                    emoji_surface.blit(test_surface, rect)
                    
                    return emoji_surface
        except:
            pass
        
        # 方法3：返回None，讓調用者使用圖形化備用方案
        return None

    def preload_emojis(self, emoji_list: list, size: int):
        """預載入emoji以提高性能"""
        for emoji in emoji_list:
            key = f"{emoji}_{size}"
            if key not in self.pygame_emojis:
                surface = self.render_emoji(emoji, size)
                if surface:
                    self.pygame_emojis[key] = surface

class EmojiRenderer:
    """Emoji 渲染器 - 使用精美圖形符號代替真實emoji"""
    
    @staticmethod
    def draw_emoji(surface, emoji_type: str, x: int, y: int, size: int):
        """繪製精美的emoji風格圖形"""
        center_x = x + size // 2
        center_y = y + size // 2
        
        if emoji_type == 'sword':
            # 繪製精美的劍
            blade_color = (220, 220, 235)
            handle_color = (139, 69, 19)
            guard_color = (184, 134, 11)
            
            # 劍刃（漸變效果）
            blade_width = size // 8
            for i in range(blade_width):
                color_intensity = 255 - i * 20
                blade_shade = (min(255, color_intensity), min(255, color_intensity), min(255, color_intensity + 20))
                pygame.draw.line(surface, blade_shade, 
                               (center_x - blade_width//2 + i, y + 5), 
                               (center_x - blade_width//2 + i, y + size - 12), 1)
            
            # 劍尖
            point = [(center_x, y + 2), 
                    (center_x - blade_width//2, y + 5), 
                    (center_x + blade_width//2, y + 5)]
            pygame.draw.polygon(surface, blade_color, point)
            
            # 護手
            pygame.draw.rect(surface, guard_color, 
                           (center_x - size//4, y + size - 12, size//2, 4))
            pygame.draw.circle(surface, guard_color, (center_x - size//4, y + size - 10), 3)
            pygame.draw.circle(surface, guard_color, (center_x + size//4, y + size - 10), 3)
            
            # 劍柄
            pygame.draw.rect(surface, handle_color, 
                           (center_x - 3, y + size - 10, 6, 8))
            
            # 高光效果
            pygame.draw.line(surface, (255, 255, 255), 
                           (center_x - 1, y + 8), 
                           (center_x - 1, y + size - 15), 1)
            
        elif emoji_type == 'shield':
            # 繪製精美盾牌
            shield_color = (120, 120, 170)
            border_color = (80, 80, 120)
            accent_color = (200, 170, 0)
            
            # 盾牌主體（更複雜的形狀）
            points = [
                (center_x, y + 3),
                (center_x - size//3, y + size//4),
                (center_x - size//3, y + size*2//3),
                (center_x, y + size - 3),
                (center_x + size//3, y + size*2//3),
                (center_x + size//3, y + size//4)
            ]
            
            # 陰影
            shadow_points = [(p[0] + 2, p[1] + 2) for p in points]
            pygame.draw.polygon(surface, (0, 0, 0, 100), shadow_points)
            
            # 主體
            pygame.draw.polygon(surface, shield_color, points)
            
            # 邊框
            pygame.draw.polygon(surface, border_color, points, 3)
            
            # 中央裝飾
            pygame.draw.circle(surface, accent_color, (center_x, center_y), size//6)
            pygame.draw.circle(surface, border_color, (center_x, center_y), size//6, 2)
            
            # 十字圖案
            cross_size = size // 8
            pygame.draw.rect(surface, accent_color, 
                           (center_x - 1, center_y - cross_size, 2, cross_size * 2))
            pygame.draw.rect(surface, accent_color, 
                           (center_x - cross_size, center_y - 1, cross_size * 2, 2))
            
        elif emoji_type == 'potion':
            # 繪製精美藥水瓶
            bottle_color = (100, 150, 200, 180)
            cork_color = (139, 90, 43)
            liquid_color = (255, 100, 100, 200)
            
            # 瓶身（圓形底部）
            bottle_rect = pygame.Rect(center_x - size//4, center_y - size//6, 
                                    size//2, size//2)
            pygame.draw.ellipse(surface, bottle_color, bottle_rect)
            pygame.draw.ellipse(surface, (255, 255, 255, 100), bottle_rect, 1)
            
            # 瓶頸
            neck_rect = pygame.Rect(center_x - size//8, y + size//4, size//4, size//3)
            pygame.draw.rect(surface, bottle_color, neck_rect)
            
            # 液體（在瓶子裡）
            liquid_rect = pygame.Rect(center_x - size//5, center_y, 
                                    size*2//5, size//3)
            pygame.draw.ellipse(surface, liquid_color, liquid_rect)
            
            # 瓶塞
            cork_rect = pygame.Rect(center_x - size//6, y + size//5, size//3, size//8)
            pygame.draw.rect(surface, cork_color, cork_rect)
            pygame.draw.rect(surface, (100, 50, 0), cork_rect, 1)
            
            # 高光
            highlight_rect = pygame.Rect(center_x - size//6, center_y - size//8, 
                                       size//8, size//4)
            pygame.draw.ellipse(surface, (255, 255, 255, 150), highlight_rect)
            
        elif emoji_type == 'coin':
            # 繪製精美金幣
            # 外圈
            pygame.draw.circle(surface, (255, 215, 0), (center_x, center_y), size//3)
            pygame.draw.circle(surface, (218, 165, 32), (center_x, center_y), size//3, 2)
            
            # 內圈
            pygame.draw.circle(surface, (255, 223, 0), (center_x, center_y), size//4)
            
            # 金幣符號
            font = pygame.font.Font(None, size//3)
            text = font.render("$", True, (184, 134, 11))
            text_rect = text.get_rect(center=(center_x, center_y))
            surface.blit(text, text_rect)
            
            # 高光
            pygame.draw.arc(surface, (255, 255, 200), 
                          (center_x - size//3, center_y - size//3, size*2//3, size*2//3),
                          -math.pi/4, math.pi/4, 2)
            
        elif emoji_type == 'heart':
            # 繪製精美愛心
            heart_color = Colors.HEALTH_RED
            
            # 使用貝塞爾曲線繪製更平滑的愛心
            def draw_heart(x, y, size, color):
                # 愛心的數學公式
                points = []
                for angle in range(0, 360, 5):
                    rad = math.radians(angle)
                    hx = 16 * (math.sin(rad)**3)
                    hy = -(13 * math.cos(rad) - 5 * math.cos(2*rad) - 
                          2 * math.cos(3*rad) - math.cos(4*rad))
                    points.append((x + int(hx * size / 32), 
                                 y + int(hy * size / 32)))
                
                if len(points) > 2:
                    pygame.draw.polygon(surface, color, points)
                    
            # 陰影
            draw_heart(center_x + 1, center_y + 1, size * 0.8, (150, 0, 0))
            # 主體
            draw_heart(center_x, center_y, size * 0.8, heart_color)
            # 高光
            pygame.draw.circle(surface, (255, 150, 150), 
                             (center_x - size//6, center_y - size//6), size//8)
            
        elif emoji_type == 'star':
            # 繪製精美星星
            star_color = Colors.EXP_YELLOW
            
            # 繪製多層星星創造光暈效果
            for layer in range(3):
                scale = 1 - layer * 0.2
                alpha = 255 - layer * 80
                color = (*star_color, alpha)
                
                # 五角星頂點
                angle = -math.pi / 2
                outer_radius = (size // 2 - 2) * scale
                inner_radius = outer_radius // 2.5
                points = []
                
                for i in range(10):
                    radius = outer_radius if i % 2 == 0 else inner_radius
                    px = center_x + radius * math.cos(angle + i * math.pi / 5)
                    py = center_y + radius * math.sin(angle + i * math.pi / 5)
                    points.append((px, py))
                
                # 創建帶透明度的surface
                star_surface = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.polygon(star_surface, color, points)
                surface.blit(star_surface, (x, y))
            
            # 中心光點
            pygame.draw.circle(surface, Colors.WHITE, (center_x, center_y), 2)
            
        elif emoji_type == 'skull':
            # 繪製精美骷髏
            skull_color = (240, 240, 240)
            shadow_color = (200, 200, 200)
            
            # 頭骨主體
            skull_rect = pygame.Rect(center_x - size//3, center_y - size//3, 
                                   size*2//3, size*2//3)
            pygame.draw.ellipse(surface, skull_color, skull_rect)
            pygame.draw.ellipse(surface, shadow_color, skull_rect, 2)
            
            # 眼窩
            eye_size = size // 8
            left_eye = pygame.Rect(center_x - size//5 - eye_size//2, 
                                 center_y - size//6 - eye_size//2, 
                                 eye_size, eye_size + 2)
            right_eye = pygame.Rect(center_x + size//5 - eye_size//2, 
                                  center_y - size//6 - eye_size//2, 
                                  eye_size, eye_size + 2)
            pygame.draw.ellipse(surface, Colors.BLACK, left_eye)
            pygame.draw.ellipse(surface, Colors.BLACK, right_eye)
            
            # 鼻子（倒三角形）
            nose_points = [
                (center_x, center_y - 2),
                (center_x - 3, center_y + 4),
                (center_x + 3, center_y + 4)
            ]
            pygame.draw.polygon(surface, Colors.BLACK, nose_points)
            
            # 牙齒
            teeth_y = center_y + size//6
            teeth_width = 3
            teeth_height = 4
            for i in range(-2, 3):
                tooth_x = center_x + i * (teeth_width + 2)
                pygame.draw.rect(surface, skull_color, 
                               (tooth_x - teeth_width//2, teeth_y, 
                                teeth_width, teeth_height))
                pygame.draw.rect(surface, Colors.BLACK, 
                               (tooth_x - teeth_width//2, teeth_y, 
                                teeth_width, teeth_height), 1)

        elif emoji_type == 'boots':
            # 繪製精美鞋子
            boots_color = (139, 69, 19)  # 棕色
            sole_color = (80, 40, 20)    # 深棕色
            
            # 鞋子主體
            boot_rect = pygame.Rect(center_x - size//3, center_y - size//4, 
                                   size*2//3, size//2)
            pygame.draw.ellipse(surface, boots_color, boot_rect)
            pygame.draw.ellipse(surface, Colors.BLACK, boot_rect, 2)
            
            # 鞋底
            sole_rect = pygame.Rect(center_x - size//3, center_y + size//6, 
                                  size*2//3, size//8)
            pygame.draw.rect(surface, sole_color, sole_rect)
            pygame.draw.rect(surface, Colors.BLACK, sole_rect, 1)
            
            # 鞋帶（如果是運動鞋風格）
            if emoji_type == 'speed_boots':
                lace_color = Colors.WHITE
                # 繪製鞋帶孔
                for i in range(3):
                    hole_y = center_y - size//6 + i * 8
                    pygame.draw.circle(surface, Colors.BLACK, 
                                     (center_x - 8, hole_y), 2)
                    pygame.draw.circle(surface, Colors.BLACK, 
                                     (center_x + 8, hole_y), 2)
                
                # 繪製鞋帶
                pygame.draw.lines(surface, lace_color, False, [
                    (center_x - 8, center_y - size//6),
                    (center_x + 8, center_y - size//6 + 8),
                    (center_x - 8, center_y - size//6 + 16)
                ], 2)


        elif emoji_type == 'dragon':
            # 繪製精美龍頭
            dragon_color = (150, 50, 50)
            scale_color = (180, 60, 60)
            
            # 龍頭主體
            head_points = [
                (center_x, y + size//6),  # 頂部
                (center_x - size//3, center_y),  # 左側
                (center_x - size//4, y + size*2//3),  # 左下
                (center_x, y + size*3//4),  # 底部
                (center_x + size//4, y + size*2//3),  # 右下
                (center_x + size//3, center_y),  # 右側
            ]
            pygame.draw.polygon(surface, dragon_color, head_points)
            
            # 龍角
            horn_color = (255, 255, 200)
            # 左角
            pygame.draw.polygon(surface, horn_color, [
                (center_x - size//6, y + size//5),
                (center_x - size//4, y + 2),
                (center_x - size//8, y + size//4)
            ])
            # 右角
            pygame.draw.polygon(surface, horn_color, [
                (center_x + size//6, y + size//5),
                (center_x + size//4, y + 2),
                (center_x + size//8, y + size//4)
            ])
            
            # 眼睛（發光）
            eye_y = center_y - size//8
            # 眼睛光暈
            for i in range(3):
                glow_size = 6 - i * 2
                glow_alpha = 100 - i * 30
                glow_color = (*Colors.NEON_ORANGE, glow_alpha)
                glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, glow_color, 
                                 (glow_size, glow_size), glow_size)
                surface.blit(glow_surface, 
                           (center_x - size//5 - glow_size, eye_y - glow_size))
                surface.blit(glow_surface, 
                           (center_x + size//5 - glow_size, eye_y - glow_size))
            
            # 眼睛核心
            pygame.draw.circle(surface, Colors.NEON_ORANGE, 
                             (center_x - size//5, eye_y), 3)
            pygame.draw.circle(surface, Colors.NEON_ORANGE, 
                             (center_x + size//5, eye_y), 3)
            
            # 鼻孔（噴煙效果）
            nostril_y = center_y + size//6
            pygame.draw.ellipse(surface, Colors.BLACK, 
                              (center_x - size//8 - 2, nostril_y, 4, 6))
            pygame.draw.ellipse(surface, Colors.BLACK, 
                              (center_x + size//8 - 2, nostril_y, 4, 6))
            
            # 鱗片細節
            for i in range(3):
                scale_y = y + size//3 + i * 5
                pygame.draw.arc(surface, scale_color, 
                               (center_x - size//4, scale_y, size//2, 8), 
                               0, math.pi, 2)

class AssetManager:
    """資源管理器"""
    
    def __init__(self):
        self.images = {}
        self.sounds = {}
        self.fonts = FontManager()
        self.emoji_manager = EmojiManager()
        self._preload_common_emojis()
        self._load_assets()
    
    def _preload_common_emojis(self):
            """預載入常用的emoji"""
            common_emojis = ['🧙', '💀', '👹', '👺', '🐉', '👿', '👻', '🗡️', '⚔️', 
                            '🪓', '🔨', '🏹', '⭐', '🦺', '🛡️', '⛑️', '💎', 
                            '🧪', '💙', '💚', '💛', '📜', '📋', '📃', '💍', 
                            '🏅', '🪙', '🪜']
            
            # 預載入不同大小的emoji
            for size in [32, 48, 64]:
                self.emoji_manager.preload_emojis(common_emojis, size)

    def _load_assets(self):
        """載入所有遊戲資源"""
        Path("assets/images").mkdir(parents=True, exist_ok=True)
        Path("assets/sounds").mkdir(parents=True, exist_ok=True)
        
        self._load_images()
        self._load_sounds()
    
    def _load_images(self):
        """載入圖片資源，如果不存在則創建精美占位符"""
        image_assets = {
            # 角色
            'player': {'color': Colors.NEON_BLUE, 'emoji': '🧙', 'text': "勇", 'size': TILE_SIZE, 'glow': True},
            'skeleton': {'color': Colors.WHITE, 'emoji': '💀', 'text': "骷", 'size': TILE_SIZE, 'glow': False},
            'orc': {'color': Colors.NEON_GREEN, 'emoji': '👹', 'text': "獸", 'size': TILE_SIZE, 'glow': False},
            'goblin': {'color': Colors.NEON_YELLOW, 'emoji': '👺', 'text': "哥", 'size': TILE_SIZE, 'glow': False},
            'dragon': {'color': Colors.NEON_ORANGE, 'emoji': '🐉', 'text': "龍", 'size': TILE_SIZE, 'glow': True},
            'demon': {'color': Colors.NEON_PINK, 'emoji': '👿', 'text': "魔", 'size': TILE_SIZE, 'glow': True},
            'lich': {'color': Colors.NEON_PURPLE, 'emoji': '👻', 'text': "巫", 'size': TILE_SIZE, 'glow': True},
            
            # 武器
            'dagger': {'color': Colors.NEON_PURPLE, 'emoji': '🗡️', 'text': "匕", 'size': int(TILE_SIZE * 0.8), 'rarity': 'common'},
            'sword': {'color': Colors.NEON_BLUE, 'emoji': '⚔️', 'text': "劍", 'size': int(TILE_SIZE * 0.8), 'rarity': 'uncommon'},
            'axe': {'color': Colors.NEON_ORANGE, 'emoji': '🪓', 'text': "斧", 'size': int(TILE_SIZE * 0.8), 'rarity': 'uncommon'},
            'mace': {'color': Colors.NEON_PURPLE, 'emoji': '🔨', 'text': "錘", 'size': int(TILE_SIZE * 0.8), 'rarity': 'uncommon'},
            'bow': {'color': Colors.NEON_GREEN, 'emoji': '🏹', 'text': "弓", 'size': int(TILE_SIZE * 0.8), 'rarity': 'common'},
            'legendary_sword': {'color': Colors.NEON_YELLOW, 'emoji': '⭐', 'text': "聖", 'size': int(TILE_SIZE * 0.8), 'rarity': 'legendary'},
            
            # 護甲
            'leather_armor': {'color': Colors.NEON_GREEN, 'emoji': '🦺', 'text': "皮", 'size': int(TILE_SIZE * 0.8), 'rarity': 'common'},
            'chain_mail': {'color': Colors.NEON_BLUE, 'emoji': '🛡️', 'text': "鎖", 'size': int(TILE_SIZE * 0.8), 'rarity': 'uncommon'},
            'plate_armor': {'color': Colors.NEON_PURPLE, 'emoji': '🛡️', 'text': "板", 'size': int(TILE_SIZE * 0.8), 'rarity': 'rare'},
            'shield': {'color': Colors.NEON_CYAN, 'emoji': '🛡️', 'text': "盾", 'size': int(TILE_SIZE * 0.8), 'rarity': 'common'},
            'helmet': {'color': Colors.NEON_ORANGE, 'emoji': '⛑️', 'text': "盔", 'size': int(TILE_SIZE * 0.8), 'rarity': 'common'},
            'legendary_armor': {'color': Colors.NEON_YELLOW, 'emoji': '💎', 'text': "龍", 'size': int(TILE_SIZE * 0.8), 'rarity': 'legendary'},
            
            # 鞋子（在護甲定義後添加）
            'leather_boots': {'color': Colors.NEON_GREEN, 'emoji': '👢', 'text': "皮", 'size': int(TILE_SIZE * 0.8), 'rarity': 'common'},
            'speed_boots': {'color': Colors.NEON_CYAN, 'emoji': '👟', 'text': "疾", 'size': int(TILE_SIZE * 0.8), 'rarity': 'uncommon'},
            'mage_boots': {'color': Colors.NEON_PURPLE, 'emoji': '🥾', 'text': "法", 'size': int(TILE_SIZE * 0.8), 'rarity': 'uncommon'},
            'warrior_boots': {'color': Colors.NEON_ORANGE, 'emoji': '👞', 'text': "戰", 'size': int(TILE_SIZE * 0.8), 'rarity': 'uncommon'},
            'legendary_boots': {'color': Colors.NEON_YELLOW, 'emoji': '⭐', 'text': "神", 'size': int(TILE_SIZE * 0.8), 'rarity': 'legendary'},

            # 藥水 - 全部使用瓶子圖標，顏色對應實際效果
            'red_potion': {'color': Colors.HEALTH_RED, 'emoji': '🧪', 'text': '紅', 'size': int(TILE_SIZE * 0.8), 'bottle': True, 'bottle_color': Colors.HEALTH_RED},
            'blue_potion': {'color': Colors.MANA_BLUE, 'emoji': '🧪', 'text': '藍', 'size': int(TILE_SIZE * 0.8), 'bottle': True, 'bottle_color': Colors.MANA_BLUE},
            'green_potion': {'color': Colors.POISON_GREEN, 'emoji': '☠️', 'text': '毒', 'size': int(TILE_SIZE * 0.8), 'bottle': True, 'bottle_color': Colors.POISON_GREEN},
            'yellow_potion': {'color': Colors.EXP_YELLOW, 'emoji': '💪', 'text': '力', 'size': int(TILE_SIZE * 0.8), 'bottle': True, 'bottle_color': Colors.EXP_YELLOW},
            
            # 卷軸
            'scroll_unidentified': {'color': Colors.UI_TEXT_DARK, 'emoji': '📜', 'text': "?", 'size': int(TILE_SIZE * 0.8), 'scroll': True},
            'scroll_slash': {'color': Colors.NEON_ORANGE, 'emoji': '📜', 'text': "斬", 'size': int(TILE_SIZE * 0.8), 'scroll': True},
            'scroll_fireball': {'color': Colors.HEALTH_RED, 'emoji': '📜', 'text': "火", 'size': int(TILE_SIZE * 0.8), 'scroll': True},
            'scroll_heal': {'color': Colors.NEON_GREEN, 'emoji': '📜', 'text': "癒", 'size': int(TILE_SIZE * 0.8), 'scroll': True},
            'scroll_shield': {'color': Colors.NEON_CYAN, 'emoji': '📜', 'text': "盾", 'size': int(TILE_SIZE * 0.8), 'scroll': True},
            'scroll_lightning': {'color': Colors.NEON_CYAN, 'emoji': '📜', 'text': "電", 'size': int(TILE_SIZE * 0.8), 'scroll': True},
            'scroll_ice': {'color': Colors.NEON_BLUE, 'emoji': '📜', 'text': "冰", 'size': int(TILE_SIZE * 0.8), 'scroll': True},
            'scroll_summon': {'color': Colors.NEON_YELLOW, 'emoji': '📜', 'text': "召", 'size': int(TILE_SIZE * 0.8), 'scroll': True},
            # 保留舊的以便兼容
            'scroll_1': {'color': Colors.NEON_PURPLE, 'emoji': '📜', 'text': "卷", 'size': int(TILE_SIZE * 0.8), 'scroll': True},
            'scroll_2': {'color': Colors.NEON_CYAN, 'emoji': '📋', 'text': "軸", 'size': int(TILE_SIZE * 0.8), 'scroll': True},
            'scroll_3': {'color': Colors.NEON_PINK, 'emoji': '📃', 'text': "書", 'size': int(TILE_SIZE * 0.8), 'scroll': True},
            
            # 其他
            'ring': {'color': Colors.NEON_YELLOW, 'emoji': '💍', 'text': "戒", 'size': int(TILE_SIZE * 0.8), 'ring': True},
            'amulet': {'color': Colors.NEON_CYAN, 'emoji': '🏅', 'text': "符", 'size': int(TILE_SIZE * 0.8), 'amulet': True},
            'gem': {'color': Colors.NEON_PINK, 'emoji': '💎', 'text': "寶", 'size': int(TILE_SIZE * 0.8), 'gem': True},
            'coin': {'color': Colors.EXP_YELLOW, 'emoji': '🪙', 'text': "金", 'size': int(TILE_SIZE * 0.8), 'coin': True},
            
            # 地形
            'floor': {'color': Colors.FLOOR_COLOR, 'text': "", 'size': TILE_SIZE, 'floor': True},
            'wall': {'color': Colors.WALL_COLOR, 'text': "", 'size': TILE_SIZE, 'wall': True},
            'stairs': {'color': Colors.STAIRS_COLOR, 'emoji': '🪜', 'text': "梯", 'size': TILE_SIZE, 'stairs': True}
        }
        
        for key, info in image_assets.items():
            info['key'] = key  # 添加 key 到 info 字典中
            self.images[key] = self._create_enhanced_placeholder(info)

    def _create_enhanced_placeholder(self, info):
        """創建增強版占位符圖像（改進的圖標系統）"""
        size = info['size']
        surface = pygame.Surface((size, size), pygame.SRCALPHA).convert_alpha()
        
        key = info.get('key', '')
        
        # 地形特殊處理
        if info.get('floor'):
            surface.fill(info['color'])
            # 添加石磚紋理
            for y in range(0, size, 16):
                for x in range(0, size, 16):
                    rect = pygame.Rect(x, y, 15, 15)
                    pygame.draw.rect(surface, Colors.FLOOR_HIGHLIGHT, rect, 1)
            return surface
        elif info.get('wall'):
            surface.fill(info['color'])
            # 添加磚塊紋理
            for y in range(0, size, 12):
                for x in range(0, size, 16):
                    offset = 8 if (y // 12) % 2 else 0
                    rect = pygame.Rect(x + offset, y, 14, 10)
                    pygame.draw.rect(surface, Colors.WALL_HIGHLIGHT, rect, 1)
            return surface
        elif info.get('stairs'):
            # 樓梯背景
            surface.fill(info['color'])
            step_height = size // 6
            for i in range(6):
                y = i * step_height
                color = tuple(max(0, c - i * 20) for c in info['color'])
                pygame.draw.rect(surface, color, (i * 4, y, size - i * 8, step_height))
                pygame.draw.rect(surface, Colors.BLACK, (i * 4, y, size - i * 8, step_height), 2)
            return surface
        
        # 物品和角色的處理
        center = size // 2
        radius = int(size * 0.45)
        
        # 稀有度光效
        rarity = info.get('rarity', 'common')
        if rarity == 'legendary':
            # 金色光環
            for i in range(5):
                glow_surface = pygame.Surface((size, size), pygame.SRCALPHA)
                alpha = max(0, min(255, 80 - i * 15))
                glow_color = (*Colors.NEON_YELLOW, alpha)
                pygame.gfxdraw.filled_circle(glow_surface, center, center, radius + i * 4, glow_color)
                surface.blit(glow_surface, (0, 0))
        elif rarity == 'epic':
            # 紫色光環
            for i in range(3):
                glow_surface = pygame.Surface((size, size), pygame.SRCALPHA)
                alpha = max(0, min(255, 60 - i * 15))
                glow_color = (*Colors.NEON_PURPLE, alpha)
                pygame.gfxdraw.filled_circle(glow_surface, center, center, radius + i * 3, glow_color)
                surface.blit(glow_surface, (0, 0))
        elif rarity == 'rare':
            # 藍色光環
            glow_surface = pygame.Surface((size, size), pygame.SRCALPHA)
            glow_color = (*Colors.NEON_BLUE, 40)
            pygame.gfxdraw.filled_circle(glow_surface, center, center, radius + 3, glow_color)
            surface.blit(glow_surface, (0, 0))
        
        # 背景圓形
        bg_color = info['color']
        pygame.gfxdraw.filled_circle(surface, center, center, radius, bg_color)
        
        # 內圈邊框
        pygame.gfxdraw.circle(surface, center, center, radius, Colors.BLACK)
        pygame.gfxdraw.circle(surface, center, center, radius - 1, Colors.UI_BORDER)
        
        # 特殊處理藥水瓶
        if info.get('bottle') and key in ['red_potion', 'blue_potion', 'green_potion', 'yellow_potion']:
            self._draw_potion_bottle(surface, center, size, info.get('bottle_color', info['color']))
        else:
            # 嘗試渲染emoji
            emoji = info.get('emoji', '')
            emoji_rendered = False
            
            if emoji and hasattr(self, 'emoji_manager'):
                emoji_surface = self.emoji_manager.render_emoji(emoji, int(size * 0.8))
                if emoji_surface:
                    emoji_rect = emoji_surface.get_rect(center=(center, center))
                    surface.blit(emoji_surface, emoji_rect)
                    emoji_rendered = True
            
            if not emoji_rendered and emoji and self.fonts.can_render_emoji():
                try:
                    emoji_size = int(size * 0.7)
                    emoji_surface = self.fonts.render_text(emoji, emoji_size, Colors.WHITE)
                    if emoji_surface.get_width() > 0 and emoji_surface.get_height() > 0:
                        emoji_rect = emoji_surface.get_rect(center=(center, center))
                        surface.blit(emoji_surface, emoji_rect)
                        emoji_rendered = True
                except:
                    pass
            
            # 如果emoji渲染失敗，使用圖形化替代方案
            if not emoji_rendered:
                self._draw_fallback_icon(surface, key, info, center, size, radius)
        
        # 添加光澤效果
        if info.get('glow') or rarity in ['epic', 'legendary']:
            gloss_surface = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.gfxdraw.filled_ellipse(gloss_surface, center, int(center * 0.7), 
                                        int(radius * 0.8), int(radius * 0.4), 
                                        (*Colors.WHITE, 30))
            surface.blit(gloss_surface, (0, 0))
        
        return surface

    def _draw_potion_bottle(self, surface, center, size, color):
        """繪製藥水瓶圖標"""
        # 瓶身主體
        bottle_width = size // 3
        bottle_height = size // 2
        bottle_x = center - bottle_width // 2
        bottle_y = center - bottle_height // 3
        
        # 瓶身（圓形底部）
        bottle_rect = pygame.Rect(bottle_x, bottle_y, bottle_width, bottle_height)
        pygame.draw.ellipse(surface, (*Colors.WHITE, 180), bottle_rect)
        pygame.draw.ellipse(surface, Colors.BLACK, bottle_rect, 2)
        
        # 瓶頸
        neck_width = bottle_width // 2
        neck_height = size // 6
        neck_x = center - neck_width // 2
        neck_y = bottle_y - neck_height + 2
        pygame.draw.rect(surface, (*Colors.WHITE, 180), (neck_x, neck_y, neck_width, neck_height))
        pygame.draw.rect(surface, Colors.BLACK, (neck_x, neck_y, neck_width, neck_height), 2)
        
        # 瓶塞
        cork_width = int(neck_width * 1.2)
        cork_height = size // 10
        cork_x = center - cork_width // 2
        cork_y = neck_y - cork_height + 2
        pygame.draw.rect(surface, (139, 90, 43), (cork_x, cork_y, cork_width, cork_height))
        pygame.draw.rect(surface, Colors.BLACK, (cork_x, cork_y, cork_width, cork_height), 1)
        
        # 液體（在瓶子裡）
        liquid_rect = pygame.Rect(bottle_x + 3, bottle_y + bottle_height // 3, 
                                bottle_width - 6, bottle_height // 2)
        pygame.draw.ellipse(surface, (*color, 200), liquid_rect)
        
        # 高光
        highlight_rect = pygame.Rect(bottle_x + 5, bottle_y + 5, 
                                bottle_width // 3, bottle_height // 3)
        pygame.draw.ellipse(surface, (*Colors.WHITE, 150), highlight_rect)

    def _draw_fallback_icon(self, surface, key, info, center, size, radius):
        """繪製備用圖標"""
        if key == 'player':
            # 繪製法師帽子和鬍子
            hat_color = Colors.NEON_BLUE
            pygame.gfxdraw.filled_trigon(surface, center, center - radius // 2,
                                        center - radius // 3, center + radius // 4,
                                        center + radius // 3, center + radius // 4,
                                        hat_color)
            # 臉
            face_radius = radius // 3
            pygame.gfxdraw.filled_circle(surface, center, center, face_radius, Colors.WHITE)
            # 眼睛
            pygame.gfxdraw.filled_circle(surface, center - face_radius // 3, center - face_radius // 4, 2, Colors.BLACK)
            pygame.gfxdraw.filled_circle(surface, center + face_radius // 3, center - face_radius // 4, 2, Colors.BLACK)
            # 鬍子
            pygame.draw.arc(surface, Colors.WHITE, 
                        (center - face_radius // 2, center, face_radius, face_radius // 2), 
                        0, math.pi, 3)
        
        elif key == 'skeleton':
            EmojiRenderer.draw_emoji(surface, 'skull', 0, 0, size)
        
        elif key in ['sword', 'dagger', 'axe', 'mace', 'bow', 'legendary_sword']:
            EmojiRenderer.draw_emoji(surface, 'sword', 0, 0, size)
        
        elif key in ['shield', 'leather_armor', 'chain_mail', 'plate_armor', 'helmet', 'legendary_armor']:
            EmojiRenderer.draw_emoji(surface, 'shield', 0, 0, size)
        
        elif key == 'coin':
            EmojiRenderer.draw_emoji(surface, 'coin', 0, 0, size)
        
        elif key == 'dragon':
            EmojiRenderer.draw_emoji(surface, 'dragon', 0, 0, size)
        
        else:
            # 預設：顯示文字
            text_fallback_map = {
                'orc': '獸',
                'goblin': '妖',
                'demon': '魔',
                'lich': '巫',
                'scroll_1': '卷',
                'scroll_2': '書',
                'scroll_3': '符',
                'ring': '戒',
                'amulet': '符',
                'gem': '寶',
                # 添加鞋子備用文字
                'leather_boots': '靴',
                'speed_boots': '鞋',
                'mage_boots': '履',
                'warrior_boots': '甲',
                'legendary_boots': '行',
            }
            
            fallback_text = text_fallback_map.get(key, info.get('text', '?'))
            if fallback_text:
                font_size = 22 if len(fallback_text) == 1 else 18
                font = self.fonts.get_font(font_size)
                text_surface = font.render(fallback_text, True, Colors.WHITE)
                text_rect = text_surface.get_rect(center=(center, center))
                
                # 添加文字陰影
                shadow_surface = font.render(fallback_text, True, Colors.BLACK)
                for dx, dy in [(0, 1), (1, 0), (1, 1)]:
                    surface.blit(shadow_surface, (text_rect.x + dx, text_rect.y + dy))
                
                surface.blit(text_surface, text_rect)

    def _load_sounds(self):
        """載入音效資源"""
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            
            # 創建簡單的音效占位符
            self.sounds['hit_sound'] = None
            self.sounds['pickup_sound'] = None
            self.sounds['level_up_sound'] = None
            self.sounds['death_sound'] = None
            self.sounds['menu_sound'] = None
            self.sounds['skill_sound'] = None
            self.sounds['critical_sound'] = None
        except Exception as e:
            print(f"音效載入失敗: {e}")
            for key in ['hit_sound', 'pickup_sound', 'level_up_sound', 'death_sound', 
                       'menu_sound', 'skill_sound', 'critical_sound']:
                self.sounds[key] = None
    
    def get_image(self, key: str):
        """獲取圖片"""
        return self.images.get(key)
    
    def play_sound(self, key: str, volume: float = 1.0):
        """播放音效"""
        sound = self.sounds.get(key)
        if sound and sound is not None:
            sound.set_volume(volume)
            sound.play()
    
    def play_music(self, loop=-1):
        """播放背景音樂"""
        pass

class MessageLog:
    """訊息日誌系統"""
    
    def __init__(self):
        self.messages = []
        self.scroll_offset = 0  # 新增：滾動偏移量
        self.max_display_messages = 8  # 新增：最大顯示訊息數（從15減少到8）
        # emoji文字映射表
        self.emoji_text_map = {
            '⚔️': '[劍]',
            '👊': '[拳]',
            '💥': '[爆]',
            '🗡️': '[匕]',
            '💀': '[死]',
            '🎉': '[慶]',
            '❌': '[X]',
            '✨': '[魔]',
            '📦': '[箱]',
            '🔄': '[循]',
            '🧪': '[藥]',
            '📜': '[卷]',
            '🛡️': '[盾]',
            '📤': '[出]',
            '🎒': '[包]',
            '🔍': '[查]',
            '🏆': '[獎]',
            '😀': ':)',
            '😖': ':(',
            '💎': '[鑽]',
            '🪙': '[金]',
            '⛑️': '[盔]',
            '🏹': '[弓]',
            '👹': '[鬼]',
            '👺': '[妖]',
            '🐉': '[龍]',
            '👿': '[魔]',
            '👻': '[靈]',
            '🧙': '[法]',
        }
    
    def _replace_emojis(self, text: str) -> str:
        """替換文字中的emoji為可顯示的文字"""
        result = text
        for emoji, replacement in self.emoji_text_map.items():
            result = result.replace(emoji, replacement)
        return result
    
    def add_message(self, text: str, msg_type: MessageType = MessageType.NORMAL):
        """添加訊息"""
        # 替換emoji
        cleaned_text = self._replace_emojis(text)
        
        message = GameMessage(
            text=cleaned_text,
            msg_type=msg_type,
            timestamp=pygame.time.get_ticks()
        )
        self.messages.append(message)
        
        if len(self.messages) > MAX_LOG_MESSAGES:
            self.messages.pop(0)
        
        # 新訊息時重置滾動位置到底部
        self.scroll_offset = 0
    
    def update(self):
        """更新訊息（處理淡出效果）"""
        current_time = pygame.time.get_ticks()
        for message in self.messages:
            age = current_time - message.timestamp
            if age > MESSAGE_DISPLAY_TIME:
                fade_time = age - MESSAGE_DISPLAY_TIME
                message.fade_alpha = max(0, 255 - int(fade_time * 255 / 3000))
    
    def get_visible_messages(self):
        """獲取可見的訊息"""
        return [msg for msg in self.messages if msg.fade_alpha > 0]
    
    def scroll_up(self):
        """向上滾動（查看較舊的訊息）"""
        visible_messages = self.get_visible_messages()
        if len(visible_messages) > self.max_display_messages:
            max_scroll = len(visible_messages) - self.max_display_messages
            self.scroll_offset = min(self.scroll_offset + 1, max_scroll)
    
    def scroll_down(self):
        """向下滾動（查看較新的訊息）"""
        self.scroll_offset = max(0, self.scroll_offset - 1)
    
    def get_display_messages(self):
        """獲取要顯示的訊息（考慮滾動）"""
        visible_messages = self.get_visible_messages()
        if not visible_messages:
            return []
        
        # 從底部開始顯示（最新的訊息在底部）
        start_index = len(visible_messages) - self.max_display_messages - self.scroll_offset
        end_index = len(visible_messages) - self.scroll_offset
        
        # 確保索引在有效範圍內
        start_index = max(0, start_index)
        end_index = min(len(visible_messages), end_index)
        
        return visible_messages[start_index:end_index]

class TutorialSystem:
    """新手教學系統"""
    
    def __init__(self):
        self.current_step = 0
        self.completed = False
        self.tutorial_steps = [
            {
                'title': '啟程：深淵的呼喚',
                'content': [
                    '歡迎，冒險者。我是你的引路人。',
                    '你的任務是征服這座被稱為 [CONCEPT:深淵地牢] 的無盡迷宮。',
                    '地牢是 [CONCEPT:隨機生成] 的，每一次挑戰都是全新的。',
                    '你的最終目標，是擊敗潛伏在最深處的 [WARN:古老巨龍]！',
                ],
                'hint': '按 [空白鍵] 繼續'
            },
            {
                'title': '介面(HUD)導覽',
                'content': [
                    '螢幕上的資訊是你生存的儀表板：',
                    '下方是你的 [UI:狀態欄]：',
                    '  [CONCEPT:HP(生命值)]：歸零則冒險結束。',
                    '  [CONCEPT:MP(魔力值)]：施放強大技能的能源。',
                    '  [CONCEPT:EXP(經驗值)]：殺敵獲得，集滿即可 [ACTION:升級]。',
                ],
                'hint': '按 [空白鍵] 繼續'
            },
            {
                'title': '介面(HUD)導覽 Pt.2',
                'content': [
                    '螢幕的其他部分：',
                    '左側 [UI:訊息日誌]：記錄戰鬥、拾取等所有事件。按 [KEY:L] 可收起/展開。',
                    '右上方 [UI:小地圖]：描繪你走過的路。紅點是 [WARN:敵人]，黃點是 [CONCEPT:物品]。',
                    '最上方 [UI:資訊欄]：顯示你所在的 [CONCEPT:樓層] 與 [CONCEPT:回合數]。',
                ],
                'hint': '按 [空白鍵] 繼續'
            },
            {
                'title': '即時制動作系統',
                'content': [
                    '本作採用 [CONCEPT:即時制] 系統，而非傳統的回合制。',
                    '不論你移動或原地不動，時間都會流逝，[WARN:敵人會持續行動]！',
                    '你必須快速思考，果斷出擊。',
                ],
                'hint': '按 [空白鍵] 繼續'
            },
            {
                'title': '移動的藝術',
                'content': [
                    '使用 [KEY:W][KEY:A][KEY:S][KEY:D] 或 [KEY:方向鍵] 進行四向移動。',
                    '使用 [KEY:Q][KEY:E][KEY:Z][KEY:C] 進行關鍵的 [CONCEPT:斜向移動]。',
                    '或用 [CONCEPT:滑鼠左鍵] 點擊地面，角色將 [ACTION:自動] 前往。',
                ],
                'hint': '按 [空白鍵] 繼續'
            },
            {
                'title': '戰鬥的基礎',
                'content': [
                    '戰鬥的核心是 [ACTION:「碰撞攻擊」] (Bump Attack)。',
                    '[ACTION:直接移動到敵人所在的格子]，即可自動攻擊牠。',
                    '傷害取決於你的 [CONCEPT:攻擊力]、[CONCEPT:暴擊率] 與敵人的 [CONCEPT:防禦力]。',
                ],
                'hint': '按 [空白鍵] 繼續'
            },
            {
                'title': '打開你的背包',
                'content': [
                    '按下 [KEY:B] 鍵，打開你最重要的 [UI:冒險者背包]。',
                    '這裡分為三個主要區域：',
                    '  左側：[UI:角色裝備欄]。',
                    '  中間：[UI:物品庫存區]。',
                    '  右側：[UI:技能管理面板]。',
                ],
                'hint': '按 [空白鍵] 繼續'
            },
            {
                'title': '背包詳解 (1) - 裝備',
                'content': [
                    '你有 [CONCEPT:7個裝備部位]：武器、護甲、盾牌、頭盔、[CONCEPT:鞋子]、戒指、護符。',
                    '將物品欄的裝備拖曳到左側對應位置，或按 [KEY:空白鍵] 快速裝備。',
                    '有些裝備有特殊效果，例如 [CONCEPT:疾風之靴] 會 [ACTION:增加移速]，',
                    '而 [CONCEPT:戰士重靴] 則會為了防禦而 [WARN:降低移速]！',
                ],
                'hint': '按 [空白鍵] 繼續'
            },
            {
                'title': '背包詳解 (2) - 物品',
                'content': [
                    '在中間的 [UI:物品庫存區]，使用 [KEY:方向鍵] 進行選擇。',
                    '按下 [KEY:空白鍵] [ACTION:使用] 藥水或卷軸。',
                    '按下 [KEY:DELETE] 鍵可以 [ACTION:丟棄] 物品。',
                    '右側的 [UI:詳情面板] 會顯示選中物品的詳細資訊和 [CONCEPT:裝備比較]。',
                ],
                'hint': '按 [空白鍵] 繼續'
            },
            {
                'title': '核心機制：識別',
                'content': [
                    '地牢中的 [CONCEPT:藥水] 和 [CONCEPT:卷軸] 在初次獲得時都是 [WARN:未識別的]。',
                    '例如，一瓶 [CONCEPT:紅色藥水 (?)] 可能是 [CONCEPT:治療藥水]，也可能是 [WARN:劇毒]！',
                    '[ACTION:親自使用一次] 是識別它們的唯一方法。祝你好運！',
                ],
                'hint': '按 [空白鍵] 繼續'
            },
            {
                'title': '核心機制：技能與卷軸',
                'content': [
                    '卷軸的用途是 [ACTION:學習] 或 [ACTION:升級] 技能。',
                    '例如，使用一張 [CONCEPT:火球術卷軸] 會讓你學會 [CONCEPT:火球術]。',
                    '如果你 [WARN:已經學會] 該技能，卷軸 [WARN:不會被消耗]，',
                    '它將被保留，用於之後在 [UI:技能管理] 介面中升級技能。',
                ],
                'hint': '按 [空白鍵] 繼續'
            },
            {
                'title': '背包詳解 (3) - 技能管理',
                'content': [
                    '在背包中按 [KEY:TAB] 切換到 [UI:技能管理] 頁面。',
                    '在這裡，你可以消耗 [CONCEPT:金幣] 和對應的 [CONCEPT:卷軸] 來 [ACTION:升級技能]。',
                    '技能升級後效果會變得極其強大，例如：',
                    '  [CONCEPT:劍刃斬] 可能會獲得 [ACTION:擊退] 或 [ACTION:流血] 效果。',
                    '  [CONCEPT:治癒術] 在高級時甚至能 [ACTION:解除負面狀態]！',
                ],
                'hint': '按 [空白鍵] 繼續'
            },
            {
                'title': '設定你的技能快捷欄',
                'content': [
                    '在 [UI:技能管理] 頁面中，先用 [KEY:方向鍵] 選中一個技能，',
                    '然後按下 [KEY:1]、[KEY:2]、[KEY:3] 或 [KEY:4] 鍵，',
                    '即可將該技能綁定到對應的快捷鍵上。',
                    '在戰鬥中，按下數字鍵即可快速施放！',
                ],
                'hint': '按 [空白鍵] 繼續'
            },
            {
                'title': '地牢的法則',
                'content': [
                    '地牢越深，敵人越強大。',
                    '在第5層後，你會遇到 [WARN:深淵惡魔]。',
                    '在第8層後，強大的 [WARN:巫妖王] 將會現身。',
                    '發光的 [CONCEPT:Boss級敵人] 會掉落更好的寶物！',
                ],
                'hint': '按 [空白鍵] 繼續'
            },
            {
                'title': '終極指令清單',
                'content': [
                    '[KEY:B]：背包',
                    '[KEY:F]：拾取',
                    '[KEY:R]：休息 (附近無敵人時)',
                    '[KEY:L]：切換訊息日誌',
                    '[KEY:ESC]：暫停 / 選單',
                    '[KEY:F5]/[KEY:F9]：快速存檔/讀檔',
                    '[KEY:F11]：全螢幕切換',
                ],
                'hint': '按 [空白鍵] 繼續'
            },
            {
                'title': '最後的叮嚀',
                'content': [
                    '在 [UI:主選單] 可以查看你的 [CONCEPT:成就] 和 [CONCEPT:統計數據]。',
                    '[WARN:不要被敵人包圍]，利用地形和斜向移動。',
                    '合理分配你的技能點和資源。',
                    '現在，去創造你的傳說吧！深淵等待你的征服。',
                ],
                'hint': '按 [空白鍵] 結束教學'
            },
        ]

    def get_current_step(self):
        """獲取當前教學步驟"""
        if self.completed or self.current_step >= len(self.tutorial_steps):
            return None
        return self.tutorial_steps[self.current_step]
    
    def next_step(self):
        """進入下一個教學步驟"""
        self.current_step += 1
        if self.current_step >= len(self.tutorial_steps):
            self.completed = True
    
    def skip_tutorial(self):
        """跳過教學"""
        self.completed = True
# ============================================================================
# 粒子系統 - 修復版
# ============================================================================

class Particle:
    """單個粒子"""
    def __init__(self, x, y, vx, vy, color, life, size=3, gravity=0, fade=True):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.gravity = gravity
        self.fade = fade
        self.trail = []
    
    def update(self, dt):
        """更新粒子"""
        # 保存軌跡
        if len(self.trail) < 5:
            self.trail.append((self.x, self.y))
        else:
            self.trail.pop(0)
            self.trail.append((self.x, self.y))
        
        # 更新位置
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        
        # 減少生命值
        self.life -= dt
    
    def draw(self, screen, camera_offset):
        """繪製粒子（修復版）"""
        if self.life <= 0:
            return
        
        # 計算透明度
        alpha = 255
        if self.fade:
            alpha = int(255 * (self.life / self.max_life))
            alpha = max(0, min(255, alpha))
        
        # 處理顏色 - 修復顏色處理邏輯
        current_color = self.color
        
        # 如果是顏色列表（用於漸變效果）
        if isinstance(current_color, list) and len(current_color) > 0:
            # 計算當前應該使用的顏色索引
            index = int((1 - self.life / self.max_life) * (len(current_color) - 1))
            index = max(0, min(len(current_color) - 1, index))
            current_color = current_color[index]
        
        # 確保顏色是正確的格式
        if isinstance(current_color, (list, tuple)):
            # 處理嵌套的情況（如果顏色意外地被雙重包裝）
            while isinstance(current_color, (list, tuple)) and len(current_color) > 0 and isinstance(current_color[0], (list, tuple)):
                current_color = current_color[0]
            
            # 提取RGB值
            if len(current_color) >= 3:
                try:
                    r = int(current_color[0]) if not isinstance(current_color[0], (list, tuple)) else 255
                    g = int(current_color[1]) if not isinstance(current_color[1], (list, tuple)) else 255
                    b = int(current_color[2]) if not isinstance(current_color[2], (list, tuple)) else 255
                    base_color = (r, g, b)
                except (ValueError, TypeError):
                    base_color = (255, 255, 255)  # 預設白色
            else:
                base_color = (255, 255, 255)
        else:
            base_color = (255, 255, 255)
        
        # 繪製軌跡
        for i, (tx, ty) in enumerate(self.trail):
            trail_alpha = int(alpha * (i / len(self.trail)))
            trail_alpha = max(0, min(255, trail_alpha))
            trail_x = int(tx - camera_offset.x)
            trail_y = int(ty - camera_offset.y)
            trail_size = max(1, int(self.size * (i / len(self.trail))))
            
            if 0 <= trail_x <= WINDOW_WIDTH and 0 <= trail_y <= WINDOW_HEIGHT:
                trail_color = (*base_color, trail_alpha)
                trail_surface = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
                pygame.gfxdraw.filled_circle(trail_surface, trail_size, trail_size, trail_size, trail_color)
                screen.blit(trail_surface, (trail_x - trail_size, trail_y - trail_size))
        
        # 繪製粒子本體
        screen_x = int(self.x - camera_offset.x)
        screen_y = int(self.y - camera_offset.y)
        
        if 0 <= screen_x <= WINDOW_WIDTH and 0 <= screen_y <= WINDOW_HEIGHT:
            final_color = (*base_color, alpha)
            particle_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.gfxdraw.filled_circle(particle_surface, self.size, self.size, self.size, final_color)
            screen.blit(particle_surface, (screen_x - self.size, screen_y - self.size))

class EnhancedParticle(Particle):
    """增強版粒子，支援更多動畫效果"""
    def __init__(self, x, y, vx, vy, color, life, size=3, gravity=0, fade=True,
                 particle_type="normal", rotation=0, rotation_speed=0, scale_speed=0,
                 glow=False, trail_length=5):
        super().__init__(x, y, vx, vy, color, life, size, gravity, fade)
        self.particle_type = particle_type
        self.rotation = rotation
        self.rotation_speed = rotation_speed
        self.initial_size = size
        self.scale_speed = scale_speed
        self.glow = glow
        self.trail_length = trail_length
        self.pulse_phase = random.uniform(0, math.pi * 2)
        
    def update(self, dt):
        """更新增強粒子"""
        super().update(dt)
        
        # 旋轉
        self.rotation += self.rotation_speed * dt
        
        # 縮放
        if self.scale_speed != 0:
            scale_factor = 1 + (1 - self.life / self.max_life) * self.scale_speed
            self.size = max(1, int(self.initial_size * scale_factor))
        
        # 脈衝效果
        if self.particle_type == "pulse":
            pulse = abs(math.sin(self.pulse_phase + pygame.time.get_ticks() * 0.01))
            self.size = int(self.initial_size * (0.8 + pulse * 0.4))
    
    def draw_enhanced(self, screen, camera_offset):
        """繪製增強效果"""
        if self.life <= 0:
            return
        
        screen_x = int(self.x - camera_offset.x)
        screen_y = int(self.y - camera_offset.y)
        
        if not (0 <= screen_x <= WINDOW_WIDTH and 0 <= screen_y <= WINDOW_HEIGHT):
            return
        
        # 計算透明度
        alpha = 255
        if self.fade:
            alpha = int(255 * (self.life / self.max_life))
            alpha = max(0, min(255, alpha))
        
        # 獲取基礎顏色
        base_color = self.color
        if isinstance(base_color, list):
            index = int((1 - self.life / self.max_life) * (len(base_color) - 1))
            index = max(0, min(len(base_color) - 1, index))
            base_color = base_color[index]
        
        # 繪製光暈效果
        if self.glow:
            glow_surface = pygame.Surface((self.size * 4, self.size * 4), pygame.SRCALPHA)
            for i in range(3):
                glow_radius = self.size + i * self.size // 2
                glow_alpha = alpha // (i + 2)
                glow_color = (*base_color[:3], glow_alpha)
                pygame.gfxdraw.filled_circle(glow_surface, self.size * 2, self.size * 2, 
                                            glow_radius, glow_color)
            screen.blit(glow_surface, (screen_x - self.size * 2, screen_y - self.size * 2))
        
        # 繪製主體
        if self.particle_type == "star":
            # 星形粒子
            points = []
            for i in range(10):
                angle = self.rotation + i * math.pi / 5
                radius = self.size if i % 2 == 0 else self.size // 2
                px = screen_x + radius * math.cos(angle)
                py = screen_y + radius * math.sin(angle)
                points.append((px, py))
            
            if len(points) > 2:
                particle_color = (*base_color[:3], alpha)
                pygame.gfxdraw.filled_polygon(screen, points, particle_color)
        
        elif self.particle_type == "ring":
            # 環形粒子
            if self.size > 3:
                outer_color = (*base_color[:3], alpha)
                inner_color = (*base_color[:3], alpha // 2)
                pygame.gfxdraw.filled_circle(screen, screen_x, screen_y, self.size, outer_color)
                pygame.gfxdraw.filled_circle(screen, screen_x, screen_y, 
                                            max(1, self.size - 3), (*Colors.BLACK, alpha))
        
        elif self.particle_type == "spark":
            # 火花粒子（帶尾跡的線條）
            if len(self.trail) > 1:
                trail_points = [(int(tx - camera_offset.x), int(ty - camera_offset.y)) 
                               for tx, ty in self.trail]
                for i in range(len(trail_points) - 1):
                    trail_alpha = int(alpha * (i / len(trail_points)))
                    trail_color = (*base_color[:3], trail_alpha)
                    pygame.draw.line(screen, trail_color, trail_points[i], 
                                   trail_points[i + 1], max(1, self.size - i))
        
        else:
            # 普通圓形粒子
            particle_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            final_color = (*base_color[:3], alpha)
            pygame.gfxdraw.filled_circle(particle_surface, self.size, self.size, 
                                        self.size, final_color)
            screen.blit(particle_surface, (screen_x - self.size, screen_y - self.size))

class ParticleSystem:
    """粒子系統"""
    
    def __init__(self):
        self.particles = []
        self.text_particles = []
        self.animation_time = 0  # 新增這個屬性
    
    def add_damage_text(self, position: Position, text: str, color=None, critical=False):
        """添加傷害數字"""
        if color is None:
            color = Colors.HEALTH_RED
        size = 20 if not critical else 28
        particle = {
            'pos': [position.x * TILE_SIZE + TILE_SIZE // 2, position.y * TILE_SIZE],
            'vel': [random.randint(-20, 20), -35],
            'text': str(text),
            'color': color,
            'life': 100,
            'max_life': 100,
            'size': size,
            'critical': critical
        }
        self.text_particles.append(particle)
    
    def add_heal_text(self, position: Position, heal: int):
        """添加治療數字"""
        self.add_damage_text(position, f"+{heal}", Colors.NEON_GREEN)
    
    def add_exp_text(self, position: Position, exp: int):
        """添加經驗值數字"""
        self.add_damage_text(position, f"+{exp} EXP", Colors.EXP_YELLOW)
    
    def add_level_up_effect(self, position: Position):
        """添加升級特效"""
        # 光柱效果
        for i in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            self.particles.append(Particle(
                position.x * TILE_SIZE + TILE_SIZE // 2,
                position.y * TILE_SIZE + TILE_SIZE // 2,
                math.cos(angle) * speed,
                math.sin(angle) * speed - 100,
                Colors.PARTICLE_HEAL,
                2.0,
                size=4,
                gravity=-200
            ))
        
        # 星星效果
        for i in range(8):
            angle = i * math.pi / 4
            self.particles.append(Particle(
                position.x * TILE_SIZE + TILE_SIZE // 2,
                position.y * TILE_SIZE + TILE_SIZE // 2,
                math.cos(angle) * 100,
                math.sin(angle) * 100,
                [Colors.EXP_YELLOW, Colors.WHITE],
                1.5,
                size=6
            ))
    
    def add_hit_effect(self, position: Position, critical=False):
        """添加擊中效果"""
        count = 15 if not critical else 30
        colors = Colors.PARTICLE_FIRE if not critical else [Colors.NEON_ORANGE, Colors.NEON_YELLOW, Colors.WHITE]
        
        for i in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 200)
            self.particles.append(Particle(
                position.x * TILE_SIZE + TILE_SIZE // 2,
                position.y * TILE_SIZE + TILE_SIZE // 2,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                colors,
                0.8,
                size=random.randint(2, 5),
                gravity=200
            ))
    
    def add_skill_effect(self, position: Position, skill_type: str):
        """添加技能效果"""
        if skill_type == "fireball":
            # 火球效果
            for i in range(50):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(100, 300)
                self.particles.append(Particle(
                    position.x * TILE_SIZE + TILE_SIZE // 2,
                    position.y * TILE_SIZE + TILE_SIZE // 2,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    Colors.PARTICLE_FIRE,
                    1.5,
                    size=random.randint(3, 8),
                    gravity=100
                ))
        elif skill_type == "heal":
            # 治療效果
            for i in range(30):
                angle = random.uniform(0, 2 * math.pi)
                radius = random.uniform(0, TILE_SIZE)
                x = position.x * TILE_SIZE + TILE_SIZE // 2 + math.cos(angle) * radius
                y = position.y * TILE_SIZE + TILE_SIZE // 2 + math.sin(angle) * radius
                self.particles.append(Particle(
                    x, y,
                    0, -50,
                    Colors.PARTICLE_HEAL,
                    2.0,
                    size=random.randint(2, 4),
                    gravity=-50
                ))
        elif skill_type == "shield":
            # 護盾效果
            for i in range(40):
                angle = i * math.pi * 2 / 40
                radius = TILE_SIZE
                x = position.x * TILE_SIZE + TILE_SIZE // 2 + math.cos(angle) * radius
                y = position.y * TILE_SIZE + TILE_SIZE // 2 + math.sin(angle) * radius
                self.particles.append(Particle(
                    x, y,
                    math.cos(angle) * 20,
                    math.sin(angle) * 20,
                    Colors.PARTICLE_ICE,
                    1.5,
                    size=3
                ))
        elif skill_type == "lightning":
            # 閃電鏈效果
            for i in range(20):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(200, 400)
                self.particles.append(Particle(
                    position.x * TILE_SIZE + TILE_SIZE // 2,
                    position.y * TILE_SIZE + TILE_SIZE // 2,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    [Colors.NEON_CYAN, Colors.WHITE],
                    0.8,
                    size=random.randint(2, 5),
                    gravity=0
                ))
                
            # 電弧效果
            for i in range(5):
                start_angle = random.uniform(0, 2 * math.pi)
                end_angle = start_angle + random.uniform(0.5, 1.5)
                for j in range(10):
                    t = j / 10.0
                    angle = start_angle + (end_angle - start_angle) * t
                    radius = random.uniform(TILE_SIZE, TILE_SIZE * 2)
                    x = position.x * TILE_SIZE + TILE_SIZE // 2 + math.cos(angle) * radius
                    y = position.y * TILE_SIZE + TILE_SIZE // 2 + math.sin(angle) * radius
                    self.particles.append(Particle(
                        x, y,
                        random.randint(-50, 50),
                        random.randint(-50, 50),
                        Colors.NEON_CYAN,
                        0.5,
                        size=2
                    ))
                    
        elif skill_type == "ice_spike" or skill_type == "ice":
            # 冰錐術效果
            for i in range(30):
                # 冰錐從地面向上生長
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(0, TILE_SIZE * 1.5)
                x = position.x * TILE_SIZE + TILE_SIZE // 2 + math.cos(angle) * distance
                y = position.y * TILE_SIZE + TILE_SIZE // 2 + math.sin(angle) * distance
                
                self.particles.append(Particle(
                    x, y + TILE_SIZE,  # 從下方開始
                    0,
                    -random.uniform(100, 300),  # 向上噴射
                    Colors.PARTICLE_ICE,
                    1.5,
                    size=random.randint(3, 7),
                    gravity=-50  # 反重力效果
                ))
                
            # 冰晶效果
            for i in range(20):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(50, 150)
                self.particles.append(Particle(
                    position.x * TILE_SIZE + TILE_SIZE // 2,
                    position.y * TILE_SIZE + TILE_SIZE // 2,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    [Colors.NEON_BLUE, Colors.WHITE],
                    2.0,
                    size=random.randint(2, 4),
                    gravity=100
                ))
                
        elif skill_type == "summon":
            # 召喚術效果 - 魔法陣
            center_x = position.x * TILE_SIZE + TILE_SIZE // 2
            center_y = position.y * TILE_SIZE + TILE_SIZE // 2
            
            # 魔法陣光環
            for ring in range(3):
                radius = (ring + 1) * TILE_SIZE // 2
                for i in range(40):
                    angle = i * math.pi * 2 / 40
                    x = center_x + math.cos(angle) * radius
                    y = center_y + math.sin(angle) * radius
                    
                    self.particles.append(Particle(
                        x, y,
                        0,
                        -50,
                        [Colors.NEON_PURPLE, Colors.NEON_YELLOW],
                        2.0 - ring * 0.3,
                        size=4 - ring,
                        gravity=-30
                    ))
                    
            # 上升的靈魂粒子
            for i in range(50):
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(0, TILE_SIZE * 2)
                x = center_x + math.cos(angle) * distance
                y = center_y + math.sin(angle) * distance
                
                self.particles.append(Particle(
                    x, y,
                    random.randint(-20, 20),
                    -random.uniform(50, 150),
                    [Colors.NEON_PURPLE, Colors.WHITE],
                    3.0,
                    size=random.randint(2, 5),
                    gravity=-50
                ))

    def add_enhanced_skill_effect(self, position: Position, skill_type: str):
        """添加增強版技能特效"""
        x = position.x * TILE_SIZE + TILE_SIZE // 2
        y = position.y * TILE_SIZE + TILE_SIZE // 2
        
        if skill_type == "slash_enhanced":
            # 劍氣波動效果
            for wave in range(3):
                delay = wave * 0.1
                for i in range(40):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(100, 400 - wave * 50)
                    particle = EnhancedParticle(
                        x, y,
                        math.cos(angle) * speed,
                        math.sin(angle) * speed,
                        [Colors.NEON_ORANGE, Colors.NEON_YELLOW, Colors.WHITE],
                        1.5 - delay,
                        size=random.randint(4, 8),
                        gravity=0,
                        particle_type="spark",
                        glow=True,
                        trail_length=10
                    )
                    self.particles.append(particle)
            
            # 中心爆發效果
            for i in range(20):
                angle = i * math.pi * 2 / 20
                particle = EnhancedParticle(
                    x, y,
                    math.cos(angle) * 300,
                    math.sin(angle) * 300,
                    Colors.NEON_ORANGE,
                    1.0,
                    size=10,
                    gravity=0,
                    particle_type="star",
                    rotation_speed=10,
                    scale_speed=-0.5,
                    glow=True
                )
                self.particles.append(particle)
        
        elif skill_type == "fireball_enhanced":
            # 螺旋火焰效果
            for i in range(60):
                t = i / 60.0
                angle = t * math.pi * 4
                radius = t * 50
                px = x + math.cos(angle) * radius
                py = y + math.sin(angle) * radius
                
                particle = EnhancedParticle(
                    px, py,
                    random.randint(-50, 50),
                    random.randint(-100, -50),
                    Colors.PARTICLE_FIRE,
                    2.0,
                    size=random.randint(5, 10),
                    gravity=100,
                    particle_type="normal",
                    scale_speed=1.5,
                    glow=True
                )
                self.particles.append(particle)
            
            # 爆炸環效果
            for ring in range(3):
                delay = ring * 0.2
                for i in range(30):
                    angle = i * math.pi * 2 / 30
                    speed = 200 + ring * 100
                    particle = EnhancedParticle(
                        x, y,
                        math.cos(angle) * speed,
                        math.sin(angle) * speed,
                        [Colors.NEON_ORANGE, Colors.NEON_YELLOW],
                        1.5 - delay,
                        size=8 - ring * 2,
                        gravity=0,
                        particle_type="ring",
                        scale_speed=0.5
                    )
                    self.particles.append(particle)
            
            # 添加爆炸中心的火焰柱效果
            for i in range(40):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(50, 150)
                particle = EnhancedParticle(
                    x, y,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed - 200,  # 向上噴發
                    Colors.PARTICLE_FIRE,
                    2.5,
                    size=random.randint(6, 12),
                    gravity=150,
                    particle_type="normal",
                    scale_speed=2.0,
                    glow=True
                )
                self.particles.append(particle)
        
        elif skill_type == "lightning_enhanced":
            # 電流分支效果
            branches = 8
            for branch in range(branches):
                base_angle = branch * math.pi * 2 / branches
                branch_length = random.randint(100, 200)
                
                # 主電流
                for i in range(20):
                    t = i / 20.0
                    offset = random.randint(-20, 20)
                    bx = x + math.cos(base_angle) * branch_length * t + offset
                    by = y + math.sin(base_angle) * branch_length * t + offset
                    
                    particle = EnhancedParticle(
                        bx, by,
                        random.randint(-30, 30),
                        random.randint(-30, 30),
                        [Colors.NEON_CYAN, Colors.WHITE],
                        0.8,
                        size=random.randint(3, 6),
                        gravity=0,
                        particle_type="spark",
                        glow=True,
                        trail_length=5
                    )
                    self.particles.append(particle)
                
                # 子電流
                if random.random() < 0.5:
                    sub_angle = base_angle + random.uniform(-0.5, 0.5)
                    for i in range(10):
                        t = i / 10.0
                        sx = x + math.cos(base_angle) * branch_length * 0.5
                        sy = y + math.sin(base_angle) * branch_length * 0.5
                        
                        bx = sx + math.cos(sub_angle) * 50 * t
                        by = sy + math.sin(sub_angle) * 50 * t
                        
                        particle = EnhancedParticle(
                            bx, by,
                            random.randint(-20, 20),
                            random.randint(-20, 20),
                            Colors.NEON_CYAN,
                            0.5,
                            size=2,
                            gravity=0,
                            particle_type="normal",
                            glow=True
                        )
                        self.particles.append(particle)
        
        elif skill_type == "heal_enhanced":
            # 螺旋上升治療光環
            for spiral in range(3):
                for i in range(40):
                    t = i / 40.0
                    angle = spiral * math.pi * 2 / 3 + t * math.pi * 4
                    radius = 30 + t * 20
                    
                    px = x + math.cos(angle) * radius
                    py = y + math.sin(angle) * radius - t * 100
                    
                    particle = EnhancedParticle(
                        px, py,
                        0,
                        -50,
                        Colors.PARTICLE_HEAL,
                        2.5,
                        size=random.randint(4, 7),
                        gravity=-100,
                        particle_type="star",
                        rotation_speed=5,
                        glow=True
                    )
                    self.particles.append(particle)
            
            # 光環脈衝
            for i in range(20):
                angle = i * math.pi * 2 / 20
                particle = EnhancedParticle(
                    x + math.cos(angle) * 40,
                    y + math.sin(angle) * 40,
                    math.cos(angle) * 20,
                    math.sin(angle) * 20,
                    [Colors.NEON_GREEN, Colors.WHITE],
                    2.0,
                    size=6,
                    gravity=0,
                    particle_type="pulse",
                    glow=True
                )
                self.particles.append(particle)
        elif skill_type == "ice_spike_enhanced" or skill_type == "ice_enhanced":
            # 增強版冰錐術
            # 冰風暴效果
            for wave in range(5):
                for i in range(30):
                    angle = random.uniform(0, 2 * math.pi)
                    # 螺旋擴散
                    t = wave / 5.0
                    radius = t * TILE_SIZE * 3
                    spiral_angle = angle + t * math.pi * 4
                    
                    px = x + math.cos(spiral_angle) * radius
                    py = y + math.sin(spiral_angle) * radius
                    
                    particle = EnhancedParticle(
                        px, py,
                        math.cos(spiral_angle) * 50,
                        math.sin(spiral_angle) * 50 - 100,
                        Colors.PARTICLE_ICE,
                        3.0 - wave * 0.5,
                        size=random.randint(5, 10),
                        gravity=-100,
                        particle_type="star",
                        rotation_speed=10,
                        glow=True
                    )
                    self.particles.append(particle)
                    
            # 巨大冰柱
            for i in range(8):
                angle = i * math.pi / 4
                distance = TILE_SIZE * 2
                spike_x = x + math.cos(angle) * distance
                spike_y = y + math.sin(angle) * distance
                
                # 冰柱主體
                for j in range(20):
                    height = j * 5
                    particle = EnhancedParticle(
                        spike_x + random.randint(-10, 10),
                        spike_y + TILE_SIZE - height,
                        0,
                        -300,
                        [Colors.NEON_BLUE, Colors.NEON_CYAN, Colors.WHITE],
                        2.0,
                        size=15 - j // 2,
                        gravity=-200,
                        particle_type="normal",
                        scale_speed=-0.5,
                        glow=True
                    )
                    self.particles.append(particle)
                    
        elif skill_type == "summon_enhanced":
            # 增強版召喚術
            # 巨大魔法陣
            for ring in range(5):
                radius = (ring + 1) * TILE_SIZE
                num_points = 60 + ring * 20
                
                for i in range(num_points):
                    angle = i * math.pi * 2 / num_points + self.animation_time * (ring + 1)
                    px = x + math.cos(angle) * radius
                    py = y + math.sin(angle) * radius
                    
                    # 旋轉的符文
                    particle = EnhancedParticle(
                        px, py,
                        math.cos(angle + math.pi/2) * 30,
                        math.sin(angle + math.pi/2) * 30,
                        [Colors.NEON_PURPLE, Colors.NEON_YELLOW, Colors.WHITE],
                        3.0,
                        size=8 - ring,
                        gravity=0,
                        particle_type="star",
                        rotation_speed=5,
                        glow=True
                    )
                    self.particles.append(particle)
                    
            # 召喚門效果
            for i in range(100):
                # 垂直的能量柱
                spread = random.uniform(-TILE_SIZE, TILE_SIZE)
                height = random.uniform(0, TILE_SIZE * 3)
                
                particle = EnhancedParticle(
                    x + spread,
                    y - height,
                    random.randint(-20, 20),
                    -200,
                    [Colors.NEON_PURPLE, Colors.NEON_PINK, Colors.WHITE],
                    4.0,
                    size=random.randint(3, 8),
                    gravity=-300,
                    particle_type="normal",
                    scale_speed=1.0,
                    glow=True,
                    trail_length=10
                )
                self.particles.append(particle)
        
        # 同時播放原始效果作為補充
        self.add_skill_effect(position, skill_type.replace("_enhanced", ""))

    def add_pickup_effect(self, position: Position, item_type: str):
        """添加拾取效果"""
        # 根據物品類型選擇顏色
        if item_type == "gold" or item_type == ItemType.GOLD:
            base_color = Colors.EXP_YELLOW
        elif item_type == "potion" or item_type == ItemType.POTION:
            base_color = Colors.PARTICLE_HEAL[0] if isinstance(Colors.PARTICLE_HEAL, list) else Colors.PARTICLE_HEAL
        else:
            base_color = Colors.NEON_CYAN
        
        # 確保顏色是 tuple 格式
        if isinstance(base_color, list):
            base_color = tuple(base_color)
        
        for i in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(20, 80)
            
            # 創建顏色漸變列表（從基礎顏色到白色）
            color_list = [base_color, Colors.WHITE]
            
            self.particles.append(Particle(
                position.x * TILE_SIZE + TILE_SIZE // 2,
                position.y * TILE_SIZE + TILE_SIZE // 2,
                math.cos(angle) * speed,
                math.sin(angle) * speed - 50,
                color_list,  # 傳遞顏色列表
                1.0,
                size=random.randint(2, 4)
            ))    

    def add_achievement_effect(self, position: Position):
        """添加成就解鎖效果"""
        # 煙花效果
        for burst in range(3):
            delay = burst * 0.3
            for i in range(50):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(100, 300)
                color = random.choice([Colors.EXP_YELLOW, Colors.NEON_PINK, Colors.NEON_CYAN, Colors.NEON_GREEN])
                self.particles.append(Particle(
                    position.x * TILE_SIZE + TILE_SIZE // 2 + random.randint(-20, 20),
                    position.y * TILE_SIZE + TILE_SIZE // 2 + random.randint(-20, 20),
                    math.cos(angle) * speed,
                    math.sin(angle) * speed - 100,
                    [color, Colors.WHITE],
                    2.0 - delay,
                    size=random.randint(3, 6),
                    gravity=150
                ))
    
    def update(self, dt: float):
        # 更新動畫時間
        self.animation_time += dt
        
        # 更新普通粒子
        self.particles = [p for p in self.particles if p.life > 0]
        for particle in self.particles:
            particle.update(dt)
        
        # 更新文字粒子
        for particle in self.text_particles[:]:
            particle['pos'][0] += particle['vel'][0] * dt
            particle['pos'][1] += particle['vel'][1] * dt
            particle['vel'][1] += 35 * dt  
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.text_particles.remove(particle)

    def render(self, screen, camera_offset: Position, asset_manager: AssetManager, settings: GameSettings):
        """渲染粒子"""
        # 根據設定調整粒子數量
        if settings.particle_density == "low":
            particle_limit = len(self.particles) // 3
            text_limit = len(self.text_particles) // 2
        elif settings.particle_density == "medium":
            particle_limit = len(self.particles) // 2
            text_limit = len(self.text_particles)
        else:
            particle_limit = len(self.particles)
            text_limit = len(self.text_particles)
        
        # 渲染普通粒子
        for i, particle in enumerate(self.particles):
            if i >= particle_limit:
                break
            
            # 檢查是否是增強粒子
            if isinstance(particle, EnhancedParticle):
                particle.draw_enhanced(screen, camera_offset)
            else:
                particle.draw(screen, camera_offset)
        
        # 渲染文字粒子
        if settings.show_damage_numbers:
            for i, particle in enumerate(self.text_particles):
                if i >= text_limit:
                    break
                
                alpha = int(255 * (particle['life'] / particle['max_life']))
                
                screen_x = int(particle['pos'][0] - camera_offset.x)
                screen_y = int(particle['pos'][1] - camera_offset.y)
                
                if 0 <= screen_x <= WINDOW_WIDTH and 0 <= screen_y <= WINDOW_HEIGHT:
                    # 暴擊效果
                    if particle.get('critical'):
                        # 外發光
                        for offset in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
                            shadow_surface = asset_manager.fonts.render_text(
                                particle['text'], particle['size'], Colors.NEON_ORANGE
                            )
                            shadow_surface.set_alpha(alpha // 2)
                            screen.blit(shadow_surface, (screen_x + offset[0], screen_y + offset[1]))
                    
                    text_surface = asset_manager.fonts.render_text(
                        particle['text'], particle['size'], particle['color']
                    )
                    
                    if alpha < 255:
                        text_surface.set_alpha(alpha)
                    
                    screen.blit(text_surface, (screen_x, screen_y))

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

class DungeonMap:
    """地牢地圖"""
    
    def __init__(self, width: int, height: int, level: int = 1):
        self.width = width
        self.height = height
        self.level = level
        self.tiles = []
        self.rooms = []
        self.enemies = []
        self.items = []
        self.item_db = ItemDatabase()
        self.explored = [[False for _ in range(width)] for _ in range(height)]
        self.visible = [[False for _ in range(width)] for _ in range(height)]
        self._generate_map()
        # 同步已鑑定的藥水類型
        if hasattr(self, 'player') and hasattr(self.player, 'identified_items'):
            for item_type in self.player.identified_items:
                if item_type.endswith('_potion'):
                    self.item_db.identified_potion_types.add(item_type)        
    
    def _generate_map(self):
        """生成地牢地圖"""
        # 初始化為全牆
        self.tiles = [['wall' for _ in range(self.width)] for _ in range(self.height)]
        
        # 生成房間
        self._generate_rooms()
        
        # 連接房間
        self._connect_rooms()
        
        # 放置樓梯
        self._place_stairs()
        
        # 生成敵人和道具
        self._populate_dungeon()
    
    def _generate_rooms(self):
        """生成房間"""
        room_attempts = 50
        min_room_size = 6
        max_room_size = 15
        
        for _ in range(room_attempts):
            width = random.randint(min_room_size, max_room_size)
            height = random.randint(min_room_size, max_room_size)
            x = random.randint(1, self.width - width - 1)
            y = random.randint(1, self.height - height - 1)
            
            new_room = pygame.Rect(x, y, width, height)
            
            # 檢查重疊
            overlap = False
            for room in self.rooms:
                if new_room.colliderect(room.inflate(3, 3)):
                    overlap = True
                    break
            
            if not overlap:
                self.rooms.append(new_room)
                
                # 挖空房間
                for room_y in range(y, y + height):
                    for room_x in range(x, x + width):
                        self.tiles[room_y][room_x] = 'floor'
                
                # 添加房間裝飾
                if random.random() < 0.3 and len(self.rooms) > 1:
                    self._add_room_features(new_room)
    
    def _add_room_features(self, room):
        """添加房間特徵"""
        # 柱子
        if room.width > 8 and room.height > 8 and random.random() < 0.5:
            for x in range(room.x + 2, room.right - 2, 4):
                for y in range(room.y + 2, room.bottom - 2, 4):
                    self.tiles[y][x] = 'wall'
    
    def _connect_rooms(self):
        """用走廊連接房間"""
        for i in range(len(self.rooms) - 1):
            room1 = self.rooms[i]
            room2 = self.rooms[i + 1]
            
            # 隨機選擇L型走廊的方向
            if random.random() < 0.5:
                # 先水平再垂直
                self._create_horizontal_tunnel(room1.centerx, room2.centerx, room1.centery)
                self._create_vertical_tunnel(room1.centery, room2.centery, room2.centerx)
            else:
                # 先垂直再水平
                self._create_vertical_tunnel(room1.centery, room2.centery, room1.centerx)
                self._create_horizontal_tunnel(room1.centerx, room2.centerx, room2.centery)
    
    def _create_horizontal_tunnel(self, x1: int, x2: int, y: int):
        """創建水平走廊"""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.tiles[y][x] = 'floor'
                # 寬走廊
                if 0 <= y - 1 < self.height:
                    self.tiles[y - 1][x] = 'floor'
                if 0 <= y + 1 < self.height:
                    self.tiles[y + 1][x] = 'floor'
    
    def _create_vertical_tunnel(self, y1: int, y2: int, x: int):
        """創建垂直走廊"""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.tiles[y][x] = 'floor'
                # 寬走廊
                if 0 <= x - 1 < self.width:
                    self.tiles[y][x - 1] = 'floor'
                if 0 <= x + 1 < self.width:
                    self.tiles[y][x + 1] = 'floor'
    
    def _place_stairs(self):
        """放置下樓樓梯"""
        if self.rooms:
            # 在最後一個房間的中心放置樓梯
            last_room = self.rooms[-1]
            stairs_x = last_room.centerx
            stairs_y = last_room.centery
            self.tiles[stairs_y][stairs_x] = 'stairs'
    
    def _populate_dungeon(self):
        """在地牢中放置敵人和道具"""
        floor_tiles = []
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == 'floor':
                    floor_tiles.append(Position(x, y))
        
        # 移除樓梯位置
        stair_positions = []
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == 'stairs':
                    stair_positions.append(Position(x, y))
        
        for stair_pos in stair_positions:
            if stair_pos in floor_tiles:
                floor_tiles.remove(stair_pos)
        
        # 確保第一個房間安全
        if self.rooms:
            first_room = self.rooms[0]
            safe_zone = []
            for x in range(first_room.x - 3, first_room.right + 3):
                for y in range(first_room.y - 3, first_room.bottom + 3):
                    safe_zone.append(Position(x, y))
            
            floor_tiles = [pos for pos in floor_tiles if pos not in safe_zone]
        
        # 根據層數調整敵人強度
        level_multiplier = 1 + (self.level - 1) * 0.5
        
        # 放置敵人
        enemy_count = min(random.randint(10 + self.level, 20 + self.level * 2), len(floor_tiles) // 3)
        
        # 定義敵人類型（移除 Stats 對象，改為函數）
        def create_skeleton_stats():
            return Stats(
                hp=int(30 * level_multiplier), 
                max_hp=int(30 * level_multiplier), 
                mp=0, 
                max_mp=0, 
                attack=int(8 * level_multiplier), 
                defense=int(2 * level_multiplier)
            )
        
        def create_orc_stats():
            return Stats(
                hp=int(50 * level_multiplier), 
                max_hp=int(50 * level_multiplier), 
                mp=0, 
                max_mp=0, 
                attack=int(12 * level_multiplier), 
                defense=int(4 * level_multiplier)
            )
        
        def create_goblin_stats():
            return Stats(
                hp=int(20 * level_multiplier), 
                max_hp=int(20 * level_multiplier), 
                mp=0, 
                max_mp=0, 
                attack=int(6 * level_multiplier), 
                defense=int(1 * level_multiplier)
            )
        
        def create_demon_stats():
            return Stats(
                hp=int(100 * level_multiplier), 
                max_hp=int(100 * level_multiplier),
                mp=0, 
                max_mp=0, 
                attack=int(20 * level_multiplier), 
                defense=int(8 * level_multiplier)
            )
        
        def create_lich_stats():
            return Stats(
                hp=int(150 * level_multiplier), 
                max_hp=int(150 * level_multiplier),
                mp=0, 
                max_mp=0, 
                attack=int(25 * level_multiplier), 
                defense=int(10 * level_multiplier)
            )
        
        def create_dragon_stats():
            return Stats(
                hp=int(200 * level_multiplier), 
                max_hp=int(200 * level_multiplier),
                mp=0, 
                max_mp=0, 
                attack=int(30 * level_multiplier), 
                defense=int(15 * level_multiplier)
            )
        
        # 使用函數而不是預創建的對象
        enemy_types = [
            ('skeleton', GameTexts.ENEMY_SKELETON, create_skeleton_stats),
            ('orc', GameTexts.ENEMY_ORC, create_orc_stats),
            ('goblin', GameTexts.ENEMY_GOBLIN, create_goblin_stats)
        ]
        
        # 在較深層添加強力敵人
        if self.level >= 5:
            enemy_types.append(('demon', GameTexts.ENEMY_DEMON, create_demon_stats))
        
        if self.level >= 8:
            enemy_types.append(('lich', GameTexts.ENEMY_LICH, create_lich_stats))
        
        # 在第10層放置龍
        if self.level >= 10 and random.random() < 0.5:
            enemy_types.append(('dragon', GameTexts.ENEMY_DRAGON, create_dragon_stats))
        
        for _ in range(enemy_count):
            if floor_tiles:
                pos = floor_tiles.pop(random.randint(0, len(floor_tiles) - 1))
                enemy_type, enemy_name, create_stats_func = random.choice(enemy_types)
                # 每次創建新的 Stats 對象
                stats = create_stats_func()
                enemy = Enemy(pos, enemy_type, enemy_name, stats)
                
                # 標記Boss
                if enemy_type in ['dragon', 'lich']:
                    enemy.is_boss = True
                
                self.enemies.append(enemy)
        
        # 放置道具（以下代碼保持不變）
        item_count = random.randint(15 + self.level, 30 + self.level * 2)
        
        # 武器 (15%)
        weapon_count = max(2, item_count // 6)
        for _ in range(weapon_count):
            if floor_tiles:
                pos = floor_tiles.pop(random.randint(0, len(floor_tiles) - 1))
                
                # 根據層數選擇武器
                if self.level >= 8 and random.random() < 0.1:
                    weapon_key = 'legendary_sword'
                else:
                    weapon_key = random.choice(['dagger', 'sword', 'axe', 'mace', 'bow'])
                
                item = self.item_db.create_weapon(weapon_key)
                self.items.append((pos, item))
        
        # 護甲 (15%) - 包括鞋子
        armor_count = max(2, item_count // 6)
        for _ in range(armor_count):
            if floor_tiles:
                pos = floor_tiles.pop(random.randint(0, len(floor_tiles) - 1))
                
                # 根據層數選擇護甲
                if self.level >= 8 and random.random() < 0.1:
                    if random.random() < 0.5:
                        armor_key = 'legendary_armor'
                    else:
                        armor_key = 'legendary_boots'
                else:
                    armor_key = random.choice(['leather_armor', 'chain_mail', 'plate_armor', 
                                             'shield', 'helmet', 'leather_boots', 'speed_boots',
                                             'mage_boots', 'warrior_boots'])
                
                if armor_key.endswith('_boots'):
                    item = self.item_db.create_boots(armor_key)
                else:
                    item = self.item_db.create_armor(armor_key)
                self.items.append((pos, item))
        
        # 在生成藥水的部分（找到potion_count那段）
        potion_count = max(5, int(item_count * 0.4))
        for _ in range(potion_count):
            if floor_tiles:
                pos = floor_tiles.pop(random.randint(0, len(floor_tiles) - 1))
                potion_key = random.choice(['red_potion', 'blue_potion', 'green_potion', 'yellow_potion'])
                item = self.item_db.create_potion(potion_key)
                
                # 檢查這個藥水類型是否已被玩家鑑定過
                if hasattr(self, 'player') and hasattr(self.player, 'identified_items'):
                    if potion_key in self.player.identified_items:
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
                
                self.items.append((pos, item))
        
        # 卷軸 (20%)
        scroll_count = max(3, int(item_count * 0.2))
        for _ in range(scroll_count):
            if floor_tiles:
                pos = floor_tiles.pop(random.randint(0, len(floor_tiles) - 1))
                # 不指定類型，讓 create_scroll 隨機選擇
                item = self.item_db.create_scroll()
                self.items.append((pos, item))
        
        # 金幣 (10%)
        gold_count = max(3, item_count // 10)
        for _ in range(gold_count):
            if floor_tiles:
                pos = floor_tiles.pop(random.randint(0, len(floor_tiles) - 1))
                # 深層有更多金幣
                gold_amount = random.randint(30 + self.level * 10, 150 + self.level * 20)
                item = self.item_db.create_gold(gold_amount)
                self.items.append((pos, item))
    
    def is_walkable(self, position: Position) -> bool:
        """檢查位置是否可行走"""
        if (0 <= position.x < self.width and 
            0 <= position.y < self.height):
            return self.tiles[position.y][position.x] in ['floor', 'stairs']
        return False
    
    def get_blocking_entity(self, position: Position):
        """獲取指定位置的阻擋實體"""
        for enemy in self.enemies:
            if enemy.active and enemy.position.x == position.x and enemy.position.y == position.y:
                return enemy
        return None
    
    def get_tile(self, position: Position) -> str:
        """獲取指定位置的地形類型"""
        if (0 <= position.x < self.width and 
            0 <= position.y < self.height):
            return self.tiles[position.y][position.x]
        return 'wall'
    
    def update_fov(self, player_pos: Position, radius: int = 12):
        """更新視野（改進版）"""
        # 重置可見性
        self.visible = [[False for _ in range(self.width)] for _ in range(self.height)]
        
        # 使用改進的視線算法
        for angle in range(0, 360, 5):  # 每5度一條射線
            rad = math.radians(angle)
            dx = math.cos(rad)
            dy = math.sin(rad)
            
            for distance in range(radius):
                x = int(player_pos.x + dx * distance)
                y = int(player_pos.y + dy * distance)
                
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.visible[y][x] = True
                    self.explored[y][x] = True
                    
                    # 如果碰到牆，停止
                    if self.tiles[y][x] == 'wall':
                        break
    
    def render(self, screen, camera_offset: Position, asset_manager: AssetManager):
        """渲染地圖（優化版 - 減少閃爍）"""
        # 計算可見範圍以優化渲染
        start_x = max(0, camera_offset.x // TILE_SIZE - 1)
        end_x = min(self.width, (camera_offset.x + WINDOW_WIDTH) // TILE_SIZE + 2)
        start_y = max(0, camera_offset.y // TILE_SIZE - 1)
        end_y = min(self.height, (camera_offset.y + WINDOW_HEIGHT) // TILE_SIZE + 2)
        
        # 創建地圖表面（只渲染可見區域）
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                screen_x = (x * TILE_SIZE) - camera_offset.x
                screen_y = (y * TILE_SIZE) - camera_offset.y
                
                tile_type = self.tiles[y][x]
                
                # 根據探索狀態和可見性決定渲染方式
                if self.visible[y][x]:
                    image = asset_manager.get_image(tile_type)
                    if image:
                        screen.blit(image, (screen_x, screen_y))
                        
                        # 添加動態光照效果（減少頻率避免閃爍）
                        if tile_type == 'floor':
                            # 使用固定的棋盤格圖案，基於坐標決定是否有光效
                            if (x + y) % 8 == 0:
                                # 使用時間創建呼吸燈效果，但頻率較低
                                pulse = abs(math.sin(pygame.time.get_ticks() * 0.001 + x * 0.1 + y * 0.1))
                                alpha = int(10 + pulse * 10)  # 降低透明度範圍
                                light_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                                light_surface.fill((*Colors.WHITE, alpha))
                                screen.blit(light_surface, (screen_x, screen_y))
                elif self.explored[y][x]:
                    # 已探索但不可見的區域顯示為暗色
                    image = asset_manager.get_image(tile_type)
                    if image:
                        dark_image = image.copy()
                        dark_image.set_alpha(80)
                        screen.blit(dark_image, (screen_x, screen_y))

# ============================================================================
# UI系統 - 現代化設計
# ============================================================================

class UI:
    """用戶界面"""
    
    def __init__(self, asset_manager: AssetManager):
        self.asset_manager = asset_manager
        self.menu_selection = 0
        self.inventory_selection = 0
        self.inventory_scroll_offset = 0  # 背包滾動偏移
        self.show_inventory = False
        self.tooltip = None
        self.tooltip_timer = 0
        self.settings_selection = 0
        self.achievement_scroll = 0
        self.button_hover = {}
        self.animation_time = 0
        self.resolution = (WINDOW_WIDTH, WINDOW_HEIGHT)
        self.skill_selection = 0  # 當前選中的技能索引
        self.show_skill_panel = True  # 是否顯示技能面板
        self.inventory_panel_focused = True  # True=背包面板, False=技能面板
        self.skill_button_hover = {}  # 技能按鈕懸停狀態
        self.skill_upgrade_rects = {}  # 升級按鈕矩形
        self.skill_equip_rects = {}  # 裝備按鈕矩形
        self.inventory_panel_rect = None  # 背包面板矩形
        self.skill_panel_rect = None  # 技能面板矩形
        
        # 新增：訊息日誌折疊狀態
        self.message_log_collapsed = False  # False=展開, True=收起
        self.message_log_animation_progress = 0.0  # 動畫進度 0-1
        
        # 下拉選單狀態
        self.dropdown_open = None  # 當前打開的下拉選單
        self.dropdown_options = {
            'resolution': RESOLUTIONS,
            'particle': ['low', 'medium', 'high'],
            'difficulty': ['easy', 'normal', 'hard']
        }

    def set_mouse_pos(self, converted_pos):
        """設置轉換後的滑鼠座標"""
        self.converted_mouse_pos = converted_pos

    def update_resolution(self, resolution):
        """更新解析度"""
        self.resolution = resolution
    
    def update(self, dt):
        """更新UI動畫"""
        self.animation_time += dt
        
        # 更新工具提示
        if self.tooltip_timer > 0:
            self.tooltip_timer -= 1
        else:
            self.tooltip = None

    def render_hud(self, screen, player: Player, dungeon_level: int, turn_count: int, settings: GameSettings):
        """渲染HUD - 現代化設計（修復遮擋問題）"""
        # 頂部信息欄
        top_bar_height = 60  # 從80減少到60
        top_bar = pygame.Surface((WINDOW_WIDTH, top_bar_height), pygame.SRCALPHA)
        pygame.draw.rect(top_bar, (*Colors.UI_BG, 200), (0, 0, WINDOW_WIDTH, top_bar_height))
        pygame.draw.line(top_bar, Colors.UI_BORDER, (0, top_bar_height-1), (WINDOW_WIDTH, top_bar_height-1), 2)
        
        # 樓層信息
        floor_text = GameTexts.STATUS_FLOOR.format(dungeon_level)
        floor_surface = self.asset_manager.fonts.render_text(floor_text, 28, Colors.NEON_YELLOW)
        top_bar.blit(floor_surface, (30, 15))
        
        # 回合數
        turn_text = GameTexts.STATUS_TURN.format(turn_count)
        turn_surface = self.asset_manager.fonts.render_text(turn_text, 18, Colors.UI_TEXT)
        top_bar.blit(turn_surface, (250, 20))
        
        screen.blit(top_bar, (0, 0))
        
        # 底部狀態欄（縮小高度）
        bottom_bar_height = 140  # 從180減少到140
        bottom_bar = pygame.Surface((WINDOW_WIDTH, bottom_bar_height), pygame.SRCALPHA)
        pygame.draw.rect(bottom_bar, (*Colors.UI_BG, 220), (0, 0, WINDOW_WIDTH, bottom_bar_height))
        pygame.draw.line(bottom_bar, Colors.UI_BORDER, (0, 0), (WINDOW_WIDTH, 0), 2)
        
        # 玩家頭像區域（縮小）
        avatar_x = 20
        avatar_y = 15
        avatar_size = 60  # 從80減少到60
        pygame.draw.rect(bottom_bar, Colors.UI_BORDER, (avatar_x, avatar_y, avatar_size, avatar_size), 3)
        
        # 玩家圖標
        player_icon = self.asset_manager.get_image('player')
        if player_icon:
            scaled_icon = pygame.transform.scale(player_icon, (avatar_size - 10, avatar_size - 10))
            bottom_bar.blit(scaled_icon, (avatar_x + 5, avatar_y + 5))
        
        # 玩家等級
        level_bg = pygame.Surface((35, 20), pygame.SRCALPHA)
        pygame.draw.rect(level_bg, Colors.NEON_BLUE, (0, 0, 35, 20))
        level_text = self.asset_manager.fonts.render_text(f"Lv{player.stats.level}", 14, Colors.WHITE)
        level_bg.blit(level_text, (5, 2))
        bottom_bar.blit(level_bg, (avatar_x + avatar_size - 38, avatar_y + avatar_size - 23))
        
        # 狀態條
        bar_x = avatar_x + avatar_size + 20
        bar_y = avatar_y + 5
        bar_width = 300  # 從350減少
        bar_height = 20  # 從25減少
        bar_spacing = 28  # 從35減少
        
        # 生命值條
        self._render_modern_bar(bottom_bar, bar_x, bar_y, bar_width, bar_height,
                            player.stats.hp, player.stats.max_hp,
                            Colors.HEALTH_RED, GameTexts.STATUS_HP)
        
        # 魔力值條
        self._render_modern_bar(bottom_bar, bar_x, bar_y + bar_spacing, bar_width, bar_height,
                            player.stats.mp, player.stats.max_mp,
                            Colors.MANA_BLUE, GameTexts.STATUS_MP)
        
        # 經驗值條
        self._render_modern_bar(bottom_bar, bar_x, bar_y + bar_spacing * 2, bar_width, bar_height,
                            player.stats.exp, player.stats.exp_to_next,
                            Colors.EXP_YELLOW, GameTexts.STATUS_EXP)
        
        # 屬性信息（改進圖標顯示）
        stats_x = bar_x + bar_width + 30
        stats_y = avatar_y + 5
        
        # 攻擊力
        self._render_stat_icon(bottom_bar, stats_x, stats_y, "攻", Colors.NEON_ORANGE, 
                            str(player.get_total_attack()), "攻擊力")
        
        # 防禦力
        self._render_stat_icon(bottom_bar, stats_x, stats_y + 35, "防", Colors.NEON_CYAN,
                            str(player.get_total_defense()), "防禦力")
        
        # 金幣
        self._render_stat_icon(bottom_bar, stats_x + 100, stats_y, "金", Colors.EXP_YELLOW,
                            str(player.gold), "金幣")
        
        # 技能欄
        skill_x = stats_x + 220
        skill_y = avatar_y + 5
        
        for i in range(4):  # 固定顯示4個技能欄位
            skill_bg = pygame.Surface((50, 50), pygame.SRCALPHA)  # 從60減小到50
            
            skill = player.equipped_skills[i] if i < len(player.equipped_skills) else None
            
            if skill and skill.is_learned:
                # 技能框
                if skill.current_cooldown > 0:
                    # 冷卻中
                    pygame.draw.rect(skill_bg, Colors.UI_SECONDARY, (0, 0, 50, 50))
                    
                    # 冷卻遮罩
                    cooldown_height = int(50 * (skill.current_cooldown / skill.cooldown))
                    pygame.draw.rect(skill_bg, (*Colors.BLACK, 128), (0, 0, 50, cooldown_height))
                    
                    # 冷卻時間
                    cd_text = self.asset_manager.fonts.render_text(f"{int(skill.current_cooldown)}", 18, Colors.WHITE)
                    cd_rect = cd_text.get_rect(center=(25, 25))
                    skill_bg.blit(cd_text, cd_rect)
                else:
                    # 可用
                    pygame.draw.rect(skill_bg, Colors.UI_HIGHLIGHT, (0, 0, 50, 50))
                
                pygame.draw.rect(skill_bg, Colors.UI_BORDER, (0, 0, 50, 50), 3)
                
                # 技能圖標文字
                skill_icons = {
                    GameTexts.SKILL_SLASH: "斬",
                    GameTexts.SKILL_FIREBALL: "火",
                    GameTexts.SKILL_HEAL: "癒",
                    GameTexts.SKILL_SHIELD: "盾",
                    "閃電鏈": "電",
                    "冰錐術": "冰",
                    "瞬間移動": "瞬",
                    "召喚術": "召"
                }
                icon_text = skill_icons.get(skill.name, skill.name[0] if skill.name else "?")
                icon_colors = {
                    GameTexts.SKILL_SLASH: Colors.NEON_ORANGE,
                    GameTexts.SKILL_FIREBALL: Colors.HEALTH_RED,
                    GameTexts.SKILL_HEAL: Colors.NEON_GREEN,
                    GameTexts.SKILL_SHIELD: Colors.NEON_CYAN,
                    "閃電鏈": Colors.NEON_CYAN,
                    "冰錐術": Colors.NEON_BLUE,
                    "瞬間移動": Colors.NEON_PURPLE,
                    "召喚術": Colors.NEON_YELLOW
                }
                icon_color = icon_colors.get(skill.name, Colors.WHITE)
                
                # 技能圖標
                icon_surface = self.asset_manager.fonts.render_text(icon_text, 20, Colors.BLACK)
                icon_rect = icon_surface.get_rect(center=(25, 20))
                # 背景圓
                pygame.gfxdraw.filled_circle(skill_bg, 25, 20, 15, icon_color)
                pygame.gfxdraw.circle(skill_bg, 25, 20, 15, Colors.BLACK)
                skill_bg.blit(icon_surface, icon_rect)
                
                # 技能等級（右上角）
                if skill.current_level > 1:
                    level_text = self.asset_manager.fonts.render_text(f"{skill.current_level}", 12, Colors.EXP_YELLOW)
                    skill_bg.blit(level_text, (38, 2))
            else:
                # 空技能欄
                pygame.draw.rect(skill_bg, Colors.UI_SECONDARY, (0, 0, 50, 50))
                pygame.draw.rect(skill_bg, Colors.UI_BORDER, (0, 0, 50, 50), 2)
                
                # 空欄提示
                empty_text = self.asset_manager.fonts.render_text("?", 24, Colors.UI_TEXT_DARK)
                empty_rect = empty_text.get_rect(center=(25, 25))
                skill_bg.blit(empty_text, empty_rect)
            
            # 快捷鍵
            key_text = self.asset_manager.fonts.render_text(str(i + 1), 12, Colors.WHITE)
            skill_bg.blit(key_text, (3, 35))
            
            bottom_bar.blit(skill_bg, (skill_x + i * 55, skill_y))
        
        # 操作提示（更簡潔）
        hints_y = bottom_bar_height - 25
        hint_texts = [
            "B-背包", "F-拾取", "R-休息", "L-日誌", "ESC-選單"
        ]
        hint_x = 20
        for hint in hint_texts:
            hint_surface = self.asset_manager.fonts.render_text(hint, 12, Colors.UI_TEXT_DARK)
            bottom_bar.blit(hint_surface, (hint_x, hints_y))
            hint_x += hint_surface.get_width() + 15
        
        screen.blit(bottom_bar, (0, WINDOW_HEIGHT - bottom_bar_height))
        
        # 護盾效果指示（原有代碼）
        if player.shield_active:
            shield_text = f"護盾 {player.shield_duration:.1f}s"
            shield_surface = self.asset_manager.fonts.render_text(shield_text, 18, Colors.NEON_CYAN)
            shield_bg = pygame.Surface((shield_surface.get_width() + 20, 30), pygame.SRCALPHA)
            pygame.draw.rect(shield_bg, (*Colors.NEON_CYAN, 100), (0, 0, shield_bg.get_width(), 30))
            pygame.draw.rect(shield_bg, Colors.NEON_CYAN, (0, 0, shield_bg.get_width(), 30), 2)
            shield_bg.blit(shield_surface, (10, 5))
            screen.blit(shield_bg, (WINDOW_WIDTH // 2 - shield_bg.get_width() // 2, top_bar_height + 10))
        
        # 樓梯提示（新增）
        if hasattr(player, 'on_stairs') and player.on_stairs:
            # 創建脈衝效果
            pulse = abs(math.sin(self.animation_time * 3))
            
            # 提示文字
            stairs_text = "按 空白鍵 進入下一層"
            stairs_surface = self.asset_manager.fonts.render_text(stairs_text, 24, Colors.STAIRS_COLOR)
            
            # 背景框
            stairs_bg_width = stairs_surface.get_width() + 40
            stairs_bg_height = 50
            stairs_bg = pygame.Surface((stairs_bg_width, stairs_bg_height), pygame.SRCALPHA)
            
            # 漸變背景
            for i in range(stairs_bg_height):
                alpha = int(150 * (1 - i / stairs_bg_height))
                color = (*Colors.STAIRS_COLOR, alpha)
                pygame.draw.line(stairs_bg, color, (0, i), (stairs_bg_width, i))
            
            # 邊框（脈衝效果）
            border_alpha = int(200 + pulse * 55)
            pygame.draw.rect(stairs_bg, (*Colors.STAIRS_COLOR, border_alpha), 
                           (0, 0, stairs_bg_width, stairs_bg_height), 3)
            
            # 文字
            text_rect = stairs_surface.get_rect(center=(stairs_bg_width // 2, stairs_bg_height // 2))
            stairs_bg.blit(stairs_surface, text_rect)
            
            # 位置（屏幕中央偏上）
            stairs_x = WINDOW_WIDTH // 2 - stairs_bg_width // 2
            stairs_y = WINDOW_HEIGHT // 2 - 100
            
            # 添加箭頭指示
            arrow_y = stairs_y + stairs_bg_height + 10
            arrow_size = int(20 + pulse * 5)
            arrow_points = [
                (WINDOW_WIDTH // 2, arrow_y),
                (WINDOW_WIDTH // 2 - arrow_size // 2, arrow_y - arrow_size),
                (WINDOW_WIDTH // 2 + arrow_size // 2, arrow_y - arrow_size)
            ]
            pygame.draw.polygon(screen, Colors.STAIRS_COLOR, arrow_points)
            
            screen.blit(stairs_bg, (stairs_x, stairs_y))

    def _render_stat_icon(self, surface, x: int, y: int, icon_text: str, color: tuple, 
                        value: str, tooltip: str):
        """渲染屬性圖標（改進版）"""
        # 圖標背景
        icon_size = 30
        pygame.gfxdraw.filled_circle(surface, x + icon_size // 2, y + icon_size // 2, 
                                    icon_size // 2, color)
        pygame.gfxdraw.circle(surface, x + icon_size // 2, y + icon_size // 2, 
                            icon_size // 2, Colors.BLACK)
        
        # 圖標文字
        icon_font = self.asset_manager.fonts.render_text(icon_text, 16, Colors.BLACK)
        icon_rect = icon_font.get_rect(center=(x + icon_size // 2, y + icon_size // 2))
        surface.blit(icon_font, icon_rect)
        
        # 數值
        value_surface = self.asset_manager.fonts.render_text(value, 22, Colors.UI_TEXT)
        surface.blit(value_surface, (x + icon_size + 10, y + 3))    
   
    def _render_modern_bar(self, surface, x: int, y: int, width: int, height: int,
                          current: int, maximum: int, color: tuple, label: str):
        """渲染現代化進度條"""
        # 背景
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, Colors.UI_SECONDARY, bg_rect)
        pygame.draw.rect(surface, Colors.UI_BORDER, bg_rect, 2)
        
        # 進度
        if maximum > 0:
            progress = current / maximum
            progress_width = int((width - 4) * progress)
            
            # 漸變效果
            if progress_width > 0:
                progress_rect = pygame.Rect(x + 2, y + 2, progress_width, height - 4)
                
                # 主色條
                pygame.draw.rect(surface, color, progress_rect)
                
                # 高光效果
                highlight_rect = pygame.Rect(x + 2, y + 2, progress_width, (height - 4) // 2)
                highlight_color = tuple(min(255, c + 50) for c in color)
                pygame.draw.rect(surface, highlight_color, highlight_rect)
                
                # 動畫波紋
                wave_offset = int(self.animation_time * 100) % width
                for i in range(0, progress_width, 40):
                    wave_x = x + 2 + ((i + wave_offset) % progress_width)
                    if wave_x < x + 2 + progress_width:
                        wave_rect = pygame.Rect(wave_x, y + 2, 20, height - 4)
                        wave_surface = pygame.Surface((20, height - 4), pygame.SRCALPHA)
                        wave_surface.fill((*Colors.WHITE, 30))
                        surface.blit(wave_surface, (wave_x, y + 2))
        
        # 文字
        text = f"{label}: {current}/{maximum}"
        text_surface = self.asset_manager.fonts.render_text(text, 16, Colors.WHITE)
        text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
        surface.blit(text_surface, text_rect)
    
    def render_minimap(self, screen, dungeon_map: DungeonMap, player: Player, settings: GameSettings):
        """渲染小地圖 - 現代化設計"""
        if not settings.show_minimap:
            return
            
        # 小地圖位置
        minimap_x = WINDOW_WIDTH - MINIMAP_SIZE - 30
        minimap_y = 100
        
        # 背景
        minimap_bg = pygame.Surface((MINIMAP_SIZE + 10, MINIMAP_SIZE + 10), pygame.SRCALPHA)
        pygame.draw.rect(minimap_bg, (*Colors.UI_BG, 200), (0, 0, MINIMAP_SIZE + 10, MINIMAP_SIZE + 10))
        pygame.draw.rect(minimap_bg, Colors.UI_BORDER, (0, 0, MINIMAP_SIZE + 10, MINIMAP_SIZE + 10), 3)
        
        # 計算顯示範圍
        view_width = MINIMAP_SIZE // MINIMAP_TILE_SIZE
        view_height = MINIMAP_SIZE // MINIMAP_TILE_SIZE
        
        start_x = max(0, player.position.x - view_width // 2)
        start_y = max(0, player.position.y - view_height // 2)
        end_x = min(dungeon_map.width, start_x + view_width)
        end_y = min(dungeon_map.height, start_y + view_height)
        
        # 繪製地圖
        minimap_surface = pygame.Surface((MINIMAP_SIZE, MINIMAP_SIZE), pygame.SRCALPHA)
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                screen_x = (x - start_x) * MINIMAP_TILE_SIZE
                screen_y = (y - start_y) * MINIMAP_TILE_SIZE
                
                if dungeon_map.explored[y][x]:
                    tile_type = dungeon_map.tiles[y][x]
                    if tile_type == 'wall':
                        color = Colors.WALL_COLOR
                    elif tile_type == 'floor':
                        color = Colors.FLOOR_COLOR
                    elif tile_type == 'stairs':
                        color = Colors.STAIRS_COLOR
                    else:
                        color = Colors.UI_SECONDARY
                    
                    # 可見區域高亮
                    if dungeon_map.visible[y][x]:
                        color = tuple(min(255, c + 40) for c in color)
                    
                    pygame.draw.rect(minimap_surface, color, 
                                   (screen_x, screen_y, MINIMAP_TILE_SIZE, MINIMAP_TILE_SIZE))
                else:
                    pygame.draw.rect(minimap_surface, Colors.BLACK,
                                   (screen_x, screen_y, MINIMAP_TILE_SIZE, MINIMAP_TILE_SIZE))
        
        # 繪製敵人（只顯示可見的）
        for enemy in dungeon_map.enemies:
            if enemy.active and dungeon_map.visible[enemy.position.y][enemy.position.x]:
                if start_x <= enemy.position.x < end_x and start_y <= enemy.position.y < end_y:
                    screen_x = (enemy.position.x - start_x) * MINIMAP_TILE_SIZE
                    screen_y = (enemy.position.y - start_y) * MINIMAP_TILE_SIZE
                    
                    enemy_color = Colors.NEON_PINK if enemy.is_boss else Colors.HEALTH_RED
                    pygame.gfxdraw.filled_circle(minimap_surface, 
                                               screen_x + MINIMAP_TILE_SIZE // 2,
                                               screen_y + MINIMAP_TILE_SIZE // 2,
                                               MINIMAP_TILE_SIZE // 2,
                                               enemy_color)
        
        # 繪製物品（只顯示可見的）
        for item_pos, item in dungeon_map.items:
            if dungeon_map.visible[item_pos.y][item_pos.x]:
                if start_x <= item_pos.x < end_x and start_y <= item_pos.y < end_y:
                    screen_x = (item_pos.x - start_x) * MINIMAP_TILE_SIZE
                    screen_y = (item_pos.y - start_y) * MINIMAP_TILE_SIZE
                    
                    item_color = Colors.EXP_YELLOW
                    if item.rarity == "legendary":
                        item_color = Colors.NEON_YELLOW
                    elif item.rarity == "epic":
                        item_color = Colors.NEON_PURPLE
                    elif item.rarity == "rare":
                        item_color = Colors.NEON_CYAN
                    
                    pygame.gfxdraw.filled_circle(minimap_surface,
                                               screen_x + MINIMAP_TILE_SIZE // 2,
                                               screen_y + MINIMAP_TILE_SIZE // 2,
                                               MINIMAP_TILE_SIZE // 3,
                                               item_color)
        
        # 繪製玩家（帶脈衝效果）
        player_x = (player.position.x - start_x) * MINIMAP_TILE_SIZE
        player_y = (player.position.y - start_y) * MINIMAP_TILE_SIZE
        
        # 脈衝光環
        pulse = abs(math.sin(self.animation_time * 3))
        for i in range(3):
            radius = MINIMAP_TILE_SIZE // 2 + i * 2 + int(pulse * 3)
            alpha = int(100 - i * 30 - pulse * 50)
            alpha = max(0, min(255, alpha))
            
            # 創建一個表面來繪製帶透明度的圓
            glow_surface = pygame.Surface((MINIMAP_SIZE, MINIMAP_SIZE), pygame.SRCALPHA)
            glow_color = (*Colors.NEON_BLUE, alpha)
            pygame.gfxdraw.filled_circle(glow_surface,
                                       player_x + MINIMAP_TILE_SIZE // 2,
                                       player_y + MINIMAP_TILE_SIZE // 2,
                                       radius,
                                       glow_color)
            minimap_surface.blit(glow_surface, (0, 0))
        
        minimap_bg.blit(minimap_surface, (5, 5))
        screen.blit(minimap_bg, (minimap_x, minimap_y))
        
        # 小地圖標題
        title_surface = self.asset_manager.fonts.render_text("地圖", 18, Colors.UI_TEXT)
        screen.blit(title_surface, (minimap_x + 10, minimap_y - 25))
    
    def render_enemy_health_bars(self, screen, enemies: list, camera_offset: Position, settings: GameSettings):

        """渲染敵人血條 - 現代化設計"""
        if not settings.show_enemy_health:
            return
            
        for enemy in enemies:
            if enemy.active and enemy.visible:
                screen_x = (enemy.position.x * TILE_SIZE) - camera_offset.x
                screen_y = (enemy.position.y * TILE_SIZE) - camera_offset.y - 15
                
                # 只渲染螢幕範圍內的血條
                if (-TILE_SIZE <= screen_x <= WINDOW_WIDTH and 
                    -TILE_SIZE <= screen_y <= WINDOW_HEIGHT):
                    
                    # Boss血條特殊處理
                    if enemy.is_boss:
                        bar_width = TILE_SIZE + 20
                        bar_height = 8
                        screen_y -= 10
                    else:
                        bar_width = TILE_SIZE
                        bar_height = 5
                    
                    # 血條背景
                    bg_rect = pygame.Rect(screen_x - (bar_width - TILE_SIZE) // 2, screen_y, bar_width, bar_height)
                    pygame.draw.rect(screen, Colors.BLACK, bg_rect)
                    
                    # 血條
                    if enemy.stats.max_hp > 0:
                        health_percentage = enemy.stats.hp / enemy.stats.max_hp
                        health_width = int((bar_width - 2) * health_percentage)
                        
                        # 根據血量百分比選擇顏色
                        if health_percentage > 0.5:
                            color = Colors.NEON_GREEN
                        elif health_percentage > 0.25:
                            color = Colors.NEON_YELLOW
                        else:
                            color = Colors.HEALTH_RED
                        
                        if health_width > 0:
                            health_rect = pygame.Rect(screen_x - (bar_width - TILE_SIZE) // 2 + 1, 
                                                    screen_y + 1, health_width, bar_height - 2)
                            pygame.draw.rect(screen, color, health_rect)
                            
                            # Boss血條發光效果
                            if enemy.is_boss:
                                glow_surface = pygame.Surface((bar_width + 10, bar_height + 10), pygame.SRCALPHA)
                                # 使用 pygame.draw.rect 代替 filled_rectangle
                                glow_rect = pygame.Rect(5, 5, bar_width, bar_height)
                                pygame.draw.rect(glow_surface, (*color, 100), glow_rect)
                                screen.blit(glow_surface, 
                                          (screen_x - (bar_width - TILE_SIZE) // 2 - 5, screen_y - 5))
                    
                    # 邊框
                    pygame.draw.rect(screen, Colors.WHITE, bg_rect, 1)
                    
                    # Boss名稱
                    if enemy.is_boss:
                        name_surface = self.asset_manager.fonts.render_text(enemy.name, 14, Colors.NEON_PINK)
                        name_rect = name_surface.get_rect(centerx=screen_x + TILE_SIZE // 2, 
                                                         bottom=screen_y - 5)
                        screen.blit(name_surface, name_rect)
    def render_message_log(self, screen, message_log: MessageLog):
        """渲染訊息日誌 - 支援收起/展開功能"""
        messages = message_log.get_display_messages()
        
        # 面板基礎設定
        panel_x = 30
        panel_y = 100
        
        if self.message_log_collapsed:
            # 收起狀態 - 只顯示最新的3條訊息和展開提示
            panel_width = 400
            panel_height = 140
            
            # 創建面板
            panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            
            # 半透明背景
            pygame.draw.rect(panel_surface, (*Colors.UI_BG, 180), (0, 0, panel_width, panel_height))
            pygame.draw.rect(panel_surface, Colors.UI_BORDER, (0, 0, panel_width, panel_height), 2)
            
            # 標題欄
            title_height = 30
            pygame.draw.rect(panel_surface, (*Colors.UI_SECONDARY, 200), (0, 0, panel_width, title_height))
            pygame.draw.line(panel_surface, Colors.UI_BORDER, (0, title_height), (panel_width, title_height), 2)
            
            # 標題文字和展開提示
            title_text = "冒險日誌 [已收起]"
            title_surface = self.asset_manager.fonts.render_text(title_text, 16, Colors.UI_TEXT)
            panel_surface.blit(title_surface, (10, 8))
            
            # 展開提示
            expand_hint = "按 L 展開"
            hint_surface = self.asset_manager.fonts.render_text(expand_hint, 14, Colors.UI_TEXT_DARK)
            hint_rect = hint_surface.get_rect(right=panel_width - 10, centery=title_height // 2)
            panel_surface.blit(hint_surface, hint_rect)
            
            # 顯示最新的3條訊息
            y_pos = title_height + 10
            display_messages = messages[-3:] if len(messages) >= 3 else messages
            
            for message in display_messages:
                color_map = {
                    MessageType.NORMAL: Colors.MSG_NORMAL,
                    MessageType.COMBAT: Colors.MSG_COMBAT,
                    MessageType.ITEM: Colors.MSG_ITEM,
                    MessageType.LEVEL_UP: Colors.MSG_LEVEL,
                    MessageType.STORY: Colors.MSG_STORY,
                    MessageType.WARNING: Colors.MSG_WARNING
                }
                
                color = color_map.get(message.msg_type, Colors.WHITE)
                
                # 縮小字體
                text_surface = self.asset_manager.fonts.render_text(message.text[:50] + "..." if len(message.text) > 50 else message.text, 14, color)
                
                if message.fade_alpha < 255:
                    text_surface.set_alpha(message.fade_alpha)
                
                panel_surface.blit(text_surface, (10, y_pos))
                y_pos += 25
            
            # 如果沒有訊息
            if not display_messages:
                no_msg_surface = self.asset_manager.fonts.render_text("暫無訊息", 14, Colors.UI_TEXT_DARK)
                panel_surface.blit(no_msg_surface, (10, y_pos))
            
        else:
            # 展開狀態 - 完整顯示
            panel_width = 700
            panel_height = min(450, len(messages) * 45 + 80)
            
            # 創建面板
            panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            
            # 半透明背景
            pygame.draw.rect(panel_surface, (*Colors.UI_BG, 220), (0, 0, panel_width, panel_height))
            pygame.draw.rect(panel_surface, Colors.UI_BORDER, (0, 0, panel_width, panel_height), 3)
            
            # 標題欄
            title_height = 40
            pygame.draw.rect(panel_surface, (*Colors.UI_SECONDARY, 220), (0, 0, panel_width, title_height))
            pygame.draw.line(panel_surface, Colors.UI_BORDER, (0, title_height), (panel_width, title_height), 2)
            
            # 標題文字
            title_surface = self.asset_manager.fonts.render_text("冒險日誌", 20, Colors.UI_TEXT)
            panel_surface.blit(title_surface, (15, 10))
            
            # 收起提示
            collapse_hint = "按 L 收起"
            hint_surface = self.asset_manager.fonts.render_text(collapse_hint, 14, Colors.UI_TEXT_DARK)
            hint_rect = hint_surface.get_rect(right=panel_width - 15, centery=title_height // 2)
            panel_surface.blit(hint_surface, hint_rect)
            
            # 滾動提示（如果有更多訊息）
            visible_count = len(message_log.get_visible_messages())
            if visible_count > message_log.max_display_messages:
                scroll_hint = f"(滾輪查看 {len(messages)}/{visible_count})"
                scroll_surface = self.asset_manager.fonts.render_text(scroll_hint, 14, Colors.UI_TEXT_DARK)
                scroll_rect = scroll_surface.get_rect(right=panel_width - 100, centery=title_height // 2)
                panel_surface.blit(scroll_surface, scroll_rect)
            
            # 訊息內容
            y_pos = title_height + 20
            for message in messages:
                color_map = {
                    MessageType.NORMAL: Colors.MSG_NORMAL,
                    MessageType.COMBAT: Colors.MSG_COMBAT,
                    MessageType.ITEM: Colors.MSG_ITEM,
                    MessageType.LEVEL_UP: Colors.MSG_LEVEL,
                    MessageType.STORY: Colors.MSG_STORY,
                    MessageType.WARNING: Colors.MSG_WARNING
                }
                
                color = color_map.get(message.msg_type, Colors.WHITE)
                
                # 訊息圖標
                icon_x = 20
                icon_size = 8
                
                # 檢查訊息開頭的標記
                if message.text.startswith('[劍]') or message.text.startswith('[拳]'):
                    pygame.gfxdraw.filled_circle(panel_surface, icon_x, y_pos + 10, icon_size, Colors.HEALTH_RED)
                elif message.text.startswith('[得]') or message.text.startswith('[自]'):
                    pygame.gfxdraw.filled_circle(panel_surface, icon_x, y_pos + 10, icon_size, Colors.NEON_GREEN)
                elif message.text.startswith('[升]'):
                    pygame.gfxdraw.filled_circle(panel_surface, icon_x, y_pos + 10, icon_size, Colors.EXP_YELLOW)
                elif message.text.startswith('[藥]') or message.text.startswith('[卷]'):
                    pygame.gfxdraw.filled_circle(panel_surface, icon_x, y_pos + 10, icon_size, Colors.NEON_CYAN)
                elif message.text.startswith('[爆]'):
                    # 暴擊特殊效果 - 星形
                    for angle in range(0, 360, 45):
                        rad = math.radians(angle)
                        x1 = icon_x + int(math.cos(rad) * icon_size)
                        y1 = y_pos + 10 + int(math.sin(rad) * icon_size)
                        pygame.draw.line(panel_surface, Colors.NEON_ORANGE, (icon_x, y_pos + 10), (x1, y1), 2)
                elif message.msg_type == MessageType.COMBAT:
                    pygame.gfxdraw.filled_circle(panel_surface, icon_x, y_pos + 10, icon_size, Colors.HEALTH_RED)
                elif message.msg_type == MessageType.ITEM:
                    pygame.gfxdraw.filled_circle(panel_surface, icon_x, y_pos + 10, icon_size, Colors.NEON_GREEN)
                elif message.msg_type == MessageType.LEVEL_UP:
                    pygame.gfxdraw.filled_circle(panel_surface, icon_x, y_pos + 10, icon_size, Colors.EXP_YELLOW)
                
                # 訊息文字
                shadow_surface = self.asset_manager.fonts.render_text(message.text, 18, color)
                for dx, dy in [(0, 1), (1, 0), (1, 1)]:
                    panel_surface.blit(shadow_surface, (40 + dx, y_pos + dy))
                
                text_surface = self.asset_manager.fonts.render_text(message.text, 18, color)
                
                if message.fade_alpha < 255:
                    text_surface.set_alpha(message.fade_alpha)
                
                panel_surface.blit(text_surface, (40, y_pos))
                y_pos += 40
            
            # 滾動條（如果需要）
            if visible_count > message_log.max_display_messages:
                scrollbar_x = panel_width - 15
                scrollbar_y = title_height + 10
                scrollbar_height = panel_height - title_height - 20
                
                # 滾動條背景
                pygame.draw.rect(panel_surface, Colors.UI_SECONDARY, 
                               (scrollbar_x, scrollbar_y, 8, scrollbar_height))
                
                # 滾動條滑塊
                thumb_height = max(20, int(scrollbar_height * message_log.max_display_messages / visible_count))
                thumb_pos = message_log.scroll_offset / (visible_count - message_log.max_display_messages)
                thumb_y = scrollbar_y + int((scrollbar_height - thumb_height) * (1 - thumb_pos))
                
                pygame.draw.rect(panel_surface, Colors.UI_HIGHLIGHT, 
                               (scrollbar_x, thumb_y, 8, thumb_height))
        
        # 渲染到螢幕
        screen.blit(panel_surface, (panel_x, panel_y))
    
    def render_inventory(self, screen, player: Player):
        if not self.show_inventory:
            return
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*Colors.BLACK, 180))
        screen.blit(overlay, (0, 0))
        total_width = 1600
        total_height = 800
        panel_x = (WINDOW_WIDTH - total_width) // 2
        panel_y = (WINDOW_HEIGHT - total_height) // 2
        equipment_width = 250
        equipment_height = total_height - 150  
        equipment_rect = pygame.Rect(panel_x, panel_y, equipment_width, equipment_height)
        equipment_surface = pygame.Surface((equipment_width, equipment_height), pygame.SRCALPHA)
        pygame.draw.rect(equipment_surface, Colors.UI_BG, (0, 0, equipment_width, equipment_height))
        pygame.draw.rect(equipment_surface, Colors.UI_BORDER, (0, 0, equipment_width, equipment_height), 3)
        title_height = 50
        pygame.draw.rect(equipment_surface, Colors.UI_SECONDARY, (0, 0, equipment_width, title_height))
        pygame.draw.line(equipment_surface, Colors.UI_BORDER, (0, title_height), (equipment_width, title_height), 2)
        equip_title = self.asset_manager.fonts.render_text("裝備欄", 24, Colors.UI_TEXT)
        title_rect = equip_title.get_rect(center=(equipment_width // 2, title_height // 2))
        equipment_surface.blit(equip_title, title_rect)
        slot_size = 70
        slot_padding = 15
        slot_x = (equipment_width - slot_size) // 2
        slot_y = title_height + 20
        equipment_slots = [
            ('weapon', '武器', player.equipment.get('weapon'), '武'),
            ('armor', '護甲', player.equipment.get('armor'), '甲'),
            ('shield', '盾牌', player.equipment.get('shield'), '盾'),
            ('helmet', '頭盔', player.equipment.get('helmet'), '盔'),
            ('boots', '鞋子', player.equipment.get('boots'), '鞋'),
            ('ring', '戒指', player.equipment.get('ring'), '戒'),
            ('amulet', '護身符', player.equipment.get('amulet'), '符')
        ]
        self.equipment_slot_rects = {}
        for i, (slot_key, slot_name, item, default_icon) in enumerate(equipment_slots):
            slot_rect = pygame.Rect(slot_x, slot_y + i * (slot_size + slot_padding), slot_size, slot_size)
            if item:
                rarity_colors = {
                    'common': Colors.UI_BORDER,
                    'uncommon': Colors.NEON_GREEN,
                    'rare': Colors.NEON_BLUE,
                    'epic': Colors.NEON_PURPLE,
                    'legendary': Colors.NEON_YELLOW
                }
                border_color = rarity_colors.get(item.rarity, Colors.UI_BORDER)
                bg_color = (*border_color, 50)
            else:
                border_color = Colors.UI_BORDER
                bg_color = (*Colors.UI_SECONDARY, 100)
            pygame.draw.rect(equipment_surface, bg_color, slot_rect)
            pygame.draw.rect(equipment_surface, border_color, slot_rect, 3)
            name_surface = self.asset_manager.fonts.render_text(slot_name, 12, Colors.UI_TEXT_DARK)
            name_rect = name_surface.get_rect(centerx=slot_rect.centerx, y=slot_rect.y - 15)
            equipment_surface.blit(name_surface, name_rect)
            if item:
                if item.icon:
                    icon = self.asset_manager.get_image(item.icon)
                    if icon:
                        scaled_icon = pygame.transform.scale(icon, (slot_size - 10, slot_size - 10))
                        equipment_surface.blit(scaled_icon, (slot_rect.x + 5, slot_rect.y + 5))
                if hasattr(self, 'mouse_pos'):
                    abs_slot_rect = slot_rect.copy()
                    abs_slot_rect.x += panel_x
                    abs_slot_rect.y += panel_y
                    if abs_slot_rect.collidepoint(self.mouse_pos):
                        self._render_equipment_tooltip(screen, item, self.mouse_pos)
            else:
                icon_surface = self.asset_manager.fonts.render_text(default_icon, 36, Colors.UI_TEXT_DARK)
                icon_rect = icon_surface.get_rect(center=slot_rect.center)
                equipment_surface.blit(icon_surface, icon_rect)
            abs_rect = slot_rect.copy()
            abs_rect.x += panel_x
            abs_rect.y += panel_y
            self.equipment_slot_rects[slot_key] = abs_rect
        screen.blit(equipment_surface, (panel_x, panel_y))
        inventory_width = 500  
        inventory_x = panel_x + equipment_width + 20
        self.inventory_panel_rect = pygame.Rect(inventory_x, panel_y, inventory_width, equipment_height)
        panel_surface = pygame.Surface((inventory_width, equipment_height), pygame.SRCALPHA)
        if self.inventory_panel_focused:
            pygame.draw.rect(panel_surface, Colors.UI_BG, (0, 0, inventory_width, equipment_height))
            pygame.draw.rect(panel_surface, Colors.UI_HIGHLIGHT, (0, 0, inventory_width, equipment_height), 4)
        else:
            pygame.draw.rect(panel_surface, (*Colors.UI_BG, 200), (0, 0, inventory_width, equipment_height))
            pygame.draw.rect(panel_surface, Colors.UI_BORDER, (0, 0, inventory_width, equipment_height), 3)
        pygame.draw.rect(panel_surface, Colors.UI_SECONDARY, (0, 0, inventory_width, title_height))
        pygame.draw.line(panel_surface, Colors.UI_BORDER, (0, title_height), (inventory_width, title_height), 3)
        title_text = GameTexts.INVENTORY_TITLE
        if self.inventory_panel_focused:
            title_text = "▶ " + title_text
        title_surface = self.asset_manager.fonts.render_text(title_text, 28, Colors.UI_TEXT)
        title_rect = title_surface.get_rect(center=(inventory_width // 2, title_height // 2))
        panel_surface.blit(title_surface, title_rect)
        weight_text = GameTexts.INVENTORY_WEIGHT.format(
            current=len(player.inventory), 
            max=player.max_inventory
        )
        weight_surface = self.asset_manager.fonts.render_text(weight_text, 16, Colors.UI_TEXT_DARK)
        panel_surface.blit(weight_surface, (inventory_width - 180, 15))
        list_x = 20
        list_y = title_height + 20
        list_width = inventory_width - 40
        list_height = equipment_height - title_height - 80
        selected_item_details = None
        if not player.inventory:
            empty_text = GameTexts.INVENTORY_EMPTY
            empty_surface = self.asset_manager.fonts.render_text(empty_text, 24, Colors.UI_TEXT_DARK)
            empty_rect = empty_surface.get_rect(center=(inventory_width // 2, equipment_height // 2))
            panel_surface.blit(empty_surface, empty_rect)
        else:
            items_per_row = 2  
            item_width = (list_width - 10) // items_per_row
            item_height = 90
            visible_rows = list_height // item_height
            total_rows = (len(player.inventory) + items_per_row - 1) // items_per_row
            scroll_offset = self.inventory_scroll_offset
            for i, item in enumerate(player.inventory):
                row = i // items_per_row
                col = i % items_per_row
                if row < scroll_offset or row >= scroll_offset + visible_rows:
                    continue
                item_x = list_x + col * item_width
                item_y = list_y + (row - scroll_offset) * item_height
                item_rect = pygame.Rect(item_x, item_y, item_width - 10, item_height - 10)
                rarity_colors = {
                    'common': Colors.UI_BORDER,
                    'uncommon': Colors.NEON_GREEN,
                    'rare': Colors.NEON_BLUE,
                    'epic': Colors.NEON_PURPLE,
                    'legendary': Colors.NEON_YELLOW
                }
                border_color = rarity_colors.get(item.rarity, Colors.UI_BORDER)
                if i == self.inventory_selection and self.inventory_panel_focused:
                    pygame.draw.rect(panel_surface, (*Colors.UI_HIGHLIGHT, 50), item_rect)
                    pygame.draw.rect(panel_surface, Colors.UI_HIGHLIGHT, item_rect, 3)
                    selected_item_details = (item, player)
                else:
                    pygame.draw.rect(panel_surface, Colors.UI_SECONDARY, item_rect)
                    pygame.draw.rect(panel_surface, border_color, item_rect, 2)
                if item.icon:
                    icon = self.asset_manager.get_image(item.icon)
                    if icon:
                        icon_scaled = pygame.transform.scale(icon, (40, 40))
                        icon_x = item_x + 10
                        icon_y = item_y + (item_height - 50) // 2
                        panel_surface.blit(icon_scaled, (icon_x, icon_y))
                item_name = item.name
                if not item.identified and item.true_name:
                    item_name += " (?)"
                if len(item_name) > 12:
                    item_name = item_name[:10] + "..."
                name_surface = self.asset_manager.fonts.render_text(item_name, 14, Colors.UI_TEXT)
                panel_surface.blit(name_surface, (item_x + 60, item_y + 20))
                if item.item_type == ItemType.WEAPON:
                    desc = f"攻擊+{item.attack_bonus}"
                elif item.item_type == ItemType.ARMOR:
                    desc = f"防禦+{item.defense_bonus}"
                elif item.item_type == ItemType.POTION:
                    desc = "藥水"
                elif item.item_type == ItemType.SCROLL:
                    desc = "卷軸"
                else:
                    desc = ""
                if desc:
                    desc_surface = self.asset_manager.fonts.render_text(desc, 12, Colors.UI_TEXT_DARK)
                    panel_surface.blit(desc_surface, (item_x + 60, item_y + 40))
        help_y = equipment_height - 40
        help_text = "方向鍵選擇 | 空白鍵使用 | DELETE丟棄 | V販賣 | Tab切換到技能"
        help_surface = self.asset_manager.fonts.render_text(help_text, 14, Colors.UI_TEXT)
        help_rect = help_surface.get_rect(center=(inventory_width // 2, help_y))
        panel_surface.blit(help_surface, help_rect)
        screen.blit(panel_surface, (inventory_x, panel_y))
        detail_width = 280
        detail_x = inventory_x + inventory_width + 20
        detail_rect = pygame.Rect(detail_x, panel_y, detail_width, equipment_height)
        detail_surface = pygame.Surface((detail_width, equipment_height), pygame.SRCALPHA)
        pygame.draw.rect(detail_surface, Colors.UI_BG, (0, 0, detail_width, equipment_height))
        pygame.draw.rect(detail_surface, Colors.UI_BORDER, (0, 0, detail_width, equipment_height), 3)
        pygame.draw.rect(detail_surface, Colors.UI_SECONDARY, (0, 0, detail_width, title_height))
        pygame.draw.line(detail_surface, Colors.UI_BORDER, (0, title_height), (detail_width, title_height), 2)
        detail_title = self.asset_manager.fonts.render_text("物品詳情", 24, Colors.UI_TEXT)
        detail_title_rect = detail_title.get_rect(center=(detail_width // 2, title_height // 2))
        detail_surface.blit(detail_title, detail_title_rect)
        if selected_item_details and self.inventory_panel_focused:
            item, player = selected_item_details
            icon_y = title_height + 20
            if item.icon:
                icon = self.asset_manager.get_image(item.icon)
                if icon:
                    icon_scaled = pygame.transform.scale(icon, (64, 64))
                    icon_x = (detail_width - 64) // 2
                    detail_surface.blit(icon_scaled, (icon_x, icon_y))
            name_y = icon_y + 80
            name_surface = self.asset_manager.fonts.render_text(item.name, 24, Colors.UI_TEXT)  
            name_rect = name_surface.get_rect(center=(detail_width // 2, name_y))
            detail_surface.blit(name_surface, name_rect)
            rarity_names = {
                'common': '普通',
                'uncommon': '精良',
                'rare': '稀有',
                'epic': '史詩',
                'legendary': '傳說'
            }
            rarity_colors = {
                'common': Colors.UI_TEXT_DARK,
                'uncommon': Colors.NEON_GREEN,
                'rare': Colors.NEON_BLUE,
                'epic': Colors.NEON_PURPLE,
                'legendary': Colors.NEON_YELLOW
            }
            rarity_text = rarity_names.get(item.rarity, '普通')
            rarity_color = rarity_colors.get(item.rarity, Colors.UI_TEXT_DARK)
            rarity_y = name_y + 30
            rarity_surface = self.asset_manager.fonts.render_text(f"品質: {rarity_text}", 18, rarity_color)  
            rarity_rect = rarity_surface.get_rect(center=(detail_width // 2, rarity_y))
            detail_surface.blit(rarity_surface, rarity_rect)
            line_y = rarity_y + 30
            pygame.draw.line(detail_surface, Colors.UI_BORDER, (20, line_y), (detail_width - 20, line_y), 1)
            attr_y = line_y + 20
            attr_x = 30
            # 標記：記錄是否已經顯示過攻擊力加成（針對力量藥水的特殊處理）
            attack_bonus_displayed = False
            
            if item.identified or item.item_type != ItemType.POTION:
                if item.item_type == ItemType.WEAPON and item.attack_bonus > 0:
                    attack_surface = self.asset_manager.fonts.render_text(f"攻擊力 +{item.attack_bonus}", 18, Colors.NEON_ORANGE)
                    detail_surface.blit(attack_surface, (attr_x, attr_y))
                    attr_y += 25
                if item.item_type in [ItemType.ARMOR, ItemType.SHIELD, ItemType.HELMET, ItemType.BOOTS] and item.defense_bonus > 0:
                    defense_surface = self.asset_manager.fonts.render_text(f"防禦力 +{item.defense_bonus}", 18, Colors.NEON_CYAN)
                    detail_surface.blit(defense_surface, (attr_x, attr_y))
                    attr_y += 25
                if item.item_type == ItemType.BOOTS and item.move_speed_bonus != 0:
                    speed_text = f"移動速度 {'+' if item.move_speed_bonus > 0 else ''}{item.move_speed_bonus}"
                    speed_color = Colors.NEON_GREEN if item.move_speed_bonus > 0 else Colors.HEALTH_RED
                    speed_surface = self.asset_manager.fonts.render_text(speed_text, 18, speed_color)
                    detail_surface.blit(speed_surface, (attr_x, attr_y))
                    attr_y += 25
                if item.item_type == ItemType.POTION:
                    if item.heal_amount != 0:
                        if item.heal_amount > 0:
                            heal_text = f"恢復生命 {item.heal_amount}"
                            heal_color = Colors.NEON_GREEN
                        else:
                            heal_text = f"造成傷害 {-item.heal_amount}"
                            heal_color = Colors.HEALTH_RED
                        heal_surface = self.asset_manager.fonts.render_text(heal_text, 18, heal_color)
                        detail_surface.blit(heal_surface, (attr_x, attr_y))
                        attr_y += 25
                    elif item.mana_amount > 0:
                        mana_surface = self.asset_manager.fonts.render_text(f"恢復魔力 {item.mana_amount}", 18, Colors.MANA_BLUE)
                        detail_surface.blit(mana_surface, (attr_x, attr_y))
                        attr_y += 25
                    elif item.special_effect == 'move_speed':
                        effect_text = "移動速度 +20% (30秒)"
                        effect_surface = self.asset_manager.fonts.render_text(effect_text, 18, Colors.NEON_GREEN)
                        detail_surface.blit(effect_surface, (attr_x, attr_y))
                        attr_y += 25
                    elif item.special_effect == 'strength':
                        bonus = item.attack_bonus if hasattr(item, 'attack_bonus') and item.attack_bonus > 0 else 5
                        effect_text = f"攻擊力 +{bonus} (暫時)"
                        effect_surface = self.asset_manager.fonts.render_text(effect_text, 18, Colors.NEON_ORANGE)
                        detail_surface.blit(effect_surface, (attr_x, attr_y))
                        attr_y += 25
                        attack_bonus_displayed = True  # 標記已經顯示過攻擊力加成
            else:
                unknown_surface = self.asset_manager.fonts.render_text("效果：未知", 18, Colors.UI_TEXT_DARK)
                detail_surface.blit(unknown_surface, (attr_x, attr_y))
                attr_y += 25
            
            # 刪除了重複顯示攻擊力的代碼部分
            # 以下這段代碼被刪除，因為它會導致力量藥水的攻擊力加成顯示兩次
            # if item.attack_bonus > 0:
            #     attack_surface = self.asset_manager.fonts.render_text(f"攻擊力 +{item.attack_bonus}", 18, Colors.NEON_ORANGE)
            #     detail_surface.blit(attack_surface, (attr_x, attr_y))
            #     attr_y += 25
            # if item.defense_bonus > 0:
            #     defense_surface = self.asset_manager.fonts.render_text(f"防禦力 +{item.defense_bonus}", 18, Colors.NEON_CYAN)
            #     detail_surface.blit(defense_surface, (attr_x, attr_y))
            #     attr_y += 25
            # ...等等其他重複的屬性顯示代碼
            
            if item.item_type in [ItemType.WEAPON, ItemType.ARMOR, ItemType.SHIELD, ItemType.HELMET, ItemType.BOOTS]:
                compare_y = attr_y + 10
                pygame.draw.line(detail_surface, Colors.UI_BORDER, (20, compare_y), (detail_width - 20, compare_y), 1)
                compare_y += 15
                compare_title = self.asset_manager.fonts.render_text("裝備比較", 16, Colors.UI_TEXT_DARK)
                detail_surface.blit(compare_title, (attr_x, compare_y))
                compare_y += 25
                slot_map = {
                    ItemType.WEAPON: 'weapon',
                    ItemType.ARMOR: 'armor',
                    ItemType.SHIELD: 'shield',
                    ItemType.HELMET: 'helmet',
                    ItemType.BOOTS: 'boots'
                }
                slot = slot_map.get(item.item_type)
                current_item = player.equipment.get(slot) if slot else None
                if current_item:
                    if item.attack_bonus > 0 or (current_item and current_item.attack_bonus > 0):
                        current_attack = current_item.attack_bonus if current_item else 0
                        diff = item.attack_bonus - current_attack
                        if diff > 0:
                            symbol = "↑"
                            color = Colors.NEON_GREEN
                        elif diff < 0:
                            symbol = "↓"
                            color = Colors.HEALTH_RED
                        else:
                            symbol = "="
                            color = Colors.UI_TEXT_DARK
                        compare_text = f"攻擊: {current_attack} → {item.attack_bonus} {symbol}"
                        compare_surface = self.asset_manager.fonts.render_text(compare_text, 16, color)
                        detail_surface.blit(compare_surface, (attr_x, compare_y))
                        compare_y += 22
                    if item.defense_bonus > 0 or (current_item and current_item.defense_bonus > 0):
                        current_defense = current_item.defense_bonus if current_item else 0
                        diff = item.defense_bonus - current_defense
                        if diff > 0:
                            symbol = "↑"
                            color = Colors.NEON_GREEN
                        elif diff < 0:
                            symbol = "↓"
                            color = Colors.HEALTH_RED
                        else:
                            symbol = "="
                            color = Colors.UI_TEXT_DARK
                        compare_text = f"防禦: {current_defense} → {item.defense_bonus} {symbol}"
                        compare_surface = self.asset_manager.fonts.render_text(compare_text, 16, color)
                        detail_surface.blit(compare_surface, (attr_x, compare_y))
                        compare_y += 22
                    if item.item_type == ItemType.BOOTS:
                        current_speed = current_item.move_speed_bonus if current_item else 0
                        if item.move_speed_bonus != 0 or current_speed != 0:
                            diff = item.move_speed_bonus - current_speed
                            if diff > 0:
                                symbol = "↑"
                                color = Colors.NEON_GREEN
                            elif diff < 0:
                                symbol = "↓"
                                color = Colors.HEALTH_RED
                            else:
                                symbol = "="
                                color = Colors.UI_TEXT_DARK
                            compare_text = f"移速: {current_speed} → {item.move_speed_bonus} {symbol}"
                            compare_surface = self.asset_manager.fonts.render_text(compare_text, 16, color)
                            detail_surface.blit(compare_surface, (attr_x, compare_y))
                            compare_y += 22
            # 描述文字 - 修復重疊問題
            desc_y = equipment_height - 160
            pygame.draw.line(detail_surface, Colors.UI_BORDER, (20, desc_y - 10), (detail_width - 20, desc_y - 10), 1)
            
            # 根據物品類型和鑑定狀態獲取描述文字
            if item.identified or item.item_type != ItemType.POTION:
                if item.item_type == ItemType.POTION and item.identified:
                    if item.heal_amount > 0:
                        desc_text = f"恢復{item.heal_amount}點生命值的治療藥水"
                    elif item.heal_amount < 0:
                        desc_text = f"造成{-item.heal_amount}點傷害的毒藥"
                    elif item.mana_amount > 0:
                        desc_text = f"恢復{item.mana_amount}點魔力值的魔力藥水"
                    elif item.special_effect == 'move_speed':
                        desc_text = "暫時提升20%移動速度的疾風藥水（持續30秒）"
                    elif item.special_effect == 'strength':
                        bonus = item.attack_bonus if hasattr(item, 'attack_bonus') and item.attack_bonus > 0 else 5
                        desc_text = f"暫時提升{bonus}點攻擊力的力量藥水"
                    else:
                        desc_text = item.description
                else:
                    desc_text = item.description
            else:
                desc_text = "一瓶神秘的藥水，不知道會有什麼效果..."
            
            # 只渲染一次描述文字（移除了重複的渲染代碼）
            desc_lines = self._wrap_text(desc_text, detail_width - 40, 16)
            max_lines = 3
            for i, line in enumerate(desc_lines[:max_lines]):
                line_surface = self.asset_manager.fonts.render_text(line, 16, Colors.UI_TEXT_DARK)
                detail_surface.blit(line_surface, (20, desc_y + i * 22))
            
            if len(desc_lines) > max_lines:
                ellipsis_surface = self.asset_manager.fonts.render_text("...", 16, Colors.UI_TEXT_DARK)
                detail_surface.blit(ellipsis_surface, (detail_width - 40, desc_y + (max_lines - 1) * 22))
            
            # 價值顯示
            value_y = equipment_height - 50
            value_surface = self.asset_manager.fonts.render_text(f"價值: {item.value} 金幣", 18, Colors.EXP_YELLOW)
            value_rect = value_surface.get_rect(center=(detail_width // 2, value_y))
            detail_surface.blit(value_surface, value_rect)
        else:
            hint_text = "選擇一個物品查看詳情"
            hint_surface = self.asset_manager.fonts.render_text(hint_text, 20, Colors.UI_TEXT_DARK)  
            hint_rect = hint_surface.get_rect(center=(detail_width // 2, equipment_height // 2))
            detail_surface.blit(hint_surface, hint_rect)
        screen.blit(detail_surface, (detail_x, panel_y))
        skill_panel_width = 580
        skill_panel_x = detail_x + detail_width + 20
        self.skill_panel_rect = pygame.Rect(skill_panel_x, panel_y, skill_panel_width, equipment_height)
        self.render_skill_management_improved(screen, player, skill_panel_x, panel_y, skill_panel_width, equipment_height)
        stats_height = 130
        stats_y = panel_y + equipment_height + 10
        stats_width = total_width
        stats_surface = pygame.Surface((stats_width, stats_height), pygame.SRCALPHA)
        pygame.draw.rect(stats_surface, Colors.UI_BG, (0, 0, stats_width, stats_height))
        pygame.draw.rect(stats_surface, Colors.UI_BORDER, (0, 0, stats_width, stats_height), 3)
        stats_title_height = 35
        pygame.draw.rect(stats_surface, Colors.UI_SECONDARY, (0, 0, stats_width, stats_title_height))
        pygame.draw.line(stats_surface, Colors.UI_BORDER, (0, stats_title_height), (stats_width, stats_title_height), 2)
        stats_title = self.asset_manager.fonts.render_text("角色屬性", 20, Colors.UI_TEXT)
        stats_title_rect = stats_title.get_rect(center=(stats_width // 2, stats_title_height // 2))
        stats_surface.blit(stats_title, stats_title_rect)
        total_attack = player.get_total_attack()
        total_defense = player.get_total_defense()
        total_move_speed = player.get_total_move_speed()
        attribute_y = stats_title_height + 15
        col_width = stats_width // 4
        col1_x = 30
        attributes_col1 = [
            ("等級", f"Lv.{player.stats.level}", Colors.EXP_YELLOW),
            ("經驗值", f"{player.stats.exp}/{player.stats.exp_to_next}", Colors.EXP_YELLOW),
            ("金幣", f"{player.gold}", Colors.EXP_YELLOW),
        ]
        col2_x = col1_x + col_width
        attributes_col2 = [
            ("生命值", f"{player.stats.hp}/{player.stats.max_hp}", Colors.HEALTH_RED),
            ("魔力值", f"{player.stats.mp}/{player.stats.max_mp}", Colors.MANA_BLUE),
            ("護盾", "啟用" if player.shield_active else "未啟用", 
             Colors.NEON_CYAN if player.shield_active else Colors.UI_TEXT_DARK),
        ]
        col3_x = col2_x + col_width
        boots_speed_bonus = 0
        if player.equipment.get('boots'):
            boots_speed_bonus = player.equipment['boots'].move_speed_bonus
        attributes_col3 = [
            ("攻擊力", f"{total_attack} (+{total_attack-player.stats.attack})", Colors.NEON_ORANGE),
            ("防禦力", f"{total_defense} (+{total_defense-player.stats.defense})", Colors.NEON_CYAN),
            ("移動速度", f"{int(total_move_speed)} (+{boots_speed_bonus})", Colors.NEON_GREEN),
        ]
        col4_x = col3_x + col_width
        attributes_col4 = [
            ("暴擊率", f"{int(player.stats.crit_chance * 100)}%", Colors.NEON_YELLOW),
            ("暴擊傷害", f"{player.stats.crit_damage}x", Colors.NEON_ORANGE),
            ("背包", f"{len(player.inventory)}/{player.max_inventory}", Colors.UI_TEXT),
        ]
        row_height = 25
        for i, columns in enumerate([(col1_x, attributes_col1), (col2_x, attributes_col2), 
                                     (col3_x, attributes_col3), (col4_x, attributes_col4)]):
            x, attrs = columns
            for j, (label, value, color) in enumerate(attrs):
                y = attribute_y + j * row_height
                label_surface = self.asset_manager.fonts.render_text(f"{label}：", 16, Colors.UI_TEXT)
                stats_surface.blit(label_surface, (x, y))
                value_surface = self.asset_manager.fonts.render_text(value, 16, color)
                stats_surface.blit(value_surface, (x + 80, y))
        screen.blit(stats_surface, (panel_x, stats_y))

    def render_skill_management_improved(self, surface, player: Player, x: int, y: int, width: int, height: int):
        """渲染技能管理界面（改進版）"""
        # 背景（根據焦點調整）
        skill_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        if not self.inventory_panel_focused:
            pygame.draw.rect(skill_surface, Colors.UI_BG, (0, 0, width, height))
            pygame.draw.rect(skill_surface, Colors.NEON_PURPLE, (0, 0, width, height), 4)
        else:
            pygame.draw.rect(skill_surface, (*Colors.UI_BG, 200), (0, 0, width, height))
            pygame.draw.rect(skill_surface, Colors.UI_BORDER, (0, 0, width, height), 3)
        
        # 標題
        title_height = 60
        pygame.draw.rect(skill_surface, (*Colors.UI_SECONDARY, 220), (0, 0, width, title_height))
        pygame.draw.line(skill_surface, Colors.UI_BORDER, (0, title_height), (width, title_height), 3)
        
        # 標題文字（帶焦點指示）
        title_text = "技能管理"
        if not self.inventory_panel_focused:
            title_text = "▶ " + title_text
        title_surface = self.asset_manager.fonts.render_text(title_text, 28, Colors.WHITE)
        title_rect = title_surface.get_rect(center=(width // 2, title_height // 2))
        skill_surface.blit(title_surface, title_rect)
        
        # 清空按鈕矩形記錄
        self.skill_upgrade_rects.clear()
        self.skill_equip_rects.clear()
        
        # 已學技能列表
        learned_skills = player.get_learned_skills()
        list_y = title_height + 20
        skill_height = 120
        
        if not learned_skills:
            # 提示信息
            hint_lines = [
                "還沒有學會任何技能！",
                "",
                "使用卷軸學習新技能：",
                "• 火球術卷軸 → 學會火球術",
                "• 治療術卷軸 → 學會治癒術",
                "• 傳送術卷軸 → 學會瞬間移動"
            ]
            
            y_offset = height // 2 - len(hint_lines) * 15
            for line in hint_lines:
                hint_surface = self.asset_manager.fonts.render_text(line, 18, Colors.UI_TEXT_DARK)
                hint_rect = hint_surface.get_rect(center=(width // 2, y_offset))
                skill_surface.blit(hint_surface, hint_rect)
                y_offset += 30
        else:
            # 可滾動區域計算
            visible_skills = (height - title_height - 120) // (skill_height + 10)
            scroll_offset = max(0, self.skill_selection - visible_skills + 1)
            
            # 渲染每個已學技能
            for i, skill in enumerate(learned_skills):
                # 跳過不可見的技能
                if i < scroll_offset or i >= scroll_offset + visible_skills:
                    continue
                    
                skill_y = list_y + (i - scroll_offset) * (skill_height + 10)
                
                # 技能框
                skill_rect = pygame.Rect(10, skill_y, width - 20, skill_height)
                
                # 選中高亮（只在技能面板有焦點時顯示）
                is_selected = (i == self.skill_selection and not self.inventory_panel_focused)
                
                if is_selected:
                    pygame.draw.rect(skill_surface, (*Colors.NEON_PURPLE, 100), skill_rect)
                    pygame.draw.rect(skill_surface, Colors.NEON_PURPLE, skill_rect, 3)
                elif skill.slot_index != -1:
                    pygame.draw.rect(skill_surface, (*Colors.UI_HIGHLIGHT, 50), skill_rect)
                    pygame.draw.rect(skill_surface, Colors.NEON_CYAN, skill_rect, 2)
                else:
                    pygame.draw.rect(skill_surface, (*Colors.UI_SECONDARY, 100), skill_rect)
                    pygame.draw.rect(skill_surface, Colors.UI_BORDER, skill_rect, 2)
                
                # 技能圖標和等級
                icon_size = 60
                icon_x = 20
                icon_y = skill_y + (skill_height - icon_size) // 2
                
                # 等級星星
                for star in range(skill.max_level):
                    star_x = icon_x + star * 12
                    star_y = icon_y - 15
                    color = Colors.EXP_YELLOW if star < skill.current_level else Colors.UI_SECONDARY
                    
                    star_points = []
                    for angle in range(0, 360, 36):
                        rad = math.radians(angle)
                        r = 5 if angle % 72 == 0 else 2
                        px = star_x + 5 + r * math.cos(rad)
                        py = star_y + 5 + r * math.sin(rad)
                        star_points.append((px, py))
                    
                    pygame.draw.polygon(skill_surface, color, star_points)
                
                # 技能圖標
                icon_bg = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                icon_color = Colors.UI_HIGHLIGHT if is_selected else Colors.UI_SECONDARY
                pygame.draw.rect(icon_bg, icon_color, (0, 0, icon_size, icon_size))
                pygame.draw.rect(icon_bg, Colors.UI_BORDER, (0, 0, icon_size, icon_size), 3)
                
                # 技能圖標文字
                icon_text = skill.name[0] if skill.name else "?"
                icon_font = self.asset_manager.fonts.render_text(icon_text, 28, Colors.WHITE)
                icon_rect = icon_font.get_rect(center=(icon_size // 2, icon_size // 2))
                icon_bg.blit(icon_font, icon_rect)
                
                skill_surface.blit(icon_bg, (icon_x, icon_y))
                
                # 技能信息
                info_x = icon_x + icon_size + 15
                
                # 技能名稱
                name_text = f"{skill.name} Lv.{skill.current_level}/{skill.max_level}"
                name_surface = self.asset_manager.fonts.render_text(name_text, 20, Colors.WHITE)
                skill_surface.blit(name_surface, (info_x, skill_y + 10))
                
                # 當前效果
                current_desc = skill.get_level_description(skill.current_level)
                desc_lines = self._wrap_text(current_desc, width - info_x - 130, 14)
                desc_y = skill_y + 35
                for line in desc_lines[:2]:  # 最多顯示2行
                    desc_surface = self.asset_manager.fonts.render_text(line, 14, Colors.UI_TEXT)
                    skill_surface.blit(desc_surface, (info_x, desc_y))
                    desc_y += 18
                
                # 裝備狀態
                if skill.slot_index != -1:
                    key_text = f"已裝備在快捷鍵 {skill.slot_index + 1}"
                    key_surface = self.asset_manager.fonts.render_text(key_text, 14, Colors.NEON_CYAN)
                    skill_surface.blit(key_surface, (info_x, skill_y + 75))
                
                # 按鈕區域
                button_x = width - 120
                
                # 升級按鈕
                if not skill.is_max_level:
                    button_y = skill_y + 10
                    button_rect = pygame.Rect(button_x, button_y, 100, 30)
                    self.skill_upgrade_rects[i] = pygame.Rect(x + button_x, y + button_y, 100, 30)
                    
                    scrolls_needed, gold_needed = skill.get_upgrade_cost()
                    scroll_count = player.count_skill_scrolls(skill.id)
                    can_upgrade = scroll_count >= scrolls_needed and player.gold >= gold_needed
                    
                    if can_upgrade:
                        button_color = Colors.NEON_GREEN
                        text_color = Colors.BLACK
                    else:
                        button_color = Colors.UI_SECONDARY
                        text_color = Colors.UI_TEXT_DARK
                    
                    if is_selected:
                        pygame.draw.rect(skill_surface, Colors.WHITE, button_rect, 2)
                    
                    pygame.draw.rect(skill_surface, button_color, button_rect)
                    pygame.draw.rect(skill_surface, Colors.UI_BORDER, button_rect, 2)
                    
                    upgrade_text = "升級 (空白鍵)"
                    upgrade_surface = self.asset_manager.fonts.render_text(upgrade_text, 14, text_color)
                    upgrade_rect = upgrade_surface.get_rect(center=button_rect.center)
                    skill_surface.blit(upgrade_surface, upgrade_rect)
                    
                    # 消耗顯示
                    cost_y = button_y + 35
                    cost_text = f"需要: {scrolls_needed}卷 {gold_needed}金"
                    cost_color = Colors.NEON_GREEN if can_upgrade else Colors.HEALTH_RED
                    cost_surface = self.asset_manager.fonts.render_text(cost_text, 12, cost_color)
                    skill_surface.blit(cost_surface, (button_x - 20, cost_y))
                
                # 裝備/卸下按鈕
                equip_button_y = skill_y + 70
                equip_rect = pygame.Rect(button_x, equip_button_y, 100, 30)
                self.skill_equip_rects[i] = pygame.Rect(x + button_x, y + equip_button_y, 100, 30)
                
                if skill.slot_index == -1:
                    equip_text = "裝備 (1-4)"
                    button_color = Colors.NEON_CYAN
                    text_color = Colors.BLACK
                else:
                    equip_text = "卸下 (左鍵)"
                    button_color = Colors.UI_SECONDARY
                    text_color = Colors.UI_TEXT
                
                if is_selected:
                    pygame.draw.rect(skill_surface, Colors.WHITE, equip_rect, 2)
                
                pygame.draw.rect(skill_surface, button_color, equip_rect)
                pygame.draw.rect(skill_surface, Colors.UI_BORDER, equip_rect, 2)
                
                equip_surface = self.asset_manager.fonts.render_text(equip_text, 14, text_color)
                equip_text_rect = equip_surface.get_rect(center=equip_rect.center)
                skill_surface.blit(equip_surface, equip_text_rect)
        
        # 快捷欄預覽
        hotbar_y = height - 100
        pygame.draw.line(skill_surface, Colors.UI_BORDER, (10, hotbar_y - 10), (width - 10, hotbar_y - 10), 2)
        
        hotbar_title = "技能快捷欄"
        if not self.inventory_panel_focused:
            hotbar_title += " (按數字鍵快速裝備)"
        hotbar_surface = self.asset_manager.fonts.render_text(hotbar_title, 16, Colors.UI_TEXT)
        skill_surface.blit(hotbar_surface, (15, hotbar_y))
        
        # 顯示4個快捷欄位
        slot_size = 50
        slot_spacing = 15
        total_slots_width = 4 * slot_size + 3 * slot_spacing
        slot_x_start = (width - total_slots_width) // 2
        slot_y = hotbar_y + 30
        
        for i in range(4):
            slot_x = slot_x_start + i * (slot_size + slot_spacing)
            slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)
            
            if player.equipped_skills[i]:
                skill = player.equipped_skills[i]
                # 有技能
                pygame.draw.rect(skill_surface, Colors.UI_HIGHLIGHT, slot_rect)
                pygame.draw.rect(skill_surface, Colors.NEON_CYAN, slot_rect, 3)
                
                # 技能名稱首字
                skill_char = skill.name[0]
                char_surface = self.asset_manager.fonts.render_text(skill_char, 24, Colors.WHITE)
                char_rect = char_surface.get_rect(center=slot_rect.center)
                skill_surface.blit(char_surface, char_rect)
                
                # 等級標記
                if skill.current_level > 1:
                    lv_text = f"Lv{skill.current_level}"
                    lv_surface = self.asset_manager.fonts.render_text(lv_text, 10, Colors.EXP_YELLOW)
                    skill_surface.blit(lv_surface, (slot_x + slot_size - 20, slot_y + 2))
            else:
                # 空位
                pygame.draw.rect(skill_surface, Colors.UI_SECONDARY, slot_rect)
                pygame.draw.rect(skill_surface, Colors.UI_BORDER, slot_rect, 2)
                
                # 空位提示
                empty_surface = self.asset_manager.fonts.render_text("空", 16, Colors.UI_TEXT_DARK)
                empty_rect = empty_surface.get_rect(center=slot_rect.center)
                skill_surface.blit(empty_surface, empty_rect)
            
            # 快捷鍵提示
            key_text = str(i + 1)
            key_bg = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.rect(key_bg, (*Colors.BLACK, 180), (0, 0, 16, 16))
            pygame.draw.rect(key_bg, Colors.WHITE, (0, 0, 16, 16), 1)
            skill_surface.blit(key_bg, (slot_x + 2, slot_y + slot_size - 18))
            
            key_surface = self.asset_manager.fonts.render_text(key_text, 12, Colors.WHITE)
            skill_surface.blit(key_surface, (slot_x + 5, slot_y + slot_size - 16))
        
        surface.blit(skill_surface, (x, y))

    def _render_equipment_tooltip(self, screen, item: Item, pos: tuple):
        """渲染裝備提示框"""
        tooltip_width = 300
        tooltip_height = 200
        
        # 調整位置避免超出螢幕
        x = pos[0] + 20
        y = pos[1]
        
        if x + tooltip_width > WINDOW_WIDTH:
            x = pos[0] - tooltip_width - 20
        if y + tooltip_height > WINDOW_HEIGHT:
            y = WINDOW_HEIGHT - tooltip_height - 10
        
        # 創建提示框表面
        tooltip_surface = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
        pygame.draw.rect(tooltip_surface, (*Colors.UI_BG, 240), (0, 0, tooltip_width, tooltip_height))
        pygame.draw.rect(tooltip_surface, Colors.UI_HIGHLIGHT, (0, 0, tooltip_width, tooltip_height), 3)
        
        # 物品名稱
        y_offset = 15
        name_surface = self.asset_manager.fonts.render_text(item.name, 20, Colors.UI_TEXT)
        tooltip_surface.blit(name_surface, (15, y_offset))
        y_offset += 30
        
        # 稀有度
        rarity_names = {
            'common': '普通',
            'uncommon': '精良',
            'rare': '稀有',
            'epic': '史詩',
            'legendary': '傳說'
        }
        rarity_colors = {
            'common': Colors.UI_TEXT_DARK,
            'uncommon': Colors.NEON_GREEN,
            'rare': Colors.NEON_BLUE,
            'epic': Colors.NEON_PURPLE,
            'legendary': Colors.NEON_YELLOW
        }
        rarity_text = rarity_names.get(item.rarity, '普通')
        rarity_color = rarity_colors.get(item.rarity, Colors.UI_TEXT_DARK)
        rarity_surface = self.asset_manager.fonts.render_text(f"品質: {rarity_text}", 16, rarity_color)
        tooltip_surface.blit(rarity_surface, (15, y_offset))
        y_offset += 30
        
        # 分隔線
        pygame.draw.line(tooltip_surface, Colors.UI_BORDER, (10, y_offset), (tooltip_width - 10, y_offset), 1)
        y_offset += 15
        
        # 屬性
        if item.attack_bonus > 0:
            attack_surface = self.asset_manager.fonts.render_text(f"攻擊力 +{item.attack_bonus}", 16, Colors.NEON_ORANGE)
            tooltip_surface.blit(attack_surface, (15, y_offset))
            y_offset += 25
        
        if item.defense_bonus > 0:
            defense_surface = self.asset_manager.fonts.render_text(f"防禦力 +{item.defense_bonus}", 16, Colors.NEON_CYAN)
            tooltip_surface.blit(defense_surface, (15, y_offset))
            y_offset += 25
        
        if hasattr(item, 'move_speed_bonus') and item.move_speed_bonus != 0:
            speed_text = f"移動速度 +{item.move_speed_bonus}"
            speed_color = Colors.NEON_GREEN if item.move_speed_bonus > 0 else Colors.HEALTH_RED
            speed_surface = self.asset_manager.fonts.render_text(speed_text, 18, speed_color)  # 從16改為18
            tooltip_surface.blit(speed_surface, (15, y_offset))
            y_offset += 25
        
        # 操作提示
        hint_y = tooltip_height - 25
        hint_text = "點擊滑鼠左鍵卸下裝備"
        hint_surface = self.asset_manager.fonts.render_text(hint_text, 14, Colors.UI_TEXT_DARK)
        hint_rect = hint_surface.get_rect(center=(tooltip_width // 2, hint_y))
        tooltip_surface.blit(hint_surface, hint_rect)
        
        # 渲染到螢幕
        screen.blit(tooltip_surface, (x, y))

    def _wrap_text(self, text: str, max_width: int, font_size: int):
        """文字自動換行"""
        font = self.asset_manager.fonts.get_font(font_size)
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        
        if current_line:
            lines.append(current_line.strip())
        
        return lines
    
    def render_menu(self, screen, has_save: bool = False):
        """渲染主選單 - 現代化設計"""
        # 背景效果
        screen.fill(Colors.UI_BG)
        
        # 動態背景粒子
        for i in range(50):
            x = random.randint(0, WINDOW_WIDTH)
            y = random.randint(0, WINDOW_HEIGHT)
            size = random.randint(1, 3)
            alpha = random.randint(20, 60)
            color = (*Colors.NEON_BLUE, alpha)
            pygame.gfxdraw.filled_circle(screen, x, y, size, color)
        
        # 標題
        title_y = 150
        title_surface = self.asset_manager.fonts.render_text(GameTexts.MENU_TITLE, 64, Colors.WHITE)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, title_y))
        
        # 標題發光效果
        for i in range(3):
            glow_surface = title_surface.copy()
            glow_surface.set_alpha(100 - i * 30)
            glow_rect = glow_surface.get_rect(center=(WINDOW_WIDTH // 2, title_y))
            glow_rect.inflate_ip(i * 10, i * 5)
            screen.blit(glow_surface, glow_rect)
        
        screen.blit(title_surface, title_rect)
        
        # 副標題
        subtitle_surface = self.asset_manager.fonts.render_text(GameTexts.MENU_SUBTITLE, 24, Colors.NEON_CYAN)
        subtitle_rect = subtitle_surface.get_rect(center=(WINDOW_WIDTH // 2, title_y + 70))
        screen.blit(subtitle_surface, subtitle_rect)
        
        # 選單選項
        menu_options = [
            (GameTexts.MENU_START, True),
            (GameTexts.MENU_CONTINUE if has_save else "(無存檔)", has_save),
            (GameTexts.MENU_TUTORIAL, True),
            (GameTexts.MENU_SETTINGS, True),
            (GameTexts.MENU_ACHIEVEMENTS, True),
            (GameTexts.MENU_QUIT, True)
        ]
        
        menu_y = 320
        button_spacing = 70
        button_width = 400
        button_height = 55
        
        for i, (option, enabled) in enumerate(menu_options):
            button_x = WINDOW_WIDTH // 2 - button_width // 2
            button_y = menu_y + i * button_spacing
            
            # 按鈕背景
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            
            if not enabled:
                # 禁用的按鈕
                pygame.draw.rect(screen, Colors.UI_SECONDARY, button_rect)
                pygame.draw.rect(screen, Colors.UI_BORDER, button_rect, 2)
                text_color = Colors.UI_TEXT_DARK
            elif i == self.menu_selection:
                # 選中的按鈕
                # 發光效果
                glow_rect = button_rect.inflate(20, 10)
                glow_surface = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(glow_surface, (*Colors.NEON_CYAN, 50), (0, 0, glow_rect.width, glow_rect.height))
                screen.blit(glow_surface, glow_rect)
                
                pygame.draw.rect(screen, Colors.UI_HIGHLIGHT, button_rect)
                pygame.draw.rect(screen, Colors.NEON_CYAN, button_rect, 3)
                
                # 動態邊框
                progress = abs(math.sin(self.animation_time * 3))
                border_color = tuple(int(Colors.NEON_CYAN[i] * (0.5 + progress * 0.5)) for i in range(3))
                pygame.draw.rect(screen, border_color, button_rect.inflate(4, 4), 2)
                
                text_color = Colors.WHITE
            else:
                # 普通按鈕
                pygame.draw.rect(screen, Colors.UI_SECONDARY, button_rect)
                pygame.draw.rect(screen, Colors.UI_BORDER, button_rect, 2)
                text_color = Colors.UI_TEXT
            
            # 按鈕文字
            text_surface = self.asset_manager.fonts.render_text(option, 28, text_color)
            text_rect = text_surface.get_rect(center=button_rect.center)
            screen.blit(text_surface, text_rect)
        
        # 操作提示
        hint_surface = self.asset_manager.fonts.render_text(GameTexts.MENU_HINT, 18, Colors.UI_TEXT_DARK)
        hint_rect = hint_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 80))
        screen.blit(hint_surface, hint_rect)
        
        # 版本信息
        version_text = "基於經典Roguelike設計 | 超精美視覺增強版"
        version_surface = self.asset_manager.fonts.render_text(version_text, 14, Colors.UI_TEXT_DARK)
        screen.blit(version_surface, (30, WINDOW_HEIGHT - 40))

    def render_settings(self, screen, settings: GameSettings):
        """渲染設定界面 - 現代化設計（自適應版本）"""
        # 半透明背景
        overlay = pygame.Surface((self.resolution[0], self.resolution[1]), pygame.SRCALPHA)
        overlay.fill((*Colors.BLACK, 200))
        screen.blit(overlay, (0, 0))
        
        # 根據解析度動態調整面板大小
        base_width = 1100
        base_height = 700
        
        # 計算縮放因子（基於1920x1080的基準解析度）
        scale_x = self.resolution[0] / 1920
        scale_y = self.resolution[1] / 1080
        scale_factor = min(scale_x, scale_y)
        
        # 動態面板大小
        panel_width = min(int(base_width * scale_factor), int(self.resolution[0] * 0.85))
        panel_height = min(int(base_height * scale_factor), int(self.resolution[1] * 0.85))
        
        # 確保最小尺寸
        panel_width = max(panel_width, 900)
        panel_height = max(panel_height, 600)
        
        panel_x = (self.resolution[0] - panel_width) // 2
        panel_y = (self.resolution[1] - panel_height) // 2
        
        # 創建面板表面
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        
        # 背景漸變效果
        for i in range(panel_height):
            alpha = int(20 + (i / panel_height) * 10)
            color = (alpha, alpha, alpha + 5)
            pygame.draw.line(panel_surface, color, (0, i), (panel_width, i))
        
        # 邊框
        pygame.draw.rect(panel_surface, Colors.UI_HIGHLIGHT, (0, 0, panel_width, panel_height), 4)
        
        # 發光效果
        glow_surface = pygame.Surface((panel_width + 20, panel_height + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow_surface, (*Colors.UI_HIGHLIGHT, 30), 
                        (0, 0, panel_width + 20, panel_height + 20))
        screen.blit(glow_surface, (panel_x - 10, panel_y - 10))
        
        # 標題區域
        title_height = 80
        title_surface = pygame.Surface((panel_width, title_height), pygame.SRCALPHA)
        pygame.draw.rect(title_surface, (*Colors.UI_SECONDARY, 180), (0, 0, panel_width, title_height))
        pygame.draw.line(title_surface, Colors.UI_HIGHLIGHT, (0, title_height-1), (panel_width, title_height-1), 3)
        
        # 標題文字
        title_text = self.asset_manager.fonts.render_text(GameTexts.SETTINGS_TITLE, 42, Colors.WHITE)
        title_rect = title_text.get_rect(center=(panel_width // 2, title_height // 2))
        title_surface.blit(title_text, title_rect)
        
        panel_surface.blit(title_surface, (0, 0))
        
        # 動態計算元素間距
        base_spacing = 60
        element_spacing = int(base_spacing * scale_factor)
        element_spacing = max(element_spacing, 50)  # 最小間距
        
        # 內容區域
        content_y = title_height + 30
        left_column_x = int(60 * scale_factor)
        left_column_x = max(left_column_x, 50)  # 最小邊距
        
        # 計算右欄位置（確保有足夠空間）
        column_gap = int(40 * scale_factor)
        column_gap = max(column_gap, 30)
        right_column_x = panel_width // 2 + column_gap
        
        # 確保右欄不會太靠右
        max_right_x = panel_width - 400  # 預留空間給控件
        right_column_x = min(right_column_x, max_right_x)
        
        # === 左側欄：音量和圖像設定 ===
        
        # 音量標題
        volume_title = self.asset_manager.fonts.render_text(GameTexts.SETTINGS_VOLUME, 28, Colors.NEON_CYAN)
        panel_surface.blit(volume_title, (left_column_x, content_y))
        content_y += 45
        
        # 音量滑動條
        self._render_improved_slider(panel_surface, "主音量", settings.master_volume, 
                                left_column_x, content_y, 0)
        content_y += element_spacing
        
        self._render_improved_slider(panel_surface, "音樂音量", settings.music_volume, 
                                left_column_x, content_y, 1)
        content_y += element_spacing
        
        self._render_improved_slider(panel_surface, "音效音量", settings.sfx_volume, 
                                left_column_x, content_y, 2)
        content_y += int(element_spacing * 1.3)  # 增加段落間距
        
        # 圖像設定標題
        graphics_title = self.asset_manager.fonts.render_text(GameTexts.SETTINGS_GRAPHICS, 28, Colors.NEON_CYAN)
        panel_surface.blit(graphics_title, (left_column_x, content_y))
        content_y += 45
        
        # 全螢幕開關
        self._render_improved_toggle(panel_surface, "全螢幕", settings.fullscreen, 
                                    left_column_x, content_y, 0)
        content_y += element_spacing
        
        # 解析度下拉（只在非全螢幕時顯示）
        if not settings.fullscreen:
            res_text = f"{settings.resolution[0]}x{settings.resolution[1]}"
            self._render_improved_dropdown(panel_surface, "解析度", res_text, 
                                        left_column_x, content_y, 'resolution')
            content_y += element_spacing
        else:
            # 全螢幕模式下，清除解析度下拉框的點擊區域
            if hasattr(self, 'dropdown_rects') and 'resolution' in self.dropdown_rects:
                del self.dropdown_rects['resolution']
        
        # 粒子效果下拉
        self._render_improved_dropdown(panel_surface, "粒子效果", settings.particle_density, 
                                    left_column_x, content_y, 'particle')
        
        # === 右側欄：遊戲設定 ===
        right_content_y = title_height + 30
        
        # 遊戲設定標題
        gameplay_title = self.asset_manager.fonts.render_text(GameTexts.SETTINGS_GAMEPLAY, 28, Colors.NEON_CYAN)
        panel_surface.blit(gameplay_title, (right_column_x, right_content_y))
        right_content_y += 45
        
        # 遊戲設定開關
        toggle_settings = [
            ("自動拾取", settings.auto_pickup, 1),
            ("顯示傷害數字", settings.show_damage_numbers, 2),
            ("顯示小地圖", settings.show_minimap, 3),
            ("顯示敵人血條", settings.show_enemy_health, 4),
            ("顯示工具提示", settings.show_tooltips, 5),
        ]
        
        for label, value, index in toggle_settings:
            self._render_improved_toggle(panel_surface, label, value, 
                                    right_column_x, right_content_y, index)
            right_content_y += element_spacing
        
        # 難度下拉（增加間距確保不會被擠壓）
        right_content_y += int(element_spacing * 0.5)
        self._render_improved_dropdown(panel_surface, "遊戲難度", settings.difficulty, 
                                    right_column_x, right_content_y, 'difficulty')
        
# === 底部按鈕 ===
        button_y = panel_height - 100  # 從 -90 改為 -100，給更多空間
        button_width = 180
        button_height = 50  # 從 55 改為 50
        button_spacing = 30
        total_width = button_width * 2 + button_spacing
        button_start_x = (panel_width - total_width) // 2
        
        # 套用按鈕
        apply_rect = pygame.Rect(button_start_x, button_y, button_width, button_height)
        self._render_modern_button(panel_surface, apply_rect, GameTexts.SETTINGS_APPLY, 
                                Colors.NEON_GREEN, 'apply')
        
        # 取消按鈕
        cancel_rect = pygame.Rect(button_start_x + button_width + button_spacing, 
                                button_y, button_width, button_height)
        self._render_modern_button(panel_surface, cancel_rect, GameTexts.SETTINGS_CANCEL, 
                                Colors.HEALTH_RED, 'cancel')
        
        # 渲染面板到螢幕
        screen.blit(panel_surface, (panel_x, panel_y))
        
        # 渲染下拉選單（在最上層）
        if self.dropdown_open:
            self._render_dropdown_menu(screen, settings, panel_x, panel_y)
        
        # 儲存設定面板位置供點擊檢測使用
        self.settings_panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
        # 調試模式：顯示按鈕點擊區域（可選）
        if hasattr(self, 'debug_mode') and self.debug_mode:
            # 顯示實際的點擊區域
            if hasattr(self, 'button_rects'):
                for button_id, rect in self.button_rects.items():
                    abs_rect = rect.copy()
                    abs_rect.x += panel_x
                    abs_rect.y += panel_y
                    pygame.draw.rect(screen, Colors.NEON_YELLOW, abs_rect, 1)

    def _render_improved_slider(self, surface, label: str, value: float, x: int, y: int, index: int):
        """渲染改進的滑動條（修復數值顯示）"""
        # 標籤
        label_surface = self.asset_manager.fonts.render_text(label, 20, Colors.UI_TEXT)
        surface.blit(label_surface, (x, y))
        
        # 滑動條
        slider_x = x + 180
        slider_y = y + 5
        slider_width = 250
        slider_height = 16
        
        # 背景軌道
        track_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
        pygame.draw.rect(surface, (*Colors.UI_SECONDARY, 150), track_rect, border_radius=8)
        pygame.draw.rect(surface, Colors.UI_BORDER, track_rect, 2, border_radius=8)
        
        # 進度條
        progress_width = int(slider_width * value)
        if progress_width > 0:
            progress_rect = pygame.Rect(slider_x, slider_y, progress_width, slider_height)
            # 漸變效果
            for i in range(slider_height):
                color_intensity = 255 - i * 5
                color = (0, min(255, color_intensity), min(255, color_intensity))
                pygame.draw.line(surface, color, 
                            (slider_x, slider_y + i), 
                            (slider_x + progress_width - 1, slider_y + i))
            
            # 邊框
            pygame.draw.rect(surface, Colors.NEON_CYAN, progress_rect, 2, border_radius=8)
        
        # 滑塊
        handle_x = slider_x + progress_width
        handle_size = 24
        handle_rect = pygame.Rect(handle_x - handle_size // 2, 
                                slider_y - (handle_size - slider_height) // 2, 
                                handle_size, handle_size)
        
        # 滑塊陰影
        shadow_rect = handle_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        pygame.draw.ellipse(surface, (*Colors.BLACK, 100), shadow_rect)
        
        # 滑塊本體
        pygame.draw.ellipse(surface, Colors.WHITE, handle_rect)
        pygame.draw.ellipse(surface, Colors.NEON_CYAN, handle_rect, 2)
        
        # 內圈
        inner_rect = handle_rect.inflate(-8, -8)
        pygame.draw.ellipse(surface, Colors.NEON_CYAN, inner_rect)
        
        # 數值顯示（調整位置避免遮擋）
        value_text = f"{int(value * 100)}%"
        value_surface = self.asset_manager.fonts.render_text(value_text, 16, Colors.WHITE)
        
        # 計算文字寬度以確定背景大小
        text_width = value_surface.get_width()
        text_height = value_surface.get_height()
        
        # 數值背景（加大並調整位置）
        value_bg_width = text_width + 20
        value_bg_height = text_height + 8
        value_bg_x = slider_x + slider_width + 20  # 增加間距
        value_bg_y = y - 2
        
        # 繪製數值背景
        value_bg_rect = pygame.Rect(value_bg_x, value_bg_y, value_bg_width, value_bg_height)
        pygame.draw.rect(surface, (*Colors.UI_BG, 200), value_bg_rect, border_radius=5)
        pygame.draw.rect(surface, Colors.UI_BORDER, value_bg_rect, 1, border_radius=5)
        
        # 繪製數值文字（居中）
        value_text_rect = value_surface.get_rect(center=value_bg_rect.center)
        surface.blit(value_surface, value_text_rect)
        
        # 儲存滑動條區域供點擊檢測
        if not hasattr(self, 'slider_rects'):
            self.slider_rects = {}
        self.slider_rects[index] = pygame.Rect(slider_x, slider_y - 10, slider_width, slider_height + 20)

    def _render_improved_toggle(self, surface, label: str, value: bool, x: int, y: int, index: int):
        """渲染改進的開關（純pygame.draw版本）"""
        # 標籤
        label_surface = self.asset_manager.fonts.render_text(label, 20, Colors.UI_TEXT)
        surface.blit(label_surface, (x, y))
        
        # 開關
        toggle_x = x + 250
        toggle_y = y
        toggle_width = 70
        toggle_height = 35
        
        toggle_rect = pygame.Rect(toggle_x, toggle_y, toggle_width, toggle_height)
        
        # 背景
        bg_color = Colors.NEON_GREEN if value else Colors.UI_SECONDARY
        pygame.draw.rect(surface, bg_color, toggle_rect, border_radius=toggle_height // 2)
        pygame.draw.rect(surface, Colors.UI_BORDER, toggle_rect, 2, border_radius=toggle_height // 2)
        
        # 滑塊
        handle_size = toggle_height - 10
        handle_x = toggle_x + (toggle_width - handle_size - 5 if value else 5)
        handle_y = toggle_y + 5
        
        # 滑塊陰影（使用圓形代替）
        shadow_rect = pygame.Rect(handle_x - 2, handle_y - 2, handle_size + 4, handle_size + 4)
        pygame.draw.ellipse(surface, (*Colors.BLACK, 100), shadow_rect)
        
        # 滑塊本體
        handle_rect = pygame.Rect(handle_x, handle_y, handle_size, handle_size)
        pygame.draw.ellipse(surface, Colors.WHITE, handle_rect)
        
        # 狀態圖標
        if value:
            # 勾號
            check_points = [
                (handle_x + handle_size // 4, handle_y + handle_size // 2),
                (handle_x + handle_size // 2 - 2, handle_y + handle_size * 3 // 4),
                (handle_x + handle_size * 3 // 4, handle_y + handle_size // 4)
            ]
            pygame.draw.lines(surface, Colors.NEON_GREEN, False, check_points, 3)
        else:
            # 叉號
            cross_size = handle_size // 3
            center_x = handle_x + handle_size // 2
            center_y = handle_y + handle_size // 2
            pygame.draw.line(surface, Colors.UI_TEXT_DARK, 
                        (center_x - cross_size, center_y - cross_size),
                        (center_x + cross_size, center_y + cross_size), 3)
            pygame.draw.line(surface, Colors.UI_TEXT_DARK, 
                        (center_x - cross_size, center_y + cross_size),
                        (center_x + cross_size, center_y - cross_size), 3)
        
        # 儲存開關區域供點擊檢測
        if not hasattr(self, 'toggle_rects'):
            self.toggle_rects = {}
        self.toggle_rects[index] = toggle_rect

    def _render_improved_dropdown(self, surface, label: str, value: str, x: int, y: int, dropdown_type: str):
        """渲染改進的下拉選單（修復寬度問題）"""
        # 標籤
        label_surface = self.asset_manager.fonts.render_text(label, 20, Colors.UI_TEXT)
        surface.blit(label_surface, (x, y))
        
        # 下拉框
        dropdown_x = x + 180
        dropdown_y = y
        dropdown_width = 250  # 增加寬度以容納2K+解析度
        dropdown_height = 35
        
        dropdown_rect = pygame.Rect(dropdown_x, dropdown_y, dropdown_width, dropdown_height)
        
        # 背景
        is_open = self.dropdown_open == dropdown_type
        bg_color = (*Colors.UI_HIGHLIGHT, 100) if is_open else (*Colors.UI_SECONDARY, 150)
        pygame.draw.rect(surface, bg_color, dropdown_rect, border_radius=5)
        
        # 邊框
        border_color = Colors.NEON_CYAN if is_open else Colors.UI_BORDER
        pygame.draw.rect(surface, border_color, dropdown_rect, 2, border_radius=5)
        
        # 當前值（縮短過長的文字）
        display_value = str(value)
        if len(display_value) > 15:
            display_value = display_value[:12] + "..."
            
        value_surface = self.asset_manager.fonts.render_text(display_value, 18, Colors.WHITE)
        value_rect = value_surface.get_rect(midleft=(dropdown_x + 15, dropdown_y + dropdown_height // 2))
        surface.blit(value_surface, value_rect)
        
        # 下拉箭頭
        arrow_x = dropdown_x + dropdown_width - 25
        arrow_y = dropdown_y + dropdown_height // 2
        arrow_size = 8
        
        if is_open:
            # 向上箭頭
            pygame.draw.lines(surface, Colors.WHITE, False, [
                (arrow_x - arrow_size, arrow_y + arrow_size // 2),
                (arrow_x, arrow_y - arrow_size // 2),
                (arrow_x + arrow_size, arrow_y + arrow_size // 2)
            ], 2)
        else:
            # 向下箭頭
            pygame.draw.lines(surface, Colors.WHITE, False, [
                (arrow_x - arrow_size, arrow_y - arrow_size // 2),
                (arrow_x, arrow_y + arrow_size // 2),
                (arrow_x + arrow_size, arrow_y - arrow_size // 2)
            ], 2)
        
        # 儲存下拉框區域供點擊檢測
        if not hasattr(self, 'dropdown_rects'):
            self.dropdown_rects = {}
        self.dropdown_rects[dropdown_type] = dropdown_rect

    def _render_modern_button(self, surface, rect: pygame.Rect, text: str, color: tuple, button_id: str):
        """渲染現代風格按鈕（修正儲存相對座標）"""
        # 陰影
        shadow_rect = rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pygame.draw.rect(surface, (*Colors.BLACK, 100), shadow_rect, border_radius=rect.height // 4)
        
        # 按鈕背景
        pygame.draw.rect(surface, color, rect, border_radius=rect.height // 4)
        
        # 高光效果
        highlight_rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height // 2)
        highlight_surface = pygame.Surface((rect.width, rect.height // 2), pygame.SRCALPHA)
        # 填充高光（漸變效果）
        for i in range(rect.height // 2):
            alpha = int(30 * (1 - i / (rect.height // 2)))
            pygame.draw.line(highlight_surface, (*Colors.WHITE, alpha), 
                            (0, i), (rect.width, i))
        
        surface.blit(highlight_surface, (rect.x, rect.y))
        
        # 邊框
        pygame.draw.rect(surface, Colors.WHITE, rect, 3, border_radius=rect.height // 4)
        
        # 文字（修改為黑色並加粗）
        # 獲取字體並設置粗體
        font = self.asset_manager.fonts.get_font(22)
        if hasattr(font, 'bold'):
            font.bold = True
        
        # 渲染黑色文字
        text_surface = font.render(text, True, Colors.BLACK)  # 改為黑色
        
        # 如果第一種方法不行，使用多次渲染來模擬粗體效果
        if not hasattr(font, 'bold'):
            # 創建一個稍大的表面來容納粗體效果
            bold_surface = pygame.Surface((text_surface.get_width() + 2, text_surface.get_height() + 2), pygame.SRCALPHA)
            # 多次渲染文字到不同位置來模擬粗體
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx != 0 or dy != 0:
                        bold_surface.blit(text_surface, (1 + dx, 1 + dy))
            # 最後渲染主文字
            bold_surface.blit(text_surface, (1, 1))
            text_surface = bold_surface
        
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)
        
        # 儲存按鈕區域（注意：這裡儲存的是相對於panel的座標）
        if not hasattr(self, 'button_rects'):
            self.button_rects = {}
        # 創建一個新的矩形，避免修改原始矩形
        button_rect_copy = pygame.Rect(rect.x, rect.y, rect.width, rect.height)
        self.button_rects[button_id] = button_rect_copy

    def _render_dropdown_menu(self, screen, settings: GameSettings, panel_x: int, panel_y: int):
        """渲染下拉選單（修復滑鼠懸停檢測）"""
        if not self.dropdown_open:
            return
            
        # 獲取對應的下拉框矩形
        if not hasattr(self, 'dropdown_rects') or self.dropdown_open not in self.dropdown_rects:
            return
            
        dropdown_rect = self.dropdown_rects[self.dropdown_open]
        
        # 計算下拉選單的絕對位置（緊貼在下拉框下方）
        menu_x = panel_x + dropdown_rect.x
        menu_y = panel_y + dropdown_rect.y + dropdown_rect.height + 2  # 緊貼下拉框
        
        # 獲取選項列表
        if self.dropdown_open == 'resolution':
            options = RESOLUTIONS
            current_value = settings.resolution
        elif self.dropdown_open == 'particle':
            options = ['low', 'medium', 'high']
            current_value = settings.particle_density
        elif self.dropdown_open == 'difficulty':
            options = ['easy', 'normal', 'hard']
            current_value = settings.difficulty
        else:
            return
        
        # 計算選單大小
        menu_width = dropdown_rect.width  # 與下拉框同寬
        option_height = 35
        menu_height = len(options) * option_height + 10
        
        # 確保不超出螢幕（考慮實際解析度）
        if hasattr(self, 'resolution'):
            screen_width, screen_height = self.resolution
        else:
            screen_width, screen_height = screen.get_size()
            
        if menu_x + menu_width > screen_width - 20:
            menu_x = screen_width - menu_width - 20
            
        # 如果選單會超出螢幕底部，改為向上顯示
        if menu_y + menu_height > screen_height - 50:
            menu_y = panel_y + dropdown_rect.y - menu_height - 2  # 顯示在上方
        
        # 繪製選單背景
        menu_surface = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA)
        pygame.draw.rect(menu_surface, (*Colors.UI_BG, 240), (0, 0, menu_width, menu_height))
        pygame.draw.rect(menu_surface, Colors.UI_HIGHLIGHT, (0, 0, menu_width, menu_height), 3)
        
        # 獲取轉換後的滑鼠座標（重要修改）
        # 假設這個方法能訪問遊戲實例或接收轉換後的座標
        mouse_pos = pygame.mouse.get_pos()
        
        # 如果有遊戲實例的引用，使用它來轉換座標
        if hasattr(self, 'game_instance') and hasattr(self.game_instance, 'convert_mouse_pos'):
            mouse_pos = self.game_instance.convert_mouse_pos(pygame.mouse.get_pos())
        elif hasattr(self, 'converted_mouse_pos'):
            # 或者使用預先轉換的座標
            mouse_pos = self.converted_mouse_pos
        
        # 繪製選項
        for i, option in enumerate(options):
            option_y = 5 + i * option_height
            option_rect = pygame.Rect(5, option_y, menu_width - 10, option_height - 5)
            
            # 處理選項文字
            if isinstance(option, tuple):  # 解析度
                option_text = f"{option[0]}x{option[1]}"
                is_current = option == current_value
            else:
                option_text = option
                is_current = option == current_value
            
            # 滑鼠懸停效果（使用轉換後的座標）
            abs_option_rect = pygame.Rect(menu_x + 5, menu_y + option_y, 
                                        menu_width - 10, option_height - 5)
            is_hover = abs_option_rect.collidepoint(mouse_pos)
            
            # 高亮當前選項或懸停選項
            if is_current:
                pygame.draw.rect(menu_surface, Colors.UI_HIGHLIGHT, option_rect)
                text_color = Colors.WHITE
            elif is_hover:
                pygame.draw.rect(menu_surface, (*Colors.UI_HIGHLIGHT, 100), option_rect)
                text_color = Colors.WHITE
            else:
                pygame.draw.rect(menu_surface, Colors.UI_SECONDARY, option_rect)
                text_color = Colors.UI_TEXT
            
            pygame.draw.rect(menu_surface, Colors.UI_BORDER, option_rect, 1)
            
            # 渲染文字
            text_surface = self.asset_manager.fonts.render_text(option_text, 18, text_color)
            text_rect = text_surface.get_rect(center=option_rect.center)
            menu_surface.blit(text_surface, text_rect)
        
        # 渲染到螢幕
        screen.blit(menu_surface, (menu_x, menu_y))
        
        # 儲存下拉選單位置供點擊檢測
        self.dropdown_menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
                
    def render_achievements(self, screen, achievement_system: AchievementSystem):
        """渲染成就界面 - 現代化設計"""
        # 半透明背景
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*Colors.BLACK, 200))
        screen.blit(overlay, (0, 0))
        
        # 成就面板
        panel_width = 1000
        panel_height = 700
        panel_x = (WINDOW_WIDTH - panel_width) // 2
        panel_y = (WINDOW_HEIGHT - panel_height) // 2
        
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.fill(Colors.UI_BG)
        pygame.draw.rect(panel_surface, Colors.EXP_YELLOW, panel_surface.get_rect(), 4)
        
        # 標題
        title_surface = self.asset_manager.fonts.render_text("成就系統", 36, Colors.UI_TEXT)
        title_rect = title_surface.get_rect(centerx=panel_width // 2, y=30)
        panel_surface.blit(title_surface, title_rect)
        
        # 成就統計
        total_achievements = len(achievement_system.achievements)
        unlocked_achievements = sum(1 for a in achievement_system.achievements.values() if a.unlocked)
        progress = unlocked_achievements / total_achievements if total_achievements > 0 else 0
        
        # 進度條
        progress_x = panel_width // 2 - 200
        progress_y = 80
        progress_width = 400
        progress_height = 30
        
        # 進度條背景
        progress_rect = pygame.Rect(progress_x, progress_y, progress_width, progress_height)
        pygame.draw.rect(panel_surface, Colors.UI_SECONDARY, progress_rect)
        pygame.draw.rect(panel_surface, Colors.UI_BORDER, progress_rect, 2)
        
        # 進度條填充
        if progress > 0:
            fill_width = int(progress_width * progress)
            fill_rect = pygame.Rect(progress_x, progress_y, fill_width, progress_height)
            pygame.draw.rect(panel_surface, Colors.EXP_YELLOW, fill_rect)
        
        # 進度文字
        progress_text = f"{unlocked_achievements}/{total_achievements} ({int(progress * 100)}%)"
        progress_surface = self.asset_manager.fonts.render_text(progress_text, 18, Colors.WHITE)
        progress_text_rect = progress_surface.get_rect(center=progress_rect.center)
        panel_surface.blit(progress_surface, progress_text_rect)
        
        # 成就列表
        list_y = 140
        achievement_height = 80
        visible_achievements = 7
        
        achievements_list = list(achievement_system.achievements.values())
        
        # 滾動處理
        total_height = len(achievements_list) * achievement_height
        max_scroll = max(0, total_height - (visible_achievements * achievement_height))
        scroll_offset = min(self.achievement_scroll, max_scroll)
        
        for i, achievement in enumerate(achievements_list):
            y = list_y + i * achievement_height - scroll_offset
            
            # 跳過不可見的成就
            if y < list_y - achievement_height or y > list_y + visible_achievements * achievement_height:
                continue
            
            # 成就框
            achievement_rect = pygame.Rect(50, y, panel_width - 100, achievement_height - 10)
            
            if achievement.unlocked:
                pygame.draw.rect(panel_surface, (*Colors.UI_SECONDARY, 100), achievement_rect)
                pygame.draw.rect(panel_surface, Colors.NEON_GREEN, achievement_rect, 2)
                icon_color = Colors.EXP_YELLOW
                text_color = Colors.UI_TEXT
            else:
                pygame.draw.rect(panel_surface, (*Colors.UI_SECONDARY, 50), achievement_rect)
                pygame.draw.rect(panel_surface, Colors.UI_BORDER, achievement_rect, 2)
                icon_color = Colors.UI_TEXT_DARK
                text_color = Colors.UI_TEXT_DARK
            
            # 成就圖標
            icon_rect = pygame.Rect(60, y + 10, 60, 60)
            pygame.draw.rect(panel_surface, icon_color, icon_rect, 3)
            
            if achievement.unlocked:
                # 獎杯圖標
                trophy_size = 30
                trophy_x = icon_rect.centerx
                trophy_y = icon_rect.centery
                pygame.gfxdraw.filled_circle(panel_surface, trophy_x, trophy_y - 10, 15, Colors.EXP_YELLOW)
                pygame.draw.rect(panel_surface, Colors.EXP_YELLOW, 
                               (trophy_x - 10, trophy_y, 20, 20))
            else:
                # 問號
                question_surface = self.asset_manager.fonts.render_text("?", 36, icon_color)
                question_rect = question_surface.get_rect(center=icon_rect.center)
                panel_surface.blit(question_surface, question_rect)
            
            # 成就名稱
            name_surface = self.asset_manager.fonts.render_text(achievement.name, 20, text_color)
            panel_surface.blit(name_surface, (140, y + 15))
            
            # 成就描述
            desc_surface = self.asset_manager.fonts.render_text(achievement.description, 16, text_color)
            panel_surface.blit(desc_surface, (140, y + 40))
            
            # 解鎖時間
            if achievement.unlocked and achievement.unlock_time:
                time_text = achievement.unlock_time.strftime("%Y-%m-%d %H:%M")
                time_surface = self.asset_manager.fonts.render_text(time_text, 14, Colors.UI_TEXT_DARK)
                panel_surface.blit(time_surface, (panel_width - 250, y + 30))
        
        # 滾動條
        if max_scroll > 0:
            scrollbar_x = panel_width - 40
            scrollbar_y = list_y
            scrollbar_height = visible_achievements * achievement_height
            
            # 滾動條背景
            scrollbar_rect = pygame.Rect(scrollbar_x, scrollbar_y, 20, scrollbar_height)
            pygame.draw.rect(panel_surface, Colors.UI_SECONDARY, scrollbar_rect)
            
            # 滾動條滑塊
            thumb_height = int(scrollbar_height * (scrollbar_height / total_height))
            thumb_y = scrollbar_y + int((scroll_offset / max_scroll) * (scrollbar_height - thumb_height))
            thumb_rect = pygame.Rect(scrollbar_x, thumb_y, 20, thumb_height)
            pygame.draw.rect(panel_surface, Colors.UI_HIGHLIGHT, thumb_rect)
        
        # 返回提示
        hint_text = "按 ESC 返回"
        hint_surface = self.asset_manager.fonts.render_text(hint_text, 18, Colors.UI_TEXT)
        hint_rect = hint_surface.get_rect(center=(panel_width // 2, panel_height - 40))
        panel_surface.blit(hint_surface, hint_rect)
        
        screen.blit(panel_surface, (panel_x, panel_y))
    
    # 檔案: 1.py, 類別: UI

    def render_tutorial(self, screen, tutorial: TutorialSystem):
        """渲染教學界面 - 全新美化增強版"""
        step = tutorial.get_current_step()
        if not step:
            return

        # 基礎字體大小
        title_font_size = 60
        content_font_size = 45 # << 字體放大 2.5 倍 (原為 18)
        line_height = 65 # << 配合大字體的行高

        # 半透明背景
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*Colors.BLACK, 230))
        screen.blit(overlay, (0, 0))

        # 教學面板
        panel_width = 1400
        panel_height = 800
        panel_x = (WINDOW_WIDTH - panel_width) // 2
        panel_y = (WINDOW_HEIGHT - panel_height) // 2

        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.fill(Colors.UI_BG)
        pygame.draw.rect(panel_surface, Colors.NEON_CYAN, panel_surface.get_rect(), 5)

        # 教學標題
        title_surface = self.asset_manager.fonts.render_text(step['title'], title_font_size, Colors.NEON_CYAN)
        title_rect = title_surface.get_rect(centerx=panel_width // 2, y=50)
        panel_surface.blit(title_surface, title_rect)

        # 步驟指示器
        step_indicator = f"第 {tutorial.current_step + 1} / {len(tutorial.tutorial_steps)} 頁"
        indicator_surface = self.asset_manager.fonts.render_text(step_indicator, 24, Colors.UI_TEXT_DARK)
        panel_surface.blit(indicator_surface, (panel_width - 200, 30))
        pygame.draw.line(panel_surface, Colors.UI_BORDER, (50, 130), (panel_width - 50, 130), 2)


        # 教學內容 (支援顏色標記)
        content_y = 160
        
        # 定義顏色標記
        color_map = {
            'KEY': Colors.NEON_YELLOW,    # 按鍵顏色
            'CONCEPT': Colors.NEON_CYAN,  # 遊戲概念顏色
            'UI': Colors.NEON_PINK,       # UI介面元素顏色
            'ACTION': Colors.NEON_GREEN,  # 動作或指令顏色
            'WARN': Colors.HEALTH_RED,    # 警告或注意顏色
        }
        
        for line in step['content']:
            x_offset = 80
            # 使用正規表達式解析帶有標記的文字
            parts = re.split(r'(\[KEY:[^\]]+\]|\[CONCEPT:[^\]]+\]|\[UI:[^\]]+\]|\[ACTION:[^\]]+\]|\[WARN:[^\]]+\])', line)
            
            for part in parts:
                if not part:
                    continue

                tag_match = re.match(r'\[(KEY|CONCEPT|UI|ACTION|WARN):([^\]]+)\]', part)
                
                if tag_match:
                    tag_type, text = tag_match.groups()
                    color = color_map.get(tag_type, Colors.WHITE)
                else:
                    text = part
                    color = Colors.UI_TEXT

                if text:
                    text_surface = self.asset_manager.fonts.render_text(text, content_font_size, color)
                    panel_surface.blit(text_surface, (x_offset, content_y))
                    x_offset += text_surface.get_width()
            
            content_y += line_height

        # 提示文字
        hint_y = panel_height - 90
        hint_surface = self.asset_manager.fonts.render_text(step['hint'], 36, Colors.EXP_YELLOW)
        hint_rect = hint_surface.get_rect(centerx=panel_width // 2, y=hint_y)

        # 提示文字動畫
        pulse = abs(math.sin(self.animation_time * 2))
        hint_surface.set_alpha(int(200 + pulse * 55))
        panel_surface.blit(hint_surface, hint_rect)

        # 跳過提示
        skip_text = "按 [ESC] 可隨時跳過教學"
        skip_surface = self.asset_manager.fonts.render_text(skip_text, 18, Colors.UI_TEXT_DARK)
        panel_surface.blit(skip_surface, (30, panel_height - 40))

        screen.blit(panel_surface, (panel_x, panel_y))
        
    def render_game_over(self, screen, player: Player, dungeon_level: int, turn_count: int, game_stats: GameStats):
        """渲染遊戲結束畫面 - 現代化設計"""
        # 全螢幕暗化背景
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*Colors.BLACK, 240))
        screen.blit(overlay, (0, 0))
        
        # 遊戲結束面板
        panel_width = 800
        panel_height = 650
        panel_x = (WINDOW_WIDTH - panel_width) // 2
        panel_y = (WINDOW_HEIGHT - panel_height) // 2
        
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.fill(Colors.UI_BG)
        pygame.draw.rect(panel_surface, Colors.HEALTH_RED, panel_surface.get_rect(), 5)
        
        # 死亡效果
        for i in range(3):
            death_glow = pygame.Surface((panel_width + i * 20, panel_height + i * 20), pygame.SRCALPHA)
            pygame.draw.rect(death_glow, (*Colors.HEALTH_RED, 50 - i * 15), death_glow.get_rect())
            screen.blit(death_glow, (panel_x - i * 10, panel_y - i * 10))
        
        # 遊戲結束標題
        title_surface = self.asset_manager.fonts.render_text(GameTexts.GAME_OVER_TITLE, 48, Colors.HEALTH_RED)
        title_rect = title_surface.get_rect(centerx=panel_width // 2, y=50)
        panel_surface.blit(title_surface, title_rect)
        
        # 結束描述
        defeat_surface = self.asset_manager.fonts.render_text(GameTexts.GAME_OVER_DEFEAT, 20, Colors.UI_TEXT)
        defeat_rect = defeat_surface.get_rect(centerx=panel_width // 2, y=120)
        panel_surface.blit(defeat_surface, defeat_rect)
        
        # 分隔線
        pygame.draw.line(panel_surface, Colors.UI_BORDER, (50, 170), (panel_width - 50, 170), 2)
        
        # 統計數據 - 兩欄顯示
        stats_y = 200
        left_x = 80
        right_x = panel_width // 2 + 40
        line_height = 35
        
        # 左欄
        left_stats = [
            ("探索深度", GameTexts.STATUS_FLOOR.format(dungeon_level), Colors.NEON_CYAN),
            ("存活回合", f"{turn_count} 回合", Colors.NEON_GREEN),
            ("最終等級", f"Lv.{player.stats.level}", Colors.EXP_YELLOW),
            ("總擊殺數", f"{game_stats.total_kills} 個敵人", Colors.HEALTH_RED),
            ("造成傷害", f"{game_stats.total_damage_dealt}", Colors.NEON_ORANGE),
            ("承受傷害", f"{game_stats.total_damage_taken}", Colors.NEON_PINK),
        ]
        
        # 右欄
        right_stats = [
            ("收集金幣", f"{player.gold} 枚", Colors.EXP_YELLOW),
            ("背包物品", f"{len(player.inventory)} 件", Colors.NEON_CYAN),
            ("總攻擊力", f"{player.get_total_attack()}", Colors.NEON_ORANGE),
            ("總防禦力", f"{player.get_total_defense()}", Colors.NEON_CYAN),
            ("暴擊次數", f"{game_stats.total_critical_hits} 次", Colors.NEON_YELLOW),
            ("技能使用", f"{game_stats.total_skills_used} 次", Colors.NEON_PURPLE),
        ]
        
        # 渲染左欄
        for i, (label, value, color) in enumerate(left_stats):
            label_surface = self.asset_manager.fonts.render_text(label + ":", 18, Colors.UI_TEXT_DARK)
            panel_surface.blit(label_surface, (left_x, stats_y + i * line_height))
            
            value_surface = self.asset_manager.fonts.render_text(value, 20, color)
            panel_surface.blit(value_surface, (left_x + 120, stats_y + i * line_height))
        
        # 渲染右欄
        for i, (label, value, color) in enumerate(right_stats):
            label_surface = self.asset_manager.fonts.render_text(label + ":", 18, Colors.UI_TEXT_DARK)
            panel_surface.blit(label_surface, (right_x, stats_y + i * line_height))
            
            value_surface = self.asset_manager.fonts.render_text(value, 20, color)
            panel_surface.blit(value_surface, (right_x + 120, stats_y + i * line_height))
        
        # 評價
        score = turn_count * 10 + game_stats.total_kills * 50 + player.gold
        rating_y = stats_y + len(left_stats) * line_height + 30
        
        if score < 1000:
            rating = "新手冒險者"
            rating_color = Colors.UI_TEXT_DARK
        elif score < 5000:
            rating = "經驗豐富的探索者"
            rating_color = Colors.NEON_GREEN
        elif score < 10000:
            rating = "地牢征服者"
            rating_color = Colors.NEON_BLUE
        else:
            rating = "傳說英雄"
            rating_color = Colors.NEON_YELLOW
        
        rating_text = f"評價: {rating} (得分: {score})"
        rating_surface = self.asset_manager.fonts.render_text(rating_text, 24, rating_color)
        rating_rect = rating_surface.get_rect(centerx=panel_width // 2, y=rating_y)
        panel_surface.blit(rating_surface, rating_rect)
        
        # 重新開始提示
        restart_y = panel_height - 100
        
        restart_surface = self.asset_manager.fonts.render_text(GameTexts.GAME_OVER_RESTART, 20, Colors.NEON_GREEN)
        restart_rect = restart_surface.get_rect(centerx=panel_width // 2, y=restart_y)
        panel_surface.blit(restart_surface, restart_rect)
        
        menu_surface = self.asset_manager.fonts.render_text(GameTexts.GAME_OVER_MENU, 20, Colors.NEON_CYAN)
        menu_rect = menu_surface.get_rect(centerx=panel_width // 2, y=restart_y + 35)
        panel_surface.blit(menu_surface, menu_rect)
        
        screen.blit(panel_surface, (panel_x, panel_y))
    
    def show_tooltip(self, text: str, position: tuple):
        """顯示工具提示"""
        self.tooltip = {
            'text': text,
            'position': position
        }
        self.tooltip_timer = 120
    
    def render_tooltip(self, screen):
        """渲染工具提示"""
        if not self.tooltip or self.tooltip_timer <= 0:
            return
            
        text = self.tooltip['text']
        x, y = self.tooltip['position']
        
        # 創建工具提示表面
        padding = 15
        text_surface = self.asset_manager.fonts.render_text(text, 16, Colors.WHITE)
        tooltip_width = text_surface.get_width() + padding * 2
        tooltip_height = text_surface.get_height() + padding * 2
        
        # 確保工具提示不超出螢幕
        if x + tooltip_width > WINDOW_WIDTH:
            x = WINDOW_WIDTH - tooltip_width
        if y + tooltip_height > WINDOW_HEIGHT:
            y = WINDOW_HEIGHT - tooltip_height
        
        # 渲染背景
        tooltip_surface = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
        pygame.draw.rect(tooltip_surface, (*Colors.UI_BG, 230), (0, 0, tooltip_width, tooltip_height))
        pygame.draw.rect(tooltip_surface, Colors.UI_HIGHLIGHT, (0, 0, tooltip_width, tooltip_height), 2)
        
        # 渲染文字
        tooltip_surface.blit(text_surface, (padding, padding))
        
        # 淡入效果
        alpha = min(255, self.tooltip_timer * 5)
        tooltip_surface.set_alpha(alpha)
        
        screen.blit(tooltip_surface, (x, y))

# ============================================================================
# 存檔系統
# ============================================================================

class SaveSystem:
    """存檔系統"""
    
    @staticmethod
    def save_game(game_data: dict, filename: str = "savegame.dat"):
        """保存遊戲"""
        try:
            # 創建存檔目錄
            save_dir = Path("saves")
            save_dir.mkdir(exist_ok=True)
            
            # 保存檔案
            with open(save_dir / filename, 'wb') as f:
                pickle.dump(game_data, f)

            # 添加已鑑定物品的記錄
            if 'player' in game_data:
                game_data['identified_items'] = list(game_data['player'].identified_items)

            # 保存元數據
            metadata = {
                'save_time': datetime.now().isoformat(),
                'player_level': game_data['player'].stats.level,
                'dungeon_level': game_data['dungeon_level'],
                'turn_count': game_data['turn_count']
            }
            
            with open(save_dir / f"{filename}.meta", 'w') as f:
                json.dump(metadata, f)
            
            return True
        except Exception as e:
            print(f"保存失敗: {e}")
            return False
    
    @staticmethod
    def load_game(filename: str = "savegame.dat"):
        """載入遊戲"""
        try:
            save_path = Path("saves") / filename
            if not save_path.exists():
                return None
            
            with open(save_path, 'rb') as f:
                return pickle.load(f)
        # 恢復已鑑定物品記錄
            if save_data and 'identified_items' in save_data:
                save_data['player'].identified_items = set(save_data['identified_items'])
            
            return save_data
        except Exception as e:
            print(f"載入失敗: {e}")
            return None
    
    @staticmethod
    def has_save(filename: str = "savegame.dat"):
        """檢查是否有存檔"""
        return (Path("saves") / filename).exists()
    
# ============================================================================
# 主遊戲類別
# ============================================================================

class Game:
    """主遊戲類 - 超精美視覺增強版"""
    
    def __init__(self):
        # 在pygame初始化之前設置DPI感知
        self.dpi_scale = 1.0
        
        # Windows DPI設置（改進版）
        if sys.platform == 'win32':
            try:
                import ctypes
                
                # 設置DPI感知
                try:
                    # Windows 10 1703+ 方法
                    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
                except:
                    try:
                        # Windows 8.1+ 方法
                        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # PROCESS_SYSTEM_DPI_AWARE
                    except:
                        # Windows Vista+ 方法
                        ctypes.windll.user32.SetProcessDPIAware()
                
                # 獲取主螢幕DPI
                hdc = ctypes.windll.user32.GetDC(0)
                dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
                ctypes.windll.user32.ReleaseDC(0, hdc)
                self.dpi_scale = dpi / 96.0
                print(f"系統DPI: {dpi}, 縮放比例: {self.dpi_scale}")
                
            except Exception as e:
                print(f"DPI設置失敗: {e}")
        
        # 初始化pygame
        pygame.init()
        
        # 獲取螢幕資訊
        info = pygame.display.Info()
        self.native_resolution = (info.current_w, info.current_h)
        print(f"檢測到螢幕解析度: {self.native_resolution}")
        
        # 遊戲設定
        self.settings = GameSettings()
        self.settings.load()
        
        # 記錄進入全螢幕前的解析度
        self.windowed_resolution = self.settings.resolution if not self.settings.fullscreen else (1280, 720)
        
        # 遊戲的內部解析度（固定）
        self.game_resolution = (WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # 修改：不再限制解析度選擇，只確保有效的預設值
        if not self.settings.fullscreen:
            # 檢查載入的解析度是否在支援列表中
            if self.settings.resolution not in RESOLUTIONS:
                # 找到最接近當前螢幕70%大小的解析度
                default_width = int(self.native_resolution[0] * 0.7)
                default_height = int(self.native_resolution[1] * 0.7)
                
                # 從所有解析度中找到最接近的（不再限制必須小於螢幕）
                closest_res = min(RESOLUTIONS, 
                                key=lambda res: abs(res[0] - default_width) + abs(res[1] - default_height))
                
                self.settings.resolution = closest_res
                print(f"使用預設視窗大小: {self.settings.resolution}")
            
            # 更新記錄的視窗解析度
            self.windowed_resolution = self.settings.resolution
        
        # 創建虛擬遊戲表面
        self.game_surface = pygame.Surface(self.game_resolution)
        
        # 初始化縮放相關屬性（在_apply_display_settings之前）
        self.scale = 1.0
        self.scaled_size = self.game_resolution
        self.screen_offset = (0, 0)
        self.actual_resolution = self.settings.resolution
        
        # 初始化視窗
        self._apply_display_settings()
        
        self.clock = pygame.time.Clock()
        
        # 調試模式
        self.debug_mode = False
        
        # 初始化遊戲組件
        self.asset_manager = AssetManager()
        self.ui = UI(self.asset_manager)
        self.particle_system = ParticleSystem()
        self.message_log = MessageLog()
        self.tutorial = TutorialSystem()
        self.achievement_system = AchievementSystem()
        self.game_stats = GameStats()
        self.game_stats.load()
        
        # 遊戲狀態
        self.state = GameState.MENU
        self.running = True
        
        # 遊戲對象
        self.player = None
        self.dungeon_map = None
        self.camera_offset = Position(0, 0)
        self.dungeon_level = 1
        self.turn_count = 0
        
        # 完全移除回合制控制（重要修正！）
        # 不再使用 self.player_turn 和 self.action_taken
        
        # 滑鼠控制
        self.mouse_pos = (0, 0)
        self.mouse_clicked = False
        self.mouse_dragging = False
        
        # 時間追蹤
        self.dt = 0
        self.last_time = time.time()

        # 技能範圍提示
        self.showing_skill_range = False
        self.skill_range_skill = None
        self.skill_range_target = None
        self.skill_range_timer = 0
        
        # 記錄最後移動方向
        self.last_move_direction = Direction.RIGHT
        
        # 按鍵狀態追蹤（用於持續移動）
        self.keys_pressed = {
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_LEFT: False,
            pygame.K_RIGHT: False,
            pygame.K_w: False,
            pygame.K_s: False,
            pygame.K_a: False,
            pygame.K_d: False,
            pygame.K_q: False,
            pygame.K_e: False,
            pygame.K_z: False,
            pygame.K_c: False
        }
        
        # 樓梯提示
        self.on_stairs = False
        self.stairs_hint_timer = 0
        
        self.previous_state = None # 用於從設定返回

        # 開始背景音樂
        self.asset_manager.play_music()

    def find_nearest_enemy(self, from_pos: Position, max_range: float = None) -> Enemy:
        """找到最近的敵人"""
        nearest_enemy = None
        min_distance = float('inf')
        
        for enemy in self.dungeon_map.enemies:
            if enemy.active and enemy.visible:
                distance = from_pos.distance_to(enemy.position)
                if max_range is None or distance <= max_range:
                    if distance < min_distance:
                        min_distance = distance
                        nearest_enemy = enemy
        
        return nearest_enemy
    
    def get_skill_target_position(self, skill: Skill) -> Position:
        """獲取技能目標位置（自動瞄準）"""
        # 某些技能目標為自己
        if skill.id in ['heal', 'shield']:
            return self.player.position
        
        # 找最近的敵人
        nearest_enemy = self.find_nearest_enemy(self.player.position, skill.range)
        
        if nearest_enemy:
            return nearest_enemy.position
        else:
            # 沒有敵人時，向玩家面向的方向釋放
            # 這裡簡單處理，使用最後移動的方向
            if hasattr(self, 'last_move_direction'):
                dir_value = self.last_move_direction.value
                return Position(
                    self.player.position.x + dir_value[0] * skill.range,
                    self.player.position.y + dir_value[1] * skill.range
                )
            else:
                # 預設向右
                return Position(
                    self.player.position.x + skill.range,
                    self.player.position.y
                )
            
    def convert_mouse_pos(self, pos):
        """將滑鼠座標從螢幕座標轉換為遊戲座標（完整修復版）"""
        # 所有遊戲狀態都需要轉換座標，因為所有內容都渲染在虛擬表面上
        if hasattr(self, 'scale') and self.scale > 0:
            # 減去遊戲畫面在螢幕上的偏移
            x = pos[0] - self.screen_offset[0]
            y = pos[1] - self.screen_offset[1]
            
            # 檢查是否在遊戲區域內
            if x < 0 or y < 0 or x > self.scaled_size[0] or y > self.scaled_size[1]:
                # 如果在黑邊區域，返回邊界值
                x = max(0, min(self.scaled_size[0], x))
                y = max(0, min(self.scaled_size[1], y))
            
            # 轉換為遊戲座標
            game_x = int(x / self.scale)
            game_y = int(y / self.scale)
            
            # 確保在有效範圍內
            game_x = max(0, min(self.game_resolution[0] - 1, game_x))
            game_y = max(0, min(self.game_resolution[1] - 1, game_y))
            
            return (game_x, game_y)
        else:
            # 如果scale未初始化，返回原始座標
            return pos

    def _center_window(self):
        """將視窗置中到螢幕中央"""
        try:
            # 獲取當前視窗大小
            window_width, window_height = self.actual_resolution
            
            # 獲取螢幕大小
            screen_width, screen_height = self.native_resolution
            
            # 計算置中位置
            center_x = (screen_width - window_width) // 2
            center_y = (screen_height - window_height) // 2
            
            # 確保不會超出螢幕邊界
            center_x = max(0, center_x)
            center_y = max(0, center_y)
            
            # 嘗試使用 pygame 2.0+ 的方法
            if hasattr(pygame.display, 'set_window_position'):
                pygame.display.set_window_position((center_x, center_y))
                print(f"視窗已置中到: ({center_x}, {center_y})")
            else:
                # 備用方案：使用環境變數（只在創建視窗前有效）
                os.environ['SDL_VIDEO_WINDOW_POS'] = f'{center_x},{center_y}'
                print(f"使用環境變數設置視窗位置: ({center_x}, {center_y})")
                
        except Exception as e:
            print(f"置中視窗失敗: {e}")

    def _apply_display_settings(self):
        """應用顯示設定（修復版 - 支援高解析度和正確置中）"""
        # 先計算縮放資訊，避免除以零錯誤
        self.scale = 1.0
        self.scaled_size = self.game_resolution
        self.screen_offset = (0, 0)
        
        if self.settings.fullscreen:
            # 全螢幕模式
            if sys.platform == 'win32':
                try:
                    # 在全螢幕模式下總是使用真實解析度
                    import ctypes
                    user32 = ctypes.windll.user32
                    native_res = (
                        user32.GetSystemMetrics(0),
                        user32.GetSystemMetrics(1)
                    )
                except:
                    # 備用方案
                    desktop_sizes = pygame.display.get_desktop_sizes()
                    if desktop_sizes:
                        native_res = desktop_sizes[0]
                    else:
                        info = pygame.display.Info()
                        native_res = (info.current_w, info.current_h)
            else:
                desktop_sizes = pygame.display.get_desktop_sizes()
                if desktop_sizes:
                    native_res = desktop_sizes[0]
                else:
                    info = pygame.display.Info()
                    native_res = (info.current_w, info.current_h)
            
            print(f"全螢幕模式: {native_res}")
            
            # 設置全螢幕
            flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
            self.screen = pygame.display.set_mode(native_res, flags)
            
            # 記錄實際解析度
            self.settings.resolution = native_res
            self.actual_resolution = native_res
            
            # 計算縮放比例（保持長寬比）
            scale_x = native_res[0] / self.game_resolution[0]
            scale_y = native_res[1] / self.game_resolution[1]
            self.scale = min(scale_x, scale_y)
            
            # 計算遊戲畫面在螢幕上的位置（居中）
            self.scaled_size = (
                int(self.game_resolution[0] * self.scale),
                int(self.game_resolution[1] * self.scale)
            )
            self.screen_offset = (
                (native_res[0] - self.scaled_size[0]) // 2,
                (native_res[1] - self.scaled_size[1]) // 2
            )
        else:
            # 視窗模式
            flags = pygame.DOUBLEBUF
            
            # 移除解析度限制，允許選擇任何解析度
            # 但仍然檢查最小值
            min_width = 1280
            min_height = 720
            
            # 檢查解析度是否合理
            if (self.settings.resolution[0] < min_width or 
                self.settings.resolution[1] < min_height):
                self.settings.resolution = (min_width, min_height)
            
            # 如果選擇的解析度大於螢幕，pygame會自動調整到合適大小
            # 但我們仍然允許用戶選擇
            print(f"視窗模式: {self.settings.resolution}")
            
            # 判斷是否需要重新創建視窗（首次創建或解析度改變）
            need_recreate = not hasattr(self, 'screen') or self.actual_resolution != self.settings.resolution
            
            try:
                # 嘗試設置請求的解析度
                self.screen = pygame.display.set_mode(self.settings.resolution, flags)
                # 獲取實際創建的視窗大小（可能與請求的不同）
                actual_window_size = self.screen.get_size()
                self.actual_resolution = actual_window_size
                
                # 如果實際視窗大小與請求的不同，更新設定
                if actual_window_size != self.settings.resolution:
                    print(f"實際視窗大小調整為: {actual_window_size}")
                
                # 如果是新創建或改變了大小，置中視窗
                if need_recreate:
                    self._center_window()
                    
            except pygame.error as e:
                print(f"設置視窗失敗: {e}")
                # 使用預設大小
                self.settings.resolution = (1280, 720)
                self.screen = pygame.display.set_mode(self.settings.resolution, flags)
                self.actual_resolution = self.settings.resolution
                self._center_window()
            
            # 使用實際視窗大小計算縮放
            scale_x = self.actual_resolution[0] / self.game_resolution[0]
            scale_y = self.actual_resolution[1] / self.game_resolution[1]
            self.scale = min(scale_x, scale_y)
            
            # 計算遊戲畫面在視窗中的位置（確保正確置中）
            self.scaled_size = (
                int(self.game_resolution[0] * self.scale),
                int(self.game_resolution[1] * self.scale)
            )
            self.screen_offset = (
                (self.actual_resolution[0] - self.scaled_size[0]) // 2,
                (self.actual_resolution[1] - self.scaled_size[1]) // 2
            )
        
        pygame.display.set_caption(f"{GameTexts.MENU_TITLE} - {GameTexts.MENU_SUBTITLE}")
        
        # 重新設定圖標
        icon_surface = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(icon_surface, 16, 16, 15, Colors.NEON_BLUE)
        pygame.display.set_icon(icon_surface)
        
        # 更新UI解析度資訊（使用實際視窗大小）
        if hasattr(self, 'ui'):
            self.ui.update_resolution(self.actual_resolution)
        
        print(f"縮放資訊 - 比例: {self.scale}, 遊戲區域: {self.scaled_size}, 偏移: {self.screen_offset}")

    def new_game(self):
        """開始新遊戲"""
        self.player = Player(Position(1, 1))
        self.player.identified_items = set()  # 確保新遊戲時清空鑑定記錄
        self.dungeon_level = 1
        self.turn_count = 0
        self.dungeon_map = DungeonMap(MAP_WIDTH, MAP_HEIGHT, self.dungeon_level)
        
        # 將玩家放置在第一個房間
        if self.dungeon_map.rooms:
            first_room = self.dungeon_map.rooms[0]
            new_x = first_room.centerx
            new_y = first_room.centery
            
            # 設置玩家位置（確保兩個位置都正確設置）
            self.player.position = Position(new_x, new_y)
            self.player.fractional_position = Position(float(new_x), float(new_y))
            
            # 初始化玩家狀態
            self.player.velocity = Position(0, 0)
            self.player.is_moving = False
            self.player.move_cooldown = 0
            self.player.attack_cooldown = 0
        
        # 立即更新相機位置
        self._update_camera()
        
        # 更新視野
        self.dungeon_map.update_fov(self.player.position)
        
        # 重置UI狀態
        self.ui.menu_selection = 0
        self.ui.inventory_selection = 0
        self.ui.show_inventory = False
        
        # 清空訊息日誌
        self.message_log = MessageLog()
        
        # 重置統計
        self.game_stats.current_floor_damage_taken = 0
        
        # 添加歡迎訊息
        self.message_log.add_message(
            GameTexts.EXPLORE_ENTER_FLOOR.format(floor=self.dungeon_level),
            MessageType.STORY
        )
        
        # 添加起始特效
        self.particle_system.add_level_up_effect(self.player.position)
        
        self.state = GameState.PLAYING
        
        # 重置輸入鎖定
        if hasattr(self, 'input_locked'):
            self.input_locked = False
            self.input_lock_timer = 0

    def load_game(self):
        """載入遊戲"""
        save_data = SaveSystem.load_game()
        if save_data:
            self.player = save_data['player']
            self.dungeon_level = save_data['dungeon_level']
            self.turn_count = save_data['turn_count']
            self.dungeon_map = save_data['dungeon_map']
            self.game_stats = save_data['game_stats']
            self.message_log = save_data['message_log']
            
            self.state = GameState.PLAYING
            # 移除這兩行
            # self.player_turn = True
            # self.action_taken = False
            
            # 更新視野
            self.dungeon_map.update_fov(self.player.position)
            
            self.message_log.add_message("遊戲載入成功！", MessageType.NORMAL)
            return True
        return False

    def save_game(self):
        """保存遊戲"""
        save_data = {
            'player': self.player,
            'dungeon_level': self.dungeon_level,
            'turn_count': self.turn_count,
            'dungeon_map': self.dungeon_map,
            'game_stats': self.game_stats,
            'message_log': self.message_log
        }
        
        if SaveSystem.save_game(save_data):
            self.message_log.add_message("遊戲保存成功！", MessageType.NORMAL)
            self.asset_manager.play_sound('menu_sound')
            return True
        else:
            self.message_log.add_message("遊戲保存失敗！", MessageType.WARNING)
            return False
    
    def handle_events(self):
        """處理事件"""
        # 在每幀開始時清理可能的卡住狀態
        events = pygame.event.get()
        
        # 確保事件隊列不會積壓
        if len(events) > 50:  # 如果事件太多，清理舊事件
            events = events[-50:]
        
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                # 記錄按鍵按下狀態
                if event.key in self.keys_pressed:
                    self.keys_pressed[event.key] = True
                
                # 全局快捷鍵
                if event.key == pygame.K_F11:
                    # 記錄當前解析度（如果是視窗模式）
                    if not self.settings.fullscreen:
                        self.windowed_resolution = self.settings.resolution
                    
                    # 切換全螢幕
                    self.settings.fullscreen = not self.settings.fullscreen
                    
                    # 如果退出全螢幕，恢復之前的視窗解析度
                    if not self.settings.fullscreen:
                        self.settings.resolution = self.windowed_resolution
                    
                    self._apply_display_settings()
                    self.settings.save()
                    continue
                elif event.key == pygame.K_F10 and not self.settings.fullscreen:
                    current_index = RESOLUTIONS.index(self.settings.resolution)
                    new_index = (current_index + 1) % len(RESOLUTIONS)
                    self.settings.resolution = RESOLUTIONS[new_index]
                    self.windowed_resolution = self.settings.resolution
                    self._apply_display_settings()
                    self.settings.save()
                    continue
                
                self._handle_keydown(event.key)
            
            elif event.type == pygame.KEYUP:
                # 記錄按鍵釋放狀態
                if event.key in self.keys_pressed:
                    self.keys_pressed[event.key] = False
            
            elif event.type == pygame.MOUSEMOTION:
                # 轉換滑鼠座標
                self.mouse_pos = self.convert_mouse_pos(event.pos)
                self._handle_mouse_motion(self.mouse_pos)
                
                # 如果正在拖曳且在設定介面
                if hasattr(self, 'mouse_dragging') and self.mouse_dragging and self.state == GameState.SETTINGS:
                    self._handle_settings_mouse_drag(self.mouse_pos)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 轉換滑鼠座標
                converted_pos = self.convert_mouse_pos(event.pos)
                
                if event.button == 1:  # 左鍵
                    self.mouse_clicked = True
                    self.mouse_dragging = True
                    self._handle_mouse_click(converted_pos)
                elif event.button == 3:  # 右鍵
                    self._handle_mouse_right_click(converted_pos)
                elif event.button == 4:  # 滾輪上
                    self._handle_mouse_wheel(1)
                elif event.button == 5:  # 滾輪下
                    self._handle_mouse_wheel(-1)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_dragging = False
        
        # 確保按鍵狀態是最新的（處理快速按鍵）
        # 使用 pygame.key.get_pressed() 作為備份檢查
        if self.state == GameState.PLAYING:
            current_keys = pygame.key.get_pressed()
            # 同步方向鍵狀態
            for key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
                       pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d,
                       pygame.K_q, pygame.K_e, pygame.K_z, pygame.K_c]:
                if key in self.keys_pressed:
                    # 如果實際按鍵狀態與記錄不符，更新它
                    if current_keys[key] != self.keys_pressed[key]:
                        self.keys_pressed[key] = current_keys[key]

    def _handle_keydown(self, key):
        """處理按鍵按下"""
        # 修復：移除錯誤的輸入鎖定邏輯
        # 舊邏輯會阻止新按鍵的處理
        
        if self.state == GameState.MENU:
            self._handle_menu_input(key)
        
        elif self.state == GameState.TUTORIAL:
            self._handle_tutorial_input(key)
        
        elif self.state == GameState.PLAYING:
            # 直接處理輸入，不檢查輸入鎖定
            self._handle_game_input(key)
        
        elif self.state == GameState.INVENTORY:
            self._handle_inventory_input(key)
        
        elif self.state == GameState.SETTINGS:
            self._handle_settings_input(key)
            
        elif self.state == GameState.ACHIEVEMENTS:
            if key == pygame.K_ESCAPE:
                self.state = GameState.MENU
                self.asset_manager.play_sound('menu_sound')
            elif key == pygame.K_UP:
                self.ui.achievement_scroll = max(0, self.ui.achievement_scroll - 80)
            elif key == pygame.K_DOWN:
                self.ui.achievement_scroll += 80
        
        # 檔案: 1.py, 類別: Game, 函式: _handle_keydown

        elif self.state == GameState.PAUSED:
            if key == pygame.K_ESCAPE:
                self.state = GameState.PLAYING
            elif key == pygame.K_s:
                self.save_game()
            elif key == pygame.K_o: # <<< 新增這個 elif 區塊
                self.previous_state = self.state
                self.state = GameState.SETTINGS
            elif key == pygame.K_q:
                self.state = GameState.MENU
        
        elif self.state == GameState.GAME_OVER:
            if key == pygame.K_r:
                self.new_game()
            elif key == pygame.K_ESCAPE:
                self.state = GameState.MENU

    def _handle_menu_input(self, key):
        """處理主選單輸入"""
        if key == pygame.K_UP or key == pygame.K_w:
            self.ui.menu_selection = (self.ui.menu_selection - 1) % 6
            self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            self.ui.menu_selection = (self.ui.menu_selection + 1) % 6
            self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume)
        elif key == pygame.K_SPACE or key == pygame.K_RETURN:
            if self.ui.menu_selection == 0:  # 開始遊戲
                self.new_game()
            elif self.ui.menu_selection == 1:  # 繼續遊戲
                if SaveSystem.has_save():
                    self.load_game()
            elif self.ui.menu_selection == 2:  # 教學
                self.tutorial = TutorialSystem() # << 重新創建一個全新的教學物件
                self.state = GameState.TUTORIAL
           
            elif self.ui.menu_selection == 3:  # 設定
                self.previous_state = self.state # 記住是從 MENU 來的
                self.state = GameState.SETTINGS

            elif self.ui.menu_selection == 4:  # 成就
                self.state = GameState.ACHIEVEMENTS
            elif self.ui.menu_selection == 5:  # 退出
                self.running = False
        elif key == pygame.K_ESCAPE:
            self.running = False

    def _handle_tutorial_input(self, key):
        """處理教學輸入"""
        if key == pygame.K_SPACE:
            self.tutorial.next_step()
            if self.tutorial.completed:
                # 教學結束，返回主選單而不是開始遊戲
                self.state = GameState.MENU
                self.asset_manager.play_sound('menu_sound')
        elif key == pygame.K_ESCAPE:
            self.tutorial.skip_tutorial()
            self.state = GameState.MENU
            self.asset_manager.play_sound('menu_sound')    
    
    def _handle_game_input(self, key):
        """處理遊戲內輸入"""
        # 快速保存/載入
        if key == pygame.K_F5:
            self.save_game()
            return
        elif key == pygame.K_F9:
            self.load_game()

        elif key == pygame.K_l:  # 切換訊息日誌展開/收起
            self.ui.message_log_collapsed = not self.ui.message_log_collapsed
            if self.ui.message_log_collapsed:
                self.message_log.add_message("訊息日誌已收起", MessageType.NORMAL)
            else:
                self.message_log.add_message("訊息日誌已展開", MessageType.NORMAL)
            self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
        elif key == pygame.K_F1:
            # 調試移速
            self.player.debug_move_speed(self.message_log)
            return
        elif key == pygame.K_F12:
            # 切換調試模式
            self.debug_mode = not getattr(self, 'debug_mode', False)
            debug_status = "開啟" if self.debug_mode else "關閉"
            self.message_log.add_message(f"調試模式已{debug_status}", MessageType.NORMAL)
            return
        
        # 技能使用
        if key == pygame.K_1:
            self._use_skill(0)
        elif key == pygame.K_2:
            self._use_skill(1)
        elif key == pygame.K_3:
            self._use_skill(2)
        elif key == pygame.K_4:
            self._use_skill(3)
        
        # 其他行動
        elif key == pygame.K_b:  # 背包
            self.state = GameState.INVENTORY
            self.ui.show_inventory = True
        elif key == pygame.K_f:  # 拾取
            self._player_pickup()
        elif key == pygame.K_r:  # 休息
            self._player_rest()
        elif key == pygame.K_ESCAPE:
            self.state = GameState.PAUSED
        elif key == pygame.K_SPACE:
            # 檢查是否在樓梯上
            if self.dungeon_map.get_tile(self.player.position) == 'stairs':
                self._next_level()

    def _handle_settings_input(self, key):
        """處理設定輸入"""
        if key == pygame.K_ESCAPE:
            # 保存並返回上一個畫面
            self.settings.save()
            if self.previous_state:
                self.state = self.previous_state
            else:
                self.state = GameState.MENU # 如果沒有前一個狀態，則返回主選單
            self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
        elif key == pygame.K_UP or key == pygame.K_w:
            self.ui.settings_selection = (self.ui.settings_selection - 1) % 10
            self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            self.ui.settings_selection = (self.ui.settings_selection + 1) % 10
            self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
        elif key == pygame.K_LEFT or key == pygame.K_a:
            self._adjust_setting_value(-1)
        elif key == pygame.K_RIGHT or key == pygame.K_d:
            self._adjust_setting_value(1)
        elif key == pygame.K_SPACE or key == pygame.K_RETURN:
            self._toggle_setting()
        elif key == pygame.K_F11:
            # 快速切換全螢幕
            self.settings.fullscreen = not self.settings.fullscreen
            self._apply_display_settings()

    def _toggle_setting(self):
        """切換當前選中的設定"""
        selection = self.ui.settings_selection
        
        # 根據選中項目切換設定
        if selection == 3:  # 全螢幕
            # 如果即將進入全螢幕，先保存當前的視窗解析度
            if not self.settings.fullscreen:
                self.windowed_resolution = self.settings.resolution
            
            # 切換全螢幕狀態
            self.settings.fullscreen = not self.settings.fullscreen
            
            # 如果剛剛退出全螢幕，恢復之前保存的視窗解析度
            if not self.settings.fullscreen:
                self.settings.resolution = self.windowed_resolution
            
            self._apply_display_settings()
        elif selection == 5:  # 自動拾取
            self.settings.auto_pickup = not self.settings.auto_pickup
        elif selection == 6:  # 顯示傷害數字
            self.settings.show_damage_numbers = not self.settings.show_damage_numbers
        elif selection == 7:  # 顯示小地圖
            self.settings.show_minimap = not self.settings.show_minimap
        elif selection == 8:  # 顯示敵人血條
            self.settings.show_enemy_health = not self.settings.show_enemy_health
        elif selection == 9:  # 顯示工具提示
            self.settings.show_tooltips = not self.settings.show_tooltips
        
        self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)

    def _adjust_setting_value(self, direction: int):
        """調整設定值"""
        selection = self.ui.settings_selection
        
        if selection == 0:  # 主音量
            self.settings.master_volume = max(0.0, min(1.0, self.settings.master_volume + direction * 0.05))
        elif selection == 1:  # 音樂音量
            self.settings.music_volume = max(0.0, min(1.0, self.settings.music_volume + direction * 0.05))
        elif selection == 2:  # 音效音量
            self.settings.sfx_volume = max(0.0, min(1.0, self.settings.sfx_volume + direction * 0.05))
        elif selection == 4:  # 解析度（只在非全螢幕時有效）
            if not self.settings.fullscreen:
                current_index = RESOLUTIONS.index(self.settings.resolution)
                new_index = (current_index + direction) % len(RESOLUTIONS)
                self.settings.resolution = RESOLUTIONS[new_index]
                self._apply_display_settings()
        elif selection == 10:  # 粒子效果
            particle_options = ['low', 'medium', 'high']
            current_index = particle_options.index(self.settings.particle_density)
            new_index = (current_index + direction) % len(particle_options)
            self.settings.particle_density = particle_options[new_index]
        elif selection == 11:  # 遊戲難度
            difficulty_options = ['easy', 'normal', 'hard']
            current_index = difficulty_options.index(self.settings.difficulty)
            new_index = (current_index + direction) % len(difficulty_options)
            self.settings.difficulty = difficulty_options[new_index]
        
        self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.3)

    def _handle_inventory_input(self, key):
        """處理背包輸入（改進版）"""
        if key == pygame.K_ESCAPE or key == pygame.K_b:
            self.state = GameState.PLAYING
            self.ui.show_inventory = False
            self.ui.inventory_panel_focused = True  # 重置焦點

        elif key == pygame.K_v and self.ui.inventory_panel_focused:  # V鍵販賣
            if self.player.inventory and 0 <= self.ui.inventory_selection < len(self.player.inventory):
                item = self.player.inventory[self.ui.inventory_selection]
                
                # 計算販賣價格（50%的價值）
                sell_price = item.value // 2
                
                # 確認販賣
                self.message_log.add_message(
                    f"確定要以 {sell_price} 金幣賣出 {item.name} 嗎？再按一次V確認",
                    MessageType.WARNING
                )
                
                # 設置確認標記
                if hasattr(self, '_confirm_sell') and self._confirm_sell == self.ui.inventory_selection:
                    # 第二次按V，執行販賣
                    self.player.inventory.pop(self.ui.inventory_selection)
                    self.player.gold += sell_price
                    self.message_log.add_message(
                        f"你賣出了 {item.name}，獲得 {sell_price} 金幣！",
                        MessageType.ITEM
                    )
                    self.asset_manager.play_sound('pickup_sound', self.settings.sfx_volume)
                    
                    # 調整選擇索引
                    if self.ui.inventory_selection >= len(self.player.inventory):
                        self.ui.inventory_selection = max(0, len(self.player.inventory) - 1)
                    
                    # 清除確認標記
                    self._confirm_sell = -1
                else:
                    # 第一次按V，設置確認標記
                    self._confirm_sell = self.ui.inventory_selection

        elif key == pygame.K_TAB:
            # 切換焦點
            self.ui.inventory_panel_focused = not self.ui.inventory_panel_focused
            self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
            
            if self.ui.inventory_panel_focused:
                self.message_log.add_message("切換到背包管理", MessageType.NORMAL)
            else:
                self.message_log.add_message("切換到技能管理", MessageType.NORMAL)
                # 確保技能選擇索引有效
                learned_skills = self.player.get_learned_skills()
                if learned_skills:
                    self.ui.skill_selection = min(self.ui.skill_selection, len(learned_skills) - 1)
                else:
                    self.ui.skill_selection = 0
                    
        elif key == pygame.K_UP or key == pygame.K_w:
            if self.ui.inventory_panel_focused:
                # 在背包中移動
                if self.player.inventory:
                    # 向上移動兩格（上一行）
                    new_selection = self.ui.inventory_selection - 2
                    if new_selection < 0:
                        # 到達頂部，循環到底部
                        self.ui.inventory_selection = len(self.player.inventory) - 1
                    else:
                        self.ui.inventory_selection = new_selection
                    
                    # 自動調整滾動位置以顯示選中的物品
                    items_per_row = 2
                    selected_row = self.ui.inventory_selection // items_per_row
                    
                    # 如果選中的物品在可見範圍外，調整滾動
                    if selected_row < self.ui.inventory_scroll_offset:
                        self.ui.inventory_scroll_offset = selected_row
                    
                    self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
            else:
                # 在技能列表中移動
                learned_skills = self.player.get_learned_skills()
                if learned_skills:
                    self.ui.skill_selection = (self.ui.skill_selection - 1) % len(learned_skills)
                    self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
                    
        elif key == pygame.K_DOWN or key == pygame.K_s:
            if self.ui.inventory_panel_focused:
                # 在背包中移動
                if self.player.inventory:
                    # 向下移動兩格（下一行）
                    new_selection = self.ui.inventory_selection + 2
                    if new_selection >= len(self.player.inventory):
                        # 到達底部，循環到頂部
                        self.ui.inventory_selection = 0
                    else:
                        self.ui.inventory_selection = new_selection
                    
                    # 自動調整滾動位置以顯示選中的物品
                    items_per_row = 2
                    selected_row = self.ui.inventory_selection // items_per_row
                    item_height = 100
                    panel_height = 700
                    list_height = panel_height - 190
                    visible_rows = list_height // item_height
                    
                    # 如果選中的物品在可見範圍外，調整滾動
                    if selected_row >= self.ui.inventory_scroll_offset + visible_rows:
                        self.ui.inventory_scroll_offset = selected_row - visible_rows + 1
                    
                    self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
            else:
                # 在技能列表中移動
                learned_skills = self.player.get_learned_skills()
                if learned_skills:
                    self.ui.skill_selection = (self.ui.skill_selection + 1) % len(learned_skills)
                    self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
                    
        elif key == pygame.K_LEFT or key == pygame.K_a:
            if self.ui.inventory_panel_focused:
                # 在背包中左移
                if self.player.inventory:
                    if self.ui.inventory_selection % 2 == 1:  # 在右列
                        self.ui.inventory_selection -= 1
                        self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
            else:
                # 在技能面板中，卸下技能
                learned_skills = self.player.get_learned_skills()
                if learned_skills and 0 <= self.ui.skill_selection < len(learned_skills):
                    skill = learned_skills[self.ui.skill_selection]
                    if skill.slot_index != -1:
                        self.player.unequip_skill(skill.slot_index)
                        self.message_log.add_message(f"卸下了技能：{skill.name}", MessageType.ITEM)
                        self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
                        
        elif key == pygame.K_RIGHT or key == pygame.K_d:
            if self.ui.inventory_panel_focused:
                # 在背包中右移
                if self.player.inventory:
                    if self.ui.inventory_selection % 2 == 0:  # 在左列
                        if self.ui.inventory_selection + 1 < len(self.player.inventory):
                            self.ui.inventory_selection += 1
                            self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
            else:
                # 在技能面板中，裝備技能到第一個空位
                learned_skills = self.player.get_learned_skills()
                if learned_skills and 0 <= self.ui.skill_selection < len(learned_skills):
                    skill = learned_skills[self.ui.skill_selection]
                    if skill.slot_index == -1:
                        for i in range(4):
                            if self.player.equipped_skills[i] is None:
                                self.player.equip_skill(skill.id, i)
                                self.message_log.add_message(f"裝備了技能：{skill.name} 到快捷鍵 {i+1}", MessageType.ITEM)
                                self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
                                break
                                
        elif key == pygame.K_SPACE or key == pygame.K_RETURN:
            if self.ui.inventory_panel_focused:
                # 在背包中使用物品
                if self.player.inventory and 0 <= self.ui.inventory_selection < len(self.player.inventory):
                    item = self.player.inventory[self.ui.inventory_selection]
                    if self.player.use_item(item, self.asset_manager, self.message_log, self.particle_system):
                        if self.ui.inventory_selection >= len(self.player.inventory):
                            self.ui.inventory_selection = max(0, len(self.player.inventory) - 1)
            else:
                # 在技能面板中升級技能
                learned_skills = self.player.get_learned_skills()
                if learned_skills and 0 <= self.ui.skill_selection < len(learned_skills):
                    skill = learned_skills[self.ui.skill_selection]
                    if not skill.is_max_level:
                        scrolls_needed, gold_needed = skill.get_upgrade_cost()
                        scroll_count = self.player.count_skill_scrolls(skill.id)
                        
                        if scroll_count >= scrolls_needed and self.player.gold >= gold_needed:
                            if scrolls_needed > 0:
                                self.player.consume_skill_scrolls(skill.id, scrolls_needed)
                            
                            success, _, _ = self.player.upgrade_skill(skill.id)
                            if success:
                                self.message_log.add_message(
                                    f"{skill.name} 升級到 Lv.{skill.current_level}！",
                                    MessageType.LEVEL_UP
                                )
                                self.particle_system.add_level_up_effect(self.player.position)
                                self.asset_manager.play_sound('level_up_sound', self.settings.sfx_volume)
                        else:
                            if scroll_count < scrolls_needed:
                                self.message_log.add_message(f"需要 {scrolls_needed} 個對應卷軸（當前：{scroll_count}）", MessageType.WARNING)
                            if self.player.gold < gold_needed:
                                self.message_log.add_message(f"需要 {gold_needed} 金幣（當前：{self.player.gold}）", MessageType.WARNING)
                                
        elif key == pygame.K_DELETE and self.ui.inventory_panel_focused:
            # 只在背包面板可以丟棄物品
            if self.player.inventory and 0 <= self.ui.inventory_selection < len(self.player.inventory):
                item = self.player.inventory.pop(self.ui.inventory_selection)
                self.message_log.add_message(f"你丟棄了{item.name}", MessageType.ITEM)
                if self.ui.inventory_selection >= len(self.player.inventory):
                    self.ui.inventory_selection = max(0, len(self.player.inventory) - 1)
                    
        elif key >= pygame.K_1 and key <= pygame.K_4:
            # 數字鍵1-4：在技能面板快速裝備技能
            if not self.ui.inventory_panel_focused:
                slot_index = key - pygame.K_1  # 0-3
                learned_skills = self.player.get_learned_skills()
                if learned_skills and 0 <= self.ui.skill_selection < len(learned_skills):
                    skill = learned_skills[self.ui.skill_selection]
                    if self.player.equip_skill(skill.id, slot_index):
                        self.message_log.add_message(
                            f"將 {skill.name} 裝備到快捷鍵 {slot_index + 1}",
                            MessageType.ITEM
                        )
                        self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)

    def _handle_mouse_motion(self, pos):
        """處理滑鼠移動"""
        if self.state == GameState.PLAYING:
            # 檢查物品提示
            tile_x = (pos[0] + self.camera_offset.x) // TILE_SIZE
            tile_y = (pos[1] + self.camera_offset.y) // TILE_SIZE
            
            for item_pos, item in self.dungeon_map.items:
                if item_pos.x == tile_x and item_pos.y == tile_y:
                    if self.dungeon_map.visible[item_pos.y][item_pos.x]:
                        tooltip_text = f"{item.name}"
                        if item.rarity != 'common':
                            tooltip_text += f" ({item.rarity})"
                        self.ui.show_tooltip(tooltip_text, pos)
                        return
            
            # 檢查敵人提示
            for enemy in self.dungeon_map.enemies:
                if enemy.active and enemy.position.x == tile_x and enemy.position.y == tile_y:
                    if enemy.visible:
                        tooltip_text = f"{enemy.name} - HP: {enemy.stats.hp}/{enemy.stats.max_hp}"
                        self.ui.show_tooltip(tooltip_text, pos)
                        return

    def _handle_settings_mouse_click(self, pos):
        """處理設定介面的滑鼠點擊（修復版）"""
        if not hasattr(self.ui, 'settings_panel_rect'):
            return
        
        panel_rect = self.ui.settings_panel_rect
        
        # 先檢查是否點擊在下拉選單上
        if self.ui.dropdown_open and hasattr(self.ui, 'dropdown_menu_rect'):
            if self.ui.dropdown_menu_rect.collidepoint(pos):
                # 處理下拉選單點擊
                rel_y = pos[1] - self.ui.dropdown_menu_rect.y - 5
                option_index = rel_y // 35  # 每個選項高度35
                
                # 獲取選項列表
                if self.ui.dropdown_open == 'resolution':
                    options = RESOLUTIONS
                elif self.ui.dropdown_open == 'particle':
                    options = ['low', 'medium', 'high']
                elif self.ui.dropdown_open == 'difficulty':
                    options = ['easy', 'normal', 'hard']
                else:
                    return
                
                if 0 <= option_index < len(options):
                    selected_option = options[option_index]
                    
                    if self.ui.dropdown_open == 'resolution':
                        self.settings.resolution = selected_option
                        self._apply_display_settings()
                    elif self.ui.dropdown_open == 'particle':
                        self.settings.particle_density = selected_option
                    elif self.ui.dropdown_open == 'difficulty':
                        self.settings.difficulty = selected_option
                    
                    self.ui.dropdown_open = None
                    self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
                return
        
        # 檢查是否點擊在面板內
        if not panel_rect.collidepoint(pos):
            # 關閉下拉選單
            if self.ui.dropdown_open:
                self.ui.dropdown_open = None
            return
        
        # 相對於面板的座標
        rel_x = pos[0] - panel_rect.x
        rel_y = pos[1] - panel_rect.y
        
        # 檢查滑動條點擊
        if hasattr(self.ui, 'slider_rects'):
            for index, rect in self.ui.slider_rects.items():
                # 轉換為絕對座標
                abs_rect = rect.copy()
                abs_rect.x += panel_rect.x
                abs_rect.y += panel_rect.y
                
                if abs_rect.collidepoint(pos):
                    # 計算新值
                    relative_x = pos[0] - abs_rect.x
                    value = max(0.0, min(1.0, relative_x / abs_rect.width))
                    
                    # 更新對應的設定
                    if index == 0:
                        self.settings.master_volume = value
                    elif index == 1:
                        self.settings.music_volume = value
                    elif index == 2:
                        self.settings.sfx_volume = value
                    
                    self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.3)
                    return
        
        # 檢查開關點擊
        if hasattr(self.ui, 'toggle_rects'):
            for index, rect in self.ui.toggle_rects.items():
                # 轉換為絕對座標
                abs_rect = rect.copy()
                abs_rect.x += panel_rect.x
                abs_rect.y += panel_rect.y
                
                if abs_rect.collidepoint(pos):
                     # 切換對應的設定
                    if index == 0:
                        # 如果即將進入全螢幕，先保存當前的視窗解析度
                        if not self.settings.fullscreen:
                            self.windowed_resolution = self.settings.resolution
                        
                        # 切換全螢幕狀態
                        self.settings.fullscreen = not self.settings.fullscreen
                        
                        # 如果剛剛退出全螢幕，恢復之前保存的視窗解析度
                        if not self.settings.fullscreen:
                            self.settings.resolution = self.windowed_resolution

                        self._apply_display_settings()
                    elif index == 1:
                        self.settings.auto_pickup = not self.settings.auto_pickup
                    elif index == 2:
                        self.settings.show_damage_numbers = not self.settings.show_damage_numbers
                    elif index == 3:
                        self.settings.show_minimap = not self.settings.show_minimap
                    elif index == 4:
                        self.settings.show_enemy_health = not self.settings.show_enemy_health
                    elif index == 5:
                        self.settings.show_tooltips = not self.settings.show_tooltips
                    
                    self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
                    return
        
        # 檢查下拉框點擊
        if hasattr(self.ui, 'dropdown_rects'):
            for dropdown_type, rect in self.ui.dropdown_rects.items():
                # 如果是解析度下拉框且在全螢幕模式，跳過
                if dropdown_type == 'resolution' and self.settings.fullscreen:
                    continue
                    
                # 轉換為絕對座標
                abs_rect = rect.copy()
                abs_rect.x += panel_rect.x
                abs_rect.y += panel_rect.y
                
                if abs_rect.collidepoint(pos):
                    # 切換下拉選單
                    if self.ui.dropdown_open == dropdown_type:
                        self.ui.dropdown_open = None
                    else:
                        self.ui.dropdown_open = dropdown_type
                    self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
                    return
        
        # 檢查按鈕點擊
        if hasattr(self.ui, 'button_rects'):
            for button_id, rect in self.ui.button_rects.items():
                # 轉換為絕對座標
                abs_rect = rect.copy()
                abs_rect.x += panel_rect.x
                abs_rect.y += panel_rect.y
                
                if abs_rect.collidepoint(pos):
                    if button_id == 'apply':
                        self.settings.save()
                        if self.previous_state:
                            self.state = self.previous_state
                        else:
                            self.state = GameState.MENU
                        self.ui.dropdown_open = None
                        self.asset_manager.play_sound('menu_sound')
                    elif button_id == 'cancel':
                        self.settings.load()
                        self._apply_display_settings()
                        if self.previous_state:
                            self.state = self.previous_state
                        else:
                            self.state = GameState.MENU
                        self.ui.dropdown_open = None
                        self.asset_manager.play_sound('menu_sound')
                    return

    def _handle_settings_mouse_drag(self, pos):
        """處理設定介面的滑鼠拖曳（改進版）"""
        if not hasattr(self.ui, 'settings_panel_rect'):
            return
        
        panel_rect = self.ui.settings_panel_rect
        
        # 檢查滑動條拖曳
        if hasattr(self.ui, 'slider_rects'):
            for index, rect in self.ui.slider_rects.items():
                # 轉換為絕對座標
                abs_rect = rect.copy()
                abs_rect.x += panel_rect.x
                abs_rect.y += panel_rect.y
                
                # 擴大檢測範圍
                expanded_rect = abs_rect.inflate(0, 20)
                
                if expanded_rect.collidepoint(pos):
                    # 計算新值
                    relative_x = pos[0] - abs_rect.x
                    value = max(0.0, min(1.0, relative_x / abs_rect.width))
                    
                    # 更新對應的設定
                    if index == 0:
                        if abs(self.settings.master_volume - value) > 0.01:
                            self.settings.master_volume = value
                    elif index == 1:
                        if abs(self.settings.music_volume - value) > 0.01:
                            self.settings.music_volume = value
                    elif index == 2:
                        if abs(self.settings.sfx_volume - value) > 0.01:
                            self.settings.sfx_volume = value
                    
                    return

    def _handle_mouse_click(self, pos):
        """處理滑鼠點擊"""
        if self.state == GameState.SETTINGS:
            self._handle_settings_mouse_click(pos)
            return
        
        if self.state == GameState.PLAYING:  # 移除了 player_turn 和 action_taken 的檢查
            # 計算點擊的地圖位置
            tile_x = (pos[0] + self.camera_offset.x) // TILE_SIZE
            tile_y = (pos[1] + self.camera_offset.y - 60) // TILE_SIZE  # 減去頂部UI高度
            
            target_pos = Position(tile_x, tile_y)
            
            # 如果點擊相鄰格子，移動或攻擊
            dx = tile_x - self.player.position.x
            dy = tile_y - self.player.position.y
            
            if abs(dx) <= 1 and abs(dy) <= 1 and (dx != 0 or dy != 0):
                # 確定方向
                for direction in Direction:
                    if direction.value == (dx, dy):
                        self._player_move(direction)
                        break
            else:
                # 長距離移動（自動尋路簡化版）
                self._auto_move_to(target_pos)
        
        elif self.state == GameState.INVENTORY:
            # 檢查是否點擊裝備欄
            if hasattr(self.ui, 'equipment_slot_rects'):
                for slot_key, rect in self.ui.equipment_slot_rects.items():
                    if rect.collidepoint(pos):
                        # 卸下裝備
                        if self.player.equipment.get(slot_key):
                            item = self.player.equipment[slot_key]
                            # 檢查背包是否有空間
                            if len(self.player.inventory) < self.player.max_inventory:
                                self.player.equipment[slot_key] = None
                                self.player.inventory.append(item)
                                self.message_log.add_message(
                                    f"卸下了{item.name}",
                                    MessageType.ITEM
                                )
                                self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
                            else:
                                self.message_log.add_message(
                                    "背包已滿，無法卸下裝備！",
                                    MessageType.WARNING
                                )
                        break
            
            # 檢查點擊位置（原有的背包和技能面板點擊處理）
            if hasattr(self.ui, 'inventory_panel_rect') and hasattr(self.ui, 'skill_panel_rect'):
                if self.ui.inventory_panel_rect and self.ui.inventory_panel_rect.collidepoint(pos):
                    # 點擊在背包面板
                    self.ui.inventory_panel_focused = True
                    
                    # 背包點擊處理（修正面板寬度和物品列數）
                    inventory_width = 500  # 與render_inventory中的寬度一致
                    panel_height = 650  # equipment_height
                    panel_x = self.ui.inventory_panel_rect.x
                    panel_y = self.ui.inventory_panel_rect.y
                    
                    # 檢查是否點擊在物品列表區域
                    list_x = panel_x + 20
                    list_y = panel_y + 70  # 標題高度50 + 間距20
                    list_width = inventory_width - 40
                    list_height = panel_height - 150
                    
                    if list_x <= pos[0] <= list_x + list_width and list_y <= pos[1] <= list_y + list_height:
                        # 計算點擊的物品（2列）
                        items_per_row = 2  # 修正為2列
                        item_width = (list_width - 10) // items_per_row
                        item_height = 90
                        
                        rel_x = pos[0] - list_x
                        rel_y = pos[1] - list_y
                        
                        col = rel_x // item_width
                        row = rel_y // item_height
                        
                        if 0 <= col < items_per_row:  # 確保在2列範圍內
                            # 考慮滾動偏移
                            item_index = (row + self.ui.inventory_scroll_offset) * items_per_row + col
                            if 0 <= item_index < len(self.player.inventory):
                                self.ui.inventory_selection = item_index
                                # 雙擊使用
                                if hasattr(self, '_last_click_time') and time.time() - self._last_click_time < 0.3:
                                    item = self.player.inventory[item_index]
                                    if self.player.use_item(item, self.asset_manager, self.message_log, self.particle_system):
                                        # 調整選擇索引
                                        if self.ui.inventory_selection >= len(self.player.inventory):
                                            self.ui.inventory_selection = max(0, len(self.player.inventory) - 1)
                                self._last_click_time = time.time()
                                
                elif self.ui.skill_panel_rect and self.ui.skill_panel_rect.collidepoint(pos):
                    # 點擊在技能面板
                    self.ui.inventory_panel_focused = False
                    
                    # 檢查是否點擊了升級按鈕
                    for skill_idx, rect in self.ui.skill_upgrade_rects.items():
                        if rect.collidepoint(pos):
                            learned_skills = self.player.get_learned_skills()
                            if 0 <= skill_idx < len(learned_skills):
                                skill = learned_skills[skill_idx]
                                # 執行升級邏輯
                                scrolls_needed, gold_needed = skill.get_upgrade_cost()
                                scroll_count = self.player.count_skill_scrolls(skill.id)
                                
                                if scroll_count >= scrolls_needed and self.player.gold >= gold_needed:
                                    if scrolls_needed > 0:
                                        self.player.consume_skill_scrolls(skill.id, scrolls_needed)
                                    
                                    success, _, _ = self.player.upgrade_skill(skill.id)
                                    if success:
                                        self.message_log.add_message(
                                            f"{skill.name} 升級到 Lv.{skill.current_level}！",
                                            MessageType.LEVEL_UP
                                        )
                                        self.particle_system.add_level_up_effect(self.player.position)
                                        self.asset_manager.play_sound('level_up_sound', self.settings.sfx_volume)
                                else:
                                    if scroll_count < scrolls_needed:
                                        self.message_log.add_message(f"需要 {scrolls_needed} 個對應卷軸（當前：{scroll_count}）", MessageType.WARNING)
                                    if self.player.gold < gold_needed:
                                        self.message_log.add_message(f"需要 {gold_needed} 金幣（當前：{self.player.gold}）", MessageType.WARNING)
                            break
                    
                    # 檢查是否點擊了裝備按鈕
                    for skill_idx, rect in self.ui.skill_equip_rects.items():
                        if rect.collidepoint(pos):
                            learned_skills = self.player.get_learned_skills()
                            if 0 <= skill_idx < len(learned_skills):
                                skill = learned_skills[skill_idx]
                                if skill.slot_index == -1:
                                    # 裝備技能到第一個空位
                                    equipped = False
                                    for i in range(4):
                                        if self.player.equipped_skills[i] is None:
                                            self.player.equip_skill(skill.id, i)
                                            self.message_log.add_message(
                                                f"裝備了技能：{skill.name} 到快捷鍵 {i+1}",
                                                MessageType.ITEM
                                            )
                                            self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
                                            equipped = True
                                            break
                                    if not equipped:
                                        self.message_log.add_message("沒有空的快捷欄位！", MessageType.WARNING)
                                else:
                                    # 卸下技能
                                    self.player.unequip_skill(skill.slot_index)
                                    self.message_log.add_message(f"卸下了技能：{skill.name}", MessageType.ITEM)
                                    self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
                            break
                    
                    # 檢查是否點擊了技能項目本身
                    skill_panel_x = self.ui.skill_panel_rect.x
                    skill_panel_y = self.ui.skill_panel_rect.y
                    list_y = 80  # 技能列表起始Y座標
                    skill_height = 130  # 每個技能項的高度（包含間距）
                    
                    learned_skills = self.player.get_learned_skills()
                    if learned_skills:
                        # 計算可見範圍
                        visible_skills = (self.ui.skill_panel_rect.height - 180) // skill_height
                        scroll_offset = max(0, self.ui.skill_selection - visible_skills + 1)
                        
                        # 檢查點擊了哪個技能
                        for i in range(scroll_offset, min(scroll_offset + visible_skills, len(learned_skills))):
                            skill_y = skill_panel_y + list_y + (i - scroll_offset) * skill_height
                            skill_rect = pygame.Rect(skill_panel_x + 10, skill_y, self.ui.skill_panel_rect.width - 20, skill_height - 10)
                            
                            if skill_rect.collidepoint(pos):
                                self.ui.skill_selection = i
                                self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
                                break
                    
                    # 檢查是否點擊了快捷欄
                    hotbar_y = skill_panel_y + self.ui.skill_panel_rect.height - 70
                    slot_size = 50
                    slot_spacing = 15
                    total_slots_width = 4 * slot_size + 3 * slot_spacing
                    slot_x_start = skill_panel_x + (self.ui.skill_panel_rect.width - total_slots_width) // 2
                    
                    for i in range(4):
                        slot_x = slot_x_start + i * (slot_size + slot_spacing)
                        slot_rect = pygame.Rect(slot_x, hotbar_y, slot_size, slot_size)
                        
                        if slot_rect.collidepoint(pos):
                            # 點擊快捷欄，裝備當前選中的技能到這個位置
                            if learned_skills and 0 <= self.ui.skill_selection < len(learned_skills):
                                skill = learned_skills[self.ui.skill_selection]
                                if self.player.equip_skill(skill.id, i):
                                    self.message_log.add_message(
                                        f"將 {skill.name} 裝備到快捷鍵 {i + 1}",
                                        MessageType.ITEM
                                    )
                                    self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.5)
                            break
        
        elif self.state == GameState.MENU:
            # 主選單點擊處理
            menu_options = 6  # 開始、繼續、教學、設定、成就、退出
            button_width = 400
            button_height = 55
            button_spacing = 70
            menu_y = 320
            button_start_x = WINDOW_WIDTH // 2 - button_width // 2
            
            for i in range(menu_options):
                button_y = menu_y + i * button_spacing
                button_rect = pygame.Rect(button_start_x, button_y, button_width, button_height)
                
                if button_rect.collidepoint(pos):
                    self.ui.menu_selection = i
                    self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume)
                    
                    # 執行選單選項
                    if i == 0:  # 開始遊戲
                        self.new_game()
                    elif i == 1:  # 繼續遊戲
                        if SaveSystem.has_save():
                            self.load_game()
                    elif i == 2:  # 教學
                        self.tutorial = TutorialSystem() # << 同樣重新創建教學物件
                        self.state = GameState.TUTORIAL
                    elif i == 3:  # 設定
                        self.state = GameState.SETTINGS
                    elif i == 4:  # 成就
                        self.state = GameState.ACHIEVEMENTS
                    elif i == 5:  # 退出
                        self.running = False
                    break
        
        elif self.state == GameState.PAUSED:
            # 暫停選單點擊處理
            panel_width = 400
            panel_height = 350 # 使用更新後的高度
            panel_x = (WINDOW_WIDTH - panel_width) // 2
            panel_y = (WINDOW_HEIGHT - panel_height) // 2
            
            # 修改選項和對應的動作
            options = [
                (GameTexts.PAUSE_RESUME, 120),
                (GameTexts.PAUSE_SAVE, 160),
                (GameTexts.SETTINGS_TITLE, 200),
                (GameTexts.PAUSE_MENU, 240)
            ]
            
            for i, (text, y) in enumerate(options):
                button_rect = pygame.Rect(panel_x + 100, panel_y + y - 15, 200, 30)
                if button_rect.collidepoint(pos):
                    if i == 0:  # 繼續
                        self.state = GameState.PLAYING
                    elif i == 1:  # 保存
                        self.save_game()
                    elif i == 2:  # 遊戲設定
                        self.previous_state = self.state # 記住是從 PAUSED 來的
                        self.state = GameState.SETTINGS
                    elif i == 3:  # 主選單
                        self.state = GameState.MENU
                    self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume)
                    break
        
        elif self.state == GameState.GAME_OVER:
            # 遊戲結束畫面點擊處理
            # R鍵重新開始，ESC返回主選單（這裡可以添加按鈕點擊）
            panel_width = 800
            panel_height = 650
            panel_x = (WINDOW_WIDTH - panel_width) // 2
            panel_y = (WINDOW_HEIGHT - panel_height) // 2
            
            # 重新開始按鈕
            restart_button = pygame.Rect(panel_x + panel_width // 2 - 100, panel_y + panel_height - 120, 200, 40)
            if restart_button.collidepoint(pos):
                self.new_game()
                self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume)
            
            # 主選單按鈕
            menu_button = pygame.Rect(panel_x + panel_width // 2 - 100, panel_y + panel_height - 70, 200, 40)
            if menu_button.collidepoint(pos):
                self.state = GameState.MENU
                self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume)
        
        elif self.state == GameState.TUTORIAL:
            # 教學畫面點擊處理
            # 點擊任意位置進入下一步
            self.tutorial.next_step()
            if self.tutorial.completed:
                self.state = GameState.MENU
                self.asset_manager.play_sound('menu_sound')

    def _handle_mouse_right_click(self, pos):
        """處理滑鼠右鍵點擊"""
        if self.state == GameState.PLAYING:
            # 檢查物品
            tile_x = (pos[0] + self.camera_offset.x) // TILE_SIZE
            tile_y = (pos[1] + self.camera_offset.y) // TILE_SIZE
            
            # 顯示詳細信息
            self.ui.show_tooltip("右鍵查看詳情", pos)
    
    def _handle_mouse_wheel(self, direction):
        """處理滑鼠滾輪"""
        if self.state == GameState.ACHIEVEMENTS:
            self.ui.achievement_scroll += direction * 80
            self.ui.achievement_scroll = max(0, self.ui.achievement_scroll)
        elif self.state == GameState.PLAYING:
            # 在遊戲中滾動訊息日誌
            if direction > 0:
                self.message_log.scroll_up()
            else:
                self.message_log.scroll_down()
        elif self.state == GameState.INVENTORY:
            if self.ui.inventory_panel_focused:
                # 背包滾動
                if self.player.inventory:
                    # 計算每行顯示的物品數
                    items_per_row = 2
                    # 計算總行數
                    total_rows = (len(self.player.inventory) + items_per_row - 1) // items_per_row
                    # 計算可見行數（根據背包界面高度）
                    item_height = 100
                    panel_height = 700
                    list_height = panel_height - 190  # 扣除標題和底部區域
                    visible_rows = list_height // item_height
                    
                    # 計算最大滾動偏移
                    max_scroll_rows = max(0, total_rows - visible_rows)
                    
                    # 更新滾動偏移
                    if direction > 0:  # 向上滾動
                        self.ui.inventory_scroll_offset = max(0, self.ui.inventory_scroll_offset - 1)
                    else:  # 向下滾動
                        self.ui.inventory_scroll_offset = min(max_scroll_rows, self.ui.inventory_scroll_offset + 1)
            else:
                # 技能面板滾動
                learned_skills = self.player.get_learned_skills()
                if learned_skills:
                    # 向上滾動（滾輪向上）
                    if direction > 0:
                        self.ui.skill_selection = max(0, self.ui.skill_selection - 1)
                    # 向下滾動（滾輪向下）
                    else:
                        self.ui.skill_selection = min(len(learned_skills) - 1, self.ui.skill_selection + 1)
                    
                    self.asset_manager.play_sound('menu_sound', self.settings.sfx_volume * 0.3)

    def _player_move(self, direction: Direction):
        """玩家移動"""
        # 記錄移動方向
        self.last_move_direction = direction
        
        new_pos = Position(
            self.player.position.x + direction.value[0],
            self.player.position.y + direction.value[1]
        )
        
        # 檢查是否有敵人
        target_enemy = self.dungeon_map.get_blocking_entity(new_pos)
        
        if target_enemy:
            # 攻擊敵人
            self._player_attack(target_enemy)
        elif self.dungeon_map.is_walkable(new_pos):
            # 移動
            self.player.position = new_pos
            # 重要：同步更新精確位置
            self.player.fractional_position = Position(float(new_pos.x), float(new_pos.y))
            
            # 更新視野
            self.dungeon_map.update_fov(self.player.position)
            
            # 自動拾取金幣
            if self.settings.auto_pickup:
                self._auto_pickup_gold()

    def _auto_move_to(self, target_pos: Position):
        """自動移動到目標位置（簡化版）"""
        # 計算方向
        dx = target_pos.x - self.player.position.x
        dy = target_pos.y - self.player.position.y
        
        # 限制為單步移動
        if abs(dx) > 1:
            dx = 1 if dx > 0 else -1
        if abs(dy) > 1:
            dy = 1 if dy > 0 else -1
        
        # 嘗試移動
        for direction in Direction:
            if direction.value == (dx, dy):
                self._player_move(direction)
                break

    def _player_attack(self, enemy: Enemy):
        # 檢查是否為友方單位
        if hasattr(enemy, 'is_friendly') and enemy.is_friendly:
            self.message_log.add_message(
                f"你不能攻擊友方的{enemy.name}！",
                MessageType.WARNING
            )
            return
        
        is_critical = random.random() < self.player.stats.crit_chance
        damage = self.player.get_total_attack()
        if is_critical:
            damage = int(damage * self.player.stats.crit_damage)
            self.game_stats.total_critical_hits += 1
        
        hit_chance = 0.9
        if random.random() < hit_chance:
            actual_damage = enemy.take_damage(damage, self.player.name, self.message_log)
            self.particle_system.add_damage_text(enemy.position, actual_damage, critical=is_critical)
            self.particle_system.add_hit_effect(enemy.position, critical=is_critical)
            
            if is_critical:
                self.asset_manager.play_sound('critical_sound', self.settings.sfx_volume)
            else:
                self.asset_manager.play_sound('hit_sound', self.settings.sfx_volume)
            
            self.game_stats.total_damage_dealt += actual_damage
            
            if is_critical:
                self.message_log.add_message(
                    GameTexts.COMBAT_CRITICAL_HIT.format(damage=actual_damage),
                    MessageType.COMBAT
                )
            
            if not enemy.active:
                exp_gained = 20 + (self.dungeon_level - 1) * 10
                if enemy.is_boss:
                    exp_gained *= 5
                
                gold_gained = random.randint(20, 50) + (self.dungeon_level - 1) * 5
                if enemy.is_boss:
                    gold_gained *= 3
                
                self.player.gain_exp(exp_gained, self.message_log)
                self.player.gold += gold_gained
                
                self.message_log.add_message(
                    GameTexts.COMBAT_ENEMY_DEFEATED.format(
                        enemy=enemy.name, exp=exp_gained, gold=gold_gained
                    ),
                    MessageType.COMBAT
                )
                
                self.particle_system.add_exp_text(enemy.position, exp_gained)
                self.particle_system.add_pickup_effect(enemy.position, "gold")
                self.asset_manager.play_sound('level_up_sound', self.settings.sfx_volume * 0.7)
                
                self.game_stats.total_kills += 1
                self.game_stats.total_gold_collected += gold_gained
                
                if self.game_stats.total_kills == 1:
                    self.achievement_system.unlock("first_kill", self.message_log, self.particle_system, self.player.position)
                
                if enemy.image_key == 'dragon':
                    self.achievement_system.unlock("dragon_slayer", self.message_log, self.particle_system, self.player.position)
                
                if random.random() < 0.3 + (0.1 if enemy.is_boss else 0):
                    self._enemy_drop_item(enemy.position)
        else:
            self.message_log.add_message(
                GameTexts.COMBAT_MISS.format(attacker="你", target=enemy.name),
                MessageType.COMBAT
            )


    def _use_skill(self, skill_index: int):
        try:
            if skill_index >= len(self.player.equipped_skills):
                return
                
            skill = self.player.equipped_skills[skill_index]
            if skill is None:
                self.message_log.add_message(
                    f"快捷鍵 {skill_index + 1} 沒有裝備技能！",
                    MessageType.WARNING
                )
                return
                
            if not skill.is_learned:
                self.message_log.add_message(
                    f"你還沒有學會 {skill.name}！",
                    MessageType.WARNING
                )
                return
                
            if skill.current_cooldown > 0:
                self.message_log.add_message(
                    f"{skill.name}還在冷卻中！({int(skill.current_cooldown)}秒)",
                    MessageType.WARNING
                )
                return
                
            # 檢查魔力是否足夠（提前檢查，避免無謂的動畫）
            if self.player.stats.mp < skill.mp_cost:
                self.message_log.add_message("魔力不足！", MessageType.WARNING)
                return
                
            target_pos = self.get_skill_target_position(skill)
            
            # 傳遞必要的參數給玩家
            self.player.dungeon_level = self.dungeon_level
            self.player.dungeon_map = self.dungeon_map
            self.player.game_stats = self.game_stats
            self.player.achievement_system = self.achievement_system
            self.player.message_log = self.message_log
            
            # 使用技能，只有成功時才播放動畫
            skill_success = self.player.use_skill(skill_index, target_pos, self.asset_manager, 
                                                 self.message_log, self.particle_system, 
                                                 self.dungeon_map.enemies, self.dungeon_map)
            
            if skill_success:
                # 只在技能成功使用時才播放動畫和特效
                self.game_stats.total_skills_used += 1
                
                # 顯示技能範圍指示器
                self.showing_skill_range = True
                self.skill_range_skill = skill
                self.skill_range_target = target_pos
                self.skill_range_timer = 1.0
                
                # 技能特效
                skill_type_map = {
                    'slash': 'slash_enhanced',
                    'fireball': 'fireball_enhanced',
                    'lightning': 'lightning_enhanced',
                    'heal': 'heal_enhanced',
                    'shield': 'shield_enhanced',
                    'ice_spike': 'ice_spike_enhanced',
                    'summon': 'summon_enhanced'
                }
                
                enhanced_type = skill_type_map.get(skill.id, skill.id)
                
                if skill.id == 'summon':
                    pass  # 召喚已經在 use_skill 中處理特效
                elif skill.id in ['heal', 'shield']:
                    effect_position = self.player.position
                    self.particle_system.add_enhanced_skill_effect(effect_position, enhanced_type)
                else:
                    effect_position = target_pos
                    self.particle_system.add_enhanced_skill_effect(effect_position, enhanced_type)
                    
        except Exception as e:
            print(f"技能釋放錯誤: {e}")
            self.message_log.add_message("技能釋放失敗！", MessageType.WARNING)

            
    def _enemy_drop_item(self, position: Position):
        """敵人掉落物品（與Game類中的方法相同）"""
        if hasattr(self, 'dungeon_map') and hasattr(self, 'dungeon_level'):
            dungeon_level = self.dungeon_level
            dungeon_map = self.dungeon_map
            
            if dungeon_level >= 8 and random.random() < 0.1:
                if random.random() < 0.5:
                    item = dungeon_map.item_db.create_weapon('legendary_sword')
                else:
                    if random.random() < 0.5:
                        item = dungeon_map.item_db.create_armor('legendary_armor')
                    else:
                        item = dungeon_map.item_db.create_boots('legendary_boots')
            else:
                item_type = random.choice(['weapon', 'armor', 'potion', 'scroll', 'boots'])
                
                if item_type == 'weapon':
                    weapon_key = random.choice(['dagger', 'sword', 'axe', 'mace', 'bow'])
                    item = dungeon_map.item_db.create_weapon(weapon_key)
                elif item_type == 'armor':
                    armor_key = random.choice(['leather_armor', 'chain_mail', 'plate_armor', 'shield', 'helmet'])
                    item = dungeon_map.item_db.create_armor(armor_key)
                elif item_type == 'boots':
                    boots_key = random.choice(['leather_boots', 'speed_boots', 'mage_boots', 'warrior_boots'])
                    item = dungeon_map.item_db.create_boots(boots_key)
                elif item_type == 'potion':
                    potion_key = random.choice(['red_potion', 'blue_potion', 'yellow_potion'])
                    item = dungeon_map.item_db.create_potion(potion_key)
                else:
                    item = dungeon_map.item_db.create_scroll(None)
                    
            dungeon_map.items.append((position, item))
            
            if hasattr(self, 'message_log'):
                self.message_log.add_message(f"{item.name}掉落了！", MessageType.ITEM)

    def _player_pickup(self):
        """玩家拾取物品"""
        player_pos = self.player.position
        
        # 查找玩家位置的物品
        for item_pos, item in self.dungeon_map.items[:]:
            if item_pos.x == player_pos.x and item_pos.y == player_pos.y:
                if self.player.add_item(item, self.message_log):
                    self.dungeon_map.items.remove((item_pos, item))
                    self.asset_manager.play_sound('pickup_sound', self.settings.sfx_volume)
                    self.particle_system.add_pickup_effect(player_pos, item.item_type)
                    
                    # 統計
                    self.game_stats.total_items_collected += 1
                    if item.item_type == ItemType.GOLD:
                        self.game_stats.total_gold_collected += item.value
                    
                    return
        
        # 沒有物品
        self.message_log.add_message("這裡沒有可以撿起的物品", MessageType.NORMAL)
    
    def _player_rest(self):
        """玩家休息"""
        # 檢查附近是否有敵人
        nearby_enemies = []
        for enemy in self.dungeon_map.enemies:
            if enemy.active and enemy.position.distance_to(self.player.position) <= 8:
                nearby_enemies.append(enemy)
        
        if nearby_enemies:
            self.message_log.add_message(GameTexts.REST_INTERRUPTED, MessageType.WARNING)
            return
        
        if self.player.rest(self.message_log):
            self.particle_system.add_heal_text(self.player.position, 20)
            # 移除了 self.action_taken = True

    def _auto_pickup_gold(self):
        """自動拾取金幣"""
        player_pos = self.player.position
        
        for item_pos, item in self.dungeon_map.items[:]:
            if item.item_type == ItemType.GOLD and item_pos.x == player_pos.x and item_pos.y == player_pos.y:
                self.player.add_item(item, self.message_log, auto=True)
                self.dungeon_map.items.remove((item_pos, item))
                self.particle_system.add_pickup_effect(player_pos, "gold")
                
                # 統計
                self.game_stats.total_items_collected += 1
                self.game_stats.total_gold_collected += item.value

    def _auto_pickup_items(self):
        """自動拾取物品（不只是金幣）"""
        player_pos = self.player.position
        
        for item_pos, item in self.dungeon_map.items[:]:
            if item_pos.x == player_pos.x and item_pos.y == player_pos.y:
                # 金幣總是自動撿取
                if item.item_type == ItemType.GOLD:
                    if self.player.add_item(item, self.message_log, auto=True):
                        self.dungeon_map.items.remove((item_pos, item))
                        self.particle_system.add_pickup_effect(player_pos, item.item_type)
                        
                        # 統計
                        self.game_stats.total_items_collected += 1
                        self.game_stats.total_gold_collected += item.value
                # 如果開啟自動撿取，撿取所有物品（除了已經撿取的金幣）
                elif self.settings.auto_pickup:
                    if self.player.add_item(item, self.message_log, auto=True):
                        self.dungeon_map.items.remove((item_pos, item))
                        self.particle_system.add_pickup_effect(player_pos, item.item_type)
                        
                        # 統計
                        self.game_stats.total_items_collected += 1
               
    def update(self, dt: float):
        self.ui.update(dt)
        self.message_log.update()
        self.particle_system.update(dt)
        if self.showing_skill_range and self.skill_range_timer > 0:
            self.skill_range_timer -= dt
            if self.skill_range_timer <= 0:
                self.showing_skill_range = False
        if self.state != GameState.PLAYING:
            return
        if self.player:
            move_x = 0
            move_y = 0
            if self.keys_pressed[pygame.K_UP] or self.keys_pressed[pygame.K_w]:
                move_y -= 1
            if self.keys_pressed[pygame.K_DOWN] or self.keys_pressed[pygame.K_s]:
                move_y += 1
            if self.keys_pressed[pygame.K_LEFT] or self.keys_pressed[pygame.K_a]:
                move_x -= 1
            if self.keys_pressed[pygame.K_RIGHT] or self.keys_pressed[pygame.K_d]:
                move_x += 1
            if self.keys_pressed[pygame.K_q]:
                move_x -= 1
                move_y -= 1
            if self.keys_pressed[pygame.K_e]:
                move_x += 1
                move_y -= 1
            if self.keys_pressed[pygame.K_z]:
                move_x -= 1
                move_y += 1
            if self.keys_pressed[pygame.K_c]:
                move_x += 1
                move_y += 1
            self.player.set_velocity(move_x, move_y)
            self.player.update(dt)
            self.player.update_skills(dt)
            self.player.update_buffs(dt)  # 添加這行
            self.player.update_mana_regeneration(dt)  # 新增：更新魔力回復
            self.player.update_movement(dt, self.dungeon_map)
            self.player.update_combat(dt, self.dungeon_map.enemies, self.message_log, 
                                    self.particle_system, self.asset_manager, self.game_stats)
        for enemy in self.dungeon_map.enemies[:]:  
            if enemy.active:
                enemy.update(self.player, self.dungeon_map, dt)
                enemy.visible = self.dungeon_map.visible[enemy.position.y][enemy.position.x]
                if enemy.is_friendly:
                    if hasattr(enemy, 'target') and enemy.target and hasattr(enemy.target, 'active'):
                        if (enemy.target.active and 
                            isinstance(enemy.target, Enemy) and 
                            not enemy.target.is_friendly and
                            enemy.can_attack(enemy.target.position)):
                            damage = enemy.attack(enemy.target, self.asset_manager, self.message_log, 
                                                self.particle_system, self.game_stats)
                            if damage > 0:
                                self.particle_system.add_damage_text(enemy.target.position, damage)
                                enemy.attack_cooldown = 0.8
                                if not enemy.target.active:
                                    self.game_stats.total_kills += 1
                                    exp_gained = 20 + (self.dungeon_level - 1) * 10
                                    if hasattr(enemy.target, 'is_boss') and enemy.target.is_boss:
                                        exp_gained *= 5
                                    self.player.gain_exp(exp_gained, self.message_log)
                                    self.particle_system.add_exp_text(self.player.position, exp_gained)
                                    gold_gained = random.randint(20, 50) + (self.dungeon_level - 1) * 5
                                    if hasattr(enemy.target, 'is_boss') and enemy.target.is_boss:
                                        gold_gained *= 3
                                    self.player.gold += gold_gained
                                    self.game_stats.total_gold_collected += gold_gained
                                    self.message_log.add_message(
                                        f"你的{enemy.name}擊敗了{enemy.target.name}！獲得{exp_gained}經驗值和{gold_gained}金幣！",
                                        MessageType.COMBAT
                                    )
                                    if random.random() < 0.3 + (0.1 if hasattr(enemy.target, 'is_boss') and enemy.target.is_boss else 0):
                                        self._enemy_drop_item(enemy.target.position)
                else:
                    if hasattr(enemy, 'target') and enemy.target and hasattr(enemy, 'ai_state'):
                        if enemy.ai_state == "attack" and enemy.target:
                            if (isinstance(enemy.target, Enemy) and 
                                enemy.target.is_friendly and 
                                enemy.target.active and
                                enemy.can_attack(enemy.target.position)):
                                damage = enemy.attack(enemy.target, self.asset_manager, self.message_log, 
                                                    self.particle_system, self.game_stats)
                                if damage > 0:
                                    self.particle_system.add_damage_text(enemy.target.position, damage)
                                    enemy.attack_cooldown = 0.8
                                    if not enemy.target.active:
                                        self.message_log.add_message(
                                            f"你的{enemy.target.name}被{enemy.name}擊敗了！",
                                            MessageType.WARNING
                                        )
                            elif enemy.target == self.player and enemy.can_attack(self.player.position):
                                damage = enemy.attack(self.player, self.asset_manager, self.message_log, 
                                                    self.particle_system, self.game_stats)
                                if damage > 0:
                                    self.particle_system.add_damage_text(self.player.position, damage)
                                    self.game_stats.total_damage_taken += damage
                                    self.game_stats.current_floor_damage_taken += damage
                                    enemy.attack_cooldown = 0.8
                    else:
                        if enemy.can_attack(self.player.position):
                            damage = enemy.attack(self.player, self.asset_manager, self.message_log, 
                                                self.particle_system, self.game_stats)
                            if damage > 0:
                                self.particle_system.add_damage_text(self.player.position, damage)
                                self.game_stats.total_damage_taken += damage
                                self.game_stats.current_floor_damage_taken += damage
                                enemy.attack_cooldown = 0.8
            else:
                if hasattr(enemy, 'just_died') and enemy.just_died:
                    if not enemy.is_friendly:
                        if random.random() < 0.3 + (0.1 if enemy.is_boss else 0):
                            self._enemy_drop_item(enemy.position)
                    enemy.just_died = False
        self.dungeon_map.enemies = [e for e in self.dungeon_map.enemies if e.active or not hasattr(e, 'just_died')]
        if self.settings.auto_pickup:
            self._auto_pickup_items()
        if self.dungeon_map.get_tile(self.player.position) == 'stairs':
            if not self.on_stairs:
                self.on_stairs = True
                self.stairs_hint_timer = 0  
                self.message_log.add_message(
                    GameTexts.EXPLORE_FIND_STAIRS,
                    MessageType.STORY
                )
                self.message_log.add_message(
                    "按 空白鍵 進入下一層地牢",
                    MessageType.LEVEL_UP  
                )
        else:
            self.on_stairs = False
            self.stairs_hint_timer = 0
        if self.on_stairs:
            self.stairs_hint_timer += dt
        if self.player.stats.hp <= 0:
            self.state = GameState.GAME_OVER
            self.asset_manager.play_sound('death_sound', self.settings.sfx_volume)
            self.game_stats.total_deaths += 1
            self.game_stats.highest_level = max(self.game_stats.highest_level, self.player.stats.level)
            self.game_stats.deepest_floor = max(self.game_stats.deepest_floor, self.dungeon_level)
            self.game_stats.longest_run_turns = max(self.game_stats.longest_run_turns, self.turn_count)
            self.game_stats.save()
        self._update_camera()
        unlocked = self.achievement_system.check_achievements(self.player, self.dungeon_level, self.game_stats)
        for achievement_id in unlocked:
            self.particle_system.add_achievement_effect(self.player.position)
        self.turn_count = int(pygame.time.get_ticks() / 1000)
 
    def _update_camera(self):
        """更新攝像機位置（考慮UI高度）"""
        # 定義遊戲區域
        UI_TOP_HEIGHT = 60
        UI_BOTTOM_HEIGHT = 140
        GAME_AREA_HEIGHT = WINDOW_HEIGHT - UI_TOP_HEIGHT - UI_BOTTOM_HEIGHT
        
        # 讓攝像機跟隨玩家，但限制在遊戲區域內
        target_x = (self.player.position.x * TILE_SIZE) - (WINDOW_WIDTH // 2)
        target_y = (self.player.position.y * TILE_SIZE) - (GAME_AREA_HEIGHT // 2)
        
        # 限制攝像機邊界，確保不會顯示超出地圖的區域
        max_x = max(0, (self.dungeon_map.width * TILE_SIZE) - WINDOW_WIDTH)
        max_y = max(0, (self.dungeon_map.height * TILE_SIZE) - GAME_AREA_HEIGHT)
        
        self.camera_offset.x = max(0, min(target_x, max_x))
        self.camera_offset.y = max(0, min(target_y, max_y))

    def _next_level(self):
        """進入下一層"""
        # 檢查無傷成就
        if self.game_stats.current_floor_damage_taken == 0:
            self.achievement_system.unlock("no_damage_floor", self.message_log, 
                                         self.particle_system, self.player.position)
        
        self.dungeon_level += 1
        
        # 統計
        self.game_stats.total_floors_explored += 1
        self.game_stats.deepest_floor = max(self.game_stats.deepest_floor, self.dungeon_level)
        self.game_stats.current_floor_damage_taken = 0
        
        # 生成新地圖
        self.dungeon_map = DungeonMap(MAP_WIDTH, MAP_HEIGHT, self.dungeon_level)
        # 傳遞玩家資訊給地圖，以便檢查已鑑定物品
        self.dungeon_map.player = self.player
        # 將玩家放置在第一個房間
        if self.dungeon_map.rooms:
            first_room = self.dungeon_map.rooms[0]
            new_x = first_room.centerx
            new_y = first_room.centery
            
            # 重置玩家位置（重要：必須同時重置兩個位置）
            self.player.position = Position(new_x, new_y)
            self.player.fractional_position = Position(float(new_x), float(new_y))
            
            # 重置玩家速度
            self.player.velocity = Position(0, 0)
            self.player.is_moving = False
            
            # 重置移動冷卻
            self.player.move_cooldown = 0
            self.player.attack_cooldown = 0
        
        # 立即更新相機位置到玩家位置
        self._update_camera()
        
        # 更新視野
        self.dungeon_map.update_fov(self.player.position)
        
        # 治療玩家
        heal_amount = self.player.stats.max_hp // 3
        actual_heal = self.player.heal(heal_amount)
        if actual_heal > 0:
            self.particle_system.add_heal_text(self.player.position, actual_heal)
        
        # 恢復魔力
        mana_amount = self.player.stats.max_mp // 2
        self.player.restore_mana(mana_amount)
        
        # 添加進入新層的訊息
        self.message_log.add_message(
            GameTexts.EXPLORE_ENTER_FLOOR.format(floor=self.dungeon_level),
            MessageType.STORY
        )
        
        # 特效
        self.particle_system.add_level_up_effect(self.player.position)
        
        # 重置樓梯訊息標記
        if hasattr(self, '_stairs_message_shown'):
            delattr(self, '_stairs_message_shown')

    def render_skill_range_indicator(self, surface, skill: Skill, target_pos: Position, 
                                     camera_offset: Position):
        """渲染技能範圍指示器"""
        if skill.id == 'slash':
            # 劍刃斬 - 圓形範圍
            center_x = self.player.position.x * TILE_SIZE + TILE_SIZE // 2 - camera_offset.x
            center_y = self.player.position.y * TILE_SIZE + TILE_SIZE // 2 - camera_offset.y
            radius = skill.range * TILE_SIZE
            
            # 繪製半透明圓形範圍
            range_surface = pygame.Surface((int(radius * 2 + 10), int(radius * 2 + 10)), pygame.SRCALPHA)
            
            # 漸變效果
            for i in range(int(radius), 0, -5):
                alpha = int(80 * (1 - i / radius))
                color = (*Colors.NEON_ORANGE, alpha)
                pygame.gfxdraw.filled_circle(range_surface, int(radius + 5), int(radius + 5), i, color)
            
            # 邊框
            pygame.gfxdraw.circle(range_surface, int(radius + 5), int(radius + 5), int(radius), Colors.NEON_ORANGE)
            
            surface.blit(range_surface, (center_x - radius - 5, center_y - radius - 5))
            
        elif skill.id == 'fireball':
            # 火球術 - 爆炸範圍
            # 繪製瞄準線
            start_x = self.player.position.x * TILE_SIZE + TILE_SIZE // 2 - camera_offset.x
            start_y = self.player.position.y * TILE_SIZE + TILE_SIZE // 2 - camera_offset.y
            end_x = target_pos.x * TILE_SIZE + TILE_SIZE // 2 - camera_offset.x
            end_y = target_pos.y * TILE_SIZE + TILE_SIZE // 2 - camera_offset.y
            
            # 瞄準線（虛線）
            distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
            if distance > 0:
                dx = (end_x - start_x) / distance
                dy = (end_y - start_y) / distance
                
                for i in range(0, int(distance), 10):
                    if i % 20 < 10:  # 虛線效果
                        dot_x = start_x + dx * i
                        dot_y = start_y + dy * i
                        pygame.gfxdraw.filled_circle(surface, int(dot_x), int(dot_y), 2, Colors.NEON_YELLOW)
            
            # 爆炸範圍
            explosion_range = 3 if skill.current_level >= 3 else 2
            if skill.current_level >= 5:
                explosion_range = 4
            
            explosion_radius = explosion_range * TILE_SIZE
            
            # 爆炸範圍指示器
            explosion_surface = pygame.Surface((explosion_radius * 2, explosion_radius * 2), pygame.SRCALPHA)
            
            # 多層圓環效果
            for i in range(3):
                radius = explosion_radius - i * 10
                alpha = 60 - i * 15
                color = (*Colors.NEON_ORANGE, alpha)
                pygame.gfxdraw.filled_circle(explosion_surface, explosion_radius, explosion_radius, radius, color)
            
            # 外框
            pygame.gfxdraw.circle(explosion_surface, explosion_radius, explosion_radius, 
                                 explosion_radius - 1, Colors.NEON_ORANGE)
            
            surface.blit(explosion_surface, (end_x - explosion_radius, end_y - explosion_radius))
            
        elif skill.id in ['lightning', 'ice_spike']:
            # 閃電鏈/冰錐術 - 扇形範圍
            center_x = self.player.position.x * TILE_SIZE + TILE_SIZE // 2 - camera_offset.x
            center_y = self.player.position.y * TILE_SIZE + TILE_SIZE // 2 - camera_offset.y
            
            # 計算方向
            dx = target_pos.x - self.player.position.x
            dy = target_pos.y - self.player.position.y
            
            if dx != 0 or dy != 0:
                angle = math.atan2(dy, dx)
                
                # 繪製扇形
                arc_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                
                # 扇形參數
                arc_angle = math.pi / 3  # 60度扇形
                num_points = 20
                radius = skill.range * TILE_SIZE
                
                points = [(center_x, center_y)]
                
                for i in range(num_points + 1):
                    current_angle = angle - arc_angle/2 + (arc_angle * i / num_points)
                    px = center_x + radius * math.cos(current_angle)
                    py = center_y + radius * math.sin(current_angle)
                    points.append((px, py))
                
                # 填充扇形
                color = Colors.NEON_CYAN if skill.id == 'lightning' else Colors.NEON_BLUE
                pygame.gfxdraw.filled_polygon(arc_surface, points, (*color, 40))
                pygame.gfxdraw.polygon(arc_surface, points, color)
                
                surface.blit(arc_surface, (0, 0))

    def render(self):
        """渲染遊戲（使用虛擬表面解決縮放問題）"""
        # 清空虛擬遊戲表面
        self.game_surface.fill(Colors.BLACK)
        
        # 定義UI佔用的空間
        UI_TOP_HEIGHT = 60
        UI_BOTTOM_HEIGHT = 140
        GAME_AREA_Y = UI_TOP_HEIGHT
        GAME_AREA_HEIGHT = WINDOW_HEIGHT - UI_TOP_HEIGHT - UI_BOTTOM_HEIGHT
        
        if self.state == GameState.MENU:
            self.ui.render_menu(self.game_surface, SaveSystem.has_save())
        
        elif self.state == GameState.TUTORIAL:
            self.ui.render_tutorial(self.game_surface, self.tutorial)
        
        elif self.state == GameState.SETTINGS:
            # 設置轉換後的滑鼠座標給UI使用
            self.ui.set_mouse_pos(self.mouse_pos)
            
            # 創建臨時設定對象，確保UI使用正確的解析度
            temp_resolution = self.ui.resolution
            self.ui.resolution = self.game_resolution  # 使用遊戲內部解析度
            self.ui.render_settings(self.game_surface, self.settings)
            self.ui.resolution = temp_resolution  # 恢復原值
        
        elif self.state == GameState.ACHIEVEMENTS:
            self.ui.render_achievements(self.game_surface, self.achievement_system)
        
        elif self.state in [GameState.PLAYING, GameState.PAUSED, GameState.INVENTORY]:
            # 創建遊戲區域的裁剪表面
            game_area_surface = pygame.Surface((WINDOW_WIDTH, GAME_AREA_HEIGHT))
            game_area_surface.fill(Colors.BLACK)
            
            # 調整相機偏移以適應遊戲區域
            adjusted_camera_offset = Position(
                self.camera_offset.x,
                self.camera_offset.y
            )
            
            # 渲染遊戲世界到遊戲表面
            self.dungeon_map.render(game_area_surface, adjusted_camera_offset, self.asset_manager)
            
            # 渲染物品
            for item_pos, item in self.dungeon_map.items:
                if self.dungeon_map.visible[item_pos.y][item_pos.x]:
                    if item.icon:
                        image = self.asset_manager.get_image(item.icon)
                        if image:
                            screen_x = (item_pos.x * TILE_SIZE) - adjusted_camera_offset.x
                            screen_y = (item_pos.y * TILE_SIZE) - adjusted_camera_offset.y
                            
                            if (-TILE_SIZE <= screen_x <= WINDOW_WIDTH and 
                                -TILE_SIZE <= screen_y <= GAME_AREA_HEIGHT):
                                
                                float_offset = math.sin(self.ui.animation_time * 2 + item_pos.x + item_pos.y) * 3
                                game_area_surface.blit(image, (screen_x, screen_y + float_offset))
                                
                                if hasattr(self, 'debug_mode') and self.debug_mode:
                                    debug_text = f"{item.icon}"
                                    debug_surface = self.asset_manager.fonts.render_text(debug_text, 10, Colors.WHITE)
                                    game_area_surface.blit(debug_surface, (screen_x, screen_y - 10))
            
            # 渲染敵人
            for enemy in self.dungeon_map.enemies:
                if enemy.active and enemy.visible:
                    enemy.render(game_area_surface, adjusted_camera_offset, self.asset_manager)
            
            # 渲染敵人血條
            self.ui.render_enemy_health_bars(game_area_surface, self.dungeon_map.enemies, 
                                            adjusted_camera_offset, self.settings)
            
            # 渲染玩家
            self.player.render(game_area_surface, adjusted_camera_offset, self.asset_manager)
            
            # 渲染護盾效果
            if self.player.shield_active:
                shield_x = (self.player.position.x * TILE_SIZE) - adjusted_camera_offset.x
                shield_y = (self.player.position.y * TILE_SIZE) - adjusted_camera_offset.y
                shield_surface = pygame.Surface((TILE_SIZE * 2, TILE_SIZE * 2), pygame.SRCALPHA)
                
                pulse = abs(math.sin(self.ui.animation_time * 3))
                shield_alpha = int(80 + pulse * 40)
                shield_alpha = max(0, min(255, shield_alpha))
                shield_size = TILE_SIZE + int(pulse * 10)
                
                pygame.gfxdraw.filled_circle(shield_surface, TILE_SIZE, TILE_SIZE, 
                                            shield_size, (*Colors.NEON_CYAN, shield_alpha))
                pygame.gfxdraw.circle(shield_surface, TILE_SIZE, TILE_SIZE, 
                                    shield_size, Colors.NEON_CYAN)
                
                game_area_surface.blit(shield_surface, (shield_x - TILE_SIZE//2, shield_y - TILE_SIZE//2))
            
            # 渲染粒子效果
            self.particle_system.render(game_area_surface, adjusted_camera_offset, 
                                    self.asset_manager, self.settings)
            
            # 渲染技能範圍提示
            if self.showing_skill_range and self.skill_range_skill and self.skill_range_target:
                self.render_skill_range_indicator(game_area_surface, self.skill_range_skill, 
                                                 self.skill_range_target, adjusted_camera_offset)
                
            # 將遊戲表面渲染到虛擬表面的正確位置
            self.game_surface.blit(game_area_surface, (0, GAME_AREA_Y))
            
            # 渲染UI（傳遞on_stairs狀態）
            self.player.on_stairs = self.on_stairs  # 臨時將狀態附加到player對象
            self.ui.render_hud(self.game_surface, self.player, self.dungeon_level, 
                            self.turn_count, self.settings)
            self.ui.render_message_log(self.game_surface, self.message_log)
            self.ui.render_minimap(self.game_surface, self.dungeon_map, self.player, self.settings)
            
            # 渲染工具提示
            if self.settings.show_tooltips:
                self.ui.render_tooltip(self.game_surface)
            
            # 如果在背包狀態，渲染背包（同樣確保使用正確解析度）
            if self.state == GameState.INVENTORY:
                temp_resolution = self.ui.resolution
                self.ui.resolution = self.game_resolution
                self.ui.render_inventory(self.game_surface, self.player)
                self.ui.resolution = temp_resolution
            
            # 檔案: 1.py, 類別: Game, 函式: render

            # 如果暫停，渲染暫停覆蓋層
            if self.state == GameState.PAUSED:
                overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                overlay.fill((*Colors.BLACK, 150))
                self.game_surface.blit(overlay, (0, 0))
                
                # 暫停面板
                panel_width = 400
                panel_height = 350 # 增加面板高度
                panel_x = (WINDOW_WIDTH - panel_width) // 2
                panel_y = (WINDOW_HEIGHT - panel_height) // 2
                
                panel_surface = pygame.Surface((panel_width, panel_height))
                panel_surface.fill(Colors.UI_BG)
                pygame.draw.rect(panel_surface, Colors.UI_HIGHLIGHT, panel_surface.get_rect(), 4)
                
                pause_surface = self.asset_manager.fonts.render_text(GameTexts.PAUSE_TITLE, 36, Colors.UI_TEXT)
                pause_rect = pause_surface.get_rect(center=(panel_width // 2, 60))
                panel_surface.blit(pause_surface, pause_rect)
                
                # 修改選項列表
                options = [
                    (GameTexts.PAUSE_RESUME + " (ESC)", 120),
                    (GameTexts.PAUSE_SAVE + " (S)", 160),
                    (GameTexts.SETTINGS_TITLE + " (O)", 200), # 使用 GameTexts 常數
                    (GameTexts.PAUSE_MENU + " (Q)", 240)
                ]
                
                for text, y in options:
                    option_surface = self.asset_manager.fonts.render_text(text, 20, Colors.UI_TEXT)
                    option_rect = option_surface.get_rect(center=(panel_width // 2, y))
                    panel_surface.blit(option_surface, option_rect)
                
                self.game_surface.blit(panel_surface, (panel_x, panel_y))
        
        elif self.state == GameState.GAME_OVER:
            self.ui.render_game_over(self.game_surface, self.player, self.dungeon_level, 
                                self.turn_count, self.game_stats)
        
        # 調試模式：顯示滑鼠位置
        if hasattr(self, 'mouse_pos') and hasattr(self, 'debug_mode') and self.debug_mode:
            # 繪製十字準星
            pygame.draw.line(self.game_surface, Colors.NEON_GREEN, 
                            (self.mouse_pos[0] - 10, self.mouse_pos[1]), 
                            (self.mouse_pos[0] + 10, self.mouse_pos[1]), 2)
            pygame.draw.line(self.game_surface, Colors.NEON_GREEN, 
                            (self.mouse_pos[0], self.mouse_pos[1] - 10), 
                            (self.mouse_pos[0], self.mouse_pos[1] + 10), 2)
            
            # 顯示座標
            coord_text = f"遊戲座標: ({self.mouse_pos[0]}, {self.mouse_pos[1]})"
            coord_surface = self.asset_manager.fonts.render_text(coord_text, 14, Colors.NEON_GREEN)
            
            text_x = self.mouse_pos[0] + 15
            text_y = self.mouse_pos[1] + 15
            text_rect = coord_surface.get_rect()
            
            if text_x + text_rect.width > WINDOW_WIDTH:
                text_x = self.mouse_pos[0] - text_rect.width - 15
            if text_y + text_rect.height > WINDOW_HEIGHT:
                text_y = self.mouse_pos[1] - text_rect.height - 15
            
            bg_rect = pygame.Rect(text_x - 2, text_y - 2, text_rect.width + 4, text_rect.height + 4)
            pygame.draw.rect(self.game_surface, (*Colors.BLACK, 180), bg_rect)
            pygame.draw.rect(self.game_surface, Colors.NEON_GREEN, bg_rect, 1)
            
            self.game_surface.blit(coord_surface, (text_x, text_y))
        
        # === 最終渲染 ===
        # 清空實際螢幕
        self.screen.fill(Colors.BLACK)
        
        # 縮放虛擬表面到實際螢幕
        scaled_surface = pygame.transform.smoothscale(self.game_surface, self.scaled_size)
        
        # 渲染到螢幕中央
        self.screen.blit(scaled_surface, self.screen_offset)
        
        # 如果有黑邊，可以添加裝飾
        if self.screen_offset[0] > 0 or self.screen_offset[1] > 0:
            # 左右黑邊
            if self.screen_offset[0] > 0:
                # 左邊
                pygame.draw.rect(self.screen, Colors.UI_BG, 
                            (0, 0, self.screen_offset[0], self.actual_resolution[1]))
                # 右邊
                pygame.draw.rect(self.screen, Colors.UI_BG, 
                            (self.screen_offset[0] + self.scaled_size[0], 0, 
                                self.screen_offset[0], self.actual_resolution[1]))
            
            # 上下黑邊
            if self.screen_offset[1] > 0:
                # 上邊
                pygame.draw.rect(self.screen, Colors.UI_BG, 
                            (0, 0, self.actual_resolution[0], self.screen_offset[1]))
                # 下邊
                pygame.draw.rect(self.screen, Colors.UI_BG, 
                            (0, self.screen_offset[1] + self.scaled_size[1], 
                                self.actual_resolution[0], self.screen_offset[1]))
        
        pygame.display.flip()

    def run(self):
        """運行遊戲主循環"""
        while self.running:
            # 計算時間差
            current_time = time.time()
            self.dt = current_time - self.last_time
            self.last_time = current_time
            
            # 限制最大時間差（防止跳幀）
            self.dt = min(self.dt, 1.0 / 30)
            
            self.handle_events()
            self.update(self.dt)
            self.render()
            
            # 控制幀率
            self.clock.tick(FPS)
        
        # 保存設定和統計
        self.settings.save()
        self.game_stats.save()
        self.achievement_system.save()
        
        pygame.quit()
        sys.exit()

# ============================================================================
# 主程序入口
# ============================================================================

if __name__ == "__main__":
    try:
        # 創建並運行遊戲
        game = Game()
        game.run()
    except Exception as e:
        print(f"遊戲運行出錯: {e}")
        import traceback
        traceback.print_exc()
        
        # 確保pygame正確關閉
        try:
            pygame.quit()
        except:
            pass
        
        sys.exit(1)#!/usr/bin/env python3