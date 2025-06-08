"""
海龟汤游戏主类模块
"""
from src.workflow import build_graph
import asyncio
from src.state_schema import GameState

async def main():
    graph = build_graph()
    # 提供 GameState 所需的必填字段
    initial_state = GameState(game_id="game_001", player_action="None")
    result = await graph.ainvoke(initial_state.model_dump())  # 传递完整的初始状态
    print(result)

if __name__ == "__main__":
    asyncio.run(main())