"""
状态管理工具模块
"""
from typing import Callable, Coroutine, Dict, Any, TypeVar, Union
from functools import wraps
from src.state_schema import GameState

T = TypeVar('T', bound=Callable)

def with_state_update(func: T) -> T:
    """
    装饰器：自动将函数返回值合并进状态
    
    Args:
        func: 异步函数，接收状态参数，返回需要更新的字段字典
        
    Returns:
        装饰后的函数，返回更新后的状态
        
    示例:
        @with_state_update
        async def my_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
            return {"new_field": "value"}  # 会被自动合并到状态
    """
    @wraps(func)
    async def wrapper(inputs: Union[Dict[str, Any], GameState], **kwargs) -> Dict[str, Any]:
        # 如果输入是 GameState，转换为字典
        if isinstance(inputs, GameState):
            state_dict = inputs.model_dump()
        else:
            state_dict = inputs
            
        # 调用原始函数获取更新字段
        result = await func(state_dict, **kwargs)
        
        # 更新状态
        state_dict.update(result)
        return state_dict
        
    return wrapper 