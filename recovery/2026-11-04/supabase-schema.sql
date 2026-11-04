-- New table only. Existing v1 documents are untouched.
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;
CREATE TABLE IF NOT EXISTS public.ragb_documents_v2 (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 chunk_key text UNIQUE NOT NULL,
 content text NOT NULL,
 metadata jsonb NOT NULL,
 embedding extensions.vector(768) NOT NULL
);
ALTER TABLE public.ragb_documents_v2 ENABLE ROW LEVEL SECURITY;
CREATE OR REPLACE FUNCTION public.ragb_match_documents_v2(
 query_embedding extensions.vector(768), match_threshold double precision,
 match_count integer, model_name text
) RETURNS TABLE(id bigint, content text, metadata jsonb, similarity double precision)
LANGUAGE sql STABLE SET search_path = public, extensions AS $$
 SELECT d.id,d.content,d.metadata,1-(d.embedding <=> query_embedding)
 FROM public.ragb_documents_v2 d
 WHERE d.metadata->>'embedding_model'=model_name
 AND 1-(d.embedding <=> query_embedding) >= match_threshold
 ORDER BY d.embedding <=> query_embedding LIMIT LEAST(match_count,10);
$$;
REVOKE ALL ON FUNCTION public.ragb_match_documents_v2(extensions.vector,double precision,integer,text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.ragb_match_documents_v2(extensions.vector,double precision,integer,text) TO service_role;
GRANT ALL ON public.ragb_documents_v2 TO service_role;
GRANT USAGE, SELECT ON SEQUENCE public.ragb_documents_v2_id_seq TO service_role;
