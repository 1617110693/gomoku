"""
游戏对战标签页模块
包含棋盘、对战控制面板、模式选择等功能
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QGroupBox, QComboBox, QTextEdit,
                              QMessageBox, QSpinBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont

from game.board import Board
from game.human_player import HumanPlayer
from game.local_ai_player import LocalAIPlayer
from game.external_ai_player import ExternalAIPlayer
from ui.board_widget import BoardWidget
from config import get_config
from utils import format_time


class GameWidget(QWidget):
    """
    游戏对战标签页

    信号:
        gameOver: 游戏结束信号 (winner)
        moveMade: 落子信号 (row, col, player)
    """

    gameOver = pyqtSignal(int)
    moveMade = pyqtSignal(int, int, int)

    # 对战模式
    MODE_HUMAN_VS_AI = "human_vs_ai"
    MODE_HUMAN_VS_API = "human_vs_api"
    MODE_AI_VS_API = "ai_vs_api"
    MODE_AI_VS_AI = "ai_vs_ai"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()

        # 游戏状态
        self.board = None
        self.board_size = 15
        self.game_mode = self.MODE_HUMAN_VS_AI
        self.is_playing = False
        self.is_paused = False

        # 玩家
        self.player_black = None
        self.player_white = None

        # 计时器
        self.timer = QTimer()
        self.elapsed_time = 0
        self.current_player = 1  # 黑方先行

        # 悔棋相关
        self.undo_count = 0
        self.max_undo = 3
        self.last_last_move = None  # 上上次落子位置

        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        main_layout = QHBoxLayout(self)

        # 左侧：棋盘
        left_panel = QVBoxLayout()

        self.board_widget = BoardWidget(board_size=self.board_size)
        self.board_widget.cellClicked.connect(self.on_cell_clicked)
        left_panel.addWidget(self.board_widget, 1)

        # 游戏信息
        info_layout = QHBoxLayout()
        self.info_label = QLabel("准备开始")
        self.info_label.setFont(QFont("Microsoft YaHei", 10))
        info_layout.addWidget(self.info_label)

        self.timer_label = QLabel("00:00")
        self.timer_label.setFont(QFont("Microsoft YaHei", 10))
        info_layout.addWidget(self.timer_label)

        left_panel.addLayout(info_layout)

        # 控制按钮
        btn_layout = QHBoxLayout()
        self.btn_undo = QPushButton("悔棋")
        self.btn_undo.clicked.connect(self.on_undo_clicked)
        self.btn_undo.setEnabled(False)
        btn_layout.addWidget(self.btn_undo)

        self.btn_restart = QPushButton("重新开始")
        self.btn_restart.clicked.connect(self.on_restart_clicked)
        btn_layout.addWidget(self.btn_restart)

        self.btn_save = QPushButton("保存对局")
        self.btn_save.clicked.connect(self.on_save_clicked)
        btn_layout.addWidget(self.btn_save)

        self.btn_load = QPushButton("加载对局")
        self.btn_load.clicked.connect(self.on_load_clicked)
        btn_layout.addWidget(self.btn_load)

        left_panel.addLayout(btn_layout)

        main_layout.addLayout(left_panel, 1)

        # 右侧：设置面板
        right_panel = QVBoxLayout()

        # 对战模式选择
        mode_group = QGroupBox("对战模式")
        mode_layout = QVBoxLayout()

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("人类 vs 本地AI", self.MODE_HUMAN_VS_AI)
        self.mode_combo.addItem("人类 vs 外部API", self.MODE_HUMAN_VS_API)
        self.mode_combo.addItem("本地AI vs 外部API", self.MODE_AI_VS_API)
        self.mode_combo.addItem("本地AI vs 本地AI", self.MODE_AI_VS_AI)
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)

        mode_group.setLayout(mode_layout)
        right_panel.addWidget(mode_group)

        # 棋盘设置
        board_group = QGroupBox("棋盘设置")
        board_layout = QVBoxLayout()

        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("棋盘大小:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(9, 19)
        self.size_spin.setValue(15)
        self.size_spin.valueChanged.connect(self.on_size_changed)
        size_layout.addWidget(self.size_spin)
        size_layout.addStretch()
        board_layout.addLayout(size_layout)

        board_group.setLayout(board_layout)
        right_panel.addWidget(board_group)

        # AI 设置
        ai_group = QGroupBox("AI 设置")
        ai_layout = QVBoxLayout()

        ai_level_layout = QHBoxLayout()
        ai_level_layout.addWidget(QLabel("AI 难度:"))
        self.ai_level_combo = QComboBox()
        self.ai_level_combo.addItem("简单 (200次模拟)", 200)
        self.ai_level_combo.addItem("中等 (400次模拟)", 400)
        self.ai_level_combo.addItem("困难 (800次模拟)", 800)
        self.ai_level_combo.currentIndexChanged.connect(self.on_ai_level_changed)
        ai_level_layout.addWidget(self.ai_level_combo)
        ai_level_layout.addStretch()
        ai_layout.addLayout(ai_level_layout)

        ai_group.setLayout(ai_layout)
        right_panel.addWidget(ai_group)

        # 开始按钮
        self.btn_start = QPushButton("开始游戏")
        self.btn_start.clicked.connect(self.on_start_clicked)
        right_panel.addWidget(self.btn_start)

        right_panel.addStretch()

        # AI 响应显示
        response_group = QGroupBox("AI 分析")
        response_layout = QVBoxLayout()
        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)
        self.response_text.setMaximumHeight(150)
        response_layout.addWidget(self.response_text)
        response_group.setLayout(response_layout)
        right_panel.addWidget(response_group)

        main_layout.addLayout(right_panel)

        # 初始化计时器
        self.timer.timeout.connect(self.update_timer)

    def on_cell_clicked(self, row: int, col: int):
        """处理棋盘点击"""
        if not self.is_playing or self.is_paused:
            return

        # 检查是否是人类的回合
        if self.current_player == 1 and isinstance(self.player_black, HumanPlayer):
            self.try_place_stone(row, col)
        elif self.current_player == 2 and isinstance(self.player_white, HumanPlayer):
            self.try_place_stone(row, col)

    def try_place_stone(self, row: int, col: int):
        """尝试落子"""
        if self.board.is_valid_move(row, col):
            # 更新上上次落子
            if self.board.last_move:
                self.last_last_move = self.board.last_move
            self.board.place_stone(row, col, self.current_player)
            self.board_widget.place_stone(row, col, self.current_player)
            self.moveMade.emit(row, col, self.current_player)

            # 检查胜负
            winner = self.board.check_winner()
            if winner != 0:
                self.end_game(winner)
            elif self.board.is_full():
                self.end_game(0)  # 平局
            else:
                self.switch_player()

    def switch_player(self):
        """切换玩家"""
        self.current_player = 3 - self.current_player
        self.undo_count = 0
        self.update_info()

        # 如果是 AI 回合，启动 AI 思考
        QTimer.singleShot(100, self.ai_turn)

    def ai_turn(self):
        """AI 回合"""
        if not self.is_playing or self.is_paused:
            return

        player = self.player_black if self.current_player == 1 else self.player_white

        if isinstance(player, (LocalAIPlayer, ExternalAIPlayer)):
            self.info_label.setText(f"{player.name} 思考中...")

            # 在后台获取落子
            move = player.get_move(self.board)

            if move and self.board.is_valid_move(move[0], move[1]):
                # 更新上上次落子
                if self.board.last_move:
                    self.last_last_move = self.board.last_move
                self.board.place_stone(move[0], move[1], self.current_player)
                self.board_widget.place_stone(move[0], move[1], self.current_player)
                self.moveMade.emit(move[0], move[1], self.current_player)

                # 显示 AI 分析
                if hasattr(player, 'last_response') and player.last_response:
                    self.response_text.append(f"【{player.name}】\n{player.last_response[:200]}...")

                # 检查胜负
                winner = self.board.check_winner()
                if winner != 0:
                    self.end_game(winner)
                elif self.board.is_full():
                    self.end_game(0)
                else:
                    self.switch_player()
            else:
                # API 调用失败，显示错误信息
                error_msg = "API 调用失败，无法获取落子"
                if hasattr(player, 'last_response') and player.last_response:
                    error_msg = f"API 错误: {player.last_response[:100]}..."
                self.response_text.append(f"【{player.name}】{error_msg}")
                self.info_label.setText(f"{player.name} 获取落子失败")

                # 显示消息框让用户选择
                reply = QMessageBox.question(
                    self, "API 调用失败",
                    f"{player.name} 无法获取落子（API 密钥可能无效或网络错误）。\n\n"
                    f"请选择操作：\n"
                    f"是 - 重新尝试\n"
                    f"否 - 认输并结束游戏\n"
                    f"取消 - 继续（跳过此回合）",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )

                if reply == QMessageBox.StandardButton.Yes:
                    # 重试
                    QTimer.singleShot(100, self.ai_turn)
                elif reply == QMessageBox.StandardButton.No:
                    # 认输
                    self.end_game(3 - self.current_player)
                # 取消则继续游戏（允许人类落子或其他 AI 继续）

    def start_game(self):
        """开始游戏"""
        self._init_game()

    def _init_game(self):
        """初始化游戏"""
        # 重置棋盘
        self.board = Board(self.board_size)
        self.board_widget.clear()
        self.board_widget.set_board_size(self.board_size)

        # 重置状态
        self.is_playing = True
        self.is_paused = False
        self.current_player = 1
        self.elapsed_time = 0
        self.undo_count = 0
        self.last_last_move = None

        # 初始化玩家
        ai_level = self.ai_level_combo.currentData()

        if self.game_mode == self.MODE_HUMAN_VS_AI:
            self.player_black = HumanPlayer("人类", 1)
            self.player_white = LocalAIPlayer("本地AI", 2,
                                               board_size=self.board_size,
                                               num_simulations=ai_level)
        elif self.game_mode == self.MODE_HUMAN_VS_API:
            self.player_black = HumanPlayer("人类", 1)
            api_config = self.config.api.get("deepseek", {})
            self.player_white = ExternalAIPlayer("DeepSeek", 2,
                                                  api_key=api_config.get("api_key", ""),
                                                  model=api_config.get("model", "deepseek-chat"),
                                                  prompt_template=self.config.prompt_template)
        elif self.game_mode == self.MODE_AI_VS_API:
            api_config = self.config.api.get("deepseek", {})
            self.player_black = LocalAIPlayer("本地AI", 1,
                                               board_size=self.board_size,
                                               num_simulations=ai_level)
            self.player_white = ExternalAIPlayer("DeepSeek", 2,
                                                  api_key=api_config.get("api_key", ""),
                                                  model=api_config.get("model", "deepseek-chat"),
                                                  prompt_template=self.config.prompt_template)
        elif self.game_mode == self.MODE_AI_VS_AI:
            self.player_black = LocalAIPlayer("本地AI-1", 1,
                                               board_size=self.board_size,
                                               num_simulations=ai_level)
            self.player_white = LocalAIPlayer("本地AI-2", 2,
                                               board_size=self.board_size,
                                               num_simulations=ai_level)

        # 启动计时器
        self.timer.start(1000)

        # 更新 UI
        self.btn_start.setText("暂停")
        self.btn_undo.setEnabled(True)
        self.update_info()

        # 如果 AI 先手
        if isinstance(self.player_black, (LocalAIPlayer, ExternalAIPlayer)):
            QTimer.singleShot(500, self.ai_turn)

    def end_game(self, winner: int):
        """结束游戏"""
        self.is_playing = False
        self.timer.stop()

        if winner == 0:
            self.info_label.setText("平局！")
            QMessageBox.information(self, "游戏结束", "平局！")
        elif winner == 1:
            winner_name = self.player_black.name
            self.info_label.setText(f"{winner_name} 获胜！")
            QMessageBox.information(self, "游戏结束", f"{winner_name} 获胜！")
        else:
            winner_name = self.player_white.name
            self.info_label.setText(f"{winner_name} 获胜！")
            QMessageBox.information(self, "游戏结束", f"{winner_name} 获胜！")

        self.btn_start.setText("开始游戏")
        self.btn_undo.setEnabled(False)
        self.gameOver.emit(winner)

    def on_start_clicked(self):
        """开始/暂停按钮点击"""
        if self.is_playing:
            if self.is_paused:
                # 继续游戏
                self.is_paused = False
                self.timer.start()
                self.btn_start.setText("暂停")
            else:
                # 暂停游戏
                self.is_paused = True
                self.timer.stop()
                self.btn_start.setText("继续")
        else:
            # 开始新游戏
            self._init_game()

    def on_restart_clicked(self):
        """重新开始按钮点击"""
        if self.is_playing:
            reply = QMessageBox.question(self, "确认重新开始",
                                         "确定要重新开始吗？当前对局将丢失。",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.timer.stop()
        self._init_game()

    def on_undo_clicked(self):
        """悔棋按钮点击"""
        if not self.is_playing or self.undo_count >= self.max_undo:
            return

        # 保存需要移除的棋子位置（最近两步）
        move_to_remove = []
        history_len = len(self.board.move_history)
        if history_len >= 1:
            move_to_remove.append(self.board.move_history[-1][:2])  # 最后一步
        if history_len >= 2:
            move_to_remove.append(self.board.move_history[-2][:2])  # 上一步

        if self.board.undo(1):
            # 移除棋盘上的棋子（从视觉上移除最近两步）
            for row, col in move_to_remove:
                self.board_widget.remove_stone(row, col)

            self.undo_count += 1
            self.current_player = 3 - self.current_player
            self.update_info()

    def on_save_clicked(self):
        """保存对局"""
        QMessageBox.information(self, "保存对局", "保存功能开发中...")

    def on_load_clicked(self):
        """加载对局"""
        QMessageBox.information(self, "加载对局", "加载功能开发中...")

    def on_mode_changed(self, index: int):
        """对战模式改变"""
        self.game_mode = self.mode_combo.currentData()

    def on_size_changed(self, value: int):
        """棋盘大小改变"""
        self.board_size = value

    def on_ai_level_changed(self, index: int):
        """AI 难度改变"""
        pass

    def update_info(self):
        """更新信息显示"""
        player_name = self.player_black.name if self.current_player == 1 else self.player_white.name
        color_str = "黑方" if self.current_player == 1 else "白方"
        self.info_label.setText(f"当前: {player_name} ({color_str}) | 步数: {len(self.board.move_history)}")

    def update_timer(self):
        """更新计时器"""
        self.elapsed_time += 1
        self.timer_label.setText(format_time(self.elapsed_time))

    def reset(self):
        """重置游戏"""
        self.timer.stop()
        self.is_playing = False
        self.is_paused = False
        self.board_widget.clear()
        self.info_label.setText("准备开始")
        self.timer_label.setText("00:00")
        self.btn_start.setText("开始游戏")
        self.btn_undo.setEnabled(False)
        self.response_text.clear()
