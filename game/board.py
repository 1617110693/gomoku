"""
棋盘类和游戏核心逻辑模块
负责五子棋棋盘的表示、落子、胜负判断等功能
"""
from typing import List, Tuple, Optional
import copy


class Board:
    """
    五子棋棋盘类

    属性:
        size: 棋盘大小（默认15×15）
        board: 二维列表，表示棋盘状态（0=空, 1=黑, 2=白）
        move_history: 落子历史记录 [(row, col, player), ...]
        last_move: 最后一个落子位置 (row, col)
    """

    # 方向向量：横、竖、左斜、右斜
    DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]

    def __init__(self, size: int = 15):
        """
        初始化棋盘

        Args:
            size: 棋盘大小，默认15
        """
        self.size = size
        self.board = [[0] * size for _ in range(size)]
        self.move_history = []
        self.last_move = None
        self._winner = 0  # 0=无胜负, 1=黑胜, 2=白胜

    def place_stone(self, row: int, col: int, player: int) -> bool:
        """
        在指定位置落子

        Args:
            row: 行索引（0~size-1）
            col: 列索引（0~size-1）
            player: 玩家（1=黑, 2=白）

        Returns:
            bool: 落子是否成功
        """
        if not self.is_valid_move(row, col):
            return False

        self.board[row][col] = player
        self.move_history.append((row, col, player))
        self.last_move = (row, col)

        # 检查胜负
        self._winner = self._check_winner_at(row, col, player)

        return True

    def is_valid_move(self, row: int, col: int) -> bool:
        """
        检查落子是否合法

        Args:
            row: 行索引
            col: 列索引

        Returns:
            bool: 是否可以落子
        """
        if row < 0 or row >= self.size or col < 0 or col >= self.size:
            return False
        return self.board[row][col] == 0

    def get_valid_moves(self) -> List[Tuple[int, int]]:
        """
        获取所有合法落子位置

        Returns:
            List[Tuple[int, int]]: 合法位置列表
        """
        moves = []
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == 0:
                    moves.append((r, c))
        return moves

    def _check_winner_at(self, row: int, col: int, player: int) -> int:
        """
        检查以指定位置为中心的五子连珠

        Args:
            row: 行索引
            col: 列索引
            player: 玩家

        Returns:
            int: 0=无胜负, 1=黑胜, 2=白胜
        """
        for dr, dc in self.DIRECTIONS:
            count = 1

            # 正方向
            r, c = row + dr, col + dc
            while 0 <= r < self.size and 0 <= c < self.size and self.board[r][c] == player:
                count += 1
                r += dr
                c += dc

            # 反方向
            r, c = row - dr, col - dc
            while 0 <= r < self.size and 0 <= c < self.size and self.board[r][c] == player:
                count += 1
                r -= dr
                c -= dc

            if count >= 5:
                return player

        return 0

    def check_winner(self) -> int:
        """
        检查当前棋盘胜负状态

        Returns:
            int: 0=无胜负, 1=黑胜, 2=白胜
        """
        if self._winner != 0:
            return self._winner

        # 遍历所有已落子位置检查
        for r in range(self.size):
            for c in range(self.size):
                player = self.board[r][c]
                if player != 0:
                    winner = self._check_winner_at(r, c, player)
                    if winner != 0:
                        self._winner = winner
                        return winner

        return 0

    def is_full(self) -> bool:
        """检查棋盘是否已满"""
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == 0:
                    return False
        return True

    def undo(self, steps: int = 1) -> bool:
        """
        悔棋

        Args:
            steps: 悔棋步数

        Returns:
            bool: 是否成功悔棋
        """
        if len(self.move_history) < steps:
            steps = len(self.move_history)

        for _ in range(steps):
            if self.move_history:
                row, col, _ = self.move_history.pop()
                self.board[row][col] = 0

        if self.move_history:
            self.last_move = (self.move_history[-1][0], self.move_history[-1][1])
        else:
            self.last_move = None

        self._winner = 0  # 重置胜负状态
        return True

    def copy(self) -> 'Board':
        """
        深拷贝棋盘

        Returns:
            Board: 新的棋盘对象
        """
        new_board = Board(self.size)
        new_board.board = [row[:] for row in self.board]
        new_board.move_history = self.move_history[:]
        new_board.last_move = self.last_move
        new_board._winner = self._winner
        return new_board

    def to_ascii(self) -> str:
        """
        将棋盘转换为 ASCII 艺术表示

        Returns:
            str: ASCII 格式的棋盘字符串
        """
        # 列标号
        header = "    " + " ".join(chr(65 + i) for i in range(self.size)) + "\n"
        header += "  +" + "-" * (self.size * 2 - 1) + "+\n"

        rows = []
        for i, row in enumerate(self.board):
            line = []
            for cell in row:
                if cell == 0:
                    line.append("·")
                elif cell == 1:
                    line.append("●")
                else:
                    line.append("○")
            rows.append(f"{i + 1:2d}| " + " ".join(line))

        return header + "\n".join(rows) + "\n  +" + "-" * (self.size * 2 - 1) + "+"

    def get_board_state(self) -> List[List[int]]:
        """获取棋盘状态副本"""
        return [row[:] for row in self.board]

    def get_current_player(self) -> int:
        """获取当前应该落子的玩家"""
        black_count = sum(1 for r, c, p in self.move_history if p == 1)
        white_count = sum(1 for r, c, p in self.move_history if p == 2)
        return 1 if black_count == white_count else 2

    def get_piece_count(self) -> Tuple[int, int]:
        """获取黑白双方已落子数量"""
        black = sum(1 for r, c, p in self.move_history if p == 1)
        white = sum(1 for r, c, p in self.move_history if p == 2)
        return black, white

    def reset(self):
        """重置棋盘"""
        self.board = [[0] * self.size for _ in range(self.size)]
        self.move_history = []
        self.last_move = None
        self._winner = 0
