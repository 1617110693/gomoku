"""
系统设置标签页模块
包含 API 配置、提示词模板、全局选项等
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QGroupBox, QLineEdit, QComboBox,
                              QSpinBox, QDoubleSpinBox, QTextEdit, QCheckBox,
                              QMessageBox, QFormLayout, QScrollArea, QVBoxLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config import get_config
from utils import validate_api_key
from api.deepseek_api import DeepSeekApi


class SettingsWidget(QWidget):
    """
    系统设置标签页
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()

        self._init_ui()
        self.load_settings()

    def _init_ui(self):
        """初始化 UI"""
        main_layout = QVBoxLayout(self)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # API 配置
        api_group = QGroupBox("API 配置")
        api_layout = QFormLayout()

        # 提供商选择
        self.provider_combo = QComboBox()
        self.provider_combo.addItem("DeepSeek", "deepseek")
        self.provider_combo.addItem("OpenAI", "openai")
        self.provider_combo.addItem("Anthropic", "anthropic")
        api_layout.addRow("API 提供商:", self.provider_combo)

        # API 密钥
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("输入 API 密钥")
        api_layout.addRow("API 密钥:", self.api_key_edit)

        # 模型选择
        self.model_combo = QComboBox()
        self.model_combo.addItem("deepseek-chat", "deepseek-chat")
        self.model_combo.addItem("deepseek-coder", "deepseek-coder")
        api_layout.addRow("模型:", self.model_combo)

        # 验证按钮
        self.btn_validate = QPushButton("验证密钥")
        self.btn_validate.clicked.connect(self.on_validate_clicked)
        api_layout.addRow("", self.btn_validate)

        # 温度参数
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.1, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setDecimals(1)
        self.temperature_spin.setValue(0.7)
        api_layout.addRow("Temperature:", self.temperature_spin)

        # 最大 Token
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 4000)
        self.max_tokens_spin.setSingleStep(100)
        self.max_tokens_spin.setValue(1000)
        api_layout.addRow("最大 Token:", self.max_tokens_spin)

        # 超时时间
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setSingleStep(10)
        self.timeout_spin.setValue(60)
        api_layout.addRow("超时时间(秒):", self.timeout_spin)

        api_group.setLayout(api_layout)
        scroll_layout.addWidget(api_group)

        # 提示词模板
        prompt_group = QGroupBox("提示词模板")
        prompt_layout = QVBoxLayout()

        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText("输入提示词模板...")
        self.prompt_text.setMinimumHeight(200)
        prompt_layout.addWidget(self.prompt_text)

        # 模板操作
        prompt_btn_layout = QHBoxLayout()
        self.btn_reset_prompt = QPushButton("恢复默认")
        self.btn_reset_prompt.clicked.connect(self.on_reset_prompt_clicked)
        prompt_btn_layout.addWidget(self.btn_reset_prompt)

        self.btn_test_prompt = QPushButton("测试模板")
        self.btn_test_prompt.clicked.connect(self.on_test_prompt_clicked)
        prompt_btn_layout.addWidget(self.btn_test_prompt)
        prompt_btn_layout.addStretch()
        prompt_layout.addLayout(prompt_btn_layout)

        prompt_group.setLayout(prompt_layout)
        scroll_layout.addWidget(prompt_group)

        # 游戏设置
        game_group = QGroupBox("游戏设置")
        game_layout = QFormLayout()

        # 默认棋盘大小
        self.board_size_spin = QSpinBox()
        self.board_size_spin.setRange(9, 19)
        self.board_size_spin.setValue(15)
        game_layout.addRow("默认棋盘大小:", self.board_size_spin)

        # 最大悔棋步数
        self.max_undo_spin = QSpinBox()
        self.max_undo_spin.setRange(1, 10)
        self.max_undo_spin.setValue(3)
        game_layout.addRow("最大悔棋步数:", self.max_undo_spin)

        # 启用禁手规则
        self.forbidden_hand_check = QCheckBox()
        self.forbidden_hand_check.setChecked(False)
        game_layout.addRow("启用禁手规则:", self.forbidden_hand_check)

        game_group.setLayout(game_layout)
        scroll_layout.addWidget(game_group)

        # UI 设置
        ui_group = QGroupBox("界面设置")
        ui_layout = QFormLayout()

        # 主题
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("浅色", "light")
        self.theme_combo.addItem("深色", "dark")
        ui_layout.addRow("主题:", self.theme_combo)

        ui_group.setLayout(ui_layout)
        scroll_layout.addWidget(ui_group)

        # 保存按钮
        save_layout = QHBoxLayout()
        self.btn_save = QPushButton("保存设置")
        self.btn_save.clicked.connect(self.on_save_clicked)
        save_layout.addWidget(self.btn_save)

        self.btn_cancel = QPushButton("重置")
        self.btn_cancel.clicked.connect(self.load_settings)
        save_layout.addWidget(self.btn_cancel)
        save_layout.addStretch()
        scroll_layout.addLayout(save_layout)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

    def load_settings(self):
        """加载设置"""
        # API 配置
        api_config = self.config.api
        deepseek_config = api_config.get("deepseek", {})

        self.api_key_edit.setText(deepseek_config.get("api_key", ""))
        self.model_combo.setCurrentText(deepseek_config.get("model", "deepseek-chat"))
        self.temperature_spin.setValue(deepseek_config.get("temperature", 0.7))
        self.max_tokens_spin.setValue(deepseek_config.get("max_tokens", 1000))
        self.timeout_spin.setValue(deepseek_config.get("timeout", 60))

        # 提示词模板
        self.prompt_text.setText(self.config.prompt_template)

        # 游戏设置
        game_config = self.config.game
        self.board_size_spin.setValue(game_config.get("board_size", 15))
        self.max_undo_spin.setValue(game_config.get("max_undo_steps", 3))
        self.forbidden_hand_check.setChecked(game_config.get("enable_forbidden_hand", False))

        # UI 设置
        ui_config = self.config.ui
        self.theme_combo.setCurrentText(ui_config.get("theme", "浅色"))

    def on_save_clicked(self):
        """保存设置"""
        try:
            # API 配置
            self.config.set("sk-" + self.api_key_edit.text().strip(), "api", "deepseek", "api_key")
            self.config.set(self.model_combo.currentData(), "api", "deepseek", "model")
            self.config.set(self.temperature_spin.value(), "api", "deepseek", "temperature")
            self.config.set(self.max_tokens_spin.value(), "api", "deepseek", "max_tokens")
            self.config.set(self.timeout_spin.value(), "api", "deepseek", "timeout")

            # 提示词模板
            self.config.config["prompt_template"] = self.prompt_text.toPlainText()
            self.config.save()

            # 游戏设置
            self.config.set(self.board_size_spin.value(), "game", "board_size")
            self.config.set(self.max_undo_spin.value(), "game", "max_undo_steps")
            self.config.set(self.forbidden_hand_check.isChecked(), "game", "enable_forbidden_hand")

            # UI 设置
            self.config.set(self.theme_combo.currentData(), "ui", "theme")

            QMessageBox.information(self, "成功", "设置已保存！")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存设置失败: {e}")

    def on_validate_clicked(self):
        """验证 API 密钥"""
        api_key = self.api_key_edit.text().strip()

        if not api_key:
            QMessageBox.warning(self, "提示", "请输入 API 密钥")
            return

        self.btn_validate.setEnabled(False)
        self.btn_validate.setText("验证中...")

        try:
            api = DeepSeekApi(api_key=api_key)
            if api.validate_api_key():
                QMessageBox.information(self, "成功", "API 密钥有效！")
            else:
                QMessageBox.warning(self, "失败", "API 密钥无效，请检查后重试")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"验证失败: {e}")
        finally:
            self.btn_validate.setEnabled(True)
            self.btn_validate.setText("验证密钥")

    def on_reset_prompt_clicked(self):
        """恢复默认提示词"""
        from config import Config
        self.prompt_text.setText(Config.DEFAULT_CONFIG["prompt_template"])
        QMessageBox.information(self, "提示", "已恢复默认提示词模板")

    def on_test_prompt_clicked(self):
        """测试提示词"""
        prompt = self.prompt_text.toPlainText()

        # 简单的测试棋盘
        test_board = """
    A B C D E F G H I J K L M N O
  +-------------------------+
 1| · · · · · · · · · · · · · · │
 2| · · · · · · · · · · · · · · │
 3| · · · ● · · · · · · · · · · │
 4| · · · · · · · · · · · · · · │
 5| · · · · ○ · · · · · · · · · │
 6| · · · · · · · · · · · · · · │
 7| · · · · · · · · · · · · · · │
 8| · · · · · · · · · · · · · · │
 9| · · · · · · · · · · · · · · │
10| · · · · · · · · · · · · · · │
11| · · · · · · · · · · · · · · │
12| · · · · · · · · · · · · · · │
13| · · · · · · · · · · · · · · │
14| · · · · · · · · · · · · · · │
15| · · · · · · · · · · · · · · │
  +-------------------------+
        """

        # 格式化测试
        try:
            formatted = prompt.format(ascii_board=test_board, color="黑")
            self.prompt_text.setText(formatted)
            QMessageBox.information(self, "成功", "提示词模板格式正确！")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"提示词模板格式错误: {e}")
