#!/usr/bin/env python3
"""
Workload Logs
Logging functions for displaying information in various channels
"""

import logging

# Import utility functions
from workload_tools import (
    create_response,
    send_response
)

# Import embedding functions
from workload_embedding import (
    get_vectorstore_log
)

# Import LLM tools
from tools_functions import (
    get_cache_info,
    get_tools_info
)

# Logger
logger = logging.getLogger("Workload Logs")

#######################
# Channel Logging Functions
#######################

def build_vectorstore_log(client, session_id, message_id):
    """Display database logs in the Database channel (1)"""
    vectorstore_log = get_vectorstore_log()
    
    if not vectorstore_log:
        return
        
    # Join log entries into a single string
    log_text = "\n".join(vectorstore_log)
    
    # Create response for Database channel
    db_response = create_response(1, log_text, session_id, f"{message_id}_db")
    
    # Send response to the client
    send_response(client, db_response, session_id, 1, f"{message_id}_db")

def build_cache_log(client, session_id, message_id):
    """Display cache information in the Caches channel (2)"""
    try:
        # Get cache information from LLM tools module
        cache_text = get_cache_info()
        
        # Create response for Caches channel
        cache_response = create_response(2, cache_text, session_id, f"{message_id}_cache")
        
        # Send response to the client
        send_response(client, cache_response, session_id, 2, f"{message_id}_cache")
        
    except Exception as e:
        error_text = f"Error retrieving cache information: {str(e)}"
        cache_response = create_response(2, error_text, session_id, f"{message_id}_cache")
        send_response(client, cache_response, session_id, 2, f"{message_id}_cache")

def build_tools_log(client, session_id, message_id):
    """Display tools information in the Tools channel (3)"""
    try:
        # Get tools information from LLM tools module
        tools_text = get_tools_info()
        
        # Create response for Tools channel
        tools_response = create_response(3, tools_text, session_id, f"{message_id}_tools")
        
        # Send response to the client
        send_response(client, tools_response, session_id, 3, f"{message_id}_tools")
        
    except Exception as e:
        error_text = f"Error retrieving tools information: {str(e)}"
        tools_response = create_response(3, error_text, session_id, f"{message_id}_tools")
        send_response(client, tools_response, session_id, 3, f"{message_id}_tools")