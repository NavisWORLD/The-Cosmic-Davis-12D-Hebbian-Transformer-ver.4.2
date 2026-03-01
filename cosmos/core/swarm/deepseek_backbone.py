
"""
DeepSeek Backbone - Logic & Reasoning Engine
============================================
Specialized handler for DeepSeek-V3/R1 reasoning models.
Extracts "Chain of Thought" (CoT) and ensures strict logical adherence.
"""

import re
import time
import asyncio
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

@dataclass
class ReasoningResult:
    content: str
    thought_process: str
    confidence: float
    model_used: str

class DeepSeekBackbone:
    """
    Backbone for DeepSeek-R1 / Coder models.
    Handles the unique <think> tags and reasoning extraction.
    """
    
    def __init__(self, model_name: str = "deepseek-r1:8b"):
        self.model_name = model_name
        # Regex to extract content between <think> tags
        self.thought_pattern = re.compile(r'<think>(.*?)</think>', re.DOTALL)
        
    async def query_reasoning(self, prompt: str, system_context: str = "") -> ReasoningResult:
        """
        Query DeepSeek and separate reasoning from final answer.
        NOTE: R1 models do NOT support the 'system' role — merging context into user message.
        """
        import ollama
        
        try:
            logger.info(f"[DeepSeek] Reasoning on: {prompt[:50]}...")
            start_time = time.time()
            
            # Build messages for chat API
            # IMPORTANT: DeepSeek R1 does NOT support system messages (returns 400)
            # Merge system context into the user prompt instead
            if system_context:
                combined_prompt = f"{system_context}\n\n{prompt}"
            else:
                combined_prompt = prompt
            
            messages = [{"role": "user", "content": combined_prompt}]

            
            # Run in executor to avoid blocking event loop
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: ollama.chat(model=self.model_name, messages=messages)
            )
            
            raw_text = response.get('message', {}).get('content', '')
            duration = time.time() - start_time
            
            # Extract thoughts
            thought_match = self.thought_pattern.search(raw_text)
            thought_process = ""
            final_content = raw_text
            
            if thought_match:
                thought_process = thought_match.group(1).strip()
                # Remove thought tags from final content
                final_content = self.thought_pattern.sub('', raw_text).strip()
            
            # Heuristic for confidence based on reasoning length/depth
            confidence = min(0.99, 0.5 + (len(thought_process.split()) / 1000.0))
            
            logger.info(f"[DeepSeek] Finished in {duration:.2f}s. Thoughts: {len(thought_process)} chars.")
            
            return ReasoningResult(
                content=final_content,
                thought_process=thought_process,
                confidence=confidence,
                model_used=self.model_name
            )
            
        except Exception as e:
            logger.error(f"[DeepSeek] Query failed: {e}")
            return ReasoningResult(
                content=f"Logic Engine Failure: {str(e)}",
                thought_process="Error during generation.",
                confidence=0.0,
                model_used=self.model_name
            )

    def extract_code_blocks(self, text: str) -> list[str]:
        """Extract code blocks from the response."""
        code_pattern = re.compile(r'```(?:\w+)?\n(.*?)```', re.DOTALL)
        return code_pattern.findall(text)
