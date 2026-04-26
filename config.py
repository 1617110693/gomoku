"""
全局配置管理模块
负责管理应用程序的所有配置选项，包括游戏设置、训练参数、API配置等
"""
import os
import json
from pathlib import Path


class Config:
    """全局配置类"""

    # 项目根目录
    PROJECT_ROOT = Path(__file__).parent
    DATA_DIR = PROJECT_ROOT / "data"
    MODELS_DIR = DATA_DIR / "models"
    GAMES_DIR = DATA_DIR / "games"
    TRAINING_DATA_DIR = DATA_DIR / "training_data"
    DATABASE_PATH = DATA_DIR / "database.db"

    # 默认配置
    DEFAULT_BOARD_SIZE = 15
    DEFAULT_CONFIG = {
        # 游戏设置
        "game": {
            "board_size": 15,
            "enable_forbidden_hand": False,  # 禁手规则（可选）
            "max_undo_steps": 3,  # 最大悔棋步数
            "ai_think_time": 5,  # AI 思考时间（秒）
        },
        # 训练设置
        "training": {
            "learning_rate": 0.001,
            "batch_size": 256,
            "num_epochs": 100,
            "mcts_simulations": 800,  # MCTS 模拟次数
            "self_play_games": 100,  # 自我对弈局数
            "temperature": 1.0,  # 温度参数
            "c_puct": 1.41,  # PUCT 探索常数
        },
        # API 设置
        "api": {
            "provider": "deepseek",  # deepseek, openai, anthropic
            "deepseek": {
                "api_key": "",
                "model": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": 1000,
                "timeout": 60,
            },
            "openai": {
                "api_key": "",
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 1000,
                "timeout": 60,
            },
        },
        # UI 设置
        "ui": {
            "theme": "light",  # light, dark
            "window_width": 1200,
            "window_height": 800,
            "min_width": 800,
            "min_height": 600,
        },
        # 提示词模板
        "prompt_template": """你是一位世界级的五子棋大师，拥有极高的棋艺和战略眼光。

游戏规则：
- 棋盘大小：15×15，行和列都从1开始计数，左上角为(1,1)
- 黑方先行，双方轮流落子
- 先在横、竖、斜任意方向连成五子者获胜

当前棋盘状态：
{ascii_board}

你是{color}方，现在轮到你落子。

请严格按照以下格式回答：
1. 局势分析：简要分析当前双方的优劣势和关键要点
2. 最佳落子：第X行第Y列
3. 落子理由：解释为什么选择这个位置，以及后续的战略意图"""
    }

    def __init__(self):
        """初始化配置"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_file = self.PROJECT_ROOT / "config.json"
        self._ensure_directories()
        self.load()

    def _ensure_directories(self):
        """确保必要的目录存在"""
        for dir_path in [self.DATA_DIR, self.MODELS_DIR, self.GAMES_DIR, self.TRAINING_DATA_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def load(self):
        """从文件加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self._merge_config(loaded)
            except Exception as e:
                print(f"加载配置文件失败: {e}")

    def _merge_config(self, loaded):
        """合并加载的配置到默认配置"""
        for section, values in loaded.items():
            if section in self.config:
                if isinstance(values, dict):
                    self.config[section].update(values)
                else:
                    self.config[section] = values
            else:
                self.config[section] = values

    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def get(self, *keys, default=None):
        """获取配置值，支持嵌套键访问"""
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value

    def set(self, value, *keys):
        """设置配置值，支持嵌套键访问"""
        if len(keys) == 0:
            return
        target = self.config
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value
        self.save()

    @property
    def game(self):
        """获取游戏配置"""
        return self.config.get("game", {})

    @property
    def training(self):
        """获取训练配置"""
        return self.config.get("training", {})

    @property
    def api(self):
        """获取 API 配置"""
        return self.config.get("api", {})

    @property
    def ui(self):
        """获取 UI 配置"""
        return self.config.get("ui", {})

    @property
    def prompt_template(self):
        """获取提示词模板"""
        return self.config.get("prompt_template", self.DEFAULT_CONFIG["prompt_template"])


# 全局配置实例
_config = None


def get_config():
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config()
    return _config
