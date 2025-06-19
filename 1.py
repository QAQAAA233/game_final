from game.core import *
from game.resources import FontManager, EmojiManager, EmojiRenderer, AssetManager, MessageLog, TutorialSystem
from game.particles import ParticleSystem
from game.save_system import SaveSystem
from game.entities import Entity, Player, Enemy
from game.dungeon_map import DungeonMap

from game.ui import UI
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
            
            # 計算縮放比例（保持長寬比），上擴時採用整數倍提升畫質
            scale_x = native_res[0] / self.game_resolution[0]
            scale_y = native_res[1] / self.game_resolution[1]
            float_scale = min(scale_x, scale_y)
            if float_scale >= 1:
                self.scale = max(1, int(float_scale))
            else:
                self.scale = float_scale
            
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
            
            # 使用實際視窗大小計算縮放，上擴時採用整數倍
            scale_x = self.actual_resolution[0] / self.game_resolution[0]
            scale_y = self.actual_resolution[1] / self.game_resolution[1]
            float_scale = min(scale_x, scale_y)
            if float_scale >= 1:
                self.scale = max(1, int(float_scale))
            else:
                self.scale = float_scale
            
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
        
        sys.exit(1)
