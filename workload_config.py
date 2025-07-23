# Workload configuration constants
import configparser
import os

import dotenv

dotenv.load_dotenv()

AGENT_CONFIG = configparser.ConfigParser()
AGENT_CONFIG.read("config.ini")

WORKLOAD_TITLE = os.getenv("WORKLOAD_TITLE", "DEFAULT AI WORKLOAD GPTMW_v2")
WORKLOAD_HASH = os.getenv("WORKLOAD_HASH", "GPTMW_v2")
WORKLOAD_DESC = os.getenv(
    "WORKLOAD_DESC",
    "Multi-model workload with dynamic model selection, tools and structured output.",
)
SERVER_HOST = "localhost"
SERVER_PORT = 5009

WORKLOAD_CONFIG = {
    "title": WORKLOAD_TITLE,
    "hash_id": WORKLOAD_HASH,
    "description": WORKLOAD_DESC,
    "channels": {
        "0": {
            "name": "Chat",
            "data_type": "text",
            "history_mode": "append",
        },
        "1": {
            "name": "Databases",
            "data_type": "text",
            "history_mode": "replace",
        },
        "2": {
            "name": "Caches",
            "data_type": "text",
            "history_mode": "replace",
        },
        "3": {
            "name": "Modules",
            "data_type": "text",
            "history_mode": "append",
        },
        "4": {
            "name": "Prompts",
            "data_type": "text",
            "history_mode": "append",
        },
        "5": {
            "name": "Memory",
            "data_type": "text",
            "history_mode": "replace",
        },
        "6": {
            "name": "Tool Calls",
            "data_type": "text",
            "history_mode": "append",
        },
        "8": {
            "name": "Logs",
            "data_type": "text",
            "history_mode": "append",
        },
    },
    "settings": {},
}
