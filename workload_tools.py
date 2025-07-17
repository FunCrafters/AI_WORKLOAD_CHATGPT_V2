#!/usr/bin/env python3
"""
Workload Tools
Utility functions for the workload
"""

import json
import logging
import socket

logger = logging.getLogger("WorkloadTools")


class ContextAdapter(logging.LoggerAdapter):
    LOG_KWARGS = ["exc_info", "stack_info", "stacklevel"]

    def process(self, msg, kwargs):
        extra = kwargs.pop("extra", {})
        preserved_kwargs = {
            k: kwargs[k] for k in ContextAdapter.LOG_KWARGS if k in kwargs
        }

        msg_vars = ", ".join(f"{k}={v}" for k, v in extra.items())

        if msg_vars:
            msg = f"{msg} | {msg_vars}"

        # Restore preserved kwargs and update with extra
        kwargs.update(preserved_kwargs)
        kwargs["extra"] = extra

        return msg, kwargs


logger = ContextAdapter(logger)


def get_local_ip():
    """Get the local IP address of the computer."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        logger.error(f"Cannot determine local IP: {e}")
        return "127.0.0.1"


def is_host_reachable(host, port=11434, timeout=2):
    """Check if a host is reachable."""
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        logger.error(f"Host {host} is not reachable", extra=dict(host=host, port=port))
        return False


def create_response(
    channel, result="", session_id=None, message_id=None, extra_data=None
):
    """Create a standardized response object"""
    response = {"type": "response", "channel": channel, "result": result}

    # Add session_id if provided
    if session_id:
        response["session_id"] = session_id

    # Add message_id if provided
    if message_id:
        response["message_id"] = message_id

    # Add any extra data if provided
    if extra_data and isinstance(extra_data, dict):
        response.update(extra_data)

    return response


def send_response(client, response, session_id=None, channel=0, message_id=None):
    """Send response to client with standard logging"""
    # Log what we're about to send - truncate any result text
    result = response.get("result", "")
    if isinstance(result, str):
        # Replace newlines with spaces to keep log entries on one line
        result_oneline = result.replace("\n", " ").replace("\r", "")

        # Truncate if too long
        if len(result_oneline) > 250:
            log_result = f"{result_oneline[:250]}..."
        else:
            log_result = result_oneline
    else:
        log_result = str(result)

    logger.info(
        "   RESPONDING",
        extra=dict(
            session_id=session_id,
            channel=channel,
            message_id=message_id,
            preview=log_result,
        ),
    )

    # Use send_message function for reliable sending
    send_message(client, response)


def send_message(client, message_data):
    """Send a message to the server with reliability checks"""
    # Convert to JSON
    json_data = json.dumps(message_data)
    encoded_data = json_data.encode("utf-8")

    # Log message being sent
    message_type = message_data.get("type", "unknown")
    session_id = message_data.get("session_id", "none")
    message_id = message_data.get("message_id", "none")
    size = len(encoded_data)

    logger.info(
        f"<< SEND -{message_type.upper()}-",
        extra=dict(session_id=session_id, message_id=message_id, size=size),
    )

    # Send with explicit error handling
    try:
        client.sendall(encoded_data)
        logger.info("   SUCCESS: ", extra=dict(session_id=session_id))
        return True
    except Exception as e:
        logger.error("!! ERROR: ", extra=dict(session_id=session_id, error=str(e)))
        return False
