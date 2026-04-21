
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAgent(ABC):
    """모든 에이전트의 기본 클래스"""
    
    @abstractmethod
    async def run(self, input_data: Any) -> Any:
        """에이전트 실행 메서드"""
        pass
