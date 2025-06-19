from game.core import *

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
            'ring_power': {'color': Colors.NEON_YELLOW, 'emoji': '💍', 'text': "力", 'size': int(TILE_SIZE * 0.8), 'ring': True},
            'ring_agility': {'color': Colors.NEON_GREEN, 'emoji': '💍', 'text': "敏", 'size': int(TILE_SIZE * 0.8), 'ring': True},
            'ring_magic': {'color': Colors.NEON_PURPLE, 'emoji': '💍', 'text': "魔", 'size': int(TILE_SIZE * 0.8), 'ring': True},
            'ring_fire': {'color': Colors.NEON_ORANGE, 'emoji': '💍', 'text': "炎", 'size': int(TILE_SIZE * 0.8), 'ring': True},
            'ring_ice': {'color': Colors.NEON_CYAN, 'emoji': '💍', 'text': "冰", 'size': int(TILE_SIZE * 0.8), 'ring': True},
            'ring_wisdom': {'color': Colors.NEON_BLUE, 'emoji': '💍', 'text': "智", 'size': int(TILE_SIZE * 0.8), 'ring': True},
            'ring_vitality': {'color': Colors.NEON_PINK, 'emoji': '💍', 'text': "活", 'size': int(TILE_SIZE * 0.8), 'ring': True},
            'ring_fortune': {'color': Colors.EXP_YELLOW, 'emoji': '💍', 'text': "運", 'size': int(TILE_SIZE * 0.8), 'ring': True},
            'amulet_protection': {'color': Colors.NEON_CYAN, 'emoji': '🏅', 'text': "護", 'size': int(TILE_SIZE * 0.8), 'amulet': True},
            'amulet_life': {'color': Colors.NEON_PINK, 'emoji': '🏅', 'text': "命", 'size': int(TILE_SIZE * 0.8), 'amulet': True},
            'amulet_might': {'color': Colors.NEON_ORANGE, 'emoji': '🏅', 'text': "力", 'size': int(TILE_SIZE * 0.8), 'amulet': True},
            'amulet_speed': {'color': Colors.NEON_GREEN, 'emoji': '🏅', 'text': "速", 'size': int(TILE_SIZE * 0.8), 'amulet': True},
            'amulet_shadow': {'color': Colors.NEON_PURPLE, 'emoji': '🏅', 'text': "影", 'size': int(TILE_SIZE * 0.8), 'amulet': True},
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
                'ring_power': '戒',
                'ring_agility': '戒',
                'ring_magic': '戒',
                'ring_fire': '戒',
                'ring_ice': '戒',
                'ring_wisdom': '戒',
                'ring_vitality': '戒',
                'ring_fortune': '戒',
                'amulet_protection': '符',
                'amulet_life': '符',
                'amulet_might': '符',
                'amulet_speed': '符',
                'amulet_shadow': '符',
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
                    '深入地牢後會發現種類繁多的戒指與護符，請多嘗試搭配。',
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
                'title': '畫面與音效設定',
                'content': [
                    '隨時按 [KEY:O] 開啟設定畫面。',
                    '在這裡可調整音量、解析度，以及新的 [CONCEPT:像素倍增] 模式，',
                    '讓高解析度下的畫面更清晰，滑鼠定位更精準。',
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
