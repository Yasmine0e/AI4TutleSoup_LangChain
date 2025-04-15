"""思维链分析 Agent"""
from typing import Dict, Any
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_deepseek import ChatDeepSeek
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.memory.brainchain import BrainChainMemory
from src.prompts.agent_prompts import ANALYSIS_AGENT_PROMPT
import logging

logger = logging.getLogger(__name__)

class AnalysisAgent:
    """
    负责分析思维链内容，包括:
    1. 分析思维链的完整性
    2. 评估思维质量
    3. 生成分析报告
    """
    
    def __init__(self, llm: ChatDeepSeek, memory: BrainChainMemory):
        """
        初始化分析 Agent
        
        Args:
            llm: LLM 实例
            memory: BrainChainMemory 实例
        """
        # 创建 prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", ANALYSIS_AGENT_PROMPT),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        self.memory = memory
        # 创建 functions agent
        agent = create_openai_functions_agent(llm, tools=[], prompt=prompt)
        
        # 包装进 AgentExecutor
        self.executor = AgentExecutor(
            agent=agent,
            tools=[],
            memory=self.memory,
            verbose=True
        )
        
    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行分析 Agent
        
        Args:
            inputs: 输入状态字典
            
        Returns:
            Dict[str, Any]: 包含以下字段:
                - analysis_note: 分析说明
                - path_similarity: 相似度分数 (0-1)
        """
        # 转换输入格式以匹配 prompt 模板
        self.memory.action_type = "inference"
        current_chain_id = self.executor.memory.current_chain_id
        current_chain = self.executor.memory.brainchains[current_chain_id]
        agent_inputs = {
            "current_chain": current_chain,
        }
        
        # 执行分析，结果会自动写入 memory
        result = await self.executor.ainvoke(agent_inputs)
        
        return {
            "analysis_note": result.get("analysis_note", ""),
            "path_similarity": result.get("path_similarity", 0.0)
        } 