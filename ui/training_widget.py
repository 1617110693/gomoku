"""
AI训练标签页模块
包含训练控制台、实时图表和参数配置
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QGroupBox, QComboBox, QTextEdit,
                              QSpinBox, QDoubleSpinBox, QProgressBar,
                              QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont

from ai.trainer import Trainer
from config import get_config
from utils import format_timestamp
import numpy as np


class TrainingThread(QThread):
    """训练线程"""

    # 信号
    progress = pyqtSignal(int, float, float)  # epoch, loss, progress
    log = pyqtSignal(str)  # 日志消息
    finished = pyqtSignal(dict)  # 训练完成
    game_completed = pyqtSignal(int)  # 对局完成

    def __init__(self, trainer: Trainer, config: dict):
        super().__init__()
        self.trainer = trainer
        self.config = config
        self.dataset_size_before = 0

    def run(self):
        """执行训练"""
        try:
            # 生成自我对弈数据
            self.log.emit(f"[{format_timestamp()}] 开始生成自我对弈数据...")

            num_games = self.config.get('self_play_games', 100)
            self.dataset_size_before = len(self.trainer.dataset)

            # 自我对弈
            def progress_callback(progress, games, moves, elapsed):
                self.log.emit(f"进度: {games}/{num_games} 局, "
                              f"步数: {moves}, "
                              f"耗时: {elapsed:.1f}秒")
                self.game_completed.emit(games)

            self.trainer.self_play(
                num_games=num_games,
                temperature=self.config.get('temperature', 1.0),
                callback=progress_callback
            )

            new_data = len(self.trainer.dataset) - self.dataset_size_before
            self.log.emit(f"生成了 {new_data} 个训练样本")

            # 训练
            self.log.emit(f"开始训练模型...")
            num_epochs = self.config.get('num_epochs', 50)

            for epoch in range(num_epochs):
                if self.trainer.should_stop:
                    self.log.emit("训练被用户停止")
                    break

                result = self.trainer.train_step()
                self.progress.emit(epoch + 1, result['loss'],
                                   (epoch + 1) / num_epochs)
                QThread.msleep(10)  # 让出 GUI 更新

            self.log.emit("训练完成!")
            self.finished.emit({
                'epochs': num_epochs,
                'loss': result['loss']
            })

        except Exception as e:
            self.log.emit(f"训练出错: {e}")


class TrainingWidget(QWidget):
    """
    AI 训练标签页

    信号:
        trainingStarted: 训练开始
        trainingStopped: 训练停止
    """

    trainingStarted = pyqtSignal()
    trainingStopped = pyqtSignal()

    # 训练模式
    MODE_SELF_PLAY = "self_play"
    MODE_EXTERNAL = "external"
    MODE_HYBRID = "hybrid"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()

        # 训练器
        self.trainer = None
        self.training_thread = None

        # 图表数据
        self.loss_data = []

        self._init_ui()

    def _init_ui(self):
        """初始化 UI"""
        main_layout = QVBoxLayout(self)

        # 训练模式选择
        mode_group = QGroupBox("训练模式")
        mode_layout = QHBoxLayout()

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("自我博弈训练", self.MODE_SELF_PLAY)
        self.mode_combo.addItem("外部模型对战", self.MODE_EXTERNAL)
        self.mode_combo.addItem("混合训练", self.MODE_HYBRID)
        mode_layout.addWidget(QLabel("训练模式:"))
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        mode_group.setLayout(mode_layout)
        main_layout.addWidget(mode_group)

        # 参数配置
        param_group = QGroupBox("参数配置")
        param_layout = QHBoxLayout()

        # 学习率
        lr_layout = QVBoxLayout()
        lr_layout.addWidget(QLabel("学习率"))
        self.lr_spin = QDoubleSpinBox()
        self.lr_spin.setRange(0.0001, 0.1)
        self.lr_spin.setSingleStep(0.0001)
        self.lr_spin.setDecimals(4)
        self.lr_spin.setValue(0.001)
        lr_layout.addWidget(self.lr_spin)
        param_layout.addLayout(lr_layout)

        # 批次大小
        batch_layout = QVBoxLayout()
        batch_layout.addWidget(QLabel("批次大小"))
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(32, 1024)
        self.batch_spin.setSingleStep(32)
        self.batch_spin.setValue(256)
        batch_layout.addWidget(self.batch_spin)
        param_layout.addLayout(batch_layout)

        # 训练轮数
        epoch_layout = QVBoxLayout()
        epoch_layout.addWidget(QLabel("训练轮数"))
        self.epoch_spin = QSpinBox()
        self.epoch_spin.setRange(10, 1000)
        self.epoch_spin.setSingleStep(10)
        self.epoch_spin.setValue(100)
        epoch_layout.addWidget(self.epoch_spin)
        param_layout.addLayout(epoch_layout)

        # MCTS 模拟次数
        mcts_layout = QVBoxLayout()
        mcts_layout.addWidget(QLabel("MCTS 模拟次数"))
        self.mcts_spin = QSpinBox()
        self.mcts_spin.setRange(100, 2000)
        self.mcts_spin.setSingleStep(100)
        self.mcts_spin.setValue(400)
        mcts_layout.addWidget(self.mcts_spin)
        param_layout.addLayout(mcts_layout)

        # 自我对局数量
        games_layout = QVBoxLayout()
        games_layout.addWidget(QLabel("自我对局数量"))
        self.games_spin = QSpinBox()
        self.games_spin.setRange(10, 500)
        self.games_spin.setSingleStep(10)
        self.games_spin.setValue(100)
        games_layout.addWidget(self.games_spin)
        param_layout.addLayout(games_layout)

        param_group.setLayout(param_layout)
        main_layout.addWidget(param_group)

        # 进度显示
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(QLabel("训练进度:"))
        progress_layout.addWidget(self.progress_bar)
        self.epoch_label = QLabel("0 / 0")
        progress_layout.addWidget(self.epoch_label)
        main_layout.addLayout(progress_layout)

        # 训练日志
        log_group = QGroupBox("训练日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # 统计信息
        stats_group = QGroupBox("训练统计")
        stats_layout = QHBoxLayout()

        self.stats_label = QLabel("数据集大小: 0 | 当前轮数: 0 | 损失: --")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)

        # 控制按钮
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("开始训练")
        self.btn_start.clicked.connect(self.on_start_clicked)
        btn_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.clicked.connect(self.on_stop_clicked)
        self.btn_stop.setEnabled(False)
        btn_layout.addWidget(self.btn_stop)

        self.btn_save = QPushButton("保存模型")
        self.btn_save.clicked.connect(self.on_save_clicked)
        btn_layout.addWidget(self.btn_save)

        main_layout.addLayout(btn_layout)

    def _init_trainer(self):
        """初始化训练器"""
        if self.trainer is None:
            self.trainer = Trainer(
                board_size=15,
                device="cpu",
                learning_rate=self.lr_spin.value(),
                batch_size=self.batch_spin.value()
            )

    def on_start_clicked(self):
        """开始训练按钮点击"""
        self._init_trainer()

        # 获取配置
        config = {
            'learning_rate': self.lr_spin.value(),
            'batch_size': self.batch_spin.value(),
            'num_epochs': self.epoch_spin.value(),
            'mcts_simulations': self.mcts_spin.value(),
            'self_play_games': self.games_spin.value(),
            'temperature': 1.0
        }

        # 创建训练线程
        self.training_thread = TrainingThread(self.trainer, config)
        self.training_thread.progress.connect(self.on_progress)
        self.training_thread.log.connect(self.on_log)
        self.training_thread.finished.connect(self.on_finished)
        self.training_thread.game_completed.connect(self.on_game_completed)

        # 更新 UI
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.log_text.clear()
        self.loss_data = []

        # 开始训练
        self.training_thread.start()
        self.trainingStarted.emit()

    def on_stop_clicked(self):
        """停止训练按钮点击"""
        if self.trainer:
            self.trainer.stop()

        if self.training_thread:
            self.training_thread.should_stop = True

        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.trainingStopped.emit()

    def on_save_clicked(self):
        """保存模型按钮点击"""
        if self.trainer:
            from PyQt6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getSaveFileName(
                self, "保存模型", "model.pth", "模型文件 (*.pth)"
            )
            if path:
                self.trainer.save_model(path)
                self.log_text.append(f"[{format_timestamp()}] 模型已保存到: {path}")

    @pyqtSlot(int, float, float)
    def on_progress(self, epoch: int, loss: float, progress: float):
        """进度更新"""
        self.progress_bar.setValue(int(progress * 100))
        self.epoch_label.setText(f"{epoch} / {self.epoch_spin.value()}")
        self.loss_data.append(loss)
        self.stats_label.setText(
            f"数据集大小: {len(self.trainer.dataset)} | "
            f"当前轮数: {epoch} | 损失: {loss:.4f}"
        )

    @pyqtSlot(str)
    def on_log(self, message: str):
        """日志更新"""
        self.log_text.append(message)

    @pyqtSlot(int)
    def on_game_completed(self, games: int):
        """对局完成"""
        self.stats_label.setText(
            f"数据集大小: {len(self.trainer.dataset)} | "
            f"已完成对局: {games}"
        )

    @pyqtSlot(dict)
    def on_finished(self, result: dict):
        """训练完成"""
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.log_text.append(f"训练完成! 最终损失: {result.get('loss', 0):.4f}")
        self.trainingStopped.emit()

    def get_trainer(self) -> Trainer:
        """获取训练器"""
        self._init_trainer()
        return self.trainer
