"""
主窗口模块
应用程序的主窗口，包含菜单栏和标签页
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QTabWidget, QMenuBar, QMenu, QStatusBar, QLabel,
                              QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QCloseEvent


class MainWindow(QMainWindow):
    """
    主窗口类

    包含：
    - 菜单栏
    - 四个主要标签页（游戏对战、AI训练、模型管理、系统设置）
    - 状态栏
    """

    # 信号定义
    gameStarted = pyqtSignal()
    gamePaused = pyqtSignal()
    trainingStarted = pyqtSignal()
    trainingStopped = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("五子棋 AI 训练平台")
        self.setMinimumSize(1000, 700)

        # 状态栏标签
        self.status_labels = {}

        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # 创建菜单栏
        self._create_menu_bar()

        # 创建状态栏
        self._create_status_bar()

    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        new_game_action = QAction("新游戏(&N)", self)
        new_game_action.setShortcut("Ctrl+N")
        new_game_action.triggered.connect(self.on_new_game)
        file_menu.addAction(new_game_action)

        save_game_action = QAction("保存对局(&S)", self)
        save_game_action.setShortcut("Ctrl+S")
        save_game_action.triggered.connect(self.on_save_game)
        file_menu.addAction(save_game_action)

        load_game_action = QAction("加载对局(&L)", self)
        load_game_action.setShortcut("Ctrl+O")
        load_game_action.triggered.connect(self.on_load_game)
        file_menu.addAction(load_game_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 游戏菜单
        game_menu = menubar.addMenu("游戏(&G)")

        undo_action = QAction("悔棋(&U)", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.on_undo)
        game_menu.addAction(undo_action)

        restart_action = QAction("重新开始(&R)", self)
        restart_action.triggered.connect(self.on_restart)
        game_menu.addAction(restart_action)

        game_menu.addSeparator()

        pause_action = QAction("暂停(&P)", self)
        pause_action.setShortcut("Ctrl+P")
        pause_action.triggered.connect(self.on_pause)
        game_menu.addAction(pause_action)

        # 训练菜单
        train_menu = menubar.addMenu("训练(&T)")

        start_training_action = QAction("开始训练(&S)", self)
        start_training_action.setShortcut("Ctrl+T")
        start_training_action.triggered.connect(self.on_start_training)
        train_menu.addAction(start_training_action)

        stop_training_action = QAction("停止训练(&T)", self)
        stop_training_action.setShortcut("Ctrl+Shift+T")
        stop_training_action.triggered.connect(self.on_stop_training)
        train_menu.addAction(stop_training_action)

        train_menu.addSeparator()

        save_checkpoint_action = QAction("保存检查点(&C)", self)
        save_checkpoint_action.triggered.connect(self.on_save_checkpoint)
        train_menu.addAction(save_checkpoint_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)

        manual_action = QAction("使用手册(&M)", self)
        manual_action.triggered.connect(self.on_manual)
        help_menu.addAction(manual_action)

    def _create_status_bar(self):
        """创建状态栏"""
        statusbar = self.statusBar()

        # 状态标签
        self.status_labels["main"] = QLabel("就绪")
        self.status_labels["model"] = QLabel("模型: 未加载")
        self.status_labels["api"] = QLabel("DeepSeek: 未配置")
        self.status_labels["training"] = QLabel("训练: 空闲")

        separator = QLabel("  |  ")
        statusbar.addPermanentWidget(self.status_labels["main"])
        statusbar.addPermanentWidget(separator)
        statusbar.addPermanentWidget(self.status_labels["model"])
        statusbar.addPermanentWidget(separator)
        statusbar.addPermanentWidget(self.status_labels["api"])
        statusbar.addPermanentWidget(separator)
        statusbar.addPermanentWidget(self.status_labels["training"])

    def add_tab(self, widget, title: str):
        """添加标签页"""
        self.tab_widget.addTab(widget, title)

    def set_status(self, key: str, text: str):
        """设置状态栏文本"""
        if key in self.status_labels:
            self.status_labels[key].setText(text)

    def on_new_game(self):
        """新建游戏"""
        self.gameStarted.emit()

    def on_save_game(self):
        """保存对局"""
        pass

    def on_load_game(self):
        """加载对局"""
        pass

    def on_undo(self):
        """悔棋"""
        pass

    def on_restart(self):
        """重新开始"""
        pass

    def on_pause(self):
        """暂停"""
        self.gamePaused.emit()

    def on_start_training(self):
        """开始训练"""
        self.trainingStarted.emit()

    def on_stop_training(self):
        """停止训练"""
        self.trainingStopped.emit()

    def on_save_checkpoint(self):
        """保存检查点"""
        pass

    def on_about(self):
        """关于"""
        QMessageBox.about(self, "关于",
                          "五子棋 AI 训练平台 v1.0\n\n"
                          "一个支持本地 AI 训练和外部大模型对战的五子棋应用。\n\n"
                          "功能特点：\n"
                          "- 支持多种对战模式\n"
                          "- AlphaZero 风格 AI 训练\n"
                          "- DeepSeek API 集成\n"
                          "- 训练数据可视化")

    def on_manual(self):
        """使用手册"""
        QMessageBox.information(self, "使用手册",
                               "请参考 README.md 获取详细使用说明。")

    def closeEvent(self, event: QCloseEvent):
        """关闭窗口事件"""
        reply = QMessageBox.question(self, "确认退出",
                                     "确定要退出吗？未保存的数据将会丢失。",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
