from game.core import *
from game.resources import AssetManager
from game.entities import Enemy


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

        # 飾品 (戒指與護身符 10%)
        accessory_count = max(1, item_count // 10)
        for _ in range(accessory_count):
            if floor_tiles:
                pos = floor_tiles.pop(random.randint(0, len(floor_tiles) - 1))
                if random.random() < 0.5:
                    ring_key = random.choice(list(self.item_db.ring_data.keys()))
                    item = self.item_db.create_ring(ring_key)
                else:
                    amulet_key = random.choice(list(self.item_db.amulet_data.keys()))
                    item = self.item_db.create_amulet(amulet_key)
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

