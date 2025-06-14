"""
完整游戏流程测试
"""
import os
import asyncio
import pytest
from typing import Dict, Any

from src.runtime import GameRuntime
from src.context import GameContext, Story
from src.state_schema import GameState
from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv
load_dotenv()
def get_test_llm() -> ChatDeepSeek:
    """
    获取测试用的 LLM 实例
    
Returns:
        ChatDeepseek: 测试用的 LLM 实例
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("请设置 DEEPSEEK_API_KEY 环境变量")
        
    return ChatDeepSeek(
        model="deepseek-chat",
        api_key=api_key,
        api_base="https://api.deepseek.com/v1",
        temperature=0.3,
        max_tokens=2048,
    )

def build_test_context() -> GameContext:
    """
    构建测试用的游戏上下文
    
    Returns:
        GameContext: 测试用的游戏上下文
    """
    story = Story(
        story_id="test_001",
        title="密室自杀",
        content="一个男人死在了密室里，房间被反锁，没有其他人的痕迹。",
        answer="他自己锁门后自杀了。"
    )
    
    return GameContext(
        game_id="test_001",
        story=story,
        hint_templates_path="src/prompts/hint_templates.json"
    )

def print_test_result(title: str, result: Dict[str, Any]):
    """打印测试结果"""
    print(f"\n{title}:")
    print("-" * 50)
    for k, v in result.items():
        print(f"{k}: {v}")
    print("-" * 50)

@pytest.mark.asyncio
async def test_complete_game_flow():
    """测试完整游戏流程"""
    print("\n🎮 开始完整游戏流程测试...")
    
    # 初始化运行时
    llm = get_test_llm()
    context = build_test_context()
    runtime = GameRuntime(llm=llm, context=context)
    controller = runtime.get_controller()
    
    # 测试场景 1: 初始提问
    print("\n📝 测试场景 1: 初始提问")
    result = await controller.process_question(
        question="房间里有打斗痕迹吗？",
        player_action="question"
    )
    print_test_result("提问结果", result)
    
    # 测试场景 2: 继续探索细节
    print("\n📝 测试场景 2: 探索细节")
    result = await controller.process_question(
        question="死者身上有伤痕吗？",
        player_action="question"
    )
    print_test_result("提问结果", result)
    
    # 测试场景 3: 请求提示
    print("\n💡 测试场景 3: 请求提示")
    result = await controller.process_question(
        question="我需要一些提示",
        player_action="hint_request"
    )
    print_test_result("提示结果", result)
    
    # 测试场景 4: 根据提示继续提问
    print("\n📝 测试场景 4: 根据提示提问")
    result = await controller.process_question(
        question="房间是从内部锁住的吗？",
        player_action="question"
    )
    print_test_result("提问结果", result)
    
    # 测试场景 5: 提交答案
    print("\n✅ 测试场景 5: 提交答案")
    result = await controller.process_question(
        question="我要提交答案：这个男人是自己锁门后自杀的。",
        player_action="submit_answer",
        current_answer="这个男人是自己锁门后自杀的。"
    )
    print_test_result("判题结果", result)

async def main():
    """主函数"""
    try:
        await test_complete_game_flow()
        print("\n✨ 所有测试完成!")
    except Exception as e:
        print(f"\n❌ 测试过程出错: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 