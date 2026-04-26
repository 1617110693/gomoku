"""
DeepSeek API 实现模块
"""
import requests
import re
from typing import Tuple, Optional
from .base_api import BaseLLMApi
from utils import parse_move, Logger


class DeepSeekApi(BaseLLMApi):
    """
    DeepSeek API 实现

    支持 deepseek-chat、deepseek-coder 等模型
    """

    API_URL = "https://api.deepseek.com/chat/completions"

    def __init__(self, api_key: str, model: str = "deepseek-chat",
                 temperature: float = 0.7,
                 max_tokens: int = 1000,
                 timeout: int = 60):
        """
        初始化 DeepSeek API

        Args:
            api_key: DeepSeek API 密钥
            model: 模型名称，默认 deepseek-chat
            temperature: 温度参数
            max_tokens: 最大 token 数
            timeout: 超时时间（秒）
        """
        super().__init__(api_key, model, temperature, max_tokens, timeout)
        self.logger = Logger("DeepSeek API")

    def validate_api_key(self) -> bool:
        """验证 API 密钥"""
        if not self.api_key or not self.api_key.startswith("sk-"):
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 10
            }
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=data,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"API 验证失败: {e}")
            return False

    def get_move(self, ascii_board: str, color: str, prompt_template: str) -> str:
        """
        调用 DeepSeek API 获取落子

        Args:
            ascii_board: ASCII 格式的棋盘
            color: 当前玩家颜色
            prompt_template: 提示词模板

        Returns:
            str: API 响应内容
        """
        prompt = self.format_prompt(ascii_board, color, prompt_template)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        try:
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            elif response.status_code == 401:
                raise Exception("API 密钥无效")
            elif response.status_code == 429:
                raise Exception("请求过于频繁，请稍后重试")
            else:
                raise Exception(f"API 请求失败: {response.status_code}")

        except requests.exceptions.Timeout:
            raise Exception("API 请求超时")
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络错误: {e}")

    def parse_move(self, response: str) -> Optional[Tuple[int, int]]:
        """
        从 API 响应中解析落子坐标

        支持格式：
        - "第8行第5列"
        - "第8行 第5列"
        - "H5"
        - "(8,5)"
        - "8,5"

        Args:
            response: API 响应字符串

        Returns:
            Tuple[int, int] or None: (row, col)，使用 1-indexed
        """
        # 尝试多种方式解析
        # 1. 直接搜索 "第X行第Y列" 格式
        patterns = [
            r'第\s*(\d+)\s*行\s*第?\s*(\d+)\s*列',  # 第8行第5列
            r'\((\d+)\s*,\s*(\d+)\)',  # (8, 5)
            r'([A-Za-z])(\d+)',  # H5
        ]

        for pattern in patterns:
            match = re.search(pattern, response)
            if match:
                if pattern == r'([A-Za-z])(\d+)':
                    # 字母+数字格式
                    col_letter = match.group(1).upper()
                    row = int(match.group(2))
                    col = ord(col_letter) - ord('A')
                else:
                    row = int(match.group(1))
                    col = int(match.group(2))

                if 1 <= row <= 15 and 1 <= col <= 15:
                    return (row - 1, col - 1)  # 转换为 0-indexed

        # 2. 尝试直接在回复中搜索数字坐标
        # 查找类似 "8, 5" 或 "8 5" 的模式
        match = re.search(r'(\d+)\s*[,\s]\s*(\d+)', response)
        if match:
            row, col = int(match.group(1)), int(match.group(2))
            if 1 <= row <= 15 and 1 <= col <= 15:
                return (row - 1, col - 1)

        # 3. 查找中文字符"行"和"列"附近
        match = re.search(r'行.*?(\d+).*?列.*?(\d+)', response)
        if match:
            row, col = int(match.group(1)), int(match.group(2))
            if 1 <= row <= 15 and 1 <= col <= 15:
                return (row - 1, col - 1)

        return None

    def get_response_with_retry(self, ascii_board: str, color: str,
                                 prompt_template: str,
                                 max_retries: int = 3) -> Tuple[Optional[Tuple[int, int]], str]:
        """
        获取落子，带重试机制

        Args:
            ascii_board: ASCII 格式的棋盘
            color: 当前玩家颜色
            prompt_template: 提示词模板
            max_retries: 最大重试次数

        Returns:
            Tuple[落子位置, 响应内容]
        """
        last_response = ""

        for attempt in range(max_retries):
            try:
                response = self.get_move(ascii_board, color, prompt_template)
                last_response = response

                move = self.parse_move(response)
                if move is not None:
                    return move, response

                if attempt < max_retries - 1:
                    # 添加错误纠正提示
                    correction = "\n\n请注意，您的落子格式不明确。请明确说出落子位置，例如：第8行第5列。"
                    prompt_template = prompt_template + correction

            except Exception as e:
                self.logger.error(f"API 调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None, f"错误: {e}"

        return None, last_response
