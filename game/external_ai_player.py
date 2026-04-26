"""
外部大模型 AI 玩家模块
"""
from typing import Optional, Tuple
from .player import Player
from api.deepseek_api import DeepSeekApi
from utils import Logger


class ExternalAIPlayer(Player):
    """
    外部大模型 AI 玩家

    通过 API 调用外部大模型（如 DeepSeek）进行落子
    """

    def __init__(self, name: str = "DeepSeek", color: int = 1,
                 api_key: str = "",
                 model: str = "deepseek-chat",
                 temperature: float = 0.7,
                 max_tokens: int = 1000,
                 timeout: int = 60,
                 prompt_template: str = None):
        """
        初始化外部 AI 玩家

        Args:
            name: 玩家名称
            color: 棋子颜色（1=黑, 2=白）
            api_key: API 密钥
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            timeout: 超时时间
            prompt_template: 提示词模板
        """
        super().__init__(name, color)
        self.logger = Logger(f"ExternalAI({name})")

        self.api = DeepSeekApi(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )

        self.prompt_template = prompt_template or self._default_prompt_template()
        self.last_response = ""
        self.last_move = None

    def _default_prompt_template(self) -> str:
        """默认提示词模板"""
        return """你是一位世界级的五子棋大师，拥有极高的棋艺和战略眼光。

游戏规则：
- 棋盘大小：15×15，行和列都从1开始计数，左上角为(1,1)
- 黑方先行，双方轮流落子
- 先在横、竖、斜任意方向连成五子者获胜

当前棋盘状态：
{ascii_board}

你是{color}方，现在轮到你落子。

请严格按照以下格式回答：
1. 局势分析：简要分析当前双方的优劣势和关键要点
2. 最佳落子：第X行第Y列
3. 落子理由：解释为什么选择这个位置"""

    def get_move(self, board) -> Optional[Tuple[int, int]]:
        """
        获取外部 AI 的落子

        Args:
            board: 当前棋盘

        Returns:
            Tuple[int, int] or None: 落子位置
        """
        if board.check_winner() != 0 or board.is_full():
            return None

        # 转换为 ASCII 棋盘
        ascii_board = board.to_ascii()
        color_str = "黑" if self.color == 1 else "白"

        # 调用 API 获取落子
        self.last_response = ""

        try:
            move, response = self.api.get_response_with_retry(
                ascii_board, color_str, self.prompt_template
            )
            self.last_response = response
            self.last_move = move

            if move is not None and board.is_valid_move(move[0], move[1]):
                return move

            # API 返回的落子无效
            self.logger.error(f"API 返回的落子无效: {move}")

        except Exception as e:
            self.logger.error(f"获取落子失败: {e}")
            self.last_response = f"错误: {e}"

        return None

    def set_prompt_template(self, template: str):
        """设置提示词模板"""
        self.prompt_template = template

    def update_api_config(self, api_key: str = None, model: str = None,
                          temperature: float = None, max_tokens: int = None,
                          timeout: int = None):
        """更新 API 配置"""
        if api_key is not None:
            self.api.api_key = api_key
        if model is not None:
            self.api.model = model
        if temperature is not None:
            self.api.temperature = temperature
        if max_tokens is not None:
            self.api.max_tokens = max_tokens
        if timeout is not None:
            self.api.timeout = timeout

    def validate_api_key(self) -> bool:
        """验证 API 密钥"""
        return self.api.validate_api_key()

    def reset(self):
        """重置状态"""
        self.last_response = ""
        self.last_move = None
