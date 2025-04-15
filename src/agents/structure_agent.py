"""结构判断 Agent"""
from typing import Dict, Any
import logging
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_deepseek import ChatDeepSeek
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import StructuredTool
from src.memory.brainchain import BrainChainMemory
from src.prompts.agent_prompts import STRUCTURE_AGENT_PROMPT
from src.tools.structure_tools import GenerateUUIDTool, GetCurrentTimeTool

logger = logging.getLogger(__name__)

class StructureAgent:
    """
    负责结构判断，包括:
    1. 生成必要的结构参数(chain_id, node_id, timestamp等)
    2. 判断是否需要创建新结构
    """
    
    def __init__(self, llm: ChatDeepSeek, memory: BrainChainMemory):
        """
        初始化结构判断 Agent
        
        Args:
            llm: LLM 实例
            memory: BrainChainMemory 实例
        """
        # 初始化工具
        self.memory = memory
        self.tools = [
            StructuredTool.from_function(
                func=GenerateUUIDTool().run,
                name="generate_uuid",
                description="生成 chain_id 和 node_id"
            ),
            StructuredTool.from_function(
                func=GetCurrentTimeTool().run,
                name="get_current_time",
                description="生成 timestamp"
            )
        ]
        
        # 创建 prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", STRUCTURE_AGENT_PROMPT),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # 创建 functions agent
        agent = create_openai_functions_agent(llm, tools=self.tools, prompt=prompt)
        
        # 包装进 AgentExecutor
        self.executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )
        
    async def _arun(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行结构判断 Agent
        
        Args:
            inputs: 输入状态字典
            
        Returns:
            Dict[str, Any]: 包含以下字段:
                - chain_id: 链ID
                - node_id: 节点ID
                - timestamp: 时间戳
                - created_at: 创建时间（仅在非重访时）
                - is_revisit: 是否重访
        """
        # 转换输入格式以匹配 prompt 模板
        self.memory.action_type = "creat_add"
        logger.info(f"结构判断 Agent 输入: {inputs}")
        agent_inputs = {
            "question": inputs.get("current_question", ""),
            "host_reply": inputs.get("current_host_reply", ""),
            "reply_type": inputs.get("current_reply_type", ""),
            "notes": inputs.get("reply_notes", ""),
            "current_brainchain": inputs.get("current_brainchain", ""),
            "current_chain_id": inputs.get("current_chain_id", ""),
            "current_node_id": inputs.get("current_node_id", "")
        }
        
        await self.executor.ainvoke(agent_inputs)
        # 从memroy中取出current_brainchain_id
        current_brainchain_id = self.executor.memory.current_chain_id
        current_node_id = self.executor.memory.current_focus_id
        logger.warning(f"structure_agent 结束，当前脑图: {self.executor.memory.brainchains}")
        # 构建返回结果
        response = {
            "chain_id": current_brainchain_id,
            "node_id": current_node_id,
        }
        
        
            
        return response 