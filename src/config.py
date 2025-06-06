from typing import Dict, Any
from pathlib import Path
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 游戏配置
GAME_CONFIG = {
    "max_turns": 20,  # 最大回合数
    "confidence_threshold": 0.7,  # 置信度阈值
    "story_dir": Path(__file__).parent / "stories",  # 故事目录
    "log_dir": Path(__file__).parent / "logs",  # 日志目录
}

# LLM 配置
LLM_CONFIG = {
    "model_name": "deepseek-chat",  # DeepSeek 模型名称
    "temperature": 0.7,
    "max_tokens": 1000,
    "api_key": os.getenv("DEEPSEEK_API_KEY"),  
    "api_base": "https://api.deepseek.com/v1",  # DeepSeek API 基础URL
}

# 提示配置
PROMPT_CONFIG = {
    "welcome_message": "欢迎来到海龟汤游戏！\n我会给你一个故事，你需要通过提问来找出故事的真相。\n你可以：\n1. 提问（例如：'这个人是不是死了？'）\n2. 请求提示（输入：'hint'）\n3. 尝试回答（输入：'answer: 你的答案'）\n\n准备好了吗？让我们开始吧！",
    "game_over_message": "游戏结束！\n正确答案是：{answer}\n\n你的表现：\n- 总回合数：{turns}\n- 提问数量：{questions}\n- 提示次数：{hints}\n\n感谢参与！",
    "error_message": "抱歉，发生了错误：{error}\n请重试或输入 'quit' 退出游戏。",
}

# 故事配置
STORY_CONFIG = {
    "default_story": {
        "id": "story_001",
        "title": "消失的乘客",
        "text": "一个男人上了公交车，车上有很多空位。他选择了一个座位坐下，但很快就下车了。为什么？",
        "answer": "这个男人是公交车司机，他下班了。"
    }
} 