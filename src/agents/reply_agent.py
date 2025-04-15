"""
回复生成Agent模块
"""
from typing import Dict, Any, Union, Optional
import logging
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.output_parsers import PydanticOutputParser
from langchain_core.messages import BaseMessage
from src.memory.brainchain import BrainChainMemory
from src.prompts.reply_prompts import REPLY_AGENT_PROMPT, ReplyOutput

logger = logging.getLogger(__name__)

class ReplyAgent:
    """负责生成对玩家问题的回复"""
    
    def __init__(self, llm: ChatOpenAI, memory: BrainChainMemory):
        """
        初始化ReplyAgent
        
        Args:
            llm: LLM模型
            memory: 思维链记忆
        """
        self.llm = llm
        self.memory = memory
        self.memory.brainchains = memory.brainchains
        self.memory.current_chain_id = memory.current_chain_id
        self.output_parser = PydanticOutputParser(pydantic_object=ReplyOutput)
        
        # 创建 agent
        self.agent = create_openai_functions_agent(
            llm=llm,
            tools=[],  # 无工具调用
            prompt=REPLY_AGENT_PROMPT
        )
        

        # 创建executor
        self.executor = AgentExecutor.from_agent_and_tools(
            self.agent,
            tools=[],
            memory=self.memory,
            verbose=True
        )
        
    async def _arun(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行回复生成
        
        Args:
            inputs: 输入状态字典
            
        Returns:
            Dict[str, Any]: 包含以下字段：
                - current_host_reply: 主持人回复
                - current_reply_type: 回复类型
                - current_reply_notes: 回复说明
                - reply_invalid: 是否无效回复
        """
        try:
            self.memory.action_type = "no_action"
            # 准备输入
            brain_chain = self.memory.load_memory_variables({})
            
            # 转换输入格式以匹配 prompt 模板
            agent_inputs = {
                "question": inputs.get("current_question", ""),
                "true_answer": inputs.get("true_answer", ""),
                "brain_chain": inputs.get("current_brainchain") or brain_chain.get("brain_chain", "")
            }
            
            # 调用agent生成回复
            result = await self.executor.ainvoke(agent_inputs)
            
            # 尝试从不同可能的结构中获取输出内容
            content = (
                result if isinstance(result, str)
                else result.get("output", result.get("content", str(result)))
            )
            
            # 解析输出
            reply = self.output_parser.parse(content)
            
            # 返回结果
            return {
                "current_host_reply": reply.host_reply,
                "current_reply_type": reply.reply_type,
                "current_reply_notes": reply.notes,
                "reply_invalid": reply.reply_type == "error"
            }
            
        except Exception as e:
            logger.error("[ReplyAgent] 处理失败: %s", str(e))
            
            # 返回错误状态
            return {
                "current_host_reply": "抱歉，我现在无法理解这个问题，请重新提问",
                "current_reply_type": "error",
                "current_reply_notes": f"解析回复时出错：{str(e)}",
                "reply_invalid": True
            } 