import json
import logging
import os
import socket
import sys
import textwrap
import time
from typing import Any, Dict

from dotenv import dotenv_values, load_dotenv

from game_state_parser.parser import GameStateParser
from session import Session
from workload_chat import process_main_channel
from workload_config import SERVER_HOST, SERVER_PORT, WORKLOAD_CONFIG
from workload_tools import create_response, send_message, send_response

# Load environment variables from .env file
load_dotenv()
config = dotenv_values(".env")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("LLM Workload")
logger = logging.LoggerAdapter(logger)

active_sessions: Dict[str, Any] = {}


def connect_to_server():
    """Connect to RathTAR socket server"""
    # Check if port was overridden from env
    socket_port = int(os.environ.get("WORKLOAD_SOCKET", SERVER_PORT))

    # Create socket and connect
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        logger.info(f"CONNECTING: host={SERVER_HOST}, port={socket_port}")
        client.connect((SERVER_HOST, socket_port))
        logger.info("SUCCESS: connected to RathTAR server")
        return client
    except Exception as e:
        logger.error(f"ERROR: error={e}")
        return None


def register_workload(client):
    """Register workload with RathTAR"""
    # Send registration message
    registration = {
        "title": WORKLOAD_CONFIG["title"],
        "hash_id": WORKLOAD_CONFIG["hash_id"],
        "description": WORKLOAD_CONFIG.get("description", ""),
        "channels": WORKLOAD_CONFIG["channels"],
        "settings": WORKLOAD_CONFIG.get("settings", {}),
    }

    try:
        # Send registration data
        logger.info(f"REGISTERING: title={registration['title']}, hash_id={registration['hash_id']}")
        reg_data = json.dumps(registration).encode("utf-8")
        client.sendall(reg_data)

        response = client.recv(4096)

        if not response:
            logger.error("!! ERROR: no response from server")
            return None

        data = json.loads(response.decode("utf-8"))
        if data.get("status") == "connected":
            workload_id = data.get("id")
            logger.info(f"   SUCCESS: workload_id={workload_id}")
            return workload_id
        else:
            logger.error(f"!! ERROR: status={data.get('status')}, response={data}")
            return None
    except Exception as e:
        logger.error(f"!! ERROR: error={e}")
        return None


def create_or_update_session(data: dict):
    session_id = data["session_id"]
    message_type = data["type"]

    message_id = data.get("message_id", None)
    channel = data.get("channel")
    text = data.get("text")

    is_initialization = message_type == "initialization"

    if not session_id:
        return None

    if session_id not in active_sessions:
        active_sessions[session_id] = Session(
            created_at=time.time(),
            last_activity=time.time(),
            session_id=session_id,
            channel=channel,
            message_id=message_id,
            user_message=text,
        )

    if not is_initialization:
        active_sessions[session_id].last_activity = time.time()
        if channel is not None:
            active_sessions[session_id].channel = channel
        if text is not None:
            active_sessions[session_id].user_message = text
        if message_id is not None:
            active_sessions[session_id].message_id = message_id

    return active_sessions[session_id]


def process_message(client, message):
    """Process a message from RathTAR"""
    try:
        # Parse the message
        raw_message = message.decode("utf-8")
        # Log limited data preview for privacy/brevity

        data = json.loads(raw_message)

        # Extract common message data
        message_type = data.get("type")

        session = create_or_update_session(data)

        if not session:
            logger.error("!! ERROR_SESSION_CREATION", extra=dict(raw_message=raw_message))
            return

        # Log standardized message receipt info
        logger.info(
            f"Recived Message='{message_type}'",
            extra=dict(session_id=session.session_id, message_id=session.message_id),
        )

        # Wrap preview text for better readability
        preview_text = textwrap.shorten(raw_message, width=250)
        logger.info("PREVIEW", extra=dict(preview=preview_text))

        # Handle message based on its type
        #   - {'type': 'initialization', 'text': '', 'channel': 0, 'session_id': '5YG83K'}
        if message_type == "initialization":
            process_initialization_message(client, session)
        elif message_type == "process":
            #  - {'type': 'process', 'text': 'Hello friend', 'channel': 0, 'session_id': '5YG83K', 'message_id': 1752050086246}
            process_text_message(client, session)
        elif message_type == "settings":
            process_settings_message(client, session, data)
        elif message_type == "data":
            #  - {'type': 'data', 'data':
            # {'main': {'media_id': 'screenshot_1752049288153',
            # 'media_type': 'image', 'filename': 'screenshot_2025-07-09T08-21-25.506Z.png',
            # 'user_id': '108336033121275716906', 'user_name': 'Maciej Kołodziejczyk',
            # 'user_email': 'maciej.kolodziejczyk@fun-crafters.com',
            # 'device_id': 'RZCY40W0NXV', 'device_model': 'SM-A556B',
            # 'device_manufacturer': 'samsung', 'android_version': '15',
            # 'title': '[Battle Scene] Bottom part of a board does not render properly',
            # 'notes': 'Initial steps:\nPlayer is in a battle\n\nReproduction:\n1. Observe the bottom part of the board\n\nReproduction rate:\n100%\n\nActual result:\n\nBottom part of the board is completely black.\n\nExpected result:\n\nThe entire board renders correctly.\n\n', 'referers': [], 'severity': 'Trivial', 'category': 'Gameplay', 'labels': '', 'visibility': 'public'}}, 'session_id': '5YG83K'}
            process_json_data_message(client, session, data)

        else:
            logger.error(f"Recive unknown message type: {message_type}")

    except Exception as e:
        logger.error("!! ERROR_PROCESSING", extra=dict(error=str(e)))
        import traceback

        logger.error(traceback.format_exc())


def process_initialization_message(client, session: Session):
    """Process an initialization message"""
    logger.info(
        "   PROCESSING",
        extra=dict(session_id=session.session_id, channel=session.channel),
    )

    response = create_response(session.channel, "", session.session_id, session.message_id)
    send_response(client, response, session.session_id, session.channel or 0, session.message_id)

    # Immediately after initialization, send a separate message to request JSON data
    # This is a separate message to ensure proper socket communication
    request_json_data(client, session.session_id)

    # if session is initialized, we can send previous messages to the agent.

    chat_response = create_response(0, "Rawrrr", session.session_id, session.message_id)
    send_response(client, chat_response, session.session_id, session.channel or 0, session.message_id)


def process_settings_message(client, session: Session, data: dict):
    """Process a settings message (all settings at once)"""
    logger.info("-- PROCESS_SETTINGS", extra=dict(session_id=session.session_id))

    # Extract settings
    settings_data = data.get("settings", {})
    if settings_data:
        # TODO THAT IS UNSAFE, WHat is going on here? Check what it is doing
        logger.info(
            "   PROCESS_SETTINGS",
            extra=dict(session_id=session.session_id, keys=list(settings_data.keys())),
        )
        # Store settings directly in session
        for key, value in settings_data.items():
            session.__dict__[key] = value

        logger.info(
            "   PROCESS_SETTINGS_STORED",
            extra=dict(session_id=session.session_id, keys=list(settings_data.keys())),
        )

        logger.info("   SETTINGS_CONFIRMATION", extra=dict(session_id=session.session_id))
        response = {
            "type": "settings_response",
            "success": True,
            "session_id": session.session_id,
            "message_id": session.message_id,
        }

        # Send settings response confirmation
        send_message(client, response)
    else:
        logger.info("!! PROCESS_SETTINGS_EMPTY", extra=dict(session_id=session.session_id))


def request_json_data(client, session_id):
    """Send request for JSON data"""
    logger.info("   REQUEST JSON DATA", extra=dict(session_id=session_id))

    # Create JSON request message
    json_request = {
        "type": "request_data",
        "data_type": "json",
        "session_id": session_id,
        "message_id": f"json_req_{int(time.time())}",
    }

    # Send JSON request to server - send_message function handles the logging
    send_message(client, json_request)


def process_json_data_message(client, session: Session, data: dict):
    """Process a JSON data message from the server"""

    try:
        json_data = data["data"]
        data_size_bytes = len(json.dumps(json_data))
        data_size_kb = data_size_bytes / 1024

        logger.info(
            "JSON DATA",
            extra=dict(
                session_id=session.session_id,
                size_bytes=data_size_bytes,
                size_kb=f"{data_size_kb:.2f}",
            ),
        )

        # Store a small sample and summary
        session.game_state = GameStateParser(json.dumps(json_data))

        # Send confirmation response
        response = {
            "type": "data_received",
            "status": "success",
            "bytes_received": data_size_bytes,
            "kb_received": round(data_size_kb, 2),
            "session_id": session.session_id,
            "message_id": session.message_id,
        }

        logger.info(
            "JSON DATA RECEIVED",
            extra=dict(session_id=session.session_id, channel=2, message_id=session.message_id),
        )

        logger.info("ERROR_JSON_DATA_MISSING", extra=dict(session_id=session.session_id))
    except KeyError:
        response = {
            "type": "data_received",
            "status": "error",
            "error": "No data field in message",
            "session_id": session.session_id,
            "message_id": session.message_id,
        }

        send_message(client, response)
    except Exception:
        logger.error("!! ERROR_PROCESSING_JSON_DATA", extra=dict(session_id=session.session_id))
        response = {
            "type": "data_received",
            "status": "error",
            "error": "Failed to process JSON data",
            "session_id": session.session_id,
            "message_id": session.message_id,
        }


def process_text_message(client, session: Session):
    text = session.user_message or ""
    channel = session.channel
    session_id = session.session_id
    message_id = session.message_id

    logger.info(f'TEXT PROCESSING: session={session_id}, channel={channel}, message_id={message_id}, text="{text}"')

    if channel == 0:
        process_main_channel(
            client,
            session,
        )
    else:
        response = create_response(channel, f"Received on channel {channel}: {text}", session_id, message_id)
        send_response(client, response, session_id, session.channel or 0, session.message_id)


def receive_full_message(client, delimiter=b"\n"):
    """
    Receive a complete message from socket until delimiter is found

    Args:
        client: Socket client
        delimiter: Message delimiter (default: newline)

    Returns:
        Complete message as bytes or None if connection closed
    """
    buffer = b""
    chunk_size = 4096

    try:
        while True:
            chunk = client.recv(chunk_size)
            if not chunk:
                # Connection closed
                return None

            buffer += chunk

            # Check if we have a complete message
            if delimiter in buffer:
                # Split at first delimiter
                message, remainder = buffer.split(delimiter, 1)

                # For now, we'll assume one message per receive cycle
                # If remainder is not empty, it would need to be handled
                # but current protocol seems to send one message at a time
                if remainder:
                    logger.warning(f"RECEIVE_REMAINDER: {len(remainder)} bytes remaining after delimiter")

                return message

            # Prevent infinite buffer growth
            if len(buffer) > 1024 * 1024:  # 1MB limit
                logger.error(f"RECEIVE_BUFFER_OVERFLOW: buffer size {len(buffer)} bytes")
                return None

    except socket.timeout:
        logger.warning("RECEIVE_TIMEOUT: no complete message received")
        return None
    except Exception as e:
        logger.error(f"RECEIVE_ERROR: {str(e)}")
        return None


def reconnect_loop():
    """Main reconnection loop with retry logic"""
    max_retry_interval = 30  # Maximum retry interval in seconds
    retry_interval = 1  # Start with 1 second

    while True:
        # Connect to server
        client = connect_to_server()
        if not client:
            logger.error(f"CONNECTION_FAILED: retry in {retry_interval} seconds")
            time.sleep(retry_interval)
            retry_interval = min(retry_interval * 2, max_retry_interval)  # Exponential backoff
            continue

        # Reset retry interval on successful connection
        retry_interval = 1

        try:
            # Register workload
            workload_id = register_workload(client)
            if not workload_id:
                logger.error(f"REGISTRATION_FAILED: retry in {retry_interval} seconds")
                client.close()
                time.sleep(retry_interval)
                retry_interval = min(retry_interval * 2, max_retry_interval)
                continue

            # Main processing loop
            while True:
                try:
                    # Wait for complete messages using delimiter-based protocol
                    message = receive_full_message(client, delimiter=b"\n")
                    if not message:
                        logger.warning("CONNECTION_CLOSED: by server or receive error")
                        break

                    # Log message size for debugging
                    message_size = len(message)
                    if message_size > 50000:  # Log large messages
                        logger.info(f"LARGE_MESSAGE: size={message_size} bytes ({message_size / 1024:.1f}KB)")

                    # Process complete message
                    process_message(client, message)

                except socket.timeout:
                    # Just continue on timeout
                    continue
                except Exception as e:
                    logger.error(f"MAIN_LOOP_ERROR: error={e}")
                    # Check if socket is still connected
                    try:
                        # Try to send a heartbeat message
                        client.sendall(b"")
                    except socket.error:
                        # If it fails, socket is disconnected
                        logger.error("CONNECTION_BROKEN: socket disconnected")
                        break

        except KeyboardInterrupt:
            logger.info("SHUTDOWN: received interrupt signal")
            if client:
                client.close()
            return 0
        except Exception as e:
            logger.error(f"UNEXPECTED_ERROR: error={e}")
        finally:
            # Clean up
            if client:
                try:
                    client.close()
                except socket.error:
                    logger.error("CLOSE_ERROR: failed to close socket")
                logger.info("CONNECTION_CLOSED")

        logger.info(f"CONNECTION_LOST: retry in {retry_interval} seconds")
        time.sleep(retry_interval)
        retry_interval = min(retry_interval * 2, max_retry_interval)


def main():
    logger.info(f"WORKLOAD_STARTING: name={WORKLOAD_CONFIG['title']}, hash={WORKLOAD_CONFIG['hash_id']}")

    try:
        reconnect_loop()
    except KeyboardInterrupt:
        logger.info("SHUTDOWN: received interrupt signal")
    except Exception as e:
        logger.error(f"INITIALIZATION_ERROR: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
