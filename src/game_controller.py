"""
游戏流程控制模块
"""
from typing import Dict, Any, Optional
import logging
from langgraph.graph import StateGraph, END, START
from pydantic import BaseModel
from langchain_core.tools import BaseTool
from langchain.schema.runnable import RunnableLambda
from src.tools.detection_tools import DetectStuckTool
from src.state_schema import GameState
from src.agents.reply_agent import ReplyAgent
from src.agents.structure_agent import StructureAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.detection_agent import DetectionAgent
from src.tools.hint_generator import HintGenerator
from src.context import GameContext
from src.utils.state_utils import with_state_update

logger = logging.getLogger(__name__)

class GameController:
    """游戏流程控制器"""
    
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
        
        # 构建流程图
        self.graph = self.build_graph()
    
    async def reply_generation_node(self, state: GameState) -> Dict[str, Any]:
        """
        回复生成节点
        
        Args:
            state: 游戏状态
            
        Returns:
            Dict[str, Any]: 回复生成结果
        """
        try:
            result = await self.reply_agent._arun(state.model_dump())
            return {
                "current_host_reply": result["current_host_reply"],
                "current_reply_type": result["current_reply_type"],
                "current_reply_notes": result["current_reply_notes"],
                "reply_invalid": result["reply_invalid"]
            }
        except Exception as e:
            logger.error(f"回复生成失败: {str(e)}")
            return {
                "current_host_reply": "抱歉，我现在无法理解这个问题，请重新提问",
                "current_reply_type": "error",
                "current_reply_notes": f"生成回复时出错：{str(e)}",
                "reply_invalid": True
            }
        
    async def structure_analysis_node(self, state: GameState) -> Dict[str, Any]:
        """
        结构分析节点
        
        Args:
            state: 游戏状态
            
        Returns:
            Dict[str, Any]: 结构分析结果
        """
        try:
            result = await self.structure_agent._arun(state.model_dump())
            return {
                "current_chain_id": result["chain_id"],
                "current_node_id": result["node_id"],

            }
        except Exception as e:
            logger.error(f"结构分析失败: {str(e)}")
            return {
                "chain_id": state.current_chain_id,
                "node_id": state.current_node_id,
                "timestamp": state.timestamp,
                "is_revisit": False
            }

    async def analysis_node(self, state: GameState) -> Dict[str, Any]:
        """
        思维链分析节点
        
        Args:
            state: 游戏状态
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            result = await self.analysis_agent.run(state.model_dump())
            return {
                "analysis_note": result["analysis_note"],
                "path_similarity": result["path_similarity"]
            }
        except Exception as e:
            logger.error(f"思维链分析失败: {str(e)}")
            return {
                "analysis_note": f"分析失败：{str(e)}",
                "path_similarity": 0.0
            }

    async def detection_node(self, state: GameState) -> Dict[str, Any]:
        """
        状态检测节点
        
        Args:
            state: 游戏状态
            
        Returns:
            Dict[str, Any]: 检测结果
        """
        try:
            result = await self.detection_agent.run(state.model_dump())
            print(f"状态检测结果: {result}")
            return {
                "is_deviated": result["is_deviated"],
                "is_looping": result["is_looping"],
                "hint": result["hint"]
            }
        except Exception as e:
            logger.error(f"状态检测失败: {str(e)}")
            return {
                "is_deviated": False,
                "is_looping": False,
                "hint": "状态检测失败，请继续游戏"
            }

    async def detect_stuck(self, state: GameState) -> Dict[str, Any]:
        """
        卡住检测节点
        
        Args:
            state: 游戏状态
            
        Returns:
            Dict[str, Any]: 检测结果，包含 is_stuck 字段
        """
        try:
            result = await self.stuck_detector._arun(**state.model_dump())
            logger.info(f"卡住检测结果: {result}")
            return {
                "is_stuck": result["is_stuck"]
            }
        except Exception as e:
            self.logger.error(f"卡住检测失败: {str(e)}")
            return {
                "is_stuck": False
            }

    async def reveal_answer(self, state: GameState) -> Dict[str, Any]:
        """显示标准答案"""
        return {
            "answer_result": {
                "is_correct": False,
                "explanation": "这是标准答案，不计入评分",
                "revealed_answer": self.context.answer
            }
        }
    
    async def judge_answer(self, state: GameState) -> Dict[str, Any]:
        """判断玩家答案"""
        # 简化版：字符串完全匹配判断
        is_correct = state.current_answer.strip() == self.context.answer.strip()
        return {
            "answer_result": {
                "is_correct": is_correct,
                "explanation": "你说对了！" if is_correct else "不太对，再想想~"
            }
        }
    
    async def answer_analysis(self, state: GameState) -> Dict[str, Any]:
        """分析玩家答案"""
        return {
            "analysis_note": "你能推到这个答案，说明你推理路径上有一定逻辑关联。"
        }
    
    async def output_result(self, state: GameState) -> Dict[str, Any]:
        """输出最终结果"""
        return {
            "final_score": 90,
            "message": "回答得不错，你通过较少提示完成了推理~"
        }
    
    async def hint_generation(self, state: GameState) -> Dict[str, Any]:
        """生成提示"""
        return {
            "hint_result": {
                "hint_text": "你可以从时间点入手，看看案发时每个人在哪里？",
                "hint_type": "default"
            }
        }
    
    async def request_hint(self, state: GameState) -> Dict[str, Any]:
        """请求提示"""
        return {
            "hint_result": {
                "hint_text": "你可以从时间点入手，看看案发时每个人在哪里？",
                "hint_type": "default"
            }
        }

    def build_graph(self) -> StateGraph:
        """
        构建游戏流程图
        
        Returns:
            StateGraph: LangGraph 流程图
        """
        # 创建工作流
        workflow = StateGraph(GameState)
        
        # 注册节点
        workflow.add_node("stuck_detection", RunnableLambda(self.detect_stuck))
        workflow.add_node("structure_analysis", RunnableLambda(self.structure_analysis_node))
        workflow.add_node("reply_generation", RunnableLambda(self.reply_generation_node))
        workflow.add_node('request_hint', RunnableLambda(self.request_hint))
        workflow.add_node("hint_generation", RunnableLambda(self.hint_generation))
        workflow.add_node("analysis", RunnableLambda(self.analysis_node))
        workflow.add_node("detection", RunnableLambda(self.detection_node))
        workflow.add_node("reveal_answer", RunnableLambda(self.reveal_answer))
        workflow.add_node("judge_answer", RunnableLambda(self.judge_answer))
        workflow.add_node("answer_analysis", RunnableLambda(self.answer_analysis))
        workflow.add_node("output_result", RunnableLambda(self.output_result))
        
        # 设置条件路由
        def route_by_action(state: GameState) -> str:
            """根据玩家动作选择路径"""
            if state.player_action == "hint_request":
                return "request_hint"
            elif state.player_action == "answer_request":
                return "reveal_answer"
            elif state.player_action == "submit_answer":
                return "judge_answer"
            else:
                return "stuck_detection"
                
        def check_detection_result(state: GameState) -> str:
            """检查检测结果决定下一步"""
            if state.is_stuck:
                return "hint_generation"
            elif state.is_looping:
                return "hint_generation"
            elif state.is_deviated:
                return "hint_generation"
            else:
                return "reply_generation"
                
        # 设置入口点
        workflow.add_conditional_edges(
            START,
            route_by_action,
            {
                "request_hint": "request_hint",
                "reveal_answer": "reveal_answer",
                "judge_answer": "judge_answer",
                "stuck_detection": "stuck_detection"
            }
        )
        
        # 设置其他边
        workflow.add_conditional_edges(
            "stuck_detection",
            check_detection_result,
            {
                "hint_generation": "hint_generation",
                "reply_generation": "reply_generation"
            }
        )
        
        # 设置基本流程边
        workflow.add_edge("hint_generation", "reply_generation")
        workflow.add_edge("reply_generation", "structure_analysis")
        workflow.add_edge("structure_analysis", "analysis")
        workflow.add_edge("analysis", "detection")
        workflow.add_edge("detection", END)
        
        # 设置提示请求路径
        workflow.add_edge("request_hint", END)
        
        # 设置答案相关路径
        workflow.add_edge("reveal_answer", END)
        workflow.add_edge("judge_answer", "answer_analysis")
        workflow.add_edge("answer_analysis", "output_result")
        workflow.add_edge("output_result", END)
        
        # 编译工作流
        return workflow.compile()
        
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