"""结构相关工具"""
import time
import uuid
from typing import Dict, Any

class GenerateUUIDTool:
    """生成 UUID 工具"""
    def run(self) -> Dict[str, str]:
        return {
            "chain_id": str(uuid.uuid4()),
            "node_id": str(uuid.uuid4())
        }

class GetCurrentTimeTool:
    """获取当前时间工具"""
    def run(self) -> Dict[str, float]:
        current = time.time()
        return {
            "timestamp": current,
            "created_at": current
        } 