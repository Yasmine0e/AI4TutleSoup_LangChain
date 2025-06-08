from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
import time
from src.memory.brainchain import BrainChainMemory
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated

class GameState(BaseModel):
    """
    LangGraph 流程状态，仅包含当前轮次需要的状态
    """
    # LangGraph Studio 兼容字段
    player_action: Literal["question", "hint_request", "answer_request", "submit_answer","None"] = Field(
    game_id: str = Field(None, description="游戏ID")
    messages: Annotated[list[BaseMessage], add_messages] = []
    # 当前动作
    user_input: Optional[str] = Field(None, description="用户输入")
    current_question: Optional[str] = Field(None, description="当前问题")
    current_answer: Optional[str] = Field(None, description="当前回答")
    current_chain_id: Optional[str] = Field(None, description="当前焦点思维链")
    current_node_id: Optional[str] = Field(None, description="当前焦点节点")
   
    
    timestamp: float = Field(default_factory=time.time, description="流动时间戳")
    # 检测状态
    is_deviated: bool = Field(False, description="是否偏离主题")
    is_looping: bool = Field(False, description="是否在绕圈")
    is_stuck: bool = Field(False, description="是否卡住/尝试不足")
    
    # 回复状态
    current_host_reply: Optional[str] = Field(None, description="主持人回复内容")
    current_reply_type: Optional[Literal["yes", "no", "irrelevant", "error"]] = Field(
        None, 
        description="回复类型"
    )
    current_reply_notes: Optional[str] = Field(None, description="回复解释")
    current_reply_invalid: bool = Field(False, description="回复是否无效")
    current_timestamp: float = Field(default_factory=time.time, description="状态创建时间戳")
    
    # 当前轮次结果
    detection_result: Optional[Dict[str, Any]] = Field(None, description="当前轮次的检测结果")
    hint_result: Optional[Dict[str, Any]] = Field(None, description="当前轮次的提示结果")
    answer_result: Optional[Dict[str, Any]] = Field(None, description="当前轮次的答案判断结果")
    current_brain_context: Optional[str] = Field(None, description="当前轮次的思维链上下文")

    # 分析相关
    analysis_note: Optional[str] = Field(None, description="推理链分析说明")
    path_similarity: Optional[float] = Field(None, description="当前推理链相似度")

    # 提示相关
    hint_text: Optional[str] = Field(None, description="提示内容")
    hint_type: Optional[str] = Field(None, description="提示类型")

    # 谜底
    true_answer: Optional[str] = Field(None, description="谜底")

    def copy_with_updates(self, **updates) -> 'GameState':
        """
        创建状态的副本并更新指定字段
        
        Args:
            **updates: 要更新的字段
            
        Returns:
            GameState: 更新后的新状态
        """
        data = self.dict()
        data.update(updates)
        return GameState(**data)

class GameContext(BaseModel):
    """
    游戏持久化上下文，存储跨轮次的信息
    """
    # 游戏基本信息
    game_id: str = Field(..., description="游戏唯一标识符")
    story_id: str = Field(..., description="当前故事ID")
    story_text: str = Field(..., description="故事文本内容")
    answer: str = Field(..., description="故事答案")
    
    # 历史记录
    question_history: List[str] = Field(default_factory=list, description="问题历史")
    answer_history: List[str] = Field(default_factory=list, description="回答历史")
    hint_history: List[Dict[str, Any]] = Field(default_factory=list, description="提示历史")
    
    # 游戏状态
    turn_count: int = Field(0, description="当前回合数")
    game_over: bool = Field(False, description="游戏是否结束")
    
    # 思维链记忆
    brain_chain: BrainChainMemory = Field(default_factory=BrainChainMemory, description="思维链记忆系统")
    
    def update_from_state(self, state: GameState) -> None:
        """
        从当前轮次状态更新持久化信息
        
        Args:
            state: 当前轮次的状态
        """
        # 更新回合数
        self.turn_count += 1
        
        # 更新历史记录
        if state.current_question:
            self.question_history.append(state.current_question)
        if state.current_answer:
            self.answer_history.append(state.current_answer)
        if state.hint_result:
            self.hint_history.append(state.hint_result)
            
        # 更新游戏结束状态
        if state.answer_result and state.answer_result.get("is_correct"):
            self.game_over = True