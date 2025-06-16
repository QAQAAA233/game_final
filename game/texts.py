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
    AMULET_PROTECTION = "護身符"
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

