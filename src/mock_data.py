'''
定义一些模拟agent和tool，跑通图的运转
'''
from src.state_schema import GameState

class MockReplyAgent:
    def __init__(self):
        pass
    
    async def run(self, state: GameState):
        return {
            "current_host_reply": "你好，我是海龟汤游戏助手，请问有什么可以帮你的吗？ 🐢",
            "current_reply_type": "irrelevant",
            "current_reply_notes": "这是一个测试回复",
            "current_reply_invalid": False
        }

class MockStructureAgent:
    def __init__(self):
        pass
    
    async def run(self, state: GameState):
        return {
            "chain_id": "test_chain_001",
            "node_id": "test_node_001"
        }

class MockAnalysisAgent:
    def __init__(self):
        pass
    
    async def run(self, state: GameState):
        return {
            "analysis_note": "这是测试分析注释 📝",
            "path_similarity": 0.8
        }

class MockDetectionAgent:
    def __init__(self):
        pass
    
    async def run(self, state: GameState):
        return {
            "is_deviated": False,
            "is_looping": False,
            "hint": "测试提示信息 💡"
        }

class MockHintTool:
    def __init__(self):
        pass
    
    def run(self, state: GameState):
        return {
            "current_hint_reply": "你好，我是海龟汤游戏助手，请问有什么可以帮你的吗？",
            "current_hint_type": "host",
            "current_hint_notes": "这是一个测试回复",
            "hint_invalid": False
        }

class MockStuckDetector:
    def __init__(self):
        pass
    
    async def run(self, state: GameState):
        return {
            "is_stuck": False  # workflow期待这个字段
        }
