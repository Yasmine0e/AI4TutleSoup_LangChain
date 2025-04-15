"""
检测玩家是否在逻辑游戏中卡住的工具模块
"""
import logging
import json
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import BaseOutputParser
from src.state_schema import GameState
from src.utils.prompt_utils import STUCK_DETECTION_PROMPT

class DetectionResult(BaseModel):
    """检测结果"""
    is_stuck: bool = Field(description="是否卡住")
    confidence: float = Field(description="置信度")
    reasoning: str = Field(description="推理过程")

class DetectionResultParser(BaseOutputParser[DetectionResult]):
    """检测结果解析器"""
    
    def parse(self, text: str) -> DetectionResult:
        """
        解析 LLM 输出的文本
        
        Args:
            text: LLM 输出的文本
            
        Returns:
            DetectionResult: 解析后的检测结果
            
        Raises:
            ValueError: 解析失败时抛出
        """
        try:
            text = text.strip()

            # 去掉 markdown 的 ```json 包裹
            if text.startswith("```json"):
                text = text[len("```json"):].strip()
            if text.endswith("```"):
                text = text[:-3].strip()

            data = json.loads(text)

            if not all(k in data for k in ["is_stuck", "confidence", "reasoning"]):
                raise ValueError("缺少必要字段")

            return DetectionResult(
                is_stuck=bool(data["is_stuck"]),
                confidence=float(data["confidence"]),
                reasoning=str(data["reasoning"])
            )

        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 解析失败: {str(e)}\n原始文本: {repr(text)}")
        except Exception as e:
            raise ValueError(f"解析检测结果失败: {str(e)}\n原始文本: {repr(text)}")

class DetectStuckTool(BaseTool):
    """检测玩家是否卡住的工具"""
    name: str = "detect_stuck"
    description: str = "检测玩家是否在游戏中卡住"
    llm: BaseChatModel
    parser: BaseOutputParser[DetectionResult] = Field(default_factory=DetectionResultParser)
    logger: logging.Logger = Field(default_factory=lambda: logging.getLogger(__name__))
    
    def _run(
        self,
        tool_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        同步检测玩家是否卡住
        
        Args:
            tool_input: 包含以下字段的字典：
                - current_question: 当前问题
                - current_brainchain: 当前思维链摘要
            
        Returns:
            Dict[str, Any]: 检测结果
        """
        try:
            # 验证输入
            if not tool_input.get("current_question"):
                raise ValueError("current_question 不能为空")
            
            # 构建提示
            prompt = STUCK_DETECTION_PROMPT.format_prompt(
                current_brainchain=tool_input.get("current_brainchain", []),
                current_question=tool_input["current_question"]
            )
            
            # 调用 LLM
            response = self.llm.predict(prompt.to_string())
            
            # 解析结果
            result = self.parser.parse(response)
            
            return {
                "is_stuck": result.is_stuck,
                "confidence": result.confidence,
                "reasoning": result.reasoning
            }
            
        except Exception as e:
            self.logger.error(f"检测卡住状态时出错: {str(e)}")
            return {
                "is_stuck": False,
                "confidence": 0.0,
                "reasoning": f"检测过程出错: {str(e)}"
            }
    
    async def _arun(
        self,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        异步检测玩家是否卡住
        
        Args:
            tool_input: 包含以下字段的字典：
                - current_question: 当前问题
                - current_brainchain: 当前思维链摘要
            
        Returns:
            Dict[str, Any]: 检测结果
        """
     
        try:
            current_question = kwargs.get("current_question", "")
            current_brainchain = kwargs.get("current_brainchain", [])
            self.logger.info(f"[DetectStuckTool] 参数 current_brainchain 类型: {type(current_brainchain)}，内容: {repr(current_brainchain)}")
            self.logger.info(f"[DetectStuckTool] 参数 current_question 类型: {type(current_question)}，内容: {repr(current_question)}")

            # 构建提示
            prompt = STUCK_DETECTION_PROMPT.format_prompt(
                current_brainchain=current_brainchain,
                current_question=current_question,
            )
            
            # 调用 LLM
            self.logger.info(f"[DetectStuckTool] 发送提示: {prompt}")
            response = await self.llm.ainvoke(prompt.to_string())
            self.logger.info(f"[DetectStuckTool] LLM 原始输出: {repr(response)}")
            
            # 预处理响应
            if not response:
                raise ValueError("LLM 返回空响应")
            
            # 解析结果
            result = self.parser.parse(response.content)
            self.logger.info(f"[DetectStuckTool] 解析结果: {result}")
            
            return {
                "is_stuck": result.is_stuck,
                "confidence": result.confidence,
                "reasoning": result.reasoning
            }
            
        except Exception as e:
            self.logger.error(f"[DetectStuckTool] 检测失败: {str(e)}", exc_info=True)
            return {
                "is_stuck": False,
                "confidence": 0.0,
                "reasoning": f"检测过程出错: {str(e)}"
            }

