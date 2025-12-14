"""
GreenGuard ESG Platform - Embedding Service
Handles text chunking, embedding generation using Voyage AI, and vector storage in Supabase.
"""
import logging
import hashlib
from typing import List, Dict, Any, Optional
import voyageai
from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing document embeddings using Voyage AI."""
    
    def __init__(self):
        self._voyage_client: Optional[voyageai.Client] = None
        self._supabase_client: Optional[Client] = None
    
    @property
    def voyage_client(self) -> voyageai.Client:
        """Lazy initialization of Voyage AI client."""
        if self._voyage_client is None:
            if not settings.VOYAGE_API_KEY:
                raise ValueError("VOYAGE_API_KEY is not configured")
            self._voyage_client = voyageai.Client(api_key=settings.VOYAGE_API_KEY)
        return self._voyage_client
    
    @property
    def supabase(self) -> Client:
        """Lazy initialization of Supabase client."""
        if self._supabase_client is None:
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be configured")
            self._supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return self._supabase_client
    
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks for embedding.
        
        Args:
            text: The full document text
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        chunk_size = chunk_size or settings.CHUNK_SIZE
        overlap = overlap or settings.CHUNK_OVERLAP
        
        if not text or len(text.strip()) == 0:
            return []
        
        # Clean the text
        text = text.strip()
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for sep in ['. ', '.\n', '! ', '!\n', '? ', '?\n', '\n\n']:
                    last_sep = text[start:end].rfind(sep)
                    if last_sep != -1:
                        end = start + last_sep + len(sep)
                        break
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    "index": chunk_index,
                    "text": chunk_text,
                    "start_char": start,
                    "end_char": end,
                    "token_count": len(chunk_text.split())  # Approximate token count
                })
                chunk_index += 1
            
            start = end - overlap
            if start >= len(text) - overlap:
                break
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def generate_embedding(self, text: str, input_type: str = "document") -> List[float]:
        """
        Generate embedding for a text using Voyage AI.
        
        Args:
            text: Text to embed
            input_type: Either "document" or "query" for optimal retrieval
            
        Returns:
            Embedding vector as list of floats
        """
        if not settings.VOYAGE_API_KEY:
            logger.error("VOYAGE_API_KEY is not configured")
            raise ValueError("VOYAGE_API_KEY is not configured")
        
        if not text or len(text.strip()) == 0:
            logger.error("Cannot generate embedding for empty text")
            raise ValueError("Text cannot be empty")
        
        logger.debug(f"Generating embedding for text of length {len(text)}")
        
        try:
            result = self.voyage_client.embed(
                texts=[text],
                model=settings.VOYAGE_EMBEDDING_MODEL,
                input_type=input_type,
                output_dimension=settings.EMBEDDING_DIMENSION
            )
            logger.debug(f"Successfully generated embedding with dimension {len(result.embeddings[0])}")
            return result.embeddings[0]
        except Exception as e:
            logger.error(f"Error generating embedding: {type(e).__name__}: {str(e)}")
            raise
    
    def generate_embeddings_batch(
        self, 
        texts: List[str], 
        input_type: str = "document"
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch using Voyage AI.
        
        Args:
            texts: List of texts to embed
            input_type: Either "document" or "query" for optimal retrieval
            
        Returns:
            List of embedding vectors
        """
        if not settings.VOYAGE_API_KEY:
            logger.error("VOYAGE_API_KEY is not configured")
            raise ValueError("VOYAGE_API_KEY is not configured")
        
        if not texts:
            logger.error("Cannot generate embeddings for empty text list")
            raise ValueError("Text list cannot be empty")
        
        # Filter out empty texts
        valid_texts = [t for t in texts if t and len(t.strip()) > 0]
        if len(valid_texts) != len(texts):
            logger.warning(f"Filtered out {len(texts) - len(valid_texts)} empty texts")
        
        logger.info(f"Generating embeddings for {len(valid_texts)} texts using model {settings.VOYAGE_EMBEDDING_MODEL}")
        
        try:
            # Voyage AI supports up to 1000 texts per batch
            # Process in batches of 128 for efficiency
            batch_size = 128
            all_embeddings = []
            
            for i in range(0, len(valid_texts), batch_size):
                batch = valid_texts[i:i + batch_size]
                logger.debug(f"Processing batch {i//batch_size + 1} with {len(batch)} texts")
                
                result = self.voyage_client.embed(
                    texts=batch,
                    model=settings.VOYAGE_EMBEDDING_MODEL,
                    input_type=input_type,
                    output_dimension=settings.EMBEDDING_DIMENSION
                )
                all_embeddings.extend(result.embeddings)
                logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{(len(valid_texts) + batch_size - 1)//batch_size}")
            
            logger.info(f"Successfully generated {len(all_embeddings)} embeddings")
            return all_embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def store_embeddings(
        self, 
        document_id: int, 
        chunks: List[Dict[str, Any]], 
        embeddings: List[List[float]]
    ) -> List[str]:
        """
        Store embeddings in Supabase vector store.
        
        Args:
            document_id: ID of the source document
            chunks: List of chunk dictionaries
            embeddings: List of embedding vectors
            
        Returns:
            List of embedding IDs
        """
        embedding_ids = []
        
        for chunk, embedding in zip(chunks, embeddings):
            # Generate unique ID for this embedding
            content_hash = hashlib.md5(chunk["text"].encode()).hexdigest()[:12]
            embedding_id = f"doc_{document_id}_chunk_{chunk['index']}_{content_hash}"
            
            try:
                # Insert into Supabase
                data = {
                    "id": embedding_id,
                    "document_id": document_id,
                    "chunk_index": chunk["index"],
                    "content": chunk["text"],
                    "embedding": embedding,
                    "metadata": {
                        "start_char": chunk["start_char"],
                        "end_char": chunk["end_char"],
                        "token_count": chunk["token_count"]
                    }
                }
                
                self.supabase.table("document_embeddings").upsert(data).execute()
                embedding_ids.append(embedding_id)
                
            except Exception as e:
                logger.error(f"Error storing embedding {embedding_id}: {str(e)}")
                raise
        
        logger.info(f"Stored {len(embedding_ids)} embeddings for document {document_id}")
        return embedding_ids
    
    def search_similar(
        self, 
        query: str, 
        document_id: Optional[int] = None,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using vector similarity.
        
        Args:
            query: Query text
            document_id: Optional - filter to specific document
            top_k: Number of results to return
            
        Returns:
            List of similar chunks with scores
        """
        top_k = top_k or settings.TOP_K_RETRIEVAL
        
        # Generate query embedding with input_type="query" for better retrieval
        query_embedding = self.generate_embedding(query, input_type="query")
        
        try:
            # Call Supabase RPC function for vector similarity search
            params = {
                "query_embedding": query_embedding,
                "match_count": top_k
            }
            
            if document_id:
                params["filter_document_id"] = document_id
            
            result = self.supabase.rpc("match_document_embeddings", params).execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Error searching similar chunks: {str(e)}")
            raise
    
    def delete_document_embeddings(self, document_id: int) -> bool:
        """
        Delete all embeddings for a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Success status
        """
        try:
            self.supabase.table("document_embeddings").delete().eq(
                "document_id", document_id
            ).execute()
            logger.info(f"Deleted embeddings for document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting embeddings: {str(e)}")
            return False
    
    async def process_document(self, document_id: int, text: str) -> Dict[str, Any]:
        """
        Full pipeline: chunk text, generate embeddings, store in Supabase.
        
        Args:
            document_id: Document ID
            text: Full document text
            
        Returns:
            Processing summary
        """
        # Step 1: Chunk the text
        chunks = self.chunk_text(text)
        
        if not chunks:
            return {"status": "error", "message": "No text to process"}
        
        # Step 2: Generate embeddings in batch
        chunk_texts = [c["text"] for c in chunks]
        embeddings = self.generate_embeddings_batch(chunk_texts, input_type="document")
        
        # Step 3: Store in Supabase
        embedding_ids = self.store_embeddings(document_id, chunks, embeddings)
        
        return {
            "status": "success",
            "document_id": document_id,
            "chunks_created": len(chunks),
            "embeddings_stored": len(embedding_ids),
            "embedding_ids": embedding_ids
        }


# Singleton instance
embedding_service = EmbeddingService()
