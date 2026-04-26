"""
通用工具函数模块
提供日志、验证、格式化等工具函数
"""
import time
import re
from datetime import datetime
from typing import Tuple, Optional, List


def format_time(seconds: int) -> str:
    """格式化时间（秒）为 MM:SS 格式"""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def format_timestamp(timestamp: float = None) -> str:
    """格式化时间戳为可读格式"""
    if timestamp is None:
        timestamp = time.time()
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_move(move_str: str) -> Optional[Tuple[int, int]]:
    """
    解析多种格式的落子字符串，返回 (row, col)（0索引）
    支持格式：
    - "第8行第5列" -> (7, 4)
    - "H5" -> (7, 4)  （列用字母表示）
    - "(8,5)" -> (7, 4)
    - "8,5" -> (7, 4)
    - "8 5" -> (7, 4)
    """
    move_str = move_str.strip()

    # 格式1: "第8行第5列" 或 "第8行 第5列"
    match = re.search(r'第\s*(\d+)\s*行\s*第?\s*(\d+)\s*列', move_str)
    if match:
        row, col = int(match.group(1)), int(match.group(2))
        if 1 <= row <= 15 and 1 <= col <= 15:
            return (row - 1, col - 1)

    # 格式2: "H5" 或 "h5"（字母列+数字行）
    match = re.match(r'^([A-Za-z])(\d+)$', move_str)
    if match:
        col_letter = match.group(1).upper()
        row = int(match.group(2))
        col = ord(col_letter) - ord('A')
        if 0 <= col <= 14 and 1 <= row <= 15:
            return (row - 1, col)

    # 格式3: "(8,5)" 或 "(8, 5)"
    match = re.match(r'\(\s*(\d+)\s*,\s*(\d+)\s*\)', move_str)
    if match:
        row, col = int(match.group(1)), int(match.group(2))
        if 1 <= row <= 15 and 1 <= col <= 15:
            return (row - 1, col - 1)

    # 格式4: "8,5" 或 "8 5"
    match = re.match(r'^(\d+)\s*[,\s]\s*(\d+)$', move_str)
    if match:
        row, col = int(match.group(1)), int(match.group(2))
        if 1 <= row <= 15 and 1 <= col <= 15:
            return (row - 1, col - 1)

    return None


def board_to_feature(board) -> List:
    """
    将棋盘转换为神经网络输入特征
    返回 4 个通道的 Feature Plane：
    - 通道0: 黑棋位置
    - 通道1: 白棋位置
    - 通道2: 当前玩家棋子（用于区分视角）
    - 通道3: 空白位置
    """
    size = board.size
    features = [
        [[0.0] * size for _ in range(size)],  # 黑棋
        [[0.0] * size for _ in range(size)],  # 白棋
        [[0.0] * size for _ in range(size)],  # 当前玩家
        [[0.0] * size for _ in range(size)],  # 空白
    ]

    for r in range(size):
        for c in range(size):
            piece = board.board[r][c]
            if piece == 1:  # 黑棋
                features[0][r][c] = 1.0
            elif piece == 2:  # 白棋
                features[1][r][c] = 1.0
            else:  # 空白
                features[3][r][c] = 1.0

    return features


def get_opponent(player: int) -> int:
    """获取对手玩家"""
    return 3 - player  # 1 -> 2, 2 -> 1


def format_game_record(move_history: List) -> str:
    """格式化对局记录为可读字符串"""
    lines = []
    for i, (row, col, player) in enumerate(move_history):
        player_name = "黑" if player == 1 else "白"
        lines.append(f"{i + 1}. {player_name}({chr(65 + col)}{row + 1})")
    return "\n".join(lines)


def validate_api_key(provider: str, api_key: str) -> bool:
    """验证 API 密钥格式"""
    if not api_key:
        return False

    if provider == "deepseek":
        # DeepSeek API 密钥格式: sk-xxx...
        return api_key.startswith("sk-") and len(api_key) > 10
    elif provider == "openai":
        # OpenAI API 密钥格式: sk-xxx...
        return api_key.startswith("sk-") and len(api_key) > 10
    elif provider == "anthropic":
        # Anthropic API 密钥格式: sk-ant-xxx...
        return api_key.startswith("sk-ant-") and len(api_key) > 10

    return False


class Logger:
    """简单的日志记录器"""

    def __init__(self, name: str = "Gomoku"):
        self.name = name

    def info(self, msg: str):
        print(f"[{self.name}] {format_timestamp()} - {msg}")

    def error(self, msg: str):
        print(f"[{self.name}] ERROR - {format_timestamp()} - {msg}")

    def debug(self, msg: str):
        print(f"[{self.name}] DEBUG - {format_timestamp()} - {msg}")
