from langchain.prompts import PromptTemplate

STUCK_DETECTION_PROMPT = PromptTemplate(
    input_variables=["current_brainchain", "current_question"],
    template="""
你是一个海龟汤游戏的裁判助手。你需要判断玩家是否在游戏中陷入了困境。

玩家之前的提问历史:
{current_brainchain}

玩家当前的提问:
{current_question}

请你判断玩家是否卡住，并严格输出以下 JSON（不要添加任何注释或解释）：
{{  
  "is_stuck": true,
  "confidence": 0.92,
  "reasoning": "请填写你的推理过程"
}}
"""
)
