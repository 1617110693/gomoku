"""
大模型 API 抽象基类模块
定义通用接口，其他 API 实现需继承此类
"""
from abc import ABC, abstractmethod
from typing import Tuple, Optional


class BaseLLMApi(ABC):
    """
    大模型 API 抽象基类

    所有外部大模型 API 都应继承此类并实现相应方法
    """

    def __init__(self, api_key: str, model: str = "gpt-4",
                 temperature: float = 0.7,
                 max_tokens: int = 1000,
                 timeout: int = 60):
        """
        初始化 API

        Args:
            api_key: API 密钥
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            timeout: 超时时间（秒）
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    @abstractmethod
    def get_move(self, ascii_board: str, color: str, prompt_template: str) -> str:
        """
        获取落子

        Args:
            ascii_board: ASCII 格式的棋盘
            color: 当前玩家颜色（"黑" 或 "白"）
            prompt_template: 提示词模板

        Returns:
            str: API 的原始响应
        """
        pass

    @abstractmethod
    def validate_api_key(self) -> bool:
        """
        验证 API 密钥是否有效

        Returns:
            bool: 是否有效
        """
        pass

    @abstractmethod
    def parse_move(self, response: str) -> Optional[Tuple[int, int]]:
        """
        解析 API 响应中的落子坐标

        Args:
            response: API 响应字符串

        Returns:
            Tuple[int, int] or None: (row, col)，解析失败返回 None
        """
        pass

    def format_prompt(self, ascii_board: str, color: str, prompt_template: str) -> str:
        """
        格式化提示词

        Args:
            ascii_board: ASCII 格式的棋盘
            color: 当前玩家颜色
            prompt_template: 提示词模板

        Returns:
            str: 格式化后的提示词
        """
        return prompt_template.format(ascii_board=ascii_board, color=color)
