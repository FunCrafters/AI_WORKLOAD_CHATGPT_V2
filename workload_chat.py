#!/usr/bin/env python3
"""
Workload Chat Functions
Chat processing functionality for the workload
"""

import time
import logging
import json

# Import utility functions
from workload_tools import (
    log_message,
    create_response,
    send_response
)

# Import agent system
from workload_agent_system import (
    process_llm_agents
)

# Import channel logger
from channel_logger import ChannelLogger

# Logger
logger = logging.getLogger("Workload Chat")

#######################
# Main Processing Function
#######################

def process_main_channel(client, session, text, channel, session_id, message_id, 
                         active_sessions, create_response, send_response, log_message):
    """Process text on the main channel (0) with agent-based function calling"""
    # Skip processing for empty messages
    if not text:
        response = create_response(channel, "", session_id, message_id)
        send_response(client, response, session_id, channel, message_id)
        return
    
    # Add client and session_id to session for agent use
    session['client'] = client
    session['session_id'] = session_id
    
    # Create channel logger for multi-channel logging
    channel_logger = ChannelLogger(client, session_id, message_id)
    
    # Import available functions count from LLM module
    from tools_functions import available_llm_functions
    
    # Initial logging
    channel_logger.log_to_logs(f"🚀 Processing with Agent-Based System: \"{text}\"")
    channel_logger.log_to_logs(f"💬 Session ID: {session_id}")
    channel_logger.log_to_logs(f"🔧 Available tools: {len(available_llm_functions)} tools")
        
    log_message(f"   AGENT-BASED PROCESSING", session_id=session_id)
    
    try:
        # Process with agent-based function calling
        start_time = time.time()        
        final_answer = process_llm_agents(text, session, channel_logger)
        process_time = time.time() - start_time

        channel_logger.log_to_logs(f"✅ Agent processing completed in {process_time:.2f} seconds")
        channel_logger.log_to_logs(f"📝 Answer length: {len(final_answer)} characters")
        
        # Send processed_answer to channel 0 (Chat)
        #channel_logger.log_to_chat(final_answer)
        chat_response = create_response(0, final_answer, session_id, message_id)
        send_response(client, chat_response, session_id, channel, message_id)
        
        # All other information (tools, thinking, errors) is logged automatically 
        # by process_llm_agents via channel_logger
        
    except Exception as e:
        # Log the error
        log_message("!! AGENT PROCESSING ERROR", session_id=session_id, error=str(e))
        
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        # Use ChannelLogger for error reporting
        action_id = session.get('action_id', 'Unknown')
        channel_logger.set_action_id(action_id)
        channel_logger.log_exception(e, error_traceback)
        
        # Send error message to the user
        channel_logger.log_to_chat(f"Error processing your question: {str(e)}")
    
    # ChannelLogger handles all logging automatically - no need for manual log building
