"""
本地 AI 玩家模块
使用神经网络 + MCTS 进行落子
"""
import torch
import numpy as np
from typing import Optional, Tuple
from .player import Player
from ai.model import create_model, get_optimal_move
from ai.mcts import MCTS


class LocalAIPlayer(Player):
    """
    本地训练 AI 玩家

    使用神经网络模型和 MCTS 进行决策
    """

    def __init__(self, name: str = "本地AI", color: int = 1,
                 model_path: str = None,
                 board_size: int = 15,
                 device: str = "cpu",
                 num_simulations: int = 400,
                 temperature: float = 1.0):
        """
        初始化本地 AI 玩家

        Args:
            name: 玩家名称
            color: 棋子颜色（1=黑, 2=白）
            model_path: 模型权重文件路径
            board_size: 棋盘大小
            device: 运行设备（"cpu" 或 "cuda"）
            num_simulations: MCTS 模拟次数
            temperature: 温度参数
        """
        super().__init__(name, color)
        self.board_size = board_size
        self.device = device
        self.num_simulations = num_simulations
        self.temperature = temperature

        # 创建模型
        self.model = create_model(board_size, model_type="small", device=device)

        # 如果有预训练权重则加载
        if model_path:
            try:
                self.model.load(model_path)
            except Exception as e:
                print(f"加载模型失败: {e}")

        # 创建 MCTS
        self.mcts = MCTS(
            model=self.model,
            board_size=board_size,
            num_simulations=num_simulations
        )

        self.last_policy = None

    def get_move(self, board) -> Optional[Tuple[int, int]]:
        """
        获取 AI 落子

        Args:
            board: 当前棋盘

        Returns:
            Tuple[int, int] or None: 落子位置
        """
        if board.check_winner() != 0 or board.is_full():
            return None

        # 执行 MCTS 搜索
        policy, move = self.mcts.search(
            board,
            temperature=self.temperature,
            self_play=True
        )

        self.last_policy = policy

        if move and board.is_valid_move(move[0], move[1]):
            return move

        # 如果 MCTS 返回的位置无效，选择概率最高的有效位置
        valid_moves = board.get_valid_moves()
        if valid_moves:
            best_move = valid_moves[0]
            best_prob = 0
            for mv in valid_moves:
                idx = mv[0] * self.board_size + mv[1]
                if policy[idx] > best_prob:
                    best_prob = policy[idx]
                    best_move = mv
            return best_move

        return None

    def get_policy(self, board) -> np.ndarray:
        """
        获取当前策略（用于训练分析）

        Args:
            board: 棋盘

        Returns:
            策略概率数组
        """
        return self.mcts.get_policy(board, temperature=0.01)

    def set_model_path(self, model_path: str):
        """加载新的模型"""
        try:
            self.model.load(model_path)
        except Exception as e:
            print(f"加载模型失败: {e}")

    def update_config(self, num_simulations: int = None, temperature: float = None):
        """更新配置"""
        if num_simulations is not None:
            self.num_simulations = num_simulations
            self.mcts.num_simulations = num_simulations
        if temperature is not None:
            self.temperature = temperature

    def reset(self):
        """重置状态"""
        self.last_policy = None
