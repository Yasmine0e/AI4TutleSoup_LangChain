"""
游戏上下文模型定义
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from src.state_schema import GameState
from src.memory.brainchain import BrainChainMemory

class Story(BaseModel):
    """故事数据结构"""
    story_id: str
    title: str = ""
    content: str
    answer: str
    difficulty: int = 1
    
class GameContext(BaseModel):
    """游戏上下文"""
    game_id: str
    story: Story
    brain_chain: BrainChainMemory = Field(default_factory=BrainChainMemory)
    hint_templates_path: str = "src/prompts/hint_templates.json"
    
    # 历史记录
    question_history: List[str] = Field(default_factory=list, description="问题历史")
    answer_history: List[str] = Field(default_factory=list, description="回答历史")
    hint_history: List[Dict[str, Any]] = Field(default_factory=list, description="提示历史")
    
    @property
    def story_text(self) -> str:
        return self.story.content
        
    @property
    def answer(self) -> str:
        return self.story.answer
    
    # 游戏配置
    max_hints: int = Field(3, description="最大提示次数")
    max_rounds: int = Field(20, description="最大回合数")
    
    # 游戏状态
    current_round: int = Field(0, description="当前回合数")
    hint_count: int = Field(0, description="已使用提示次数")
    score: Optional[int] = Field(None, description="当前玩家分数")
    final_analysis: Optional[str] = Field(None, description="结束时评语")
    
    # 存档相关
    state_history: List[GameState] = Field(default_factory=list, description="状态记录（用于回放）")
    
    def update_from_state(self, state: GameState):
        """
        从游戏状态更新上下文
        
        Args:
            state: 当前游戏状态
        """
        # 更新回合数
        self.current_round += 1
        
        # 更新提示次数
        if state.hint_type is not None:
            self.hint_count += 1
        
        # 更新脑链
        self.brain_chain.update_from_state(state.brain_chain)
        
        # 保存状态记录
        self.state_history.append(state.copy())
    
    def calculate_score(self) -> int:
        """
        计算玩家得分
        
        Returns:
            int: 得分
        """
        base_score = 100
        
        # 回合数惩罚
        round_penalty = max(0, self.current_round - 10) * 5
        
        # 提示使用惩罚
        hint_penalty = self.hint_count * 10
        
        # 计算最终得分
        final_score = base_score - round_penalty - hint_penalty
        self.score = max(0, final_score)
        
        return self.score
    
    def generate_final_analysis(self) -> str:
        """
        生成游戏结束评语
        
        Returns:
            str: 评语
        """
        score = self.calculate_score()
        
        if score >= 90:
            analysis = "🌟 完美的推理！你展现出了出色的逻辑思维能力。"
        elif score >= 70:
            analysis = "👏 不错的表现！虽然用了一些提示，但推理过程很流畅。"
        elif score >= 50:
            analysis = "💪 基本完成推理，但还有提升空间。"
        else:
            analysis = "🤔 这个谜题对你来说有点困难，建议多练习。"
        
        self.final_analysis = analysis
        return analysis
    
    def save_to_file(self, filename: str):
        """
        保存游戏记录到文件
        
        Args:
            filename: 文件名
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.json(indent=2, ensure_ascii=False))
    
    @classmethod
    def load_from_file(cls, filename: str) -> 'GameContext':
        """
        从文件加载游戏记录
        
        Args:
            filename: 文件名
            
        Returns:
            GameContext: 游戏上下文
        """
        with open(filename, 'r', encoding='utf-8') as f:
            data = f.read()
            return cls.model_validate_json(data) 