from game.core import *
from game.resources import AssetManager

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

