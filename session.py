from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from agents.memory_manager import MemoryManager
    from game_state_parser.parser import GameStateParser


@dataclass
class Session:
    created_at: float
    last_activity: float
    message_count: int
    session_id: int
    action_id: int = 1
    channel: Optional[int] = None
    message_id: Optional[int] = None
    user_message: Optional[str] = None
    memory_manager: Optional["MemoryManager"] = None
    game_state: Optional["GameStateParser"] = None

    def get_memory(self):
        if self.memory_manager is None:
            raise Exception("Memory must be initalized")

        return self.memory_manager
