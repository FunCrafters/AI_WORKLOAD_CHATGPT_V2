#!/usr/bin/env python3
"""
Channel Logger
Unified logging system for multi-channel output
"""

import logging
import textwrap
import time
from typing import Any, Dict, List, Optional

from workload_tools import create_response, send_response


class ChannelLogFormatter(logging.Formatter):
    CHANNEL_NAMES = {
        0: "CHAT",
        1: "DATABASES",
        2: "CACHES",
        3: "TOOLS",
        4: "PROMPTS",
        5: "MEMORY",
        6: "TOOL_CALLS",
        8: "LOGS",
    }

    def format(self, record):
        """
        Format the log record with additional context

        Adds:
        - Channel name
        - Session ID (if available)
        - Message ID (if available)
        """
        channel_id = getattr(record, "channel", "UNKNOWN")

        if isinstance(channel_id, int):
            channel_name = self.CHANNEL_NAMES.get(channel_id, f"CHANNEL_{channel_id}")
        else:
            channel_name = str(channel_id)

        record.channel_name = channel_name

        session_id = getattr(record, "session_id", "-")
        message_id = getattr(record, "message_id", "-")

        # Customize format
        log_format = (
            f"[{channel_name}] "
            f"[Session: {session_id}] "
            f"[Message: {message_id}] "
            f"- {record.getMessage()}"
        )

        return log_format


logger = logging.getLogger("ChannelLogger")
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(ChannelLogFormatter())
logger.addHandler(console_handler)


# I still refuse to belive this is best way to do it
# for feature - consider creating loggingHandler that does that automatically
# and instead of passing channel logger everywhere I would create local logger
class ChannelLogger:
    """Handles logging into web server"""

    # Channel IDs as constants
    CHAT = 0
    DATABASES = 1
    CACHES = 2
    TOOLS = 3
    PROMPTS = 4
    MEMORY = 5
    TOOL_CALLS = 6  # Previously LLM Tools
    LOGS = 8  # Channel 7 (Errors) is removed

    def __init__(self, client, session_id: int, message_id: int | None):
        """Initialize the channel logger

        Args:
            client: Socket client for sending messages
            session_id: Current session ID
            message_id: Current message ID
        """
        self.client = client
        self.session_id = session_id
        self.message_id = message_id
        self.action_id = None

        # Store logs for batch sending if needed
        self.logs_buffer: Dict[int, List[str]] = {
            self.CHAT: [],
            self.DATABASES: [],
            self.CACHES: [],
            self.TOOLS: [],
            self.PROMPTS: [],
            self.MEMORY: [],
            self.TOOL_CALLS: [],
            self.LOGS: [],
        }

    def set_action_id(self, action_id: int):
        """Set the current action ID for all subsequent logs"""
        self.action_id = action_id

    def log_to_chat(self, content: str):
        """Log to Chat channel (0)"""
        self._send_to_channel(self.CHAT, content)

    def log_to_databases(self, content: str):
        """Log to Databases channel (1)"""
        self._send_to_channel(self.DATABASES, content)

    def log_to_caches(self, content: str):
        """Log to Caches channel (2)"""
        self._send_to_channel(self.CACHES, content)

    def log_to_tools(self, content: str):
        """Log to Tools channel (3)"""
        self._send_to_channel(self.TOOLS, content)

    def log_to_prompts(self, content: str):
        """Log to Prompts channel (4)"""
        if self.action_id:
            content = f"[Action {self.action_id}] {content}"
        self._send_to_channel(self.PROMPTS, content)

    def log_to_memory(self, content: str):
        """Log to Memory channel (5)"""
        self._send_to_channel(self.MEMORY, content)

    def log_to_tool_calls(self, content: str):
        """Log to Tool Calls channel (6, previously LLM Tools)"""
        if self.action_id:
            content = f"[Action {self.action_id}] {content}"
        self._send_to_channel(self.TOOL_CALLS, content)

    def log_to_logs(self, content: str):
        """Log to Logs channel (8) - buffered for better organization"""
        # Remove any existing [Action X] prefix since we'll add it during flush
        if content.startswith("[Action ") and "]" in content:
            bracket_end = content.find("]")
            if bracket_end != -1:
                content = content[bracket_end + 1 :].strip()

        logger.info(content)

        self.buffer_log(self.LOGS, content)

    def log_error(self, error: str, traceback: Optional[str] = None):
        """Log error information to Logs channel (previously would go to Errors)"""
        error_content = f"❌ ERROR: {error}"
        if traceback:
            error_content += f"\n\n=== TRACEBACK ===\n{traceback}"
        self.log_to_logs(error_content)
        logging.error(f"Logged error: {error}")

    def log_exception(self, exception: Exception, traceback_str: str):
        """Log exception details to Logs channel"""
        exception_content = f"=== PROCESSING EXCEPTION ===\nError: {str(exception)}\n\n=== FULL TRACEBACK ===\n{traceback_str}"
        self.log_to_logs(exception_content)

    def log_tool_call(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        result: Any,
        call_number: int = 1,
    ):
        """Log a tool call to Tool Calls channel"""
        import json

        # Format arguments for display
        args_display = json.dumps(tool_args, indent=2) if tool_args else "No arguments"

        # Truncate result to 500 bytes max
        result_str = str(result)
        result_display = textwrap.shorten(result_str, width=500)

        # Build tool call info
        tool_info = f"TOOL CALL #{call_number}\n"
        tool_info += f"🔧 Tool: {tool_name}\n"
        tool_info += f"📋 Parameters: {args_display}\n"
        tool_info += f"📄 Result:\n{result_display}\n"

        self.log_to_tool_calls(tool_info)

    def buffer_log(self, channel: int, content: str):
        """Add content to buffer instead of sending immediately"""
        if channel in self.logs_buffer:
            self.logs_buffer[channel].append(content)

    def flush_buffer(self, channel: int):
        """Flush buffer for a specific channel"""
        if channel in self.logs_buffer and self.logs_buffer[channel]:
            combined_content = "\n".join(self.logs_buffer[channel])

            # For Logs channel, add Action header
            if channel == self.LOGS and self.action_id:
                combined_content = f"[Action {self.action_id}]\n{combined_content}"

            self._send_to_channel(channel, combined_content)
            self.logs_buffer[channel] = []

    def flush_all_buffers(self):
        """Flush all buffered logs"""
        for channel in self.logs_buffer:
            self.flush_buffer(channel)

    def _send_to_channel(self, channel: int, content: str):
        """Internal method to send content to a specific channel"""
        if not self.client or not content:
            return

        try:
            # Create unique sub-message ID for this channel
            sub_message_id = f"{self.message_id}_{channel}_{int(time.time() * 1000)}"

            response = create_response(
                channel, content, self.session_id, sub_message_id
            )
            send_response(
                self.client, response, self.session_id, channel, sub_message_id
            )
        except Exception as e:
            # If we can't log, print to console as fallback
            print(f"Failed to log to channel {channel}: {str(e)}")
