"""提示生成工具"""
import json
import logging
from typing import Dict, Any, Literal
from pathlib import Path
from langchain.tools import StructuredTool
from langchain_deepseek import ChatDeepSeek
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from src.state_schema import GameState, GameContext

logger = logging.getLogger(__name__)

class HintToolInput(BaseModel):
    hint_type: Literal["default", "direction", "deviation", "strategy"]
    question: str
    story: str


class HintOutput(BaseModel):
    """提示输出模型"""
    hint_text: str = Field(..., description="提示文本")
    confidence: float = Field(0.0, description="提示的置信度")
    hint_type: Literal["direction", "deviation", "default", "strategy"] = Field(..., description="提示类型")

class HintGenerator:
    """提示生成器核心类"""
    
    def __init__(self, llm: ChatDeepSeek):
        """初始化提示生成器
        
        Args:
            llm: 语言模型实例
        """
        self.llm = llm
        self.templates = self._load_templates()
        self.output_parser = PydanticOutputParser(pydantic_object=HintOutput)
    
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载提示模板"""
        template_path = Path(__file__).parent.parent / "prompts" / "hint_templates.json"
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[HintGenerator] 加载模板失败: {e}")
            return {}
    
    def _get_prompt(self, hint_type: str, **kwargs) -> ChatPromptTemplate:
        """获取指定类型的提示模板"""
        if hint_type not in self.templates:
            logger.warning(f"[HintGenerator] 未找到提示类型 {hint_type} 的模板")
            raise ValueError(f"未找到提示类型 {hint_type} 的模板")
            
        template = self.templates[hint_type]
        return ChatPromptTemplate.from_messages([
            ("system", template["system"]),
            ("human", template["template"].format(**kwargs))
        ])
    
    def generate(self, hint_type: str, context: GameContext) -> Dict[str, Any]:
        """生成提示
        
        Args:
            hint_type: 提示类型
            context: 游戏上下文
        
        Returns:
            Dict[str, Any]: 提示结果
        """
        try:
            # 转换输入
            brain_context = context.brain_chain
            
            # 准备模板参数
            template_args = {
                "story": context.story_text,
                "current_question": context.current_question,
                "brain_chain": brain_context
            }
            
            # 获取并填充提示模板
            prompt = self._get_prompt(hint_type, **template_args)
            
            # 调用 LLM 生成提示
            response = self.llm(prompt.format_messages())
            
            # 解析输出
            output = self.output_parser.parse(response.content)
            
            return {
                "hint_text": output.hint_text,
                "confidence": output.confidence,
                "hint_type": output.hint_type,
            }
            
        except Exception as e:
            logger.warning(
                f"[HintGenerator] 生成提示失败: {str(e)}\n"
                f"提示类型: {hint_type}\n"
            )
            raise e

# 创建 StructuredTool 实例
def create_hint_tool(llm: ChatDeepSeek, context: GameContext) -> StructuredTool:
    generator = HintGenerator(llm)
    
    def hint_tool_fn(hint_type: str, question: str, story: str) -> Dict[str, Any]:
        return generator.generate(
            hint_type=hint_type,
            context=GameContext(
                story_text=story,
                brain_chain=context.brain_chain  
            ),
            current_question=question
        )
    
    return StructuredTool.from_function(
        func=hint_tool_fn,
        name="generate_hint",
        args_schema=HintToolInput,
        description="根据当前问题生成提示。支持 hint_type=['default','direction','deviation','strategy']"
    )
