"""
独立的工作流定义模块 - 支持LangGraph Studio
"""
from typing import Dict, Any
import logging
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.state_schema import GameState

logger = logging.getLogger(__name__)

class WorkflowNodes:
    """工作流节点类 - 组织所有节点函数 🎯"""
    
    def __init__(
        self,
        reply_agent=None,
        structure_agent=None,
        analysis_agent=None,
        detection_agent=None,
        hint_tool=None,
        stuck_detector=None,
    ):
        """初始化节点处理器"""
        self.reply_agent = reply_agent
        self.structure_agent = structure_agent
        self.analysis_agent = analysis_agent
        self.detection_agent = detection_agent
        self.hint_tool = hint_tool
        self.stuck_detector = stuck_detector

    async def reply_generation_node(self, state: GameState) -> Dict[str, Any]:
        """回复生成节点 🎯"""

        try:
            result = await self.reply_agent.run(state)
            return {
                "current_host_reply": result["current_host_reply"],
                "current_reply_type": result["current_reply_type"],
                "current_reply_notes": result["current_reply_notes"],
                "current_reply_invalid": result["current_reply_invalid"]
            }
        except Exception as e:
            logger.error(f"回复生成失败: {str(e)}")
            

    async def structure_analysis_node(self, state: GameState) -> Dict[str, Any]:
        """结构分析节点 🧠"""

            
        try:
            result = await self.structure_agent.run(state)
            return {
                "current_chain_id": result["chain_id"],
                "current_node_id": result["node_id"],
            }
        except Exception as e:
            logger.error(f"结构分析失败: {str(e)}")
            

    async def analysis_node(self, state: GameState) -> Dict[str, Any]:
        """思维链分析节点 🔍"""
    
        try:
            result = await self.analysis_agent.run(state)
            return {
                "analysis_note": result["analysis_note"],
                "path_similarity": result["path_similarity"]
            }
        except Exception as e:
            logger.error(f"思维链分析失败: {str(e)}")
            

    async def detection_node(self, state: GameState) -> Dict[str, Any]:
        """状态检测节点 🕵️"""

        try:
            result = await self.detection_agent.run(state)
            return {
                "is_deviated": result["is_deviated"],
                "is_looping": result["is_looping"],
                "hint": result["hint"]
            }
        except Exception as e:
            logger.error(f"状态检测失败: {str(e)}")
            

    async def detect_stuck_node(self, state: GameState) -> Dict[str, Any]:
        """卡住检测节点 🚫"""

        try:
            result = await self.stuck_detector.run(state)
            return {"is_stuck": result["is_stuck"]}
        except Exception as e:
            logger.error(f"卡住检测失败: {str(e)}")
            return {"is_stuck": False}

    async def hint_generation_node(self, state: GameState) -> Dict[str, Any]:
        """生成提示节点 💡"""
        return {
            "hint_result": {
                "hint_text": "你可以从时间点入手，看看案发时每个人在哪里？",
                "hint_type": "default"
            }
        }

    async def judge_answer_node(self, state: GameState) -> Dict[str, Any]:
        """判断答案节点 ⚖️"""
        return {
            "answer_result": {
                "is_correct": True,
                "explanation": "你说对了！🎉"
            }
        }

    async def answer_analysis_node(self, state: GameState) -> Dict[str, Any]:
        """分析答案节点 📊"""
        return {
            "analysis_note": "你能推到这个答案，说明你推理路径上有一定逻辑关联。"
        }

    async def output_result_node(self, state: GameState) -> Dict[str, Any]:
        """输出结果节点 🎉"""
        return {
            "final_score": 90,
            "message": "回答得不错，你通过较少提示完成了推理~"
        }

    async def reveal_answer_node(self, state: GameState) -> Dict[str, Any]:
        """显示答案节点 📖"""
        answer = "答案未知"
        return {
            "answer_result": {
                "is_correct": False,
                "explanation": "这是标准答案，不计入评分",
                "revealed_answer": answer
            }
        }

    def check_detection_result(self, state: GameState) -> str:
        """
        检查检测结果，决定下一步流向 🔍
        
        Args:
            state: 游戏状态
            
        Returns:
            str: 下一个节点的标识
        """
        if state.is_stuck:
            return "stuck"
        elif state.hint_text:
            return "hint"
        elif state.current_answer:
            return "answer"
        else:
            return "continue"
    
    async def get_player_action_node(self, state: GameState) -> Dict[str, Any]:
        """获取玩家动作节点 🔍"""
        user_action = await input("请输入(question/hint_request/answer_request/submit_answer): ")
        
        return {
            "player_action": user_action
        }
    
    async def give_hint_node(self, state: GameState) -> Dict[str, Any]:
        """给出提示节点 🔍"""
        response = AIMessage(content=state.hint)
        return {    
            "messages": [response]
        }

# Studio兼容的工厂函数 🎨
def build_graph(config: dict = None) -> StateGraph:
    """
    构建游戏流程图 🏗️ (LangGraph Studio兼容版本)
    
    Args:
        config: 运行时配置 (LangGraph Studio会传入这个参数)
         
    Returns:
        StateGraph: 游戏流程图
    """
    # 导入Mock组件
    from src.mock_data import (
        MockReplyAgent, 
        MockStructureAgent, 
        MockAnalysisAgent, 
        MockDetectionAgent, 
        MockStuckDetector, 
        MockHintTool
    )
    
    # 创建Mock实例
    mock_reply_agent = MockReplyAgent()
    mock_structure_agent = MockStructureAgent()
    mock_analysis_agent = MockAnalysisAgent()
    mock_detection_agent = MockDetectionAgent()
    mock_stuck_detector = MockStuckDetector()
    hint_tool = MockHintTool()
    
    # 把内部构建函数直接写进来
    # 创建节点处理器
    nodes = WorkflowNodes(
        reply_agent=mock_reply_agent,
        structure_agent=mock_structure_agent,
        analysis_agent=mock_analysis_agent,
        detection_agent=mock_detection_agent,
        hint_tool=hint_tool,
        stuck_detector=mock_stuck_detector,
    )
    
    # 创建流程图
    graph = StateGraph(GameState)
    
    # 添加节点 - 使用类方法
    graph.add_node("start", START)
    graph.add_node("end", END)
    graph.add_node("Get_player_action", nodes.get_player_action_node)
    graph.add_node("reply_generation", nodes.reply_generation_node)
    graph.add_node("structure_analysis", nodes.structure_analysis_node)
    graph.add_node("analysis", nodes.analysis_node)
    graph.add_node("detection", nodes.detection_node)
    graph.add_node("reveal_answer", nodes.reveal_answer_node)
    graph.add_node("judge_answer", nodes.judge_answer_node)
    graph.add_node("answer_analysis", nodes.answer_analysis_node)
    graph.add_node("output_result", nodes.output_result_node)
    graph.add_node("hint_generation", nodes.hint_generation_node)
    graph.add_node("Give_hint", nodes.give_hint_node)
    
    graph.add_edge(START, "Get_player_action")
    
    # 玩家行为路由
    graph.add_conditional_edges(
        "Get_player_action",
        nodes.get_player_action_node,
        {
            "question": "reply_generation",
            "hint_request": "hint_generation",
            "answer_request": "show_answer",
            "submit_answer": "judge_answer"
        }
    )

    #问答子图
    graph.add_edge("reply_generation", "structure_analysis")
    graph.add_edge("structure_analysis", "analysis")
    graph.add_edge("analysis", "detection")
    graph.add_conditional_edges(
        "detection",
        nodes.check_detection_result,
        {
            "is_stuck": "hint_generation",
            "not_stuck": "Get_player_action"
        }
    )
    
    # 求提示子图
    graph.add_edge("hint_generation", "Give_hint")
    graph.add_edge("Give_hint", "Get_player_action")

    # 判断答案子图
    graph.add_edge("judge_answer", "answer_analysis")
    graph.add_edge("answer_analysis", "output_result")
    graph.add_edge("output_result", END)

    # 显示答案子图
    graph.add_edge("show_answer", END)

    return graph.compile()
