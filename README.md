# AI4TurtleSoup - 智能海龟汤推理游戏

基于 LangGraph + LangChain 构建的智能"海龟汤"推理游戏系统。玩家通过提问逐步接近谜底，系统会通过智能分析提供合适的提示和引导。

## 🌟 特性

- 多类型智能提示（方向线索、偏离提醒等）
- 思维链结构维护 (BrainChainMemory)
- LLM 智能判断玩家状态（偏离、绕圈、尝试不足）
- LangGraph 驱动的游戏流程

## 🛠️ 技术栈

- Python 3.8+
- LangChain >= 0.1.0
- LangGraph >= 0.0.10
- DeepSeek LLM API

## 📦 安装

1. 克隆仓库：
```bash
git clone https://github.com/Yasmine0e/AI4TutleSoup_LangChain.git
cd AI4TurtleSoup_LangChain
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 设置环境变量：
```bash
export DEEPSEEK_API_KEY="your_api_key_here"
```

## 🎮 快速开始

1. 运行测试游戏：
```bash
python tests/game_flow_test.py
```

2. 开始新游戏：
```bash
python src/main.py  # 暂时没放外循环
```

## 📁 项目结构

```
src/
├── main.py              # 主程序入口
├── graph.py             # LangGraph 构建流程
├── state_schema.py      # GameState 结构定义
├── memory/
│   └── brainchain.py    # BrainChainMemory 类
├── tools/
│   ├── hint_generator.py    # 提示生成工具
│   ├── detectors.py         # 状态检测工具
│   └── answer_judge.py      # 答案判断工具
└── prompts/
    └── hint_templates.json  # 提示模板
```

## ⏳ TODO & 重构计划

1. 核心功能优化
   - [ ] **重构 Reply 后的Agent 以提高状态检测准确性**
   - [ ] **细化分支功能以实现系统完整**
   - [ ] **游戏外循环接入**
   - ...

3. 提示系统升级
   - [ ] 实现动态提示模板生成

4. 测试与监控
   - [ ] 添加单元测试覆盖
   - [ ] **集成 LangSmith 监测系统**
     - [ ] 实现对话流程追踪
     - [ ] 添加性能监控指标
     - [ ] 配置提示效果评估
   - [ ] **更多测试情景**

5. 用户体验
   - [ ] 添加 Web 界面

## 🎯 游戏流程

1. 初始化游戏环境和故事内容
2. 玩家提出问题
3. 生成回答
4. 更新思维链
3. 系统分析：
   - 检测是否偏离主题
   - 检测是否在绕圈
   - 检测是否需要提示
   - 生成提示
4. 返回回答和提示
5. 更新游戏状态
6. 重复步骤 2-5 直到玩家找到答案

## 🔄 状态检测

系统会自动检测以下状态：
- 偏离主题：提示目前推理方向不对
- 绕圈子：提供新的思路
- 尝试不足：鼓励继续探索

## 💡 提示系统

提供四种类型的提示：
- direction：方向性提示
- deviation：偏离提醒
- strategy：策略建议
- default：基础提示

## 🧪 测试

- 手写测试脚本，正在测试中...

## 📝 示例故事

```python
story = Story(
    story_id="test_001",
    title="密室自杀",
    content="一个男人死在了密室里，房间被反锁，没有其他人的痕迹。",
    answer="他自己锁门后自杀了。"
)
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ✨ 致谢

- LangChain 团队
- DeepSeek API 团队
