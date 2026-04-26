"""
训练器模块
实现三种训练模式：自我博弈、外部对战、混合训练
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import numpy as np
from typing import List, Dict, Tuple, Optional
import time
import copy

from game.board import Board
from game.local_ai_player import LocalAIPlayer
from ai.model import GomokuNet, SmallGomokuNet, create_model
from ai.mcts import MCTS
from ai.data_utils import GomokuDataset, GameRecorder, board_to_features


class Trainer:
    """
    五子棋 AI 训练器

    支持三种训练模式：
    1. 自我博弈训练（纯 AlphaZero 风格）
    2. 外部模型对战训练
    3. 混合训练
    """

    def __init__(self, model: Optional[nn.Module] = None,
                 board_size: int = 15,
                 device: str = "cpu",
                 learning_rate: float = 0.001,
                 batch_size: int = 256):
        """
        初始化训练器

        Args:
            model: 神经网络模型（如果为None则创建新模型）
            board_size: 棋盘大小
            device: 运行设备
            learning_rate: 学习率
            batch_size: 批次大小
        """
        self.board_size = board_size
        self.device = device
        self.batch_size = batch_size

        # 创建或使用模型
        if model is None:
            self.model = create_model(board_size, model_type="small", device=device)
        else:
            self.model = model.to(device)

        # 优化器
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)

        # 数据集
        self.dataset = GomokuDataset()
        self.game_recorder = GameRecorder(board_size)

        # 训练统计
        self.epoch = 0
        self.best_win_rate = 0.0
        self.loss_history = []
        self.win_rate_history = []

        # MCTS
        self.mcts = MCTS(model=self.model, board_size=board_size)

        # 训练状态
        self.is_training = False
        self.should_stop = False

    def self_play(self, num_games: int = 100,
                  temperature: float = 1.0,
                  callback=None) -> Dict:
        """
        自我博弈生成训练数据

        Args:
            num_games: 生成对局数量
            temperature: 温度参数
            callback: 进度回调函数

        Returns:
            训练统计信息
        """
        games_completed = 0
        total_moves = 0
        start_time = time.time()

        for game_idx in range(num_games):
            if self.should_stop:
                break

            game_data = self._self_play_game(temperature)

            # 添加到数据集
            for sample in game_data:
                self.dataset.add_sample(
                    sample['board'],
                    sample['policy'],
                    sample['value']
                )

            games_completed += 1
            total_moves += len(game_data)

            if callback:
                progress = (game_idx + 1) / num_games
                elapsed = time.time() - start_time
                callback(progress, games_completed, total_moves, elapsed)

        return {
            'games_completed': games_completed,
            'total_moves': total_moves,
            'elapsed_time': time.time() - start_time,
            'dataset_size': len(self.dataset)
        }

    def _self_play_game(self, temperature: float = 1.0) -> List[Dict]:
        """
        自我博弈一局

        Args:
            temperature: 温度参数

        Returns:
            训练数据列表
        """
        board = Board(self.board_size)
        game_samples = []
        move_count = 0

        while board.check_winner() == 0 and not board.is_full():
            # 获取当前玩家
            current_player = board.get_current_player()

            # 获取棋盘特征
            board_features = board_to_features(board, current_player)

            # MCTS 搜索
            policy, move = self.mcts.search(board, temperature=temperature, self_play=True)

            if move is None:
                break

            # 记录
            game_samples.append({
                'board': board_features.tolist(),
                'policy': policy.tolist(),
                'value': 0  # 稍后填充
            })

            # 落子
            board.place_stone(move[0], move[1], current_player)
            move_count += 1

        # 确定胜负
        winner = board.check_winner()

        # 回填价值
        for sample in game_samples:
            # 价值基于最终结果
            # 注意：这里的逻辑与具体实现有关
            if winner == 0:
                sample['value'] = 0
            else:
                # 简单处理：所有样本都是0价值（等后续实现更复杂的价值评估）
                sample['value'] = 0

        return game_samples

    def train_step(self, batch_size: int = None) -> Dict:
        """
        执行一步训练

        Args:
            batch_size: 批次大小

        Returns:
            训练损失
        """
        if len(self.dataset) == 0:
            return {'loss': 0, 'policy_loss': 0, 'value_loss': 0}

        if batch_size is None:
            batch_size = self.batch_size

        # 创建数据加载器
        dataloader = DataLoader(self.dataset, batch_size=batch_size, shuffle=True)

        self.model.train()
        total_loss = 0
        total_policy_loss = 0
        total_value_loss = 0
        num_batches = 0

        for batch in dataloader:
            boards, policies, values = batch
            boards = boards.to(self.device)
            policies = policies.to(self.device)
            values = values.to(self.device)

            # 前向传播
            self.optimizer.zero_grad()
            policy_pred, value_pred = self.model(boards)

            # 计算损失
            policy_loss = -torch.sum(policies * torch.log(policy_pred + 1e-8)) / batch_size
            value_loss = torch.mean((value_pred - values) ** 2)
            loss = policy_loss + value_loss

            # 反向传播
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()
            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()
            num_batches += 1

        self.epoch += 1

        avg_loss = total_loss / num_batches if num_batches > 0 else 0
        avg_policy_loss = total_policy_loss / num_batches if num_batches > 0 else 0
        avg_value_loss = total_value_loss / num_batches if num_batches > 0 else 0

        self.loss_history.append(avg_loss)

        return {
            'loss': avg_loss,
            'policy_loss': avg_policy_loss,
            'value_loss': avg_value_loss
        }

    def train(self, num_epochs: int, callback=None) -> Dict:
        """
        执行训练

        Args:
            num_epochs: 训练轮数
            callback: 回调函数 (epoch, loss, progress)

        Returns:
            训练结果
        """
        self.is_training = True
        self.should_stop = False

        start_time = time.time()

        for epoch in range(num_epochs):
            if self.should_stop:
                break

            # 训练一步
            result = self.train_step()

            if callback:
                progress = (epoch + 1) / num_epochs
                callback(epoch + 1, result['loss'], progress)

        self.is_training = False

        return {
            'epochs_completed': epoch + 1,
            'elapsed_time': time.time() - start_time,
            'final_loss': result['loss']
        }

    def stop(self):
        """停止训练"""
        self.should_stop = True

    def save_model(self, path: str):
        """保存模型"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epoch': self.epoch,
            'best_win_rate': self.best_win_rate,
            'loss_history': self.loss_history
        }, path)

    def load_model(self, path: str):
        """加载模型"""
        checkpoint = torch.load(path, weights_only=False)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epoch = checkpoint.get('epoch', 0)
        self.best_win_rate = checkpoint.get('best_win_rate', 0.0)
        self.loss_history = checkpoint.get('loss_history', [])

    def evaluate(self, num_games: int = 20, opponent=None) -> Dict:
        """
        评估模型

        Args:
            num_games: 评估对局数
            opponent: 对手（如果为None则使用随机策略）

        Returns:
            评估结果
        """
        wins = 0
        losses = 0
        draws = 0

        for _ in range(num_games):
            board = Board(self.board_size)

            while board.check_winner() == 0 and not board.is_full():
                current_player = board.get_current_player()

                if current_player == 1:
                    # 使用当前模型
                    policy, move = self.mcts.search(board, temperature=0.0, self_play=False)
                else:
                    # 对手：随机落子
                    valid_moves = board.get_valid_moves()
                    if valid_moves:
                        move = valid_moves[np.random.randint(len(valid_moves))]
                    else:
                        move = None

                if move is None:
                    break

                board.place_stone(move[0], move[1], current_player)

            winner = board.check_winner()
            if winner == 1:
                wins += 1
            elif winner == 2:
                losses += 1
            else:
                draws += 1

        win_rate = wins / num_games

        return {
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'win_rate': win_rate
        }

    def get_statistics(self) -> Dict:
        """获取训练统计信息"""
        return {
            'epoch': self.epoch,
            'dataset_size': len(self.dataset),
            'best_win_rate': self.best_win_rate,
            'loss_history': self.loss_history[-100:],
            'is_training': self.is_training
        }
