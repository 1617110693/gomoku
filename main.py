"""
五子棋 AI 训练平台
程序入口文件
"""
import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from config import get_config
from ui.main_window import MainWindow
from ui.game_widget import GameWidget
from ui.training_widget import TrainingWidget
from ui.model_widget import ModelWidget
from ui.settings_widget import SettingsWidget


def exception_hook(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"未捕获的异常:\n{error_msg}")

    # 显示错误对话框
    error_dialog = QMessageBox()
    error_dialog.setIcon(QMessageBox.Icon.Critical)
    error_dialog.setWindowTitle("应用程序错误")
    error_dialog.setText("应用程序遇到了一个错误:")
    error_dialog.setDetailedText(error_msg)
    error_dialog.exec()


def setup_stylesheet(app: QApplication):
    """设置应用程序样式表"""
    app.setStyleSheet("""
        QMainWindow, QWidget {
            font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
            font-size: 10pt;
        }

        QGroupBox {
            font-weight: bold;
            border: 1px solid #ccc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }

        QPushButton {
            min-width: 80px;
            padding: 5px 15px;
            background-color: #0078d4;
            color: white;
            border: none;
            border-radius: 3px;
        }

        QPushButton:hover {
            background-color: #106ebe;
        }

        QPushButton:pressed {
            background-color: #005a9e;
        }

        QPushButton:disabled {
            background-color: #cccccc;
            color: #888888;
        }

        QTabWidget::pane {
            border: 1px solid #ccc;
            border-radius: 3px;
        }

        QTabBar::tab {
            padding: 8px 20px;
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-bottom: none;
            border-top-left-radius: 3px;
            border-top-right-radius: 3px;
        }

        QTabBar::tab:selected {
            background-color: white;
        }

        QTextEdit, QLineEdit {
            border: 1px solid #ccc;
            border-radius: 3px;
            padding: 5px;
        }

        QComboBox {
            border: 1px solid #ccc;
            border-radius: 3px;
            padding: 5px;
        }

        QSpinBox, QDoubleSpinBox {
            border: 1px solid #ccc;
            border-radius: 3px;
            padding: 5px;
        }

        QProgressBar {
            border: 1px solid #ccc;
            border-radius: 3px;
            text-align: center;
        }

        QProgressBar::chunk {
            background-color: #0078d4;
            border-radius: 2px;
        }

        QStatusBar {
            background-color: #f0f0f0;
        }
    """)


def main():
    """主函数"""
    # 设置全局异常处理
    sys.excepthook = exception_hook

    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("五子棋 AI 训练平台")
    app.setApplicationVersion("1.0.0")

    # 设置样式
    setup_stylesheet(app)

    # 创建配置
    config = get_config()

    # 创建主窗口
    window = MainWindow()
    window.setWindowTitle("五子棋 AI 训练平台 v1.0")

    # 设置窗口大小
    ui_config = config.ui
    window.resize(ui_config.get("window_width", 1200),
                  ui_config.get("window_height", 800))

    # 创建并添加标签页
    game_widget = GameWidget()
    training_widget = TrainingWidget()
    model_widget = ModelWidget()
    settings_widget = SettingsWidget()

    window.add_tab(game_widget, "游戏对战")
    window.add_tab(training_widget, "AI 训练")
    window.add_tab(model_widget, "模型管理")
    window.add_tab(settings_widget, "系统设置")

    # 连接信号
    def on_training_started():
        window.set_status("training", "训练: 进行中")

    def on_training_stopped():
        window.set_status("training", "训练: 已停止")

    training_widget.trainingStarted.connect(on_training_started)
    training_widget.trainingStopped.connect(on_training_stopped)

    # 显示窗口
    window.show()

    # 更新状态栏
    window.set_status("main", "就绪")
    window.set_status("model", "模型: 未加载")

    # 检查 API 配置
    api_config = config.api.get("deepseek", {})
    if api_config.get("api_key"):
        if api_config["api_key"].startswith("sk-"):
            window.set_status("api", "DeepSeek: 已配置")
        else:
            window.set_status("api", "DeepSeek: 未配置")
    else:
        window.set_status("api", "DeepSeek: 未配置")

    # 启动事件循环
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
