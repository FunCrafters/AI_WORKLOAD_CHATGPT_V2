#!/usr/bin/env python3
"""
LLM Workload Configuration
Configuration parameters for the LLM Workload
"""

# Workload configuration constants
WORKLOAD_HASH = "GPTMW_v2"  # 8-character fixed hash
SERVER_HOST = "localhost"    # Server address
SERVER_PORT = 5009           # Server port (can be overridden from env)

# Workload configuration
WORKLOAD_CONFIG = {
    "title": "ChatGPT Marek v2",
    "hash_id": WORKLOAD_HASH,
    "description": "Multi-model workload with dynamic model selection, tools and structured output.",
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
