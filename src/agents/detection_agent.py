"""思维链状态检测 Agent"""
from typing import Dict, Any
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_deepseek import ChatDeepSeek
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.memory.brainchain import BrainChainMemory
from src.prompts.agent_prompts import DETECTION_AGENT_PROMPT
from src.tools.hint_generator import create_hint_tool
from src.context import GameContext
class DetectionAgent:
    """
    负责状态检测，包括:
    1. 检测思维偏离
    2. 检测绕圈状态
    3. 生成提示信息
    """
    
    def __init__(self, llm: ChatDeepSeek, memory: BrainChainMemory, context: GameContext):
        """
        初始化检测 Agent
        
        Args:
            llm: LLM 实例
            memory: BrainChainMemory 实例
        """
        # 创建 prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", DETECTION_AGENT_PROMPT),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # 创建提示工具（无 hint_type，交给 agent 来决定）
        hint_tool = create_hint_tool(llm, context)
        self.memory = memory
        # 创建 functions agent
        agent = create_openai_functions_agent(llm, tools=[hint_tool], prompt=prompt)

        # Executor 包装
        self.executor = AgentExecutor(agent=agent, tools=[hint_tool], memory=self.memory, verbose=True)

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行检测 Agent
        
        Args:
            inputs: 输入状态字典
            
        Returns:
            Dict[str, Any]: 包含检测结果
        """
        # 后期优化可放入相关字段
        self.memory.action_type = "detection"
        agent_inputs = {}
        
        result = await self.executor.ainvoke(agent_inputs)
        return {
            "is_deviated": result.get("is_deviated", False),
            "is_looping": result.get("is_looping", False),
            "hint": result.get("hint", "")
        } 