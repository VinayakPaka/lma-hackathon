-- GreenGuard ESG Platform - Supabase Vector Storage Setup
-- Run this in your Supabase SQL Editor

-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the document_embeddings table for storing vectors
CREATE TABLE IF NOT EXISTS document_embeddings (
    id TEXT PRIMARY KEY,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024),  -- Voyage AI voyage-3.5 default dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_document_embeddings_document_id 
ON document_embeddings(document_id);

CREATE INDEX IF NOT EXISTS idx_document_embeddings_created_at 
ON document_embeddings(created_at DESC);

-- Create the vector similarity search index (IVFFlat for better performance)
-- Adjust lists parameter based on your data size (lists = sqrt(n) where n is row count)
CREATE INDEX IF NOT EXISTS idx_document_embeddings_vector 
ON document_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Function to search for similar document chunks
CREATE OR REPLACE FUNCTION match_document_embeddings(
    query_embedding vector(1024),
    match_count INTEGER DEFAULT 5,
    filter_document_id INTEGER DEFAULT NULL
)
RETURNS TABLE (
    id TEXT,
    document_id INTEGER,
    chunk_index INTEGER,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        de.id,
        de.document_id,
        de.chunk_index,
        de.content,
        de.metadata,
        1 - (de.embedding <=> query_embedding) as similarity
    FROM document_embeddings de
    WHERE 
        CASE 
            WHEN filter_document_id IS NOT NULL THEN de.document_id = filter_document_id
            ELSE TRUE
        END
    ORDER BY de.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to delete embeddings for a document
CREATE OR REPLACE FUNCTION delete_document_embeddings(doc_id INTEGER)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM document_embeddings
    WHERE document_id = doc_id;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

-- Row Level Security (RLS) - Optional but recommended
-- Uncomment if you want to enable RLS

-- ALTER TABLE document_embeddings ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Users can view their own document embeddings" 
-- ON document_embeddings FOR SELECT
-- USING (true);  -- Adjust based on your auth setup

-- CREATE POLICY "Users can insert their own document embeddings" 
-- ON document_embeddings FOR INSERT
-- WITH CHECK (true);  -- Adjust based on your auth setup

-- CREATE POLICY "Users can delete their own document embeddings" 
-- ON document_embeddings FOR DELETE
-- USING (true);  -- Adjust based on your auth setup

-- Grant permissions to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON document_embeddings TO authenticated;
GRANT EXECUTE ON FUNCTION match_document_embeddings TO authenticated;
GRANT EXECUTE ON FUNCTION delete_document_embeddings TO authenticated;

-- Also grant to anon for development (remove in production)
GRANT SELECT, INSERT, UPDATE, DELETE ON document_embeddings TO anon;
GRANT EXECUTE ON FUNCTION match_document_embeddings TO anon;
GRANT EXECUTE ON FUNCTION delete_document_embeddings TO anon;

-- Verify setup
SELECT 
    'pgvector extension' as component,
    CASE WHEN EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') 
         THEN 'Installed' ELSE 'Missing' END as status
UNION ALL
SELECT 
    'document_embeddings table' as component,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'document_embeddings') 
         THEN 'Created' ELSE 'Missing' END as status
UNION ALL
SELECT 
    'match_document_embeddings function' as component,
    CASE WHEN EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'match_document_embeddings') 
         THEN 'Created' ELSE 'Missing' END as status;
