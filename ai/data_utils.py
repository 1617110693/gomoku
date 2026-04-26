"""
数据处理和数据集模块
"""
import numpy as np
from typing import List, Tuple, Dict
import torch
from torch.utils.data import Dataset


class GomokuDataset(Dataset):
    """
    五子棋训练数据集

    每个样本包含：
    - board_state: 棋盘特征 (4, board_size, board_size)
    - policy: 策略标签 (board_size * board_size,)
    - value: 价值标签 (1,)
    """

    def __init__(self, data: List[Dict] = None):
        """
        初始化数据集

        Args:
            data: 训练数据列表
        """
        self.data = data or []

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Tuple:
        """
        获取单个样本

        Returns:
            (board_state, policy, value)
        """
        sample = self.data[idx]
        return (
            torch.FloatTensor(sample['board']),
            torch.FloatTensor(sample['policy']),
            torch.FloatTensor([sample['value']])
        )

    def add_sample(self, board, policy, value: float):
        """
        添加样本

        Args:
            board: 棋盘特征
            policy: 策略
            value: 价值
        """
        self.data.append({
            'board': board,
            'policy': policy,
            'value': value
        })

    def add_game(self, game_data: List[Dict]):
        """添加一局游戏的所有样本"""
        self.data.extend(game_data)

    def clear(self):
        """清空数据"""
        self.data = []

    def save(self, path: str):
        """保存数据集"""
        np.save(path, self.data)

    def load(self, path: str):
        """加载数据集"""
        self.data = np.load(path, allow_pickle=True).tolist()


class GameRecorder:
    """
    对局记录器

    用于在自我对弈或与外部模型对弈时记录数据
    """

    def __init__(self, board_size: int = 15):
        self.board_size = board_size
        self.moves = []  # [(board_state, move, player), ...]
        self.game_history = []  # [[move1, move2, ...], ...] for multiple games

    def record(self, board_state: List, move: Tuple[int, int], player: int):
        """记录一步"""
        self.moves.append({
            'board': board_state,
            'move': move,
            'player': player
        })

    def end_game(self, winner: int):
        """
        结束一局游戏并生成训练数据

        Args:
            winner: 胜者 (0=平局, 1=黑, 2=白)

        Returns:
            List[Dict]: 训练数据
        """
        training_data = []

        # 为每一步生成训练样本
        for i, move_record in enumerate(self.moves):
            board = move_record['board']
            move = move_record['move']
            player = move_record['player']

            # 创建策略标签（只有一个1，其他为0）
            policy = np.zeros(self.board_size * self.board_size)
            move_idx = move[0] * self.board_size + move[1]
            policy[move_idx] = 1.0

            # 计算价值（如果该玩家获胜则为1，否则为-1）
            if winner == 0:
                value = 0  # 平局
            elif winner == player:
                value = 1.0  # 玩家获胜
            else:
                value = -1.0  # 玩家失败

            training_data.append({
                'board': board,
                'policy': policy.tolist(),
                'value': value
            })

        # 保存游戏记录
        self.game_history.append({
            'moves': [(m['move'], m['player']) for m in self.moves],
            'winner': winner,
            'training_data': training_data
        })

        # 清空当前对局记录
        self.moves = []

        return training_data

    def get_recent_games(self, n: int = 10) -> List:
        """获取最近 n 局游戏"""
        return self.game_history[-n:]

    def clear(self):
        """清空所有记录"""
        self.moves = []
        self.game_history = []


def augment_data(board: np.ndarray, policy: np.ndarray) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    数据增强

    对棋盘进行旋转和镜像变换，生成更多训练样本

    Args:
        board: 棋盘特征 (4, size, size)
        policy: 策略 (size * size,)

    Returns:
        增强后的数据列表
    """
    augmented = []

    for k in range(4):  # 0°, 90°, 180°, 270°
        # 旋转棋盘
        rotated_board = np.rot90(board, k, axes=(1, 2)).copy()

        # 旋转策略
        rotated_policy = np.rot90(policy.reshape(board.shape[1], board.shape[2]), k)
        rotated_policy = rotated_policy.flatten()

        augmented.append((rotated_board, rotated_policy))

        # 镜像变换
        if k < 2:  # 只做一次镜像
            mirrored_board = np.flip(rotated_board, axis=2).copy()
            mirrored_policy = np.flip(rotated_policy.reshape(board.shape[1], board.shape[2]), axis=1)
            mirrored_policy = mirrored_policy.flatten()
            augmented.append((mirrored_board, mirrored_policy))

    return augmented


def board_to_features(board, current_player: int = 1) -> np.ndarray:
    """
    将棋盘转换为神经网络输入特征

    Args:
        board: 棋盘对象或二维数组
        current_player: 当前玩家 (1=黑, 2=白)

    Returns:
        特征数组 (4, size, size)
    """
    if hasattr(board, 'board'):
        size = board.size
        board_array = board.board
    else:
        size = len(board)
        board_array = board

    features = np.zeros((4, size, size), dtype=np.float32)

    for r in range(size):
        for c in range(size):
            piece = board_array[r][c]
            if piece == 1:
                features[0, r, c] = 1.0  # 黑棋
            elif piece == 2:
                features[1, r, c] = 1.0  # 白棋

    # 空白位置
    features[2, :, :] = (features[0] == 0) & (features[1] == 0)

    # 当前玩家
    if current_player == 1:
        features[3, :, :] = 1.0

    return features


def create_empty_dataset() -> GomokuDataset:
    """创建空数据集"""
    return GomokuDataset()
