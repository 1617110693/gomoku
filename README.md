# 五子棋 AI 训练平台

一个功能完整的五子棋对战与 AI 训练桌面应用，支持本地 AI 模型训练和外部大模型 API（DeepSeek）对战。

## 功能特点

### 游戏模式
- **人类 vs 本地 AI**：与本地训练的 AI 对战
- **人类 vs 外部 API**：与 DeepSeek 等大模型对战
- **本地 AI vs 外部 API**：让本地 AI 与外部大模型对战
- **本地 AI vs 本地 AI**：不同版本 AI 之间的对战

### AI 训练系统
- **自我博弈训练**：传统的 AlphaZero 式自我对弈
- **外部模型对战训练**：与外部大模型进行大量对局
- **混合训练**：结合多种数据源的训练方式
- **实时监控**：训练进度、损失值、胜率变化实时显示

### 核心功能
- 15×15 标准棋盘（支持自定义大小 9×9、13×13、19×19）
- 完整的胜负判断（横、竖、斜五子连珠）
- 悔棋功能（最多悔 3 步）
- 对局保存与加载
- 训练曲线可视化
- 模型版本管理

## 环境要求

- Python 3.10+
- PyQt6 6.6.0+
- PyTorch 2.0.0+
- Windows/Linux/macOS

## 安装步骤

### 1. 克隆或下载项目

```bash
cd gomoku_desktop_ai
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install PyQt6>=6.6.0
pip install torch>=2.0.0
pip install numpy>=1.24.0
pip install matplotlib>=3.7.0
pip install requests>=2.28.0
```

### 4. 运行应用

```bash
python main.py
```

## 使用说明

### 首次启动

1. 启动应用后，默认显示"游戏对战"标签页
2. 建议先进入"系统设置"标签页配置 DeepSeek API
3. 配置 API 密钥后即可与 DeepSeek 对战

### 游戏对战

1. 选择对战模式（人类 vs AI、人类 vs API 等）
2. 设置棋盘大小和 AI 难度
3. 点击"开始游戏"按钮
4. 黑方先行，点击棋盘落子

### AI 训练

1. 进入"AI 训练"标签页
2. 选择训练模式（自我博弈/外部对战/混合训练）
3. 配置训练参数（学习率、批次大小、MCTS 模拟次数等）
4. 点击"开始训练"按钮
5. 实时查看训练日志和损失曲线

### 模型管理

1. 进入"模型管理"标签页
2. 查看已保存的模型列表
3. 选择模型进行加载、对比或删除
4. 支持两个模型之间的对战评估

### 系统设置

1. **API 配置**：设置 DeepSeek API 密钥和参数
2. **提示词模板**：自定义 AI 对战的提示词
3. **游戏设置**：调整棋盘大小、悔棋步数等
4. **界面设置**：切换深色/浅色主题

## API 密钥配置

### DeepSeek API

1. 访问 [DeepSeek API 平台](https://platform.deepseek.com/)
2. 注册账号并获取 API 密钥
3. 在"系统设置"中输入 API 密钥
4. 点击"验证密钥"确认配置正确

### 其他 API（预留）

- OpenAI API
- Anthropic API

预留接口，可通过继承 `BaseLLMApi` 类快速扩展。

## 项目结构

```
gomoku_desktop_ai/
├── main.py                 # 程序入口
├── config.py               # 全局配置管理
├── utils.py                # 工具函数
├── requirements.txt        # 依赖列表
├── game/                   # 游戏核心模块
│   ├── board.py           # 棋盘类和游戏逻辑
│   ├── player.py          # 玩家抽象基类
│   ├── human_player.py    # 人类玩家
│   ├── local_ai_player.py # 本地 AI 玩家
│   └── external_ai_player.py # 外部 API 玩家
├── ai/                     # AI 模块
│   ├── model.py           # 神经网络模型
│   ├── mcts.py            # MCTS 算法
│   ├── trainer.py         # 训练器
│   └── data_utils.py      # 数据处理
├── api/                    # API 模块
│   ├── base_api.py        # API 抽象基类
│   └── deepseek_api.py    # DeepSeek API 实现
├── ui/                     # 界面模块
│   ├── main_window.py     # 主窗口
│   ├── board_widget.py    # 棋盘组件
│   ├── game_widget.py     # 游戏标签页
│   ├── training_widget.py # 训练标签页
│   ├── model_widget.py    # 模型管理标签页
│   ├── settings_widget.py # 设置标签页
│   └── dialogs.py          # 对话框
└── data/                   # 数据目录
    ├── models/             # 模型权重
    ├── games/              # 对局记录
    └── training_data/      # 训练数据
```

## 技术架构

### 多线程设计

所有耗时操作都在独立的 QThread 中运行：
- AI 思考（MCTS 搜索）
- 模型训练
- API 调用
- 批量评估

使用 PyQt6 的信号与槽机制实现线程间通信。

### 神经网络架构

采用 AlphaZero 风格架构：
- **卷积 backbone**：提取棋盘特征
- **策略头**：预测每个位置的落子概率
- **价值头**：预测当前局面的胜率

### MCTS 算法

实现带 PUCT 选择策略的蒙特卡洛树搜索：
- 支持温度采样（训练时）
- 支持确定性选择（推理时）
- 虚拟损失（用于并行化）

## 常见问题

### Q: 应用启动报错 `ModuleNotFoundError: No module named 'PyQt6'`

A: 请确保已安装 PyQt6：
```bash
pip install PyQt6>=6.6.0
```

### Q: AI 响应很慢怎么办？

A: 可以通过以下方式优化：
- 降低 MCTS 模拟次数（设置 → AI 难度 → 简单）
- 使用 GPU 加速（需要安装 PyTorch GPU 版本）
- 减小模型规模

### Q: API 调用失败

A: 检查以下几点：
1. API 密钥是否正确配置
2. 网络连接是否正常
3. API 配额是否用完
4. 尝试降低 temperature 或 max_tokens 参数

### Q: 训练loss不下降

A: 可能的原因：
1. 学习率过高或过低
2. 训练数据不足
3. 模型规模太小
4. 训练轮数不够

建议先使用默认参数进行训练。

## 开发指南

### 添加新的 API 提供商

1. 继承 `BaseLLMApi` 类
2. 实现 `get_move`、`validate_api_key`、`parse_move` 方法
3. 在 `ExternalAIPlayer` 中添加支持

### 添加新的训练模式

1. 在 `Trainer` 类中添加新的训练方法
2. 实现数据生成逻辑
3. 在 UI 中添加对应的配置选项

### 自定义棋盘大小

修改 `config.py` 中的 `DEFAULT_BOARD_SIZE` 或在游戏界面中调整。

## 许可证

本项目仅供学习和研究使用。

## 致谢

- AlphaZero 论文：Mastering Chess and Shogi by Self-Play with a General Reinforcement Learning Algorithm
- PyQt6 官方文档
- PyTorch 官方文档
