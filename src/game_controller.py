"""
游戏流程控制模块（简化版）
"""
from typing import Dict, Any, Optional
import logging
from langgraph.graph import StateGraph

from src.state_schema import GameState
from src.agents.reply_agent import ReplyAgent
from src.agents.structure_agent import StructureAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.detection_agent import DetectionAgent
from src.tools.hint_generator import HintGenerator
from src.tools.detection_tools import DetectStuckTool
from src.context import GameContext
from src.workflow import build_graph

logger = logging.getLogger(__name__)

class GameController:
    """游戏流程控制器（简化版）"""
    
    def __init__(
        self,
        reply_agent: ReplyAgent,
        structure_agent: StructureAgent,
        analysis_agent: AnalysisAgent,
        detection_agent: DetectionAgent,
        hint_tool: HintGenerator,
        stuck_detector: DetectStuckTool,
        context: GameContext
    ):
        """
        初始化控制器
        
        Args:
            reply_agent: 回复生成 Agent
            structure_agent: 结构分析 Agent
            analysis_agent: 推理分析 Agent
            detection_agent: 状态检测 Agent
            hint_tool: 提示生成工具
            stuck_detector: 卡住检测器
            context: 游戏上下文
        """
        self.reply_agent = reply_agent
        self.structure_agent = structure_agent
        self.analysis_agent = analysis_agent
        self.detection_agent = detection_agent
        self.hint_tool = hint_tool
        self.stuck_detector = stuck_detector
        self.context = context
        self.logger = logger
        
        # 构建流程图，直接传递依赖
        self.graph = build_graph(
            reply_agent=reply_agent,
            structure_agent=structure_agent,
            analysis_agent=analysis_agent,
            detection_agent=detection_agent,
            hint_tool=hint_tool,
            stuck_detector=stuck_detector,
            context=context
        )
    

    async def process_question(self, question: str, player_action: str = "question", current_answer: str = None) -> Dict[str, Any]:
        """
        处理玩家问题
        
        Args:
            question: 玩家问题
            player_action: 玩家动作类型，默认为"question"
            current_answer: 当提交答案时的答案内容
            
        Returns:
            Dict[str, Any]: 处理结果状态
        """
        # 创建初始状态
        initial_state = GameState(
            player_action=player_action,
            current_question=question,
            current_answer=current_answer,
            true_answer=self.context.answer
        )
        
        # 运行工作流
        try:
            result = await self.graph.ainvoke(
                initial_state.model_dump()
            )
            return result
        except Exception as e:
            self.logger.error("处理问题时出错: %s", str(e))
            raise 