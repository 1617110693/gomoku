"""
人类玩家模块
处理人类玩家的输入
"""
from typing import Tuple, Optional
from .player import Player


class HumanPlayer(Player):
    """
    人类玩家类

    等待人类在界面上点击落子位置
    """

    def __init__(self, name: str = "人类", color: int = 1):
        """
        初始化人类玩家

        Args:
            name: 玩家名称
            color: 棋子颜色（1=黑, 2=白）
        """
        super().__init__(name, color)
        self.pending_move = None

    def set_move(self, row: int, col: int):
        """
        设置待执行的落子（由GUI调用）

        Args:
            row: 行索引
            col: 列索引
        """
        self.pending_move = (row, col)

    def get_move(self, board) -> Optional[Tuple[int, int]]:
        """
        获取人类选择的落子位置

        Args:
            board: 当前棋盘状态（未使用）

        Returns:
            Tuple[int, int] or None: 落子位置
        """
        move = self.pending_move
        self.pending_move = None
        return move

    def reset(self):
        """重置玩家状态"""
        self.pending_move = None
