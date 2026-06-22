-- =========================================================
-- HEALTHCARE RAG ANALYTICAL SQL QUERIES
-- =========================================================

-- Project:
-- Retrieval-Augmented Generation (RAG) Healthcare Dataset

-- Description:
-- This file contains analytical SQL queries designed
-- to evaluate and analyze:

--   - semantic chunk distribution
--   - AI response reliability
--   - retrieval effectiveness
--   - topic coverage
--   - confidence scoring
--   - semantic relevance ranking

-- Query Categories:
--   1. Aggregation Queries
--   2. Join Queries
--   3. Subqueries
--   4. CTE Queries
--   5. Window Function Queries

-- Database:
-- PostgreSQL

-- =========================================================


-- =========================================================
-- AGGREGATION QUERIES
-- Used for dataset statistics and reliability analysis
-- =========================================================

-- Query 1: Count number of chunks in each section

SELECT 
    section_id,
    COUNT(*) AS total_chunks
FROM chunk
GROUP BY section_id
ORDER BY total_chunks DESC;


-- Query 2: Average factuality and consistency scores

SELECT
    AVG(factuality_score) AS avg_factuality,
    AVG(consistency_score) AS avg_consistency
FROM evaluation;


-- Query 3: Total number of user queries

SELECT
    COUNT(*) AS total_queries
FROM user_query;


-- Query 4: Average confidence score of generated responses

SELECT
    AVG(confidence_score) AS average_confidence
FROM response;


-- =========================================================
-- JOIN QUERIES
-- Used for relational analysis across RAG tables
-- =========================================================

-- Query 5: Show responses with their factuality and consistency scores

SELECT
    response.response_id,
    response.generated_answer,
    evaluation.factuality_score,
    evaluation.consistency_score
FROM response
JOIN evaluation
ON response.response_id = evaluation.response_id;


-- Query 6: Show chunk text with associated topic names

SELECT
    chunk.chunk_id,
    chunk.chunk_text,
    topic.topic_name
FROM chunk
JOIN chunk_topic
ON chunk.chunk_id = chunk_topic.chunk_id
JOIN topic
ON chunk_topic.topic_id = topic.topic_id;


-- =========================================================
-- SUBQUERY ANALYSIS
-- Used for comparative semantic analysis
-- =========================================================

-- Query 7: Find responses with confidence score higher than average

SELECT
    response_id,
    generated_answer,
    confidence_score
FROM response
WHERE confidence_score > (
    SELECT AVG(confidence_score)
    FROM response
);


-- Query 8: Find chunks that have above-average relevance scores

SELECT
    query_id,
    chunk_id,
    relevance_score
FROM retrieved_chunk
WHERE relevance_score > (
    SELECT AVG(relevance_score)
    FROM retrieved_chunk
);


-- =========================================================
-- COMMON TABLE EXPRESSIONS (CTEs)
-- Used for modular analytical workflows
-- =========================================================

-- Query 9: Average chunk relevance per query using CTE

WITH relevance_summary AS (
    SELECT
        query_id,
        AVG(relevance_score) AS avg_relevance
    FROM retrieved_chunk
    GROUP BY query_id
)

SELECT *
FROM relevance_summary
ORDER BY avg_relevance DESC;


-- Query 10: Count chunks per topic using CTE

WITH topic_chunk_count AS (
    SELECT
        topic.topic_name,
        COUNT(chunk_topic.chunk_id) AS total_chunks
    FROM topic
    JOIN chunk_topic
    ON topic.topic_id = chunk_topic.topic_id
    GROUP BY topic.topic_name
)

SELECT *
FROM topic_chunk_count
ORDER BY total_chunks DESC;


-- =========================================================
-- WINDOW FUNCTION ANALYSIS
-- Used for ranking and retrieval prioritization
-- =========================================================

-- Query 11: Rank responses by confidence score

SELECT
    response_id,
    confidence_score,
    RANK() OVER (ORDER BY confidence_score DESC) AS confidence_rank
FROM response;


-- Query 12: Rank chunks by relevance score within each query

SELECT
    query_id,
    chunk_id,
    relevance_score,
    ROW_NUMBER() OVER (
        PARTITION BY query_id
        ORDER BY relevance_score DESC
    ) AS relevance_rank
FROM retrieved_chunk;