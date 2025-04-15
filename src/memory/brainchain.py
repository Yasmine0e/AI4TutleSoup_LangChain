from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.memory import BaseMemory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import time
import uuid
import logging
import json
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class BrainNode(BaseModel):
    """思维链节点"""
    id: str = Field(..., description="节点唯一标识符")
    content: str = Field(..., description="节点内容")
    timestamp: float = Field(..., description="节点创建时间戳")
    parent_id: Optional[str] = Field(None, description="父节点ID")
    host_reply: str = Field("", description="主持人回复")
    reply_type: str = Field("irrelevant", description="回复类型")
    notes: str = Field("", description="备注信息")

    class Config:
        arbitrary_types_allowed = True

class BrainChain(BaseModel):
    """思维链"""
    chain_id: Optional[str] = Field(None, description="思维链唯一标识符")
    nodes: Dict[str, BrainNode] = Field(default_factory=dict, description="节点存储")
    root_node_id: Optional[str] = Field(None, description="根节点ID")
    current_focus_id: Optional[str] = Field(None, description="当前焦点节点ID")
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "created_at": time.time(), #创建时间
            "last_used_at": time.time(), #最后使用时间  
            "revisit_count": 0, #当前思维链被回溯的次数
            "analysis_note": "", #当前思维链的分析说明
            "path_similarity": 0.0 #当前思维链与谜底的关联度
        },
        description="思维链元数据"
    )

    def add_node(self, node_data: Dict[str, Any]) -> BrainNode:
        """添加节点
        
        Args:
            node_data: 节点数据字典
            
        Returns:
            BrainNode: 创建的节点实例
        """
        # 创建 BrainNode 实例
        node = BrainNode(**node_data)
        
        # 添加到节点集合
        self.nodes[node.id] = node
        self.current_focus_id = node.id
        
        return node

    def get_focus_path(self) -> List[BrainNode]:
        """获取所有节点，按时间戳排序"""
        return sorted(self.nodes.values(), key=lambda x: x.timestamp)

class BrainChainMemory(BaseMemory):
    """
    思维链记忆类，用于管理游戏中的思维链结构
    继承 BaseMemory 以便与 LangChain 生态集成
    """
    memory_key: str = "brain_chain"
    brainchains: Dict[str, BrainChain] = {}
    current_chain_id: Optional[str] = None
    current_focus_id: Optional[str] = None
    action_type: Literal["creat_add", "inference", "no_action"] = "no_action"
    
    def __init__(self, **kwargs):
        super().__init__()
        self._via_agent_tool = False
        self.memory_key = kwargs.get("memory_key", "brain_chain")
        self.brainchains = kwargs.get("brainchains", {})
        self.current_chain_id = kwargs.get("current_chain_id", None)
        self.current_focus_id = kwargs.get("current_focus_id", None)
        
    def summarize_brainchains(self) -> str:
        """
        生成所有思维链的结构化摘要
        
        Returns:
            str: 格式化的思维链摘要
        """
        lines = []
        
        for chain_id, chain in self.brainchains.items():
            meta = chain.metadata
            lines.append(f"🔮 思维链 {chain_id}")
            lines.append(f"  - 创建时间: {meta.get('created_at')}")
            lines.append(f"  - 最近使用: {meta.get('last_used_at')}")
            lines.append(f"  - 被访问次数: {meta.get('revisit_count')}")
            lines.append(f"  - 相似性分数: {meta.get('path_similarity')}")
            lines.append(f"  - 根节点 ID: {chain.root_node_id}")
            
            path = chain.get_focus_path()
            lines.append(f"  - 焦点路径长度: {len(path)}")
            lines.append("  - 节点路径:")
            
            for depth, node in enumerate(path):
                indent = "    " * (depth + 1)
                lines.append(f"{indent}🔸 {node.content} ({node.id})")
                lines.append(f"{indent}↳ 回复类型: {node.reply_type}")
                if node.host_reply:
                    lines.append(f"{indent}↳ 回答内容: {node.host_reply}")
                if node.notes:
                    lines.append(f"{indent}↳ 备注: {node.notes}")
                    
            lines.append("")  # 每条链之间空行分隔
            
        return "\n".join(lines)
    
    def create_chain(self) -> str:
        """
        创建新的思维链
        
        Returns:
            str: 新思维链ID
        """
        chain_id = str(uuid.uuid4())
        self.brainchains[chain_id] = BrainChain(chain_id=chain_id)
        self.current_chain_id = chain_id
        return chain_id
    
    def get_chain(self, chain_id: Optional[str] = None) -> Optional[BrainChain]:
        """
        获取思维链实例
        
        Args:
            chain_id: 思维链ID，如果为None则返回当前活动思维链
            
        Returns:
            Optional[BrainChain]: 思维链实例
        """
        target_id = chain_id or self.current_chain_id
        return self.brainchains.get(target_id)
    
    def add_node(
        self,
        content: str,
        chain_id: str,
        host_reply: str,
        reply_type: str,
        notes: str,
        parent_id: Optional[str] = None,
    ) -> str:
        """
        向指定的思维链中添加新节点
        
        Args:
            content: 节点内容
            chain_id: 思维链ID
            parent_id: 父节点ID，如果为 None 则作为根节点
            host_reply: 主持人回复内容
            reply_type: 回复类型
            notes: 节点备注
            via_tool: 是否通过工具添加
            
        Returns:
            新节点的ID
        """
            
        if chain_id not in self.brainchains:
            raise ValueError(f"思维链 {chain_id} 不存在")
            
        chain = self.brainchains[chain_id]
        node_id = str(uuid.uuid4())
        timestamp = time.time()
        
        node_data = {
            "id": node_id,
            "content": content,
            "timestamp": timestamp,
            "parent_id": parent_id,
            "host_reply": host_reply,
            "reply_type": reply_type,
            "notes": notes
        }
        
        node = chain.add_node(node_data)
        self.current_focus_id = node_id
        logger.warning(f"添加节点 {node_id} 到思维链 {chain_id}")
        return node_id
    
    @property
    def memory_variables(self) -> List[str]:
        """实现 BaseMemory 接口，返回记忆变量列表"""
        return [self.memory_key]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        加载所有思维链的完整内容
        
        Args:
            inputs: 输入参数字典
            
        Returns:
            Dict[str, str]: 包含所有思维链内容的字典
        """
        return {
            self.memory_key: self.summarize_brainchains()
        }

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """
        实现 BaseMemory 接口，保存上下文
        
        Args:
            inputs: 输入参数字典，包含玩家问题
            outputs: 输出参数字典，包含主持人回答
        """
        logger.warning(f"save_context 开始，action_type: {self.action_type}")
        if self.action_type == "creat_add":
            if isinstance(outputs, dict) and "output" in outputs and isinstance(outputs["output"], str):
                output_str = outputs["output"]
                logger.warning(f"⚠️ LLM 输出为字符串，尝试解析 JSON：{output_str[:100]}...")

            match = re.search(r"\{[\s\S]*\}", output_str)
            if match:
                try:
                    outputs = json.loads(match.group(0))
                    logger.warning(f"✅ 解析后的 outputs: {outputs}")
                except Exception as e:
                    logger.error(f"❌ JSON解析失败: {e}")
                    return
            else:
                logger.error("❌ 无法从输出中提取 JSON 对象，跳过保存")
                return
            structure_type = outputs.get("structure_type", "")
            question = inputs.get("question", "")
            host_reply = inputs.get("host_reply", "")
            reply_type = inputs.get("reply_type", "irrelevant")
            notes = inputs.get("notes", "")
            parent_id = outputs.get("parent_id", "")
            chain_id = outputs.get("chain_id", "")
            if not question or not host_reply:
                logger.warning("问题或回答为空，跳过保存")
                return
                
            logger.warning(f"save_context 开始，结构类型: {structure_type}")
            if structure_type == "new":
                chain_id = self.create_chain()
                self.add_node(
                    content=question,
                    chain_id=chain_id,
                    parent_id=None,
                    host_reply=host_reply,
                    reply_type=reply_type,
                    notes=notes
                )
            elif structure_type == "old":
                self.add_node(
                    content=question,
                    chain_id=chain_id,
                    parent_id=parent_id,
                    host_reply=host_reply,
                    reply_type=reply_type,
                    notes=notes
                )
            elif structure_type == "current":
                self.add_node(
                    content=question,
                    chain_id=self.current_chain_id,
                    parent_id=parent_id,
                    host_reply=host_reply,
                    reply_type=reply_type,
                    notes=notes
                )
            else:
                logger.warning("结构类型错误，跳过保存")
                return
            
            logger.warning(f"save_context 结束，当前思维链: {self.brainchains}\n"
                        f"当前焦点: {self.current_focus_id}\n"
                        f"当前思维链ID: {self.current_chain_id}")
        if self.action_type == "inference":
            if isinstance(outputs, dict) and "output" in outputs and isinstance(outputs["output"], str):
                output_str = outputs["output"]
                logger.warning(f"⚠️ LLM 输出为字符串，尝试解析 JSON：{output_str[:100]}...")

            match = re.search(r"\{[\s\S]*\}", output_str)
            if match:
                try:
                    outputs = json.loads(match.group(0))
                    logger.warning(f"✅ 解析后的 outputs: {outputs}")
                except Exception as e:
                    logger.error(f"❌ JSON解析失败: {e}")
                    return
            else:
                logger.error("❌ 无法从输出中提取 JSON 对象，跳过保存")
                return

            chain = self.get_chain(self.current_chain_id)
            if chain:
                chain.metadata["analysis_note"] = outputs.get("analysis_note", "")
                chain.metadata["path_similarity"] = outputs.get("path_similarity", 0.0)
        if self.action_type == "no_action":
            pass

    def clear(self) -> None:
        """
        实现 BaseMemory 接口，清除所有记忆
        """
        self.brainchains.clear()
        self.current_chain_id = None
        logger.info("清除所有思维链")

