"""
蒙特卡洛树搜索（MCTS）模块
实现 AlphaZero 风格的 MCTS 算法
"""
import numpy as np
import torch
import math
from typing import Dict, Tuple, List, Optional


class MCTSNode:
    """
    MCTS 树节点

    属性:
        board: 棋盘状态
        parent: 父节点
        move: 到达此节点的落子
        prior: 先验概率
        visit_count: 访问次数
        value_sum: 价值累积和
        children: 子节点字典 {move: node}
    """

    def __init__(self, board, parent=None, move=None, prior: float = 0.0):
        self.board = board.copy()
        self.parent = parent
        self.move = move
        self.prior = prior
        self.visit_count = 0
        self.value_sum = 0.0
        self.children = {}  # {move: MCTSNode}

    def is_expanded(self) -> bool:
        """检查是否已展开"""
        return len(self.children) > 0

    def get_value(self) -> float:
        """获取节点价值（平均价值）"""
        if self.visit_count == 0:
            return 0.0
        return self.value_sum / self.visit_count

    def expand(self, policy_probs: np.ndarray):
        """
        展开子节点

        Args:
            policy_probs: 策略概率数组，形状 (board_size * board_size,)
        """
        board_size = self.board.size
        for i in range(board_size * board_size):
            row, col = i // board_size, i % board_size
            if self.board.is_valid_move(row, col):
                # 计算此移动的先验概率
                prior = policy_probs[i]
                if prior > 0:  # 只添加有概率的节点
                    move = (row, col)
                    new_board = self.board.copy()
                    current_player = self.board.get_current_player()
                    new_board.place_stone(row, col, current_player)
                    self.children[move] = MCTSNode(
                        board=new_board,
                        parent=self,
                        move=move,
                        prior=prior
                    )

    def backpropagate(self, value: float):
        """
        反向传播更新值

        Args:
            value: 模拟结果值
        """
        self.visit_count += 1
        self.value_sum += value

        if self.parent is not None:
            # 价值需要取反（因为切换了玩家视角）
            self.parent.backpropagate(-value)


class MCTS:
    """
    蒙特卡洛树搜索

    实现 AlphaZero 风格的 MCTS：
    - PUCT 选择策略
    - 支持自对弈训练
    - 支持推理模式
    """

    def __init__(self, model, board_size: int = 15, c_puct: float = 1.41,
                 virtual_loss: float = 0.0, num_simulations: int = 800):
        """
        初始化 MCTS

        Args:
            model: 神经网络模型
            board_size: 棋盘大小
            c_puct: PUCT 探索常数
            virtual_loss: 虚拟损失（用于并行化）
            num_simulations: 模拟次数
        """
        self.model = model
        self.board_size = board_size
        self.c_puct = c_puct
        self.virtual_loss = virtual_loss
        self.num_simulations = num_simulations

    def search(self, board, temperature: float = 1.0, self_play: bool = True) -> Tuple[np.ndarray, int]:
        """
        执行 MCTS 搜索

        Args:
            board: 当前棋盘
            temperature: 温度参数
            self_play: 是否为自对弈模式

        Returns:
            policy: 改进后的策略概率
            root_move: 选择的落子（用于自对弈）
        """
        root = MCTSNode(board)

        # 神经网络预测根节点的策略和价值
        board_features = self._board_to_features(board)
        policy_probs, value = self.model.predict(board_features)

        # 展开根节点
        root.expand(policy_probs)
        root.visit_count = 1
        root.value_sum = value

        # 执行模拟
        for _ in range(self.num_simulations - 1):
            node = self._select_node(root)

            if node.board.check_winner() != 0 or node.board.is_full():
                # 游戏结束，反向传播最终价值
                winner = node.board.check_winner()
                if winner == 0:
                    value = 0  # 平局
                else:
                    # 判断当前节点的玩家是否获胜
                    current_player = node.board.get_current_player()
                    # 如果当前玩家是最后落子的那一位，那胜利属于对手
                    if len(node.board.move_history) > 0:
                        last_player = node.board.move_history[-1][2]
                        value = 1.0 if winner == last_player else -1.0
                    else:
                        value = 0
                node.backpropagate(value)
            else:
                # 神经网络评估
                board_features = self._board_to_features(node.board)
                policy_probs, value = self.model.predict(board_features)

                # 展开节点
                node.expand(policy_probs)
                node.backpropagate(value)

        # 获取改进后的策略
        policy = self._get_improved_policy(root)

        if self_play:
            # 自对弈模式：使用温度采样选择落子
            root_move = self._sample_move(root, policy, temperature)
        else:
            # 推理模式：选择访问次数最多的落子
            root_move = self._get_best_move(root)

        return policy, root_move

    def _select_node(self, node: MCTSNode) -> MCTSNode:
        """
        使用 PUCT 选择最优子节点

        Args:
            node: 当前节点

        Returns:
            选择的子节点
        """
        while node.is_expanded():
            best_score = -float('inf')
            best_child = None

            for move, child in node.children.items():
                score = self._uct_score(node, child)
                if score > best_score:
                    best_score = score
                    best_child = child

            node = best_child

            # 添加虚拟损失（用于并行化）
            if self.virtual_loss > 0:
                node.visit_count += self.virtual_loss
                node.value_sum -= self.virtual_loss

        return node

    def _uct_score(self, parent: MCTSNode, child: MCTSNode) -> float:
        """
        计算 UCT/PUCT 分数

        Args:
            parent: 父节点
            child: 子节点

        Returns:
            UCT 分数
        """
        exploit = child.get_value()  # 利用项
        explore = self.c_puct * child.prior * math.sqrt(parent.visit_count) / (1 + child.visit_count)
        return exploit + explore

    def _get_improved_policy(self, root: MCTSNode) -> np.ndarray:
        """
        获取改进后的策略（基于访问次数）

        Args:
            root: 根节点

        Returns:
            策略概率数组
        """
        policy = np.zeros(self.board_size * self.board_size)

        for move, child in root.children.items():
            idx = move[0] * self.board_size + move[1]
            policy[idx] = child.visit_count

        # 归一化
        total = policy.sum()
        if total > 0:
            policy /= total

        return policy

    def _sample_move(self, root: MCTSNode, policy: np.ndarray, temperature: float) -> Tuple[int, int]:
        """
        使用温度采样选择落子

        Args:
            root: 根节点
            policy: 策略概率
            temperature: 温度参数

        Returns:
            落子位置 (row, col)
        """
        if temperature == 0:
            # 直接选择概率最高的落子
            idx = policy.argmax()
        else:
            # 概率加权随机选择
            try:
                probs = policy ** (1 / temperature)
                probs /= probs.sum()
                idx = np.random.choice(len(policy), p=probs)
            except:
                idx = policy.argmax()

        row, col = idx // self.board_size, idx % self.board_size
        return (row, col)

    def _get_best_move(self, root: MCTSNode) -> Tuple[int, int]:
        """
        选择访问次数最多的落子

        Args:
            root: 根节点

        Returns:
            落子位置 (row, col)
        """
        max_visits = -1
        best_move = None

        for move, child in root.children.items():
            if child.visit_count > max_visits:
                max_visits = child.visit_count
                best_move = move

        return best_move

    def _board_to_features(self, board) -> List[List[List[float]]]:
        """
        将棋盘转换为神经网络输入特征

        Args:
            board: 棋盘对象

        Returns:
            特征数组，形状 (4, board_size, board_size)
        """
        size = board.size
        current_player = board.get_current_player()

        features = np.zeros((4, size, size), dtype=np.float32)

        for r in range(size):
            for c in range(size):
                piece = board.board[r][c]
                if piece == 1:  # 黑棋
                    features[0, r, c] = 1.0
                elif piece == 2:  # 白棋
                    features[1, r, c] = 1.0

        # 空白位置
        features[2, :, :] = (features[0, :, :] == 0) & (features[1, :, :] == 0)

        # 当前玩家（用于区分视角）
        if current_player == 1:
            features[3, :, :] = 1.0

        return features.tolist()

    def get_policy(self, board, temperature: float = 1.0) -> np.ndarray:
        """
        获取策略（仅用于推理，不实际选择落子）

        Args:
            board: 棋盘
            temperature: 温度参数

        Returns:
            策略概率
        """
        root = MCTSNode(board)

        # 神经网络预测
        board_features = self._board_to_features(board)
        policy_probs, _ = self.model.predict(board_features)
        root.expand(policy_probs)

        # 多次模拟
        for _ in range(self.num_simulations):
            node = self._select_node(root)
            if node.board.check_winner() != 0 or node.board.is_full():
                winner = node.board.check_winner()
                if winner == 0:
                    value = 0
                else:
                    if len(node.board.move_history) > 0:
                        last_player = node.board.move_history[-1][2]
                        value = 1.0 if winner == last_player else -1.0
                    else:
                        value = 0
                node.backpropagate(value)
            else:
                board_features = self._board_to_features(node.board)
                policy_probs, value = self.model.predict(board_features)
                node.expand(policy_probs)
                node.backpropagate(value)

        return self._get_improved_policy(root)
