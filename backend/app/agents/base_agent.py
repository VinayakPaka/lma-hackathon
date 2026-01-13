from typing import List, Dict, Any, Optional
import os
import json
import logging
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.memory_store import MemoryStore

class BaseAgent:
    """
    Base agent class using Google Gemini and MemVid memory.
    """
    
    def __init__(self, name: str, company_id: str, memory_store: MemoryStore):
        self.name = name
        self.company_id = company_id
        self.memory = memory_store
        
        # Initialize LLM (Priority: DeepSeek -> Gemini -> Perplexity fallback logic implied)
        from app.config import settings
        
        # 1. Try OpenRouter (Priority: Cloud Open Source)
        openrouter_key = os.getenv("OPENROUTER_API_KEY") or settings.OPENROUTER_API_KEY
        if openrouter_key:
             try:
                from langchain_openai import ChatOpenAI
                
                # Model Selection Logic (OpenRouter IDs)
                if any(x in self.name.lower() for x in ["document", "verifier", "tracker", "completeness", "chart"]):
                    model_name = "qwen/qwen-2.5-72b-instruct"
                elif "extractor" in self.name.lower():
                    model_name = "meta-llama/llama-3.1-8b-instruct"
                elif any(x in self.name.lower() for x in ["benchmark", "orchestrator"]):
                    model_name = "qwen/qwen-2.5-72b-instruct" # Full power for core reasoning
                elif "analysis" in self.name.lower():
                    # model_name = "deepseek/deepseek-r1" # 402 Payment Required
                    model_name = "qwen/qwen-2.5-72b-instruct" # Fallback to working model
                else:
                    model_name = "qwen/qwen-2.5-72b-instruct" # Default to strong model

                logging.info(f"Using OpenRouter ({model_name}) for {self.name}")
                self.llm = ChatOpenAI(
                    model=model_name,
                    api_key=openrouter_key,
                    base_url=settings.OPENROUTER_BASE_URL,
                    temperature=0
                )
             except Exception as e:
                logging.error(f"OpenRouter init failed: {e}")

        # 2. Try DeepSeek Direct (Backup)
        if not hasattr(self, 'llm'):
             deepseek_key = os.getenv("DEEPSEEK_API_KEY") or settings.DEEPSEEK_API_KEY
             if deepseek_key:
                try:
                    from langchain_openai import ChatOpenAI
                    logging.info(f"Using DeepSeek-R1 (Direct) for {self.name}")
                    self.llm = ChatOpenAI(
                        model="deepseek-reasoner",
                        api_key=deepseek_key,
                        base_url=settings.DEEPSEEK_BASE_URL,
                        temperature=0
                    )
                except Exception:
                    pass

        # 3. Try Ollama (Local Fallback)
        if not hasattr(self, 'llm'):
            try:
                 # Check/Init Ollama
                 if os.getenv("OLLAMA_BASE_URL") or not api_key: 
                     from langchain_community.chat_models import ChatOllama
                     
                     # Model Selection Logic based on Agent Role (Tier)
                     model_name = "deepseek-r1" # Default fallback
                     
                     name_lower = self.name.lower()
                     
                     # Tier 1: Document Intelligence (Qwen2.5-32B)
                     if any(x in name_lower for x in ["document", "verifier", "tracker", "completeness", "chart"]):
                         model_name = "qwen2.5:32b"
                     
                     # Tier 2: Extraction (Llama-3.1-8B)
                     elif "extractor" in name_lower:
                         model_name = "llama3.1"
                     
                     # Tier 3 & 5: Benchmarking & Orchestrator (Qwen2.5-72B/32B - Reasoning Heavy)
                     elif any(x in name_lower for x in ["benchmark", "orchestrator"]):
                         model_name = "qwen2.5:32b" # Using 32b as safer default than 72b
                         
                     # Tier 4: Analysis (DeepSeek-R1 Distill)
                     elif "analysis" in name_lower:
                         model_name = "deepseek-r1"
                     
                     logging.info(f"Using Ollama ({model_name}) for {self.name}")
                     self.llm = ChatOllama(
                         model=model_name,
                         base_url=settings.OLLAMA_BASE_URL,
                         temperature=0
                     )
            except Exception as e:
                 logging.warning(f"Ollama initialization failed: {e}")

        # 3. Fallback to Gemini
        api_key = os.getenv("GOOGLE_API_KEY") or settings.GEMINI_API_KEY
        
        if not hasattr(self, 'llm'):
            if not api_key:
                logging.warning("No API Keys set (DeepSeek, Ollama, or Google). Agents will fail.")
            else:
                logging.info(f"Using Gemini (Fallback) for {self.name}")
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",  # Use 1.5-flash for better free tier quota
                    google_api_key=api_key,
                    temperature=0,
                    convert_system_message_to_human=True
                )
        self.agent_logs = []

    async def think_with_memory(self, task: str, context_categories: List[str], timeout_seconds: int = 180) -> str:
        """
        Agent thinks through a task with memory context.
        
        Args:
            task: The task/prompt for the LLM
            context_categories: Memory categories to retrieve context from
            timeout_seconds: Maximum time to wait for LLM response (default 180s = 3 minutes)
        """
        logging.info(f"{self.name} is thinking about: {task[:200]}...")  # Log truncated task
        
        # 1. Retrieve relevant memory
        relevant_memory_str = ""
        for category in context_categories:
            memories = await self.memory.retrieve_memory(query=task, category=category)
            if memories:
                relevant_memory_str += f"\n[{category.upper()} CONTEXT]:\n"
                for mem in memories:
                    # formatted string representation
                    relevant_memory_str += f"- {mem}\n"

        if not relevant_memory_str:
            relevant_memory_str = "No specific valid memories found for this context."

        # 2. Construct Prompt
        system_prompt = f"""You are {self.name}, an expert banking ESG analyst assistant supporting a loan credit process.

    GOAL
    - Produce bank-grade, audit-friendly analysis.

    HARD RULES (CRITICAL)
    - Use ONLY facts present in the provided MEMORY CONTEXT or explicitly provided in the task.
    - Never invent numbers, dates, peer counts, citations, or document references.
    - If information is missing, write "Not evidenced" / "Unknown" and explain what evidence would be required.
    - If the task requests JSON, output STRICT JSON only (no markdown fences, no commentary).
    - Do not reveal hidden chain-of-thought; provide conclusions + supporting evidence succinctly.

    MEMORY CONTEXT
    {relevant_memory_str}

    OUTPUT STYLE
    - Write like a credit memo / ESG due diligence note for a Credit Committee audience.
    - Keep language precise and professional.
    """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=task)
        ]

        # 3. Call LLM with Multi-Level Fallback and TIMEOUT
        import asyncio
        content = ""
        try:
            # ATTEMPT 1: Primary (OpenRouter / DeepSeek / Ollama as configured)
            logging.info(f"{self.name}: Attempting Primary LLM (timeout: {timeout_seconds}s)...")
            try:
                response = await asyncio.wait_for(
                    self.llm.ainvoke(messages),
                    timeout=timeout_seconds
                )
                content = response.content
                logging.info(f"{self.name}: LLM response received, length: {len(content)} chars")
            except asyncio.TimeoutError:
                logging.error(f"{self.name}: Primary LLM timed out after {timeout_seconds}s")
                raise Exception(f"LLM timeout after {timeout_seconds}s")
        except Exception as e1:
            logging.warning(f"Primary LLM failed: {e1}")
            
            # ATTEMPT 2: MoonshotAI Kimi (OpenRouter Free)
            try:
                logging.info(f"{self.name}: Attempting Fallback 1 - MoonshotAI Kimi...")
                openrouter_key = os.getenv("OPENROUTER_API_KEY")
                if openrouter_key:
                    from langchain_openai import ChatOpenAI
                    from app.config import settings
                    fallback_kimi = ChatOpenAI(
                        model="moonshotai/kimi-k2:free",
                        api_key=openrouter_key,
                        base_url=settings.OPENROUTER_BASE_URL,
                        temperature=0
                    )
                    response = await fallback_kimi.ainvoke(messages)
                    content = response.content
                else:
                    raise ValueError("No OpenRouter Key")
            except Exception as e2:
                logging.warning(f"Fallback 1 (MoonshotAI) failed: {e2}")
                
                # ATTEMPT 3: Bytez (GPT-4)
                try:
                    logging.info(f"{self.name}: Attempting Fallback 2 - Bytez GPT-4...")
                    bytez_key = os.getenv("BYTEZ_API_KEY")
                    if bytez_key:
                        from bytez import Bytez
                        client = Bytez(bytez_key)
                        model = client.model("openai/gpt-4")
                        
                        # Convert messages to Bytez format (simple string or list of dicts)
                        # We extract the last user prompt for simplicity or reconstruct basic history
                        user_msg = next((m.content for m in reversed(messages) if isinstance(m, HumanMessage)), task)
                        system_msg = next((m.content for m in messages if isinstance(m, SystemMessage)), "")
                        
                        bytez_messages = [
                            {"role": "system", "content": system_msg} if system_msg else None,
                            {"role": "user", "content": user_msg}
                        ]
                        bytez_messages = [m for m in bytez_messages if m] # Remove None
                        
                        results = model.run(bytez_messages)
                        if results.error:
                            raise ValueError(f"Bytez Error: {results.error}")
                        content = results.output
                    else:
                        raise ValueError("No Bytez Key")
                except Exception as e3:
                    logging.warning(f"Fallback 2 (Bytez) failed: {e3}")
                    
                    # ATTEMPT 4: Gemini (Final Safety Net)
                    try:
                        logging.info(f"{self.name}: Attempting Fallback 3 - Gemini...")
                         # Lazy init Gemini if not already primary
                        if not isinstance(self.llm, ChatGoogleGenerativeAI):
                             from app.config import settings
                             gemini_key = os.getenv("GOOGLE_API_KEY") or settings.GEMINI_API_KEY
                             if gemini_key:
                                 fallback_gemini = ChatGoogleGenerativeAI(
                                    model="gemini-1.5-flash",  # Use 1.5-flash for better free tier quota
                                    google_api_key=gemini_key,
                                    temperature=0,
                                    convert_system_message_to_human=True
                                )
                                 response = await fallback_gemini.ainvoke(messages)
                                 content = response.content
                             else:
                                 raise ValueError("No Gemini Key")
                        else:
                             raise ValueError("Gemini is already primary and failed")
                    except Exception as e4:
                         logging.error(f"ALL FALLBACKS FAILED. Final Error: {e4}")
                         content = f"Error: All AI providers failed. {e4}"
        
        # 4. Log
        self.agent_logs.append({
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "task": task,
            "response": content
        })

        return content

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
