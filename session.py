from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from agents.memory_manager import MemoryManager


@dataclass
class Session:
    created_at: float
    last_activity: float
    message_count: int
    session_id: int
    action_id: int = 1
    channel: Optional[int] = None
    message_id: Optional[int] = None
    json_data: Optional[Dict[str, Any]] = None
    user_message: Optional[str] = None
    memory_manager: Optional["MemoryManager"] = None

    def get_memory(self):
        if self.memory_manager is None:
            raise Exception("Memory must be initalized")

        return self.memory_manager
