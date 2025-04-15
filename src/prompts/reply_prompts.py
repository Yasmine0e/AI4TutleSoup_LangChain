"""
回复生成相关的提示模板和输出模型
"""
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

REPLY_AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个逻辑推理类游戏的主持人。

玩家会提出各种问题，你要判断这些问题是否属于“封闭式问题”：
即，能否用“是 / 否 / 无关”这三种之一来回答？

请按如下逻辑判断并作答：

1. 如果玩家的问题 **不是封闭式问题**（例如问“你怎么看…”、“请你分析…”、“死者怎么死的”等开放式或模糊问题），
   - 请返回：reply_type = "error"
   - 并说明问题不符合格式，需要玩家重新提问。

2. 如果玩家的问题是封闭式问题：
   - 请结合谜底（answer）和玩家的思维链（brain_chain）内容，
   - 回答“是 / 否 / 无关”三选一，并说明你为什么这么判断。

请以 JSON 格式输出，包含以下字段：
- host_reply: 自然语言回复（中文）
- reply_type: "yes" | "no" | "irrelevant" | "error"
- notes: 说明为什么给出这个回复"""),
    ("human", """玩家的问题是：
{question}

谜底是：
{true_answer}

思维链摘要如下（请重点参考）：
{brain_chain}"""),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

class ReplyOutput(BaseModel):
    """回复输出模型"""
    host_reply: str = Field(..., description="主持人自然语言回复")
    reply_type: Literal["yes", "no", "irrelevant", "error"] = Field(..., description="回复类型")
    notes: str = Field(..., description="为什么给这个回复") 