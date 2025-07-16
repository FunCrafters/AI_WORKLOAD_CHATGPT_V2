
from typing import List
from openai.types.chat import ChatCompletionMessageParam
from agents.modules.module import T3RNModule
from session import Session
from proactive_tool_executor import get_proactive_tool_messages


class ScreenContextInjector(T3RNModule):
    def inject_start(self, session: Session)  -> List[ChatCompletionMessageParam]:
        if session.json_data is None:
            return []

        json_data = session.json_data
        
        proactive_messages, prompt_injection = get_proactive_tool_messages(json_data)
            
        injection_messages = []
        
        # Add screen context as assistant message if we have prompt injection
        if prompt_injection:
            injection_messages.append({
                "role": "assistant", 
                "content": f"I can see you're currently on a specific screen. Let me provide context: {prompt_injection}"
            })
            
            self.channel_logger.log_to_memory(f"🎯 Injected screen context: {len(prompt_injection)} chars")
        
        # Add proactive tool results and cache them
        if proactive_messages:
            injection_messages.extend(proactive_messages)
            
            # self._cache_proactive_tool_results(proactive_messages)
            
            self.channel_logger.log_to_memory(f"🔧 Injected {len(proactive_messages)} proactive tool messages")
    
        
        return injection_messages


    def inject_before_user_message(
        self, session: Session
    ) -> List[ChatCompletionMessageParam]:
        return []

        
    def inject_after_user_message(
        self, session: Session
    ) -> List[ChatCompletionMessageParam]:
        return []
