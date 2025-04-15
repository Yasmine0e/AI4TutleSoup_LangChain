"""
Summary Agent模块，用于定期总结玩家的推理进展
"""
from typing import Dict, Any
from langchain.agents import AgentExecutor
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

class SummaryAgent:
    def __init__(self, llm: ChatOpenAI = None):
        self.llm = llm or ChatOpenAI()
        self.summary_count = 0
        self.summary_interval = 5  # 每5个回合触发一次总结
        
    def should_summarize(self) -> bool:
        """
        判断是否需要触发总结
        """
        self.summary_count += 1
        return self.summary_count >= self.summary_interval
        
    async def generate_summary(self, story: str, brain_chain: str) -> Dict[str, Any]:
        """
        生成推理过程的总结
        
        Args:
            story: 故事背景
            brain_chain: 推理链内容
            
        Returns:
            Dict[str, Any]: 包含总结内容的字典
        """
        # 使用hint_templates.json中的summary模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个推理链总结专家。你需要对玩家的推理过程进行简明扼要的总结。"),
            ("human", "这是故事背景：\n{story}\n\n玩家的推理链如下：\n{brain_chain}")
        ])
        
        # 重置计数器
        self.summary_count = 0
        
        # 使用invoke方法调用LLM
        response = await self.llm.invoke(
            prompt.invoke({
                "story": story,
                "brain_chain": brain_chain
            })
        )
        
        return {
            "hint_text": response.content,  # 使用.content获取响应内容
            "confidence": 0.9,
            "hint_type": "summary",
            "reason": "定期总结已发现的关键线索"
        } 