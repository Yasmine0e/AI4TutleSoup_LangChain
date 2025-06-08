"""
游戏运行时环境，负责初始化和管理所有 Agent 和工具
"""
from typing import Dict, Any, Optional
from langchain_deepseek import ChatDeepSeek
from langchain_core.memory import BaseMemory

from src.agents.reply_agent import ReplyAgent
from src.agents.structure_agent import StructureAgent 
from src.agents.analysis_agent import AnalysisAgent
from src.agents.detection_agent import DetectionAgent
from src.tools.hint_generator import HintGenerator
from src.tools.detection_tools import DetectStuckTool
from src.context import GameContext
from src.game_controller import GameController
from src.memory.brainchain import BrainChainMemory
from src.memory.brainchain import BrainChain
class GameRuntime:
    """游戏运行时环境"""
    
    def __init__(
        self,
        llm: ChatDeepSeek,
        context: GameContext,
        memory_config: Optional[dict] = None
    ):
        """
        初始化游戏运行时环境
        
        Args:
            llm: LLM模型
            context: 游戏上下文
            memory_config: 可选的记忆配置
        """
        # 初始化记忆系统
        self.memory_config = memory_config or {}

        self.brain_chain = context.brain_chain
        self.brain_chain.brainchains = {"main": BrainChain()}
        self.brain_chain.current_chain_id = "main"
        # 初始化工具
        self.hint_tool = HintGenerator(llm=llm)
        self.stuck_detector = DetectStuckTool(llm=llm)
        
        # 初始化 Agents
        self.reply_agent = ReplyAgent(llm=llm, memory=self.brain_chain)
        self.structure_agent = StructureAgent(llm=llm, memory=self.brain_chain)
        self.analysis_agent = AnalysisAgent(llm=llm, memory=self.brain_chain)
        self.detection_agent = DetectionAgent(llm=llm, memory=self.brain_chain, context=context)
        
        # 初始化控制器
        self.controller = GameController(
            reply_agent=self.reply_agent,
            structure_agent=self.structure_agent,
            analysis_agent=self.analysis_agent,
            detection_agent=self.detection_agent,
            hint_tool=self.hint_tool,
            stuck_detector=self.stuck_detector,
            context=context
        )
        
        # 流程图已经在controller中构建完成
        self.graph = self.controller.graph
    
    def get_controller(self) -> GameController:
        """
        获取游戏控制器
        
        Returns:
            GameController: 游戏控制器实例
        """
        return self.controller 