from game.core import *
from game.entities import Player
from game.dungeon_map import DungeonMap
from game.resources import AssetManager, MessageLog

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
# 主遊戲類別
# ============================================================================

