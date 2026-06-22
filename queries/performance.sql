USE healthcare_rag;
GO
-- FINAL UPDATED PERFORMANCE VERSION
--------------------------------------------------
-- MILESTONE 3 PERFORMANCE TESTING
--------------------------------------------------

SET STATISTICS TIME ON;
SET STATISTICS IO ON;
GO

--------------------------------------------------
-- QUERY 1
-- Healthcare RAG Retrieval Query
--------------------------------------------------

SELECT q.query_id,
       rc.chunk_id,
       rc.relevance_score,
       c.chunk_text
FROM user_query q
JOIN retrieved_chunk rc
    ON q.query_id = rc.query_id
JOIN chunk c
    ON rc.chunk_id = c.chunk_id
WHERE q.query_id = 4
ORDER BY rc.relevance_score DESC;
GO

--------------------------------------------------
-- QUERY 2
-- Document Retrieval by Medical Speciality
--------------------------------------------------

SELECT d.title,
       d.medical_speciality,
       s.source_name
FROM document d
JOIN source s
    ON d.source_id = s.source_id
WHERE d.medical_speciality = 'Infectious Diseases';
GO

--------------------------------------------------
-- QUERY 3
-- Topic Lookup Query
--------------------------------------------------

SELECT ct.chunk_id,
       t.topic_name
FROM chunk_topic ct
JOIN topic t
    ON ct.topic_id = t.topic_id;
GO


--------------------------------------------------
-- INDEXES USED FOR OPTIMIZATION
--------------------------------------------------

CREATE NONCLUSTERED INDEX IX_Chunk_ChunkID
ON chunk(chunk_id)
INCLUDE (chunk_text);
GO

CREATE NONCLUSTERED INDEX IX_RetrievedChunk_QueryID_Cover
ON retrieved_chunk(query_id)
INCLUDE (chunk_id, relevance_score);
GO

CREATE NONCLUSTERED INDEX IX_Document_Speciality
ON document(medical_speciality);
GO

--------------------------------------------------
-- STORED PROCEDURE EXECUTION
--------------------------------------------------

/*
Uncomment if procedure exists

EXEC usp_GetChunksForQuery @QueryID = 4;
GO
*/

--------------------------------------------------
-- INDEX VERIFICATION
--------------------------------------------------

SELECT
    i.name AS index_name,
    t.name AS table_name
FROM sys.indexes i
JOIN sys.tables t
    ON i.object_id = t.object_id
WHERE i.name IS NOT NULL
ORDER BY t.name;
GO

--------------------------------------------------
-- DISABLE STATISTICS
--------------------------------------------------

SET STATISTICS TIME OFF;
SET STATISTICS IO OFF;
GO