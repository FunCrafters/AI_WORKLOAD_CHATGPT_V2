#!/usr/bin/env python3
"""
LLM Workload
Connects to RathTAR and processes text using LLM models with RAG capabilities
"""

import os
import socket
import json
import time
import sys
import logging
from dotenv import load_dotenv, dotenv_values

# Import workload configuration
from workload_config import WORKLOAD_CONFIG, WORKLOAD_HASH, SERVER_HOST, SERVER_PORT

# Import embedding functionality for agent system
from workload_embedding import (
    initialize_embeddings_and_vectorstore
)

# Import chat functionality
from workload_chat import (
    process_main_channel
)

# Import logging functionality
from workload_logs import (
    build_vectorstore_log,
    build_cache_log,
    build_tools_log
)

# Import utility functions
from workload_tools import (
    create_response,
    send_response,
    send_message
)

# For typing annotations
from typing import Union, Optional, Dict, List, Any

# Load environment variables from .env file
load_dotenv()
config = dotenv_values(".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LLM Workload")
logger = logging.LoggerAdapter(logger)

# Dictionary to store session data for multiple users
active_sessions = {}

def connect_to_server():
    """Connect to RathTAR socket server"""
    # Check if port was overridden from env
    socket_port = int(os.environ.get('WORKLOAD_SOCKET', SERVER_PORT))
    
    # Create socket and connect
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        logger.info(f"<< CONNECTING: host={SERVER_HOST}, port={socket_port}")
        client.connect((SERVER_HOST, socket_port))
        logger.info("   SUCCESS: connected to RathTAR server")
        return client
    except Exception as e:
        logger.error(f"!!  ERROR: error={e}")
        return None

def register_workload(client):
    """Register workload with RathTAR"""
    # Send registration message
    registration = {
        "title": WORKLOAD_CONFIG["title"],
        "hash_id": WORKLOAD_CONFIG["hash_id"],
        "description": WORKLOAD_CONFIG.get("description", ""),
        "channels": WORKLOAD_CONFIG["channels"],
        "settings": WORKLOAD_CONFIG.get("settings", {})
    }
    
    try:
        # Send registration data
        logger.info(f"<< REGISTERING: title={registration['title']}, hash_id={registration['hash_id']}")
        reg_data = json.dumps(registration).encode('utf-8')
        client.sendall(reg_data)
        
        response = client.recv(4096)
        
        if not response:
            logger.error("!! ERROR: no response from server")
            return None
            
        data = json.loads(response.decode('utf-8'))
        if data.get('status') == 'connected':
            workload_id = data.get('id')
            logger.info(f"   SUCCESS: workload_id={workload_id}")
            return workload_id
        else:
            logger.error(f"!! ERROR: status={data.get('status')}, response={data}")
            return None
    except Exception as e:
        logger.error(f"!! ERROR: error={e}")
        return None

#TODO Session handling?
def create_or_update_session(session_id, text="", channel=0, is_initialization=False):
    """Create a new session or update an existing one"""
    if not session_id:
        return None
        
    if session_id not in active_sessions:
        # Create new session
        active_sessions[session_id] = {
            "created_at": time.time(),
            "last_activity": time.time(),
            "message_count": 0,  # todo - do czego to sluzy
            "session_id": session_id
        }
    
    # Update session activity
    if not is_initialization:
        active_sessions[session_id]["last_activity"] = time.time()
        active_sessions[session_id]["message_count"] += 1
        
    return active_sessions[session_id]


def process_message(client, message):
    """Process a message from RathTAR"""
    try:
        # Parse the message
        raw_message = message.decode('utf-8')
        # Log limited data preview for privacy/brevity
        
        data = json.loads(raw_message)
        
        # Extract common message data
        message_type = data.get('type')
        session_id = data.get('session_id')
        message_id = data.get('message_id', 0)
        
        # Log standardized message receipt info
        preview = raw_message[:250] + "..." if len(raw_message) > 250 else raw_message
        logger.info(f"Recived Message {message_type}", extra=dict(session_id=session_id, message_id=message_id))
        logger.info("PREVIEW", extra=dict(preview=preview))

        # Handle message based on its type
        if message_type == 'initialization':
            # Handle session initialization
            process_initialization_message(client, data, session_id, message_id)
                
        elif message_type == 'process':
            # Process text on channel
            process_text_message(client, data, session_id, message_id)

        elif message_type == 'settings':
            # Handle settings updates (all settings at once)
            process_settings_message(client, data, session_id, message_id)
                
        elif message_type == 'data':
            # Handle JSON data
            process_json_data_message(client, data, session_id, message_id)
                
        else:
            logger.error(f"Recive unknown message type: {message_type}")
            
    except Exception as e:
        logger.error("!! ERROR_PROCESSING", extra=dict(error=str(e)))
        import traceback
        logger.error(traceback.format_exc())

def process_initialization_message(client, data, session_id, message_id):
    """Process an initialization message"""
    channel = data.get('channel', 0)
    logger.info("   PROCESSING", extra=dict(session_id=session_id, channel=channel))
    
    # Create a new session
    create_or_update_session(session_id, is_initialization=True)
        
    # Send empty response for initialization
    response = create_response(channel, "", session_id, message_id)
    send_response(client, response, session_id, channel, message_id)
    
    # Immediately after initialization, send a separate message to request JSON data
    # This is a separate message to ensure proper socket communication
    request_json_data(client, session_id)


def process_settings_message(client, data, session_id, message_id):
    """Process a settings message (all settings at once)"""
    logger.info("-- PROCESS_SETTINGS", extra=dict(session_id=session_id))
    
    # Get or create session
    session = create_or_update_session(session_id, is_initialization=True)
    
    if not session:
        logger.info("!! PROCESS_SETTINGS_NO_SESSION", extra=dict(session_id=session_id))
        return
    
    # Extract settings
    settings_data = data.get('settings', {})
    if settings_data:
        # Store settings directly in session
        for key, value in settings_data.items():
            session[key] = value
        logger.info("   PROCESS_SETTINGS_STORED", extra=dict(session_id= session_id, keys=list(settings_data.keys())))

        logger.info("   SETTINGS_CONFIRMATION", extra=dict(session_id=session_id))        
        response = {
            'type': 'settings_response',
            'success': True,
            'session_id': session_id,
            'message_id': message_id
        }

        # Send settings response confirmation
        send_message(client, response)
    else:
        logger.info("!! PROCESS_SETTINGS_EMPTY", extra=dict(session_id= session_id))

def request_json_data(client, session_id):
    """Send request for JSON data"""
    logger.info("   REQUEST JSON DATA", extra=dict(session_id=session_id))
    
    # Create JSON request message
    json_request = {
        "type": "request_data",
        "data_type": "json",
        "session_id": session_id,
        "message_id": f"json_req_{int(time.time())}"
    }
    
    # Send JSON request to server - send_message function handles the logging
    send_message(client, json_request)

def process_json_data_message(client, data, session_id, message_id):
    """Process a JSON data message from the server"""
    # Get or create session
    session = create_or_update_session(session_id, is_initialization=True)
    
    if not session:
        logger.info("!! PROCESS_JSON_DATA_NO_SESSION", extra=dict(session_id=session_id))
        return
    
    # Store JSON data in session
    if 'data' in data:
        # Get JSON data and calculate size
        json_data = data['data']
        data_size_bytes = len(json.dumps(json_data))
        data_size_kb = data_size_bytes / 1024
        
        # Log detailed information about received JSON
        logger.info("   JSON DATA", extra=dict(session_id=session_id, size_bytes=data_size_bytes, size_kb=f"{data_size_kb:.2f}"))
        
        # Log top-level keys in the JSON
        if isinstance(json_data, dict):
            top_keys = list(json_data.keys())
            logger.info("   JSON STRUCTURE", extra=dict(session_id=session_id, top_keys=top_keys))
            
        elif isinstance(json_data, list):
            logger.info("   JSON STRUCTURE", extra=dict(session_id=session_id, type="list", length=len(json_data)))
            if len(json_data) > 0:
                sample_type = type(json_data[0]).__name__
                logger.info("   JSON LIST SAMPLE", extra=dict(session_id=session_id, sample_type=sample_type))
        
        # IMPORTANT: Set current JSON data in game cache for screen context tool
        try:
            from workload_game_cache import set_current_json_data
            # Only set if json_data is a dictionary (required for screen context)
            if isinstance(json_data, dict):
                set_current_json_data(json_data)
                logger.info("   JSON DATA SET IN CACHE", extra=dict(session_id=session_id, success=True))
            else:
                logger.info("   JSON DATA SKIP CACHE", extra=dict(session_id=session_id, reason="not_dict", type=type(json_data).__name__))
        except Exception as e:
            logger.info("   JSON DATA CACHE ERROR", extra=dict(session_id=session_id, error=str(e)))
        
        # Store a summary of the data structure
        def get_data_summary(data):
            if isinstance(data, dict):
                return {k: get_data_summary(v) if isinstance(v, (dict, list)) and k != 'small_value' else 'data_present' for k, v in list(data.items())[:10]}
            elif isinstance(data, list):
                return [get_data_summary(item) if isinstance(item, (dict, list)) else 'data_present' for item in data[:5]]
            else:
                return 'data_present'
        
        # Store a small sample and summary
        session['json_data'] = {
            'size': data_size_bytes,
            'size_kb': data_size_kb,
            'summary': get_data_summary(json_data)
        }
        
        # Send confirmation response
        response = {
            'type': 'data_received',
            'status': 'success',
            'bytes_received': data_size_bytes,
            'kb_received': round(data_size_kb, 2),
            'session_id': session_id,
            'message_id': message_id
        }
        
        logger.info("   DATA RECEIVED CONFIRMATION", extra=dict(session_id=session_id, channel=2, message_id=message_id))
        
        #TODO Why sleep?
        time.sleep(0.1)        
        # Send the response
        send_message(client, response)
        time.sleep(0.1)
        
        # Send database information to Database channel (1)
        build_vectorstore_log(client, session_id, f"init_{int(time.time())}")
        time.sleep(0.1)
        
        # Send cache information to Caches channel (2)
        build_cache_log(client, session_id, f"init_{int(time.time())}")
        time.sleep(0.1)
        
        # Send tools information to Tools channel (3)
        build_tools_log(client, session_id, f"init_{int(time.time())}")
        time.sleep(0.1)
        
        # Send model preload log to Logs channel (8) if available
        # TODO what is model_preload_log?
        global model_preload_log
        if 'model_preload_log' in globals() and model_preload_log:
            preload_text = "\n".join(model_preload_log)
            preload_response = create_response(8, preload_text, session_id, f"init_{int(time.time())}_preload")
            send_response(client, preload_response, session_id, 8, f"init_{int(time.time())}_preload")
            time.sleep(0.1)
            logger.info("   MODEL PRELOAD LOG SENT", extra=dict(session_id=session_id, channel=8))
    else:
        # Log error and send error response
        logger.info("ERROR_JSON_DATA_MISSING", extra=dict(session_id=session_id))
        
        # Create error response
        response = {
            'type': 'data_received',
            'status': 'error',
            'error': 'No data field in message',
            'session_id': session_id,
            'message_id': message_id
        }
        
        # Send the response
        send_message(client, response)

def process_text_message(client, data, session_id, message_id):
    """Process a text message on a specific channel"""
    text = data.get('text', '')
    channel = data.get('channel', 0)
    logger.info(f"   TEXT PROCESSING: session={session_id}, channel={channel}, message_id={message_id}, text=\"{text}\"")

    # Update session data
    session = create_or_update_session(session_id, text, channel)

    # Process text based on channel
    if channel == 0:  # Main channel
        process_main_channel(
            client, session, text, channel, session_id, message_id,
            active_sessions, create_response, send_response
        )
    else:
        # For other channels, just echo back the text
        response = create_response(channel, f"Received on channel {channel}: {text}", session_id, message_id)
        send_response(client, response, session_id, channel, message_id)

def receive_full_message(client, delimiter=b'\n'):
    """
    Receive a complete message from socket until delimiter is found
    
    Args:
        client: Socket client
        delimiter: Message delimiter (default: newline)
        
    Returns:
        Complete message as bytes or None if connection closed
    """
    buffer = b''
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
    retry_interval = 1       # Start with 1 second
    
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
                    message = receive_full_message(client, delimiter=b'\n')
                    if not message:
                        logger.warning("CONNECTION_CLOSED: by server or receive error")
                        break
                        
                    # Log message size for debugging
                    message_size = len(message)
                    if message_size > 50000:  # Log large messages
                        logger.info(f"LARGE_MESSAGE: size={message_size} bytes ({message_size/1024:.1f}KB)")
                        
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
                        client.sendall(b'')
                    except:
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
                except:
                    pass
                logger.info("CONNECTION_CLOSED")
        
        logger.info(f"CONNECTION_LOST: retry in {retry_interval} seconds")
        time.sleep(retry_interval)
        retry_interval = min(retry_interval * 2, max_retry_interval)

def main():
    """Main workload function"""
    logger.info(f"WORKLOAD_STARTING: name={WORKLOAD_CONFIG['title']}, hash={WORKLOAD_CONFIG['hash_id']}")

    try:
        # Initialize embeddings and vectorstore for agent system
        ollama_host = config.get('OLLAMA_HOST') or '100.83.28.7'
        ollama_port = config.get('OLLAMA_PORT') or '11434'
        
        logger.info(f"Initializing agent system with Ollama at {ollama_host}:{ollama_port}")
        
        vectorstore_ollama = initialize_embeddings_and_vectorstore(
            config, ollama_host, ollama_port
        )
        
        if vectorstore_ollama:
            logger.info("Agent system initialized successfully")
        else:
            logger.warning("Agent system initialized with warnings - check vectorstore logs")
        

        # Start reconnection loop
        reconnect_loop()
    except KeyboardInterrupt:
        logger.info("SHUTDOWN: received interrupt signal")
    except Exception as e:
        logger.error(f"INITIALIZATION_ERROR: {str(e)}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
