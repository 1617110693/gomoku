"""
模型管理标签页模块
显示模型列表、版本信息和性能对比
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QTableWidget, QTableWidgetItem,
                              QGroupBox, QComboBox, QProgressBar, QMessageBox,
                              QSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config import get_config
from utils import format_timestamp
import os
from datetime import datetime


class ModelWidget(QWidget):
    """
    模型管理标签页
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self.models_dir = self.config.MODELS_DIR

        self._init_ui()
        self.refresh_model_list()

    def _init_ui(self):
        """初始化 UI"""
        main_layout = QVBoxLayout(self)

        # 模型列表
        list_group = QGroupBox("已保存的模型")
        list_layout = QVBoxLayout()

        self.model_table = QTableWidget()
        self.model_table.setColumnCount(4)
        self.model_table.setHorizontalHeaderLabels(["模型名称", "版本", "保存时间", "文件大小"])
        self.model_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.model_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        list_layout.addWidget(self.model_table)

        # 模型操作按钮
        btn_layout = QHBoxLayout()

        self.btn_refresh = QPushButton("刷新列表")
        self.btn_refresh.clicked.connect(self.refresh_model_list)
        btn_layout.addWidget(self.btn_refresh)

        self.btn_load = QPushButton("加载选中模型")
        self.btn_load.clicked.connect(self.on_load_clicked)
        btn_layout.addWidget(self.btn_load)

        self.btn_delete = QPushButton("删除选中")
        self.btn_delete.clicked.connect(self.on_delete_clicked)
        btn_layout.addWidget(self.btn_delete)

        self.btn_export = QPushButton("导出模型")
        self.btn_export.clicked.connect(self.on_export_clicked)
        btn_layout.addWidget(self.btn_export)

        list_layout.addLayout(btn_layout)
        list_group.setLayout(list_layout)
        main_layout.addWidget(list_group)

        # 模型对比
        compare_group = QGroupBox("模型性能对比")
        compare_layout = QVBoxLayout()

        # 选择要对比的模型
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("选择模型:"))
        self.compare_combo = QComboBox()
        self.compare_combo.addItem("选择模型...", None)
        select_layout.addWidget(self.compare_combo)
        select_layout.addWidget(QLabel("vs"))
        self.compare_combo2 = QComboBox()
        self.compare_combo2.addItem("选择模型...", None)
        select_layout.addWidget(self.compare_combo2)
        select_layout.addStretch()
        compare_layout.addLayout(select_layout)

        # 对战设置
        battle_layout = QHBoxLayout()
        battle_layout.addWidget(QLabel("对局数量:"))
        self.battle_spin = QSpinBox()
        self.battle_spin.setRange(10, 100)
        self.battle_spin.setValue(20)
        battle_layout.addWidget(self.battle_spin)

        self.btn_battle = QPushButton("开始对战评估")
        self.btn_battle.clicked.connect(self.on_battle_clicked)
        battle_layout.addWidget(self.btn_battle)
        battle_layout.addStretch()
        compare_layout.addLayout(battle_layout)

        # 对战结果
        self.result_text = QLabel("选择两个模型开始对比...")
        self.result_text.setWordWrap(True)
        compare_layout.addWidget(self.result_text)

        compare_group.setLayout(compare_layout)
        main_layout.addWidget(compare_group)

        # 模型信息
        info_group = QGroupBox("当前模型信息")
        info_layout = QVBoxLayout()

        self.model_info_label = QLabel("未加载模型")
        self.model_info_label.setWordWrap(True)
        info_layout.addWidget(self.model_info_label)
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

        main_layout.addStretch()

    def refresh_model_list(self):
        """刷新模型列表"""
        self.model_table.setRowCount(0)

        # 确保目录存在
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # 获取所有模型文件
        model_files = list(self.models_dir.glob("*.pth"))

        if not model_files:
            self.model_table.setRowCount(0)
            return

        for row, file_path in enumerate(model_files):
            self.model_table.insertRow(row)

            # 模型名称
            name_item = QTableWidgetItem(file_path.stem)
            self.model_table.setItem(row, 0, name_item)

            # 版本（从文件名提取）
            version = file_path.stem.split('_v')[-1] if '_v' in file_path.stem else '1.0'
            version_item = QTableWidgetItem(f"v{version}")
            self.model_table.setItem(row, 1, version_item)

            # 保存时间
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            time_item = QTableWidgetItem(mtime.strftime("%Y-%m-%d %H:%M"))
            self.model_table.setItem(row, 2, time_item)

            # 文件大小
            size = file_path.stat().st_size / (1024 * 1024)  # MB
            size_item = QTableWidgetItem(f"{size:.2f} MB")
            self.model_table.setItem(row, 3, size_item)

        # 更新下拉框
        self.compare_combo.clear()
        self.compare_combo.addItem("选择模型...", None)
        self.compare_combo2.clear()
        self.compare_combo2.addItem("选择模型...", None)

        for file_path in model_files:
            self.compare_combo.addItem(file_path.stem, str(file_path))
            self.compare_combo2.addItem(file_path.stem, str(file_path))

    def on_load_clicked(self):
        """加载选中模型"""
        row = self.model_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择要加载的模型")
            return

        model_name = self.model_table.item(row, 0).text()
        reply = QMessageBox.question(self, "确认",
                                     f"确定要加载模型 '{model_name}' 吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.model_info_label.setText(f"当前加载的模型: {model_name}")
            QMessageBox.information(self, "成功", f"模型 '{model_name}' 已加载")

    def on_delete_clicked(self):
        """删除选中模型"""
        row = self.model_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择要删除的模型")
            return

        model_name = self.model_table.item(row, 0).text()
        reply = QMessageBox.warning(self, "确认删除",
                                    f"确定要删除模型 '{model_name}' 吗？此操作不可恢复！",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # 删除文件
            file_path = self.models_dir / f"{model_name}.pth"
            if file_path.exists():
                file_path.unlink()
            self.refresh_model_list()

    def on_export_clicked(self):
        """导出模型"""
        row = self.model_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择要导出的模型")
            return

        model_name = self.model_table.item(row, 0).text()
        QMessageBox.information(self, "导出", f"模型 '{model_name}' 导出功能开发中...")

    def on_battle_clicked(self):
        """开始对战评估"""
        model1 = self.compare_combo.currentData()
        model2 = self.compare_combo2.currentData()

        if model1 is None or model2 is None:
            QMessageBox.warning(self, "提示", "请选择两个模型进行对比")
            return

        if model1 == model2:
            QMessageBox.warning(self, "提示", "请选择不同的模型进行对比")
            return

        self.result_text.setText("正在评估，请稍候...")
        QMessageBox.information(self, "评估", "对战评估功能开发中...")

    def get_current_model_path(self) -> str:
        """获取当前模型的路径"""
        return str(self.models_dir / "current_model.pth")
