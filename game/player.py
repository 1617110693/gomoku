"""
玩家抽象基类模块
定义所有玩家类型的接口
"""
from abc import ABC, abstractmethod
from typing import Tuple, Optional


class Player(ABC):
    """
    玩家抽象基类

    所有玩家类型（人类、本地AI、外部AI）都应该继承此类
    """

    def __init__(self, name: str, color: int):
        """
        初始化玩家

        Args:
            name: 玩家名称
            color: 棋子颜色（1=黑, 2=白）
        """
        self.name = name
        self.color = color

    @abstractmethod
    def get_move(self, board) -> Optional[Tuple[int, int]]:
        """
        获取下一步落子位置

        Args:
            board: 当前棋盘状态

        Returns:
            Tuple[int, int] or None: 落子位置 (row, col)，如果放弃落子则返回None
        """
        pass

    def reset(self):
        """重置玩家状态（用于新游戏）"""
        pass
