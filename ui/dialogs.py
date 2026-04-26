"""
对话框模块
包含各种应用程序对话框
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QTextEdit, QComboBox,
                              QFormLayout, QMessageBox, QSpinBox)
from PyQt6.QtCore import Qt


class AboutDialog(QDialog):
    """关于对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setFixedSize(400, 300)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 应用图标
        icon_label = QLabel("五子棋")
        icon_label.setStyleSheet("font-size: 48px; font-weight: bold;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # 版本信息
        version_label = QLabel("版本 1.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        # 描述
        desc_text = QTextEdit()
        desc_text.setReadOnly(True)
        desc_text.setPlainText(
            "五子棋 AI 训练平台\n\n"
            "一个支持本地 AI 训练和外部大模型对战的五子棋应用。\n\n"
            "功能特点：\n"
            "- 多种对战模式\n"
            "- AlphaZero 风格 AI 训练\n"
            "- DeepSeek API 集成\n"
            "- 训练数据可视化"
        )
        layout.addWidget(desc_text)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)


class GameReplayDialog(QDialog):
    """对局回放对话框"""

    def __init__(self, game_data: dict, parent=None):
        super().__init__(parent)
        self.game_data = game_data
        self.current_move = 0
        self.setWindowTitle("对局回放")
        self.setMinimumSize(600, 500)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 对局信息
        info_layout = QHBoxLayout()
        self.info_label = QLabel("黑方 vs 白方")
        info_layout.addWidget(self.info_label)
        self.move_label = QLabel("第 0 / 0 步")
        info_layout.addWidget(self.move_label)
        layout.addLayout(info_layout)

        # 控制按钮
        control_layout = QHBoxLayout()
        self.btn_first = QPushButton("|<")
        self.btn_first.clicked.connect(self.on_first)
        control_layout.addWidget(self.btn_first)

        self.btn_prev = QPushButton("<")
        self.btn_prev.clicked.connect(self.on_prev)
        control_layout.addWidget(self.btn_prev)

        self.btn_next = QPushButton(">")
        self.btn_next.clicked.connect(self.on_next)
        control_layout.addWidget(self.btn_next)

        self.btn_last = QPushButton(">|")
        self.btn_last.clicked.connect(self.on_last)
        control_layout.addWidget(self.btn_last)

        layout.addLayout(control_layout)

        # 回放文本
        self.replay_text = QTextEdit()
        self.replay_text.setReadOnly(True)
        layout.addWidget(self.replay_text)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self.update_display()

    def update_display(self):
        """更新显示"""
        moves = self.game_data.get('moves', [])
        self.move_label.setText(f"第 {self.current_move} / {len(moves)} 步")

        # 构建回放文本
        text = []
        for i, (move, player) in enumerate(moves[:self.current_move]):
            if i < len(moves):
                player_name = "黑" if player == 1 else "白"
                col = chr(65 + move[1])
                row = move[0] + 1
                text.append(f"{i + 1}. {player_name}({col}{row})")

        self.replay_text.setPlainText("\n".join(text))

    def on_first(self):
        """跳到开始"""
        self.current_move = 0
        self.update_display()

    def on_prev(self):
        """上一步"""
        if self.current_move > 0:
            self.current_move -= 1
            self.update_display()

    def on_next(self):
        """下一步"""
        moves = self.game_data.get('moves', [])
        if self.current_move < len(moves):
            self.current_move += 1
            self.update_display()

    def on_last(self):
        """跳到结束"""
        moves = self.game_data.get('moves', [])
        self.current_move = len(moves)
        self.update_display()


class ModelConfigDialog(QDialog):
    """模型配置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("模型配置")
        self.setFixedSize(400, 300)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 表单布局
        form = QFormLayout()

        # 模型类型
        self.model_type_combo = QComboBox()
        self.model_type_combo.addItem("小型模型 (快速)", "small")
        self.model_type_combo.addItem("完整模型 (高精度)", "full")
        form.addRow("模型类型:", self.model_type_combo)

        # 通道数
        self.channels_spin = QSpinBox()
        self.channels_spin.setRange(64, 512)
        self.channels_spin.setSingleStep(64)
        self.channels_spin.setValue(128)
        form.addRow("卷积通道数:", self.channels_spin)

        # 残差块数
        self.res_blocks_spin = QSpinBox()
        self.res_blocks_spin.setRange(5, 20)
        self.res_blocks_spin.setSingleStep(1)
        self.res_blocks_spin.setValue(10)
        form.addRow("残差块数:", self.res_blocks_spin)

        layout.addLayout(form)

        # 按钮
        btn_layout = QHBoxLayout()

        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def get_config(self) -> dict:
        """获取配置"""
        return {
            'model_type': self.model_type_combo.currentData(),
            'channels': self.channels_spin.value(),
            'res_blocks': self.res_blocks_spin.value()
        }


class PromptEditorDialog(QDialog):
    """提示词编辑器对话框"""

    def __init__(self, template: str, parent=None):
        super().__init__(parent)
        self.template = template
        self.setWindowTitle("提示词模板编辑")
        self.setMinimumSize(600, 500)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 说明
        info = QLabel(
            "提示词模板中使用 {ascii_board} 表示棋盘状态，"
            "{color} 表示当前玩家颜色（黑或白）。\n"
            "确保包含以下三个部分：\n"
            "1. 局势分析\n"
            "2. 最佳落子\n"
            "3. 落子理由"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # 模板编辑
        self.template_edit = QTextEdit()
        self.template_edit.setPlainText(self.template)
        layout.addWidget(self.template_edit)

        # 按钮
        btn_layout = QHBoxLayout()

        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        reset_btn = QPushButton("恢复默认")
        reset_btn.clicked.connect(self.on_reset)
        btn_layout.addWidget(reset_btn)

        layout.addLayout(btn_layout)

    def on_reset(self):
        """恢复默认"""
        from config import Config
        self.template_edit.setPlainText(Config.DEFAULT_CONFIG["prompt_template"])

    def get_template(self) -> str:
        """获取模板"""
        return self.template_edit.toPlainText()
