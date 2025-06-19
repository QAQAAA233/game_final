from game.core import *

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
