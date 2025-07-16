


# Workload configuration constants
import os
import dotenv

dotenv.load_dotenv()

WORKLOAD_TITLE = os.getenv('WORKLOAD_TITLE', "DEFAULT AI WORKLOAD GPTMW_v2")
WORKLOAD_HASH = os.getenv('WORKLOAD_HASH', "GPTMW_v2")
WORKLOAD_DESC = os.getenv('WORKLOAD_DESC', "Multi-model workload with dynamic model selection, tools and structured output.")  
SERVER_HOST = "localhost"
SERVER_PORT = 5009

# Workload configuration
WORKLOAD_CONFIG = {
    "title": WORKLOAD_TITLE,
    "hash_id": WORKLOAD_HASH,   
    "description": WORKLOAD_DESC,
    "channels": {
        "0": {
            "name": "Chat",
            "data_type": "text",
            "history_mode": "append"  # Show conversation history
        },
        "1": {
            "name": "Databases",
            "data_type": "text",
            "history_mode": "replace"  # Show only the latest database info
        },
        "2": {
            "name": "Caches",
            "data_type": "text",
            "history_mode": "replace"  # Show only the latest cache info
        },
        "3": {
            "name": "Tools",
            "data_type": "text",
            "history_mode": "replace"  # Show only the latest tools info
        },
        "4": {
            "name": "Prompts",
            "data_type": "text",
            "history_mode": "append"  # Show LLM prompts and messages history
        },
        "5": {
            "name": "Memory",
            "data_type": "text",
            "history_mode": "append"  # Show current memory state (replaced each time)
        },
        "6": {
            "name": "Tool Calls",
            "data_type": "text",
            "history_mode": "append"  # Show tool results history
        },
        "8": {
            "name": "Logs",
            "data_type": "text",
            "history_mode": "append"  # Show system logs
        }
    },
    "settings": {

    }
}
