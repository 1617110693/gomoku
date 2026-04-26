"""
神经网络模型模块
实现 AlphaZero 风格的网络架构：策略网络 + 价值网络
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class GomokuNet(nn.Module):
    """
    五子棋神经网络模型

    采用 AlphaZero 架构：
    - 卷积 backbone 提取棋盘特征
    - 策略头（policy head）预测每个位置的落子概率
    - 价值头（value head）预测当前局面的胜率
    """

    def __init__(self, board_size: int = 15, num_channels: int = 128, num_res_blocks: int = 10):
        """
        初始化网络

        Args:
            board_size: 棋盘大小，默认15
            num_channels: 卷积通道数，默认128
            num_res_blocks: 残差块数量，默认10
        """
        super().__init__()
        self.board_size = board_size
        self.num_channels = num_channels

        # 输入通道：4个特征平面（黑棋、白棋、当前玩家、空白）
        self.input_conv = nn.Conv2d(4, num_channels, kernel_size=3, padding=1)

        # 残差块
        self.res_blocks = nn.ModuleList([
            ResidualBlock(num_channels) for _ in range(num_res_blocks)
        ])

        # 策略头
        self.policy_conv = nn.Conv2d(num_channels, 2, kernel_size=1)
        self.policy_fc = nn.Linear(2 * board_size * board_size, board_size * board_size)

        # 价值头
        self.value_conv = nn.Conv2d(num_channels, 1, kernel_size=1)
        self.value_fc1 = nn.Linear(board_size * board_size, 256)
        self.value_fc2 = nn.Linear(256, 1)

        # 权重初始化
        self._init_weights()

    def _init_weights(self):
        """初始化网络权重"""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def forward(self, x):
        """
        前向传播

        Args:
            x: 输入张量，形状 (batch, 4, board_size, board_size)

        Returns:
            policy: 策略输出，形状 (batch, board_size * board_size)
            value: 价值输出，形状 (batch, 1)
        """
        # 输入卷积 + ReLU
        x = F.relu(self.input_conv(x))

        # 残差块
        for res_block in self.res_blocks:
            x = res_block(x)

        # 策略头
        policy = F.relu(self.policy_conv(x))
        policy = policy.view(policy.size(0), -1)
        policy = self.policy_fc(policy)
        policy = F.softmax(policy, dim=1)

        # 价值头
        value = F.relu(self.value_conv(x))
        value = value.view(value.size(0), -1)
        value = F.relu(self.value_fc1(value))
        value = torch.tanh(self.value_fc2(value))

        return policy, value

    def predict(self, board_state):
        """
        对单个棋盘状态进行预测

        Args:
            board_state: 棋盘状态，形状 (4, board_size, board_size)

        Returns:
            policy: 每个位置的落子概率
            value: 局面评估值
        """
        self.eval()
        with torch.no_grad():
            x = torch.FloatTensor(board_state).unsqueeze(0)
            policy, value = self(x)
            return policy.squeeze(0).numpy(), value.squeeze(0).item()

    def save(self, path: str):
        """保存模型"""
        torch.save(self.state_dict(), path)

    def load(self, path: str):
        """加载模型"""
        self.load_state_dict(torch.load(path, weights_only=True))


class ResidualBlock(nn.Module):
    """残差块"""

    def __init__(self, channels: int):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x):
        residual = x
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out = F.relu(out + residual)
        return out


class SmallGomokuNet(nn.Module):
    """
    小型网络（用于快速测试和预训练模型）

    使用更少的参数，适合在CPU上快速推理
    """

    def __init__(self, board_size: int = 15):
        super().__init__()
        self.board_size = board_size

        # 简化的卷积层
        self.conv1 = nn.Conv2d(4, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)

        # 策略头
        self.policy_conv = nn.Conv2d(128, 2, kernel_size=1)
        self.policy_fc = nn.Linear(2 * board_size * board_size, board_size * board_size)

        # 价值头
        self.value_conv = nn.Conv2d(128, 1, kernel_size=1)
        self.value_fc1 = nn.Linear(board_size * board_size, 64)
        self.value_fc2 = nn.Linear(64, 1)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))

        # 策略头
        policy = F.relu(self.policy_conv(x))
        policy = policy.view(policy.size(0), -1)
        policy = F.softmax(self.policy_fc(policy), dim=1)

        # 价值头
        value = F.relu(self.value_conv(x))
        value = value.view(value.size(0), -1)
        value = F.relu(self.value_fc1(value))
        value = torch.tanh(self.value_fc2(value))

        return policy, value

    def predict(self, board_state):
        """对单个棋盘状态进行预测"""
        self.eval()
        with torch.no_grad():
            x = torch.FloatTensor(board_state).unsqueeze(0)
            policy, value = self(x)
            return policy.squeeze(0).numpy(), value.squeeze(0).item()


def create_model(board_size: int = 15, model_type: str = "small", device: str = "cpu"):
    """
    创建模型实例

    Args:
        board_size: 棋盘大小
        model_type: 模型类型，"small" 或 "full"
        device: 设备，"cpu" 或 "cuda"

    Returns:
        模型实例
    """
    if model_type == "small":
        model = SmallGomokuNet(board_size)
    else:
        model = GomokuNet(board_size, num_channels=128, num_res_blocks=10)

    model = model.to(device)
    return model


def get_optimal_move(policy, temperature: float = 1.0):
    """
    根据策略概率采样落子

    Args:
        policy: 策略概率数组，形状 (board_size * board_size,)
        temperature: 温度参数，越大越随机

    Returns:
        落子位置的扁平索引
    """
    if temperature == 0:
        # 直接选择最高概率
        return policy.argmax()
    else:
        # 使用温度采样
        try:
            # 对数概率加噪声
            logits = torch.log(torch.FloatTensor(policy))
            noise = torch.randn_like(logits) * temperature
            probabilities = F.softmax((logits + noise), dim=0)
            return torch.multinomial(probabilities, 1).item()
        except:
            return policy.argmax()
