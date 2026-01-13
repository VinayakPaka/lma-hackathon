import os
import json
import logging
from typing import Any, Dict, List, Optional

try:
    from supermemory import Supermemory
    SUPERMEMORY_AVAILABLE = True
except ImportError:
    SUPERMEMORY_AVAILABLE = False
    logging.warning("Supermemory not found. MemoryStore will fail if used.")

class MemoryStore:
    """
    Wrapper for Supermemory integration to store and retrieve agent memories.
    """
    
    
    def __init__(self, api_key: Optional[str] = None):
        from app.config import settings
        self.api_key = api_key or os.getenv("SUPERMEMORY_API_KEY") or settings.SUPERMEMORY_API_KEY
        if not self.api_key:
            logging.warning("SUPERMEMORY_API_KEY not set.")
        
        self.client = None
        # Local fallback store so the agent pipeline works without Supermemory.
        # Format: list of dicts with keys: category, key, value, metadata
        self._local_facts: List[Dict[str, Any]] = []
        if SUPERMEMORY_AVAILABLE:
            try:
                # Assuming standard initialization for Supermemory SDK
                self.client = Supermemory(api_key=self.api_key)
            except Exception as e:
                logging.error(f"Failed to initialize Supermemory client: {e}")

    async def store_fact(self, category: str, key: str, value: Any, 
                        metadata: Optional[Dict] = None):
        """Store a fact in memory."""
        # ALWAYS store locally as well for immediate retrieval fallback
        # (Supermemory indexing can have delays)
        local_entry = {
            "category": category,
            "key": key,
            "value": value,
            "metadata": {"category": category, "key": key, **(metadata or {})},
        }
        self._local_facts.append(local_entry)
        
        if not self.client:
            logging.info(f"Stored fact locally: {category}/{key}")
            return

        # Prepare payload
        content = json.dumps({
            "category": category,
            "key": key,
            "value": value
        })
        
        full_metadata = {"category": category, "key": key}
        if metadata:
            full_metadata.update(metadata)

        try:
            # Supermemory add/ingest method (hypothetical, based on typical SDKs)
            # Adjust if the actual API differs (e.g. client.add_memory)
            if hasattr(self.client, 'add'):
                self.client.add(content=content, metadata=full_metadata)
            elif hasattr(self.client, 'create'):
                self.client.create(content=content, metadata=full_metadata)
            else:
                 logging.warning(f"Supermemory 'add' method not found. Available: {[m for m in dir(self.client) if not m.startswith('_')]}")
            
            logging.info(f"Stored fact in Supermemory: {category}/{key}")
        except Exception as e:
            logging.error(f"Error storing fact in Supermemory: {e}")

    async def retrieve_memory(self, query: str, category: Optional[str] = None) -> List[Dict]:
        """Retrieve memories using semantic search."""
        if not self.client:
            # Simple local retrieval: rank by substring hits in JSON-dumped value.
            q = (query or "").lower()
            results: List[Dict[str, Any]] = []
            for item in reversed(self._local_facts):
                if category and item.get("category") != category:
                    continue
                haystack = json.dumps(item, default=str).lower()
                if not q or q in haystack:
                    results.append({
                        "category": item.get("category"),
                        "key": item.get("key"),
                        "value": item.get("value"),
                        "metadata": item.get("metadata", {}),
                    })
                if len(results) >= 5:
                    break
            return results

        try:
            # Supermemory query/search method
            # Adjusted based on "SearchResource object is not callable"
            if hasattr(self.client, 'search') and callable(self.client.search):
                 # It's a method
                 response = self.client.search(query=query, top_k=5)
            elif hasattr(self.client, 'search'):
                 # It's a resource/object with documented methods: execute, memories, documents
                 search_res = self.client.search
                 if hasattr(search_res, 'execute'):
                    # execute likely takes 'q' and 'limit' or just 'q'
                    response = search_res.execute(q=query) # Removed top_k as it caused error
                 elif hasattr(search_res, 'memories'):
                    response = search_res.memories(query=query, limit=5) # standard name
                 else:
                    logging.error(f"Supermemory search resource methods: {[m for m in dir(search_res) if not m.startswith('_')]}")
                    return []
            elif hasattr(self.client, 'query'):
                 response = self.client.query(query=query, top_k=5)
            else:
                 # Fallback/Debug
                 methods = [m for m in dir(self.client) if not m.startswith('_')]
                 logging.error(f"Supermemory method not found. Available: {methods}")
                 return []
            
            # Parse response - assuming list of objects with 'content' and 'metadata'
            memories = []
            
            # Normalize response format (it might be a dict or list of objects)
            # Fix: Handle object attribute access vs dict access safely
            results = []
            if isinstance(response, list):
                results = response
            elif hasattr(response, 'results'):
                results = getattr(response, 'results', []) or []
            elif hasattr(response, 'get'):
                results = response.get('results', []) or []
            else:
                 # It might be an iterable object itself
                 try:
                     iter(response)
                     results = response
                 except:
                     logging.warning(f"Unknown response type: {type(response)}")

            for res in results:
                # Accessing attributes or dict keys depending on SDK return type
                # Handle Pydantic V1/V2 or Dict
                content = getattr(res, 'content', None) or (res.get('content') if hasattr(res, 'get') else None)
                meta = getattr(res, 'metadata', None) or (res.get('metadata', {}) if hasattr(res, 'get') else {})
                
                # Filter by category if possible (client-side)
                if category and isinstance(meta, dict) and meta.get('category') != category:
                    continue
                
                try:
                    if content:
                        # Try to parse if it looks like JSON, otherwise keep raw
                        if isinstance(content, str) and (content.startswith('{') or content.startswith('[')):
                             loaded = json.loads(content)
                             # If loaded has category/key/value structure, preserve it
                             if isinstance(loaded, dict):
                                 # Enrich with metadata if not present
                                 if "metadata" not in loaded and meta:
                                     loaded["metadata"] = meta
                                 memories.append(loaded)
                             else:
                                 memories.append({"raw": content, "metadata": meta, "parsed": loaded})
                        else:
                             memories.append({"raw": content, "metadata": meta})
                except Exception as parse_err:
                    logging.debug(f"MemoryStore: Failed to parse content as JSON: {parse_err}")
                    memories.append({"raw": content, "metadata": meta})
            
            # Fallback to local facts if Supermemory returned nothing
            # (common during indexing delays)
            if not memories:
                logging.debug(f"MemoryStore: Supermemory returned empty, falling back to local facts")
                memories = self._search_local_facts(query, category)
            
            return memories
        except Exception as e:
            logging.error(f"Error retrieving memory from Supermemory: {e}")
            # Try local fallback on error
            return self._search_local_facts(query, category)

    def _search_local_facts(self, query: str, category: Optional[str] = None, limit: int = 5) -> List[Dict]:
        """Search local facts as fallback."""
        q = (query or "").lower()
        results: List[Dict[str, Any]] = []
        for item in reversed(self._local_facts):
            if category and item.get("category") != category:
                continue
            haystack = json.dumps(item, default=str).lower()
            if not q or any(word in haystack for word in q.split()):
                results.append({
                    "category": item.get("category"),
                    "key": item.get("key"),
                    "value": item.get("value"),
                    "metadata": item.get("metadata", {}),
                })
            if len(results) >= limit:
                break
        return results
