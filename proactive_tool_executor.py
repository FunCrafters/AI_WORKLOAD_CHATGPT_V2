#!/usr/bin/env python3
"""
Proactive Tool Executor
Analyzes screen context and executes relevant tools before LLM workflow
"""

import json
import logging
import uuid
from typing import Dict, List, Optional, Tuple, Any

from screen_tool_config import get_screen_tool_rules, build_prompt_injection
from tools_functions import available_all_tools

logger = logging.getLogger("Workload Proactive Tools")


def analyze_screen_context(json_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Analyze JSON data to extract screen context information
    
    Args:
        json_data (Dict): Current JSON data from client
        
    Returns:
        Optional[Dict]: Screen context info or None if no screen data found
    """
    if not json_data:
        logger.warning("❌ No JSON data provided for screen analysis")
        return None
    
    screen_context = {}
    
    # Check for screenData structure (current format)
    if "screenData" in json_data:
        screen_data = json_data["screenData"]
        screen_context["screen_name"] = screen_data.get("Screen", "")
        screen_context["popups"] = screen_data.get("Popups", [])
        screen_context["data_fields"] = {}
        
        # Extract fields from root JSON
        for key, value in json_data.items():
            if key != "screenData" and isinstance(value, (str, int, float)):
                screen_context["data_fields"][key] = value
        
        # Extract fields from screenData.ScreensData (nested structure)
        screens_data = screen_data.get("ScreensData", {})
        for presenter_name, presenter_data in screens_data.items():
            if isinstance(presenter_data, dict):
                for field_name, field_value in presenter_data.items():
                    if isinstance(field_value, (str, int, float)):
                        # Use a unique key to avoid conflicts
                        screen_context["data_fields"][f"{presenter_name}.{field_name}"] = field_value
                        # Also add without prefix for backward compatibility
                        if field_name not in screen_context["data_fields"]:
                            screen_context["data_fields"][field_name] = field_value
        
        logger.info(f"✅ Screen context found: {screen_context['screen_name']}")
        logger.info(f"✅ Data fields available: {list(screen_context['data_fields'].keys())}")
        return screen_context
    
    # TODO: Add support for other JSON structures if needed
    logger.warning("❌ No screen context found in JSON data")
    return None


def get_applicable_tools(screen_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get list of tools that should be proactively executed for the current screen
    
    Args:
        screen_context (Dict): Screen context information
        
    Returns:
        List[Dict]: List of tool configurations to execute
    """
    tools_to_execute = []
    
    # Always add greeting tool first
    greeting_tool = {
        "tool": "db_get_random_greetings",
        "tool_type": "context",
        "parameters": {}
    }
    tools_to_execute.append(greeting_tool)
    logger.info(f"✅ Added greeting tool: db_get_random_greetings")
    
    # Process screen-specific tools if screen context is available
    if screen_context:
        screen_name = screen_context.get("screen_name", "")
        if screen_name:
            # Get rules for this screen
            rules = get_screen_tool_rules(screen_name)
            
            # Add context tool (screen-specific information)
            if "context_tool" in rules:
                context_tool = rules["context_tool"].copy()
                context_tool["tool_type"] = "context"
                tools_to_execute.append(context_tool)
                logger.info(f"✅ Added context tool: {context_tool['tool']}")
            
            # Add data tools (specific data extraction)
            if "data_tools" in rules:
                data_fields = screen_context.get("data_fields", {})
                
                for data_tool in rules["data_tools"]:
                    json_field = data_tool.get("json_field")
                    if json_field and json_field in data_fields:
                        tool_config = data_tool.copy()
                        tool_config["tool_type"] = "data"
                        tool_config["field_value"] = data_fields[json_field]
                        tools_to_execute.append(tool_config)
                        logger.info(f"✅ Added data tool: {tool_config['tool']} with {json_field}={data_fields[json_field]}")
                    else:
                        logger.warning(f"⚠️ Data tool {data_tool['tool']} skipped - field '{json_field}' not found")
    
    logger.info(f"✅ Total tools to execute: {len(tools_to_execute)}")
    return tools_to_execute


def execute_proactive_tools(tools_to_execute: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Execute the list of proactive tools and return results
    
    Args:
        tools_to_execute (List[Dict]): List of tool configurations
        
    Returns:
        List[Dict]: List of tool execution results in OpenAI message format
    """
    tool_results = []
    
    for tool_config in tools_to_execute:
        tool_name = tool_config.get("tool")
        if not tool_name:
            logger.warning("⚠️ Tool configuration missing tool name")
            continue
        
        # Check if tool exists
        if tool_name not in available_all_tools:
            logger.warning(f"⚠️ Tool '{tool_name}' not found in available functions")
            continue
        
        try:
            # Prepare tool parameters
            parameters = prepare_tool_parameters(tool_config)
            if parameters is None:
                continue
            
            # Execute the tool
            tool_function = available_all_tools[tool_name]['function']
            logger.info(f"🔧 Executing proactive tool: {tool_name} with params: {parameters}")
            
            result = tool_function(**parameters)
            
            # Generate unique call ID
            call_id = f"call_proactive_{uuid.uuid4().hex[:8]}"
            
            # Format as OpenAI messages
            assistant_message = {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(parameters)
                        }
                    }
                ]
            }
            
            tool_message = {
                "role": "tool",
                "tool_call_id": call_id,
                "name": tool_name,
                "content": str(result)
            }
            
            tool_results.extend([assistant_message, tool_message])
            logger.info(f"✅ Tool {tool_name} executed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error executing proactive tool {tool_name}: {str(e)}")
            continue
    
    logger.info(f"✅ Proactive tool execution completed. Generated {len(tool_results)} messages")
    return tool_results


def prepare_tool_parameters(tool_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Prepare parameters for tool execution based on configuration
    
    Args:
        tool_config (Dict): Tool configuration
        
    Returns:
        Optional[Dict]: Prepared parameters or None if error
    """
    tool_type = tool_config.get("tool_type")
    
    if tool_type == "context":
        # Context tool - use predefined parameters
        return tool_config.get("parameters", {})
    
    elif tool_type == "data":
        # Data tool - build parameters from JSON field values
        parameter_name = tool_config.get("parameter_name")
        field_value = tool_config.get("field_value")
        
        if not parameter_name or field_value is None:
            logger.warning(f"⚠️ Data tool missing parameter_name or field_value")
            return None
        
        return {parameter_name: field_value}
    
    else:
        logger.warning(f"⚠️ Unknown tool type: {tool_type}")
        return None


def get_proactive_tool_messages(json_data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
    """
    Main function to get proactive tool messages and prompt injection for current screen context
    
    Args:
        json_data (Dict): Current JSON data from client
        
    Returns:
        Tuple[List[Dict], str]: (List of OpenAI-formatted messages with proactive tool results, prompt injection text)
    """
    logger.info("🚀 Starting proactive tool analysis")
    
    # Step 1: Analyze screen context (optional)
    screen_context = analyze_screen_context(json_data)
    
    # Step 2: Get applicable tools (always includes greeting tool)
    tools_to_execute = get_applicable_tools(screen_context)
    
    # Step 3: Execute tools and get results
    tool_messages = []
    if tools_to_execute:
        tool_messages = execute_proactive_tools(tools_to_execute)
    
    # Step 4: Build prompt injection
    prompt_injection = ""
    if screen_context:
        screen_name = screen_context.get("screen_name", "")
        data_fields = screen_context.get("data_fields", {})
        prompt_injection = build_prompt_injection(screen_name, data_fields)
    
    # Step 5: Add greeting instruction to prompt injection
    greeting_injection = "If user greets you you can use sample greating you have in your memory - remember that you are Mandalorian droid."
    if prompt_injection:
        prompt_injection = f"{prompt_injection}\n\n{greeting_injection}"
    else:
        prompt_injection = greeting_injection
    
    logger.info(f"✅ Proactive analysis completed. Tools: {len(tool_messages)} messages, Prompt: {len(prompt_injection)} chars")
    return tool_messages, prompt_injection