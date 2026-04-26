"""
棋盘绘制组件模块
使用 PyQt6 绘制五子棋棋盘
"""
from PyQt6.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QGraphicsItem
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QMouseEvent, QPaintDevice


class BoardWidget(QWidget):
    """
    五子棋棋盘组件

    信号:
        stonePlaced: 落子信号 (row, col)
        cellClicked: 格子点击信号 (row, col)
    """

    stonePlaced = pyqtSignal(int, int)
    cellClicked = pyqtSignal(int, int)

    # 棋子颜色
    BLACK = 1
    WHITE = 2

    # 棋盘颜色
    BOARD_COLOR = QColor(220, 179, 130)  # 木质色
    LINE_COLOR = QColor(0, 0, 0)
    STAR_POINT_COLOR = QColor(0, 0, 0)

    def __init__(self, board_size: int = 15, cell_size: int = 40, parent=None):
        """
        初始化棋盘组件

        Args:
            board_size: 棋盘大小
            cell_size: 每格大小（像素）
            parent: 父组件
        """
        super().__init__(parent)
        self.board_size = board_size
        self.cell_size = cell_size

        # 计算窗口大小
        self.padding = 20  # 边距
        self.board_pixel_size = cell_size * (board_size - 1)
        self.setFixedSize(self.board_pixel_size + self.padding * 2,
                          self.board_pixel_size + self.padding * 2)

        # 棋盘状态
        self.stones = [[0] * board_size for _ in range(board_size)]
        self.last_move = None
        self.last_last_move = None

        # 落子动画相关
        self.animating_stone = None

        # 允许鼠标追踪
        self.setMouseTracking(True)

    def clear(self):
        """清空棋盘"""
        self.stones = [[0] * self.board_size for _ in range(self.board_size)]
        self.last_move = None
        self.last_last_move = None
        self.update()

    def place_stone(self, row: int, col: int, color: int):
        """
        在棋盘上放置棋子

        Args:
            row: 行索引 (0-based)
            col: 列索引 (0-based)
            color: 棋子颜色 (1=黑, 2=白)
        """
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            self.last_last_move = self.last_move
            self.last_move = (row, col)
            self.stones[row][col] = color
            self.update()

    def remove_stone(self, row: int, col: int):
        """移除棋子"""
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            self.stones[row][col] = 0
            self.update()

    def paintEvent(self, event):
        """绘制棋盘"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制棋盘背景
        painter.fillRect(self.rect(), self.BOARD_COLOR)

        # 绘制网格线
        self._draw_grid(painter)

        # 绘制星位点
        self._draw_star_points(painter)

        # 绘制棋子
        self._draw_stones(painter)

        # 绘制最后一个落子位置标记
        if self.last_move:
            self._draw_last_move_marker(painter, self.last_move)

        # 绘制当前悬停位置
        if hasattr(self, '_hover_pos') and self._hover_pos:
            self._draw_hover_indicator(painter, self._hover_pos[0], self._hover_pos[1])

    def _draw_grid(self, painter: QPainter):
        """绘制网格线"""
        pen = QPen(self.LINE_COLOR)
        pen.setWidth(1)
        painter.setPen(pen)

        # 绘制横线
        for i in range(self.board_size):
            y = self.padding + i * self.cell_size
            painter.drawLine(self.padding, y,
                             self.padding + self.board_pixel_size, y)

        # 绘制竖线
        for i in range(self.board_size):
            x = self.padding + i * self.cell_size
            painter.drawLine(x, self.padding,
                             x, self.padding + self.board_pixel_size)

    def _draw_star_points(self, painter: QPainter):
        """绘制星位点"""
        # 计算星位点位置（3-3, 3-11, 7-7, 11-3, 11-11 对于15×15棋盘）
        star_points = []
        if self.board_size == 15:
            star_points = [(3, 3), (3, 7), (3, 11),
                          (7, 3), (7, 7), (7, 11),
                          (11, 3), (11, 7), (11, 11)]
        elif self.board_size == 13:
            star_points = [(3, 3), (3, 6), (3, 9),
                          (6, 3), (6, 6), (6, 9),
                          (9, 3), (9, 6), (9, 9)]
        elif self.board_size == 9:
            star_points = [(2, 2), (2, 4), (2, 6),
                          (4, 2), (4, 4), (4, 6),
                          (6, 2), (6, 4), (6, 6)]

        painter.setBrush(QBrush(self.STAR_POINT_COLOR))
        for row, col in star_points:
            x = self.padding + col * self.cell_size
            y = self.padding + row * self.cell_size
            painter.drawEllipse(QPointF(x, y), 3, 3)

    def _draw_stones(self, painter: QPainter):
        """绘制所有棋子"""
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.stones[row][col] != 0:
                    self._draw_stone(painter, row, col, self.stones[row][col])

    def _draw_stone(self, painter: QPainter, row: int, col: int, color: int):
        """
        绘制单个棋子

        Args:
            painter: 画家
            row: 行索引
            col: 列索引
            color: 棋子颜色 (1=黑, 2=白)
        """
        x = self.padding + col * self.cell_size
        y = self.padding + row * self.cell_size
        radius = self.cell_size // 2 - 2

        # 绘制棋子阴影
        painter.setBrush(QBrush())
        if color == self.BLACK:
            # 黑棋
            gradient_color = QColor(60, 60, 60)
            painter.setBrush(QBrush(gradient_color))
        else:
            # 白棋
            gradient_color = QColor(240, 240, 240)
            painter.setBrush(QBrush(gradient_color))

        painter.drawEllipse(QPointF(x, y), radius, radius)

        # 绘制棋子主体
        if color == self.BLACK:
            painter.setBrush(QBrush(QColor(20, 20, 20)))
        else:
            painter.setBrush(QBrush(QColor(255, 255, 255)))

        painter.drawEllipse(QPointF(x, y - 1), radius - 1, radius - 1)

    def _draw_last_move_marker(self, painter: QPainter, move: tuple):
        """绘制最后一个落子位置标记"""
        row, col = move
        x = self.padding + col * self.cell_size
        y = self.padding + row * self.cell_size

        # 绘制红色圆圈标记
        pen = QPen(QColor(200, 50, 50))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(x, y), 6, 6)

    def _draw_hover_indicator(self, painter: QPainter, row: int, col: int):
        """绘制悬停指示器"""
        if self.stones[row][col] != 0:
            return  # 已有棋子不显示

        x = self.padding + col * self.cell_size
        y = self.padding + row * self.cell_size

        pen = QPen(QColor(100, 100, 100, 150))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(x, y), 6, 6)

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        pos = event.position()
        col = int((pos.x() - self.padding + self.cell_size / 2) / self.cell_size)
        row = int((pos.y() - self.padding + self.cell_size / 2) / self.cell_size)

        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            self._hover_pos = (row, col)
        else:
            self._hover_pos = None

        self.update()

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            col = int((pos.x() - self.padding + self.cell_size / 2) / self.cell_size)
            row = int((pos.y() - self.padding + self.cell_size / 2) / self.cell_size)

            if 0 <= row < self.board_size and 0 <= col < self.board_size:
                self.cellClicked.emit(row, col)

    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)

    def set_board_size(self, size: int):
        """设置棋盘大小"""
        self.board_size = size
        self.board_pixel_size = size * self.cell_size
        self.setFixedSize(self.board_pixel_size + self.padding * 2,
                          self.board_pixel_size + self.padding * 2)
        self.clear()
