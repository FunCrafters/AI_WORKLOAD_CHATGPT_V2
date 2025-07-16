import json
import hashlib
import time
from typing import Any, Dict
import uuid

# TODO this might be not nesessery with cachetools.
class ToolCacheManager:
    def __init__(self,):
        self.cache = dict()

    def _generate_key(self, tool_name, parameters):
        hash_input = f"{tool_name}:{json.dumps(parameters, sort_keys=True)}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    def add(self, tool_name: str, parameters: Dict[str, Any], result: str, llm_cache_duration: int) -> None:
        if llm_cache_duration <= 0:
            return  
            
        cache_key = self._generate_key(tool_name, parameters)
        
        call_id = f"call_cached_{uuid.uuid4().hex[:8]}"
        
        cache_entry = {
            'tool_name': tool_name,
            'parameters': parameters,
            'result': result,
            'remaining_duration': llm_cache_duration,
            'original_duration': llm_cache_duration,
            'call_id': call_id,
            'cached_at': time.time()
        }
        
        self.cache[cache_key] = cache_entry
        

    def get_all(self,):
        pass

    def cleanup(self):
        """
        Clean expired cache
        """
        pass