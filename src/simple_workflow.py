"""
简化的工作流用于测试LangGraph Studio显示
"""
from typing import Dict, Any, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


# 使用LangGraph标准的消息状态格式
class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


def chatbot(state: State) -> Dict[str, Any]:
    """聊天机器人节点"""
    return {
        "messages": [AIMessage(content="你好！欢迎来到海龟汤游戏！🐢 请问你想问什么？")]
    }


def analyzer(state: State) -> Dict[str, Any]:
    """分析节点"""
    return {
        "messages": [AIMessage(content="正在分析你的问题... 🔍 让我想想...")]
    }


def responder(state: State) -> Dict[str, Any]:
    """回复节点"""
    return {
        "messages": [AIMessage(content="基于你的问题，我的回答是：是的/不是/这个问题与关键情节无关。🎯")]
    }


def build_graph(config: dict = None) -> StateGraph:
    """
    构建简化的游戏流程图 🏗️
    
    Args:
        config: 运行时配置
         
    Returns:
        StateGraph: 简化的游戏流程图
    """
    # 创建流程图，使用标准State格式
    graph = StateGraph(State)
    
    # 添加节点
    graph.add_node("chatbot", chatbot)
    graph.add_node("analyzer", analyzer)
    graph.add_node("responder", responder)
    
    # 设置边
    graph.add_edge(START, "chatbot")
    graph.add_edge("chatbot", "analyzer")
    graph.add_edge("analyzer", "responder")
    graph.add_edge("responder", END)
    
    return graph.compile() 