""" 测试 LLM 配置是否正确 (已通过)"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


import pytest
from langchain_deepseek import ChatDeepSeek
from src.config import LLM_CONFIG

def test_llm_config():
    """测试 LLM 配置是否正确"""
    # 检查环境变量
    api_key = os.getenv("DEEPSEEK_API_KEY")
    assert api_key is not None, "DEEPSEEK_API_KEY 环境变量未设置"
    assert api_key == LLM_CONFIG["api_key"], "环境变量与配置文件中的 API key 不一致"
    
    # 初始化 LLM
    try:
        llm = ChatDeepSeek(
            model="deepseek-chat",  # 使用 deepseek-chat 模型
            temperature=LLM_CONFIG["temperature"],
            max_tokens=LLM_CONFIG["max_tokens"],
            api_key=api_key,
            api_base=LLM_CONFIG["api_base"],
            timeout=30,  # 设置超时时间
            max_retries=2  # 设置重试次数
        )
        
        # 测试简单对话
        messages = [
            ("system", "你是一个有帮助的助手。"),
            ("human", "你好,请用一句话介绍自己")
        ]
        response = llm.invoke(messages)
        print(f"\n模型回复: {response.content}\n")
        assert isinstance(response.content, str)
        assert len(response.content) > 0
        
        print("✅ LLM 配置测试通过!")
        print(f"- 使用模型: {LLM_CONFIG['model_name']}")
        print(f"- API Base: {LLM_CONFIG['api_base']}")
        print(f"- Temperature: {LLM_CONFIG['temperature']}")
        print(f"- Max Tokens: {LLM_CONFIG['max_tokens']}")
        
    except Exception as e:
        pytest.fail(f"LLM 初始化或调用失败: {str(e)}")

if __name__ == "__main__":
    test_llm_config() 