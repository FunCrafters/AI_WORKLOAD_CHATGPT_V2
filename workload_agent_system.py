#!/usr/bin/env python3
"""
Agent-Based LLM System
New agent-based architecture for processing user messages
"""

import time
import logging
from typing import List, Dict, Any, Tuple, Optional

# Import agent classes
from agents.base_agent import Agent, AgentContext, AgentResult
from agents.t3rn_agent import T3RNAgent
from agents.fallback_agent import FallbackAgent
from agents.memory_manager import MemoryManager

# Logger
logger = logging.getLogger("Agent System")

class AgentStack:
    """Manages the stack of agents to be executed"""
    
    def __init__(self):
        self.agents: List[Tuple[Agent, AgentContext]] = []
    
    def push(self, agent: Agent, context: AgentContext):
        """Add agent to stack"""
        self.agents.append((agent, context))
    
    def pop(self) -> Optional[Tuple[Agent, AgentContext]]:
        """Remove and return agent from stack"""
        if self.agents:
            return self.agents.pop(0)  # FIFO
        return None
    
    def is_empty(self) -> bool:
        """Check if stack is empty"""
        return len(self.agents) == 0
    
    def size(self) -> int:
        """Get stack size"""
        return len(self.agents)


def create_initial_context(user_message: str, session: Dict[str, Any], memory_manager: MemoryManager) -> AgentContext:
    """Create initial context for new processing with memory management"""
    context = AgentContext()
    
    context.original_user_message = user_message
    context.session_data = session
      
    # Initialize memory manager and prepare messages
    memory_manager.initialize_session_memory(session)
    memory_messages = memory_manager.prepare_messages_for_agent(session, user_message)
      
    return context

def process_llm_agents(user_message: str, session: Dict[str, Any], 
                      channel_logger) -> str:
    """
    New agent-based function calling system
    
    Returns:
        final_answer (str): The final response from the agent system
        
    All other information (tools, errors, thinking) is logged via channel_logger
    """
    
    # Get client and session_id from session
    client = session.get('client')
    session_id = session.get('session_id')
    
    # Get or create action_id in session
    if 'action_id' not in session:
        session['action_id'] = 1
    else:
        session['action_id'] += 1
    action_id = session['action_id']
    
    # Get or create memory manager from session
    if 'memory_manager' not in session:
        session['memory_manager'] = MemoryManager()
    memory_manager = session['memory_manager']

    channel_logger.set_action_id(action_id)
    channel_logger.log_to_logs(f"🚀 Starting agent-based processing [Action {action_id}]")
    channel_logger.log_to_logs("🆕 Starting new processing with T3RNAgent")
    
    context = create_initial_context(user_message, session, memory_manager)
    t3rn_agent = T3RNAgent(memory_manager)
    
    agent_stack = AgentStack()
    agent_stack.push(t3rn_agent, context)
    
    # Track failed agents to prevent infinite loops
    failed_agents = set()
    
    # Process agent stack
    while not agent_stack.is_empty():
        channel_logger.log_to_logs("🔄 Processing next agent from stack")
        
        # Get next agent
        agent_data = agent_stack.pop()
        if agent_data is None:
            channel_logger.log_to_logs("⚠️ No agent data from stack")
            break
        current_agent, current_context = agent_data
        agent_type = current_agent.__class__.__name__
        channel_logger.log_to_logs(f"🤖 Executing {agent_type}")
        
        # Check if this agent type already failed
        if agent_type in failed_agents:
            channel_logger.log_to_logs(f"⚠️ {agent_type} already failed, skipping to avoid loop")
            continue
        
        # Pass channel_logger to agent - it already has all needed info (client, session_id, action_id)
        current_agent.channel_logger = channel_logger
        
        try:
            # Execute agent
            result = current_agent.execute(current_context, channel_logger)
            
            # Check if agent provided final answer
            if result.final_answer:
                # Agent provided final answer - processing complete
                channel_logger.log_to_logs(f"✅ {current_agent.__class__.__name__} provided final answer")
                    
                # Finalize memory manager with final answer
                memory_manager.finalize_current_cycle(session, user_message, result.final_answer, channel_logger)
                    
                if result.error_content:
                    channel_logger.log_error(result.error_content)
                    
                # Flush logs buffer for organized display
                channel_logger.flush_buffer(channel_logger.LOGS)
                    
                return result.final_answer
            else:
                # Agent failed - add FallbackAgent to stack
                channel_logger.log_to_logs(f"⚠️ {current_agent.__class__.__name__} failed, spawning FallbackAgent")
                fallback_agent = FallbackAgent()
                agent_stack.push(fallback_agent, current_context)
                continue
            
                
        except Exception as e:
            channel_logger.log_to_logs(f"❌ {agent_type} error: {str(e)}")
            
            # Mark this agent type as failed
            failed_agents.add(agent_type)
            
            # Spawn FallbackAgent only if T3RNAgent failed and FallbackAgent hasn't been tried yet
            if isinstance(current_agent, T3RNAgent) and "FallbackAgent" not in failed_agents:
                fallback_agent = FallbackAgent()
                agent_stack.push(fallback_agent, current_context)
                channel_logger.log_to_logs("🔄 Added FallbackAgent for T3RNAgent error")
            else:
                # No more fallbacks available, break the loop
                channel_logger.log_to_logs("💥 All agents failed, breaking loop")
                break
    
    # If we exit the loop without a final answer, use final emergency response
    channel_logger.log_to_logs("⚠️ Agent stack empty without final answer")
    
    # Create final emergency response using T3RN malfunction messages
    try:
        import random
        from agents.agent_prompts import T3RN_MALFUNCTION_MESSAGES
        
        emergency_message = random.choice(T3RN_MALFUNCTION_MESSAGES)
        channel_logger.log_to_logs("🛡️ Using emergency T3RN malfunction response as final fallback")
        
        # Finalize memory manager with emergency answer
        memory_manager.finalize_current_cycle(session, user_message, emergency_message, channel_logger)
        
        # Flush logs buffer for organized display
        channel_logger.flush_buffer(channel_logger.LOGS)
        
        return emergency_message
        
    except Exception as e:
        channel_logger.log_to_logs(f"❌ Emergency response also failed: {str(e)}")
        
        # Absolute last resort - hardcoded response
        error_message = "Critical system malfunction. This droid requires immediate maintenance."
        
        # Finalize memory manager with error message
        try:
            memory_manager.finalize_current_cycle(session, user_message, error_message, channel_logger)
        except:
            pass  # If memory manager also fails, just continue
        
        # Log critical error information
        channel_logger.log_to_logs("💭 CRITICAL ERROR: All agents failed")
        channel_logger.log_error(f"Critical system error: {str(e)}")
        
        # Flush logs buffer for organized display
        channel_logger.flush_buffer(channel_logger.LOGS)
        
        return error_message
