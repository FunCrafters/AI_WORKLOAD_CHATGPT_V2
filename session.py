



from dataclasses import dataclass
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.memory_manager import MemoryManager


@dataclass
class Session:
    created_at: float
    last_activity: float
    message_count: int
    session_id: str
    channel: Optional[int] = None
    message_id: Optional[int] = None
    json_data: Optional[Dict[str, Any]] = None
    text: Optional[str] = None
    action_id: int = 1
    memory_manager: Optional['MemoryManager'] = None
    client: Optional[Any] = None
    conversation_memory: Optional[Dict[str, Any]] = None

    def get_memory(self,) -> Dict[str, Any]:
        if self.conversation_memory is None:
            raise ValueError("Session memory is not initialized")
        return self.conversation_memory
