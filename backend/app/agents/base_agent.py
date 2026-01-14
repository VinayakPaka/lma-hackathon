from typing import List, Dict, Any, Optional
import os
import json
import logging
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.memory_store import MemoryStore

# Global flags to track when providers have failed
_bytez_exhausted = False
_openrouter_exhausted = False

def reset_provider_flags():
    """Reset all provider exhaustion flags."""
    global _bytez_exhausted, _openrouter_exhausted
    _bytez_exhausted = False
    _openrouter_exhausted = False
    logging.info("All provider exhaustion flags have been reset")

class BaseAgent:
    """
    Base agent class using Bytez (Qwen/GPT-5) -> OpenRouter -> Perplexity.
    """
    
    def __init__(self, name: str, company_id: str, memory_store: MemoryStore):
        self.name = name
        self.company_id = company_id
        self.memory = memory_store
        self.agent_logs = []
        
        from app.config import settings
        
        # Initialize Clients
        self._bytez_client = None
        self._openrouter_client = None
        self._perplexity_client = None
        self._kimi_client = None
        
        # 1. Bytez Client (Primary)
        if settings.BYTEZ_API_KEY:
            try:
                from bytez import Bytez
                self._bytez_client = Bytez(settings.BYTEZ_API_KEY)
                logging.info(f"{self.name}: Bytez client initialized")
            except Exception as e:
                logging.warning(f"{self.name}: Bytez init failed: {e}")
        
        # 2. OpenRouter Client (Secondary)
        if settings.OPENROUTER_API_KEY:
            try:
                from langchain_openai import ChatOpenAI
                self._openrouter_client = ChatOpenAI(
                    model="meta-llama/llama-3.3-70b-instruct:free",
                    api_key=settings.OPENROUTER_API_KEY,
                    base_url=settings.OPENROUTER_BASE_URL,
                    temperature=0
                )
            except Exception as e:
                logging.warning(f"{self.name}: OpenRouter init failed: {e}")

        # 3. Perplexity Client (Fallback)
        if settings.PERPLEXITY_API_KEY:
            try:
                from langchain_openai import ChatOpenAI
                self._perplexity_client = ChatOpenAI(
                    model=settings.PERPLEXITY_MODEL,
                    api_key=settings.PERPLEXITY_API_KEY,
                    base_url="https://api.perplexity.ai",
                    temperature=0
                )
            except Exception as e:
                logging.warning(f"{self.name}: Perplexity init failed: {e}")

    async def call_llm_direct(self, prompt: str, timeout_seconds: int = 180) -> str:
        """Call LLM with simple prompt using fallback chain."""
        return await self._execute_llm_call([{"role": "user", "content": prompt}], timeout_seconds)

    async def think_with_memory(self, task: str, context_categories: List[str], timeout_seconds: int = 180) -> str:
        """Agent thinks through a task with memory context."""
        logging.info(f"{self.name} is thinking about: {task[:200]}...")
        
        # 1. Retrieve Memory with length limit
        MAX_MEMORY_CONTEXT_CHARS = 15000  # Limit context to prevent token overflow
        relevant_memory_str = ""
        for category in context_categories:
            if len(relevant_memory_str) >= MAX_MEMORY_CONTEXT_CHARS:
                break  # Stop if we've hit the limit
            memories = await self.memory.retrieve_memory(query=task, category=category)
            if memories:
                category_str = f"\n[{category.upper()} CONTEXT]:\n"
                for mem in memories:
                    mem_entry = f"- {mem}\n"
                    # Check if adding this would exceed limit
                    if len(relevant_memory_str) + len(category_str) + len(mem_entry) > MAX_MEMORY_CONTEXT_CHARS:
                        relevant_memory_str += "... (context truncated to fit token limit)\n"
                        break
                    if category_str:  # Only add header once
                        relevant_memory_str += category_str
                        category_str = ""  # Clear after first use
                    relevant_memory_str += mem_entry

        if not relevant_memory_str:
            relevant_memory_str = "No specific valid memories found for this context."

        # 2. Construct Messages
        system_prompt = f"""You are {self.name}, an expert banking ESG analyst assistant.
        
        GOAL: Produce bank-grade, audit-friendly analysis.
        
        HARD RULES:
        - Use ONLY facts from MEMORY CONTEXT.
        - If info is missing, write "Not evidenced".
        - Return STRICT JSON only if requested.
        
        MEMORY CONTEXT:
        {relevant_memory_str}
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task}
        ]

        # 3. Execute
        response = await self._execute_llm_call(messages, timeout_seconds)
        
        # 4. Log
        self.agent_logs.append({
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "task": task,
            "response": response
        })
        
        return response

    async def _execute_llm_call(self, messages: List[Dict[str, str]], timeout_seconds: int) -> str:
        """Execute LLM call with updated fallback logic: Bytez -> OpenRouter -> Perplexity."""
        from app.config import settings
        import asyncio
        global _bytez_exhausted, _openrouter_exhausted
        
        # Helper: Call Bytez
        async def call_bytez_api(model_name: str, msgs: List[Dict[str, str]]) -> str:
            if not self._bytez_client: raise ValueError("No Bytez Client")
            model = self._bytez_client.model(model_name)
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, lambda: model.run(msgs))
            
            if results.error: raise ValueError(f"Bytez Error: {results.error}")
            
            output = results.output
            if isinstance(output, dict) and "content" in output: return output["content"]
            if isinstance(output, list) and output and "content" in output[0]: return output[0]["content"]
            return str(output)

        # Helper: Call LangChain Client
        async def call_langchain(client, msgs):
            from langchain_core.messages import HumanMessage, SystemMessage
            lc_msgs = []
            for m in msgs:
                if m["role"] == "system": lc_msgs.append(SystemMessage(content=m["content"]))
                elif m["role"] == "user": lc_msgs.append(HumanMessage(content=m["content"]))
            
            resp = await client.ainvoke(lc_msgs)
            return resp.content

        # STRATEGY 1: Bytez Open Model (Qwen)
        if not _bytez_exhausted and self._bytez_client:
            try:
                logging.info(f"{self.name}: Trying Bytez Open ({settings.BYTEZ_MODEL_OPEN})...")
                return await asyncio.wait_for(call_bytez_api(settings.BYTEZ_MODEL_OPEN, messages), timeout=timeout_seconds)
            except Exception as e:
                logging.warning(f"Bytez Open failed: {e}")
                if "insufficient" in str(e).lower(): _bytez_exhausted = True

        # STRATEGY 2: Bytez Closed Model (GPT-5) - Only if Open failed but NOT exhausted specific error
        if not _bytez_exhausted and self._bytez_client:
            try:
                logging.info(f"{self.name}: Trying Bytez Closed ({settings.BYTEZ_MODEL_CLOSED})...")
                return await asyncio.wait_for(call_bytez_api(settings.BYTEZ_MODEL_CLOSED, messages), timeout=timeout_seconds)
            except Exception as e:
                logging.warning(f"Bytez Closed failed: {e}")
                if "insufficient" in str(e).lower(): _bytez_exhausted = True

        # STRATEGY 3: OpenRouter
        if not _openrouter_exhausted and self._openrouter_client:
            try:
                logging.info(f"{self.name}: Trying OpenRouter...")
                return await asyncio.wait_for(call_langchain(self._openrouter_client, messages), timeout=timeout_seconds)
            except Exception as e:
                logging.warning(f"OpenRouter failed: {e}")
                if "429" in str(e): _openrouter_exhausted = True

        # STRATEGY 4: Perplexity
        if self._perplexity_client:
            try:
                logging.info(f"{self.name}: Trying Perplexity...")
                return await asyncio.wait_for(call_langchain(self._perplexity_client, messages), timeout=timeout_seconds)
            except Exception as e:
                logging.error(f"Perplexity failed: {e}")

        return "Error: All AI providers failed."

    def parse_json_robust(self, text: str, context: str = "unknown") -> dict:
        """
        Robustly parse JSON from LLM response with multiple fallback strategies.
        Handles common issues like markdown code blocks, extra text, and malformed JSON.
        
        Args:
            text: The raw LLM response text
            context: A label for logging purposes (e.g., "baseline_verifier")
            
        Returns:
            Parsed dict, or empty dict if all strategies fail
        """
        import re
        
        if not text or not text.strip():
            logging.warning(f"[{context}] Empty response")
            return {}
        
        # Strategy 1: Clean markdown code blocks and try direct parse
        clean_text = text.strip()
        clean_text = re.sub(r'^```json\s*', '', clean_text)
        clean_text = re.sub(r'^```\s*', '', clean_text)
        clean_text = re.sub(r'\s*```$', '', clean_text)
        
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Find JSON object between first { and last }
        try:
            first_brace = clean_text.find('{')
            last_brace = clean_text.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_candidate = clean_text[first_brace:last_brace + 1]
                return json.loads(json_candidate)
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Try to find and parse only the first complete JSON object
        # (handles "Extra data" errors from trailing content)
        try:
            brace_count = 0
            json_start = None
            for i, char in enumerate(clean_text):
                if char == '{':
                    if brace_count == 0:
                        json_start = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and json_start is not None:
                        json_candidate = clean_text[json_start:i + 1]
                        return json.loads(json_candidate)
        except json.JSONDecodeError:
            pass
        
        # Strategy 4: Use regex to find nested JSON-like structure
        try:
            # Recursive matching for nested braces
            def find_json_object(s):
                start = s.find('{')
                if start == -1:
                    return None
                depth = 0
                in_string = False
                escape_next = False
                for i in range(start, len(s)):
                    c = s[i]
                    if escape_next:
                        escape_next = False
                        continue
                    if c == '\\':
                        escape_next = True
                        continue
                    if c == '"':
                        in_string = not in_string
                        continue
                    if in_string:
                        continue
                    if c == '{':
                        depth += 1
                    elif c == '}':
                        depth -= 1
                        if depth == 0:
                            return s[start:i+1]
                return None
            
            json_str = find_json_object(clean_text)
            if json_str:
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Strategy 5: Try to fix common JSON issues
        try:
            # Remove trailing commas before } or ]
            fixed_text = re.sub(r',(\s*[}\]])', r'\1', clean_text)
            # Find JSON boundaries again
            first_brace = fixed_text.find('{')
            last_brace = fixed_text.rfind('}')
            if first_brace != -1 and last_brace != -1:
                fixed_text = fixed_text[first_brace:last_brace + 1]
                return json.loads(fixed_text)
        except json.JSONDecodeError:
            pass
        
        logging.warning(f"[{context}] All JSON parsing strategies failed. Text preview: {clean_text[:200]}...")
        return {}

    async def remember(self, category: str, key: str, value: Any, 
                      metadata: Optional[Dict] = None):
        """Agent stores something in memory."""
        await self.memory.store_fact(category, key, value, metadata)
        
        self.agent_logs.append({
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "action": "remember",
            "category": category,
            "key": key
        })
