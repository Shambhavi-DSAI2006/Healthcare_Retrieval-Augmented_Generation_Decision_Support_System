-- =========================================================
-- SCHEMA: Healthcare RAG System
-- Fully reproducible, normalized (3NF), and constraint-complete
-- Runs from scratch with no manual edits
-- =========================================================

-- Enable pgvector extension (required for embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- =========================================================
-- DROP TABLES (safe restart)
-- =========================================================
DROP TABLE IF EXISTS Evaluation CASCADE;
DROP TABLE IF EXISTS Retrieved_Chunk CASCADE;
DROP TABLE IF EXISTS Chunk_Topic CASCADE;
DROP TABLE IF EXISTS Response CASCADE;
DROP TABLE IF EXISTS Query CASCADE;
DROP TABLE IF EXISTS Topic CASCADE;
DROP TABLE IF EXISTS Embedding CASCADE;
DROP TABLE IF EXISTS Chunk CASCADE;
DROP TABLE IF EXISTS Section CASCADE;
DROP TABLE IF EXISTS Document CASCADE;
DROP TABLE IF EXISTS Source CASCADE;

-- =========================================================
-- 1. SOURCE
-- Stores data sources (WHO, CDC, etc.)
-- =========================================================
CREATE TABLE Source (
    source_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    url VARCHAR(500) UNIQUE,
    source_reliability DECIMAL(3,2) NOT NULL
        CHECK (source_reliability >= 0 AND source_reliability <= 1)
);

-- =========================================================
-- 2. DOCUMENT
-- Each document belongs to one source (1:N)
-- =========================================================
CREATE TABLE Document (
    document_id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    publication_date DATE,
    source_id INT NOT NULL,
    document_type VARCHAR(100),
    medical_speciality VARCHAR(100),
    FOREIGN KEY (source_id)
        REFERENCES Source(source_id)
        ON DELETE CASCADE
);

-- =========================================================
-- 3. SECTION
-- Documents divided into sections
-- =========================================================
CREATE TABLE Section (
    section_id SERIAL PRIMARY KEY,
    section_title VARCHAR(255) NOT NULL,
    document_id INT NOT NULL,
    FOREIGN KEY (document_id)
        REFERENCES Document(document_id)
        ON DELETE CASCADE
);

-- =========================================================
-- 4. CHUNK
-- Sections split into chunks for retrieval
-- =========================================================
CREATE TABLE Chunk (
    chunk_id SERIAL PRIMARY KEY,
    chunk_text TEXT NOT NULL,
    chunk_index INT NOT NULL,
    section_id INT NOT NULL,
    FOREIGN KEY (section_id)
        REFERENCES Section(section_id)
        ON DELETE CASCADE
);

-- =========================================================
-- 5. EMBEDDING (1:1 with Chunk)
-- Vector representation for semantic search
-- =========================================================
CREATE TABLE Embedding (
    embedding_id SERIAL PRIMARY KEY,
    chunk_id INT UNIQUE NOT NULL,
    vector vector(1536),
    FOREIGN KEY (chunk_id)
        REFERENCES Chunk(chunk_id)
        ON DELETE CASCADE
);

-- =========================================================
-- 6. TOPIC
-- Semantic categories for chunks
-- =========================================================
CREATE TABLE Topic (
    topic_id SERIAL PRIMARY KEY,
    topic_name VARCHAR(255) UNIQUE NOT NULL
);

-- =========================================================
-- 7. CHUNK_TOPIC (M:N)
-- Prevents duplicate mappings via composite PK
-- =========================================================
CREATE TABLE Chunk_Topic (
    chunk_id INT NOT NULL,
    topic_id INT NOT NULL,
    PRIMARY KEY (chunk_id, topic_id),
    FOREIGN KEY (chunk_id)
        REFERENCES Chunk(chunk_id)
        ON DELETE CASCADE,
    FOREIGN KEY (topic_id)
        REFERENCES Topic(topic_id)
        ON DELETE CASCADE
);

-- =========================================================
-- 8. QUERY
-- Stores user queries
-- =========================================================
CREATE TABLE Query (
    query_id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 9. RESPONSE (1:1 with Query)
-- Each query generates one response
-- =========================================================
CREATE TABLE Response (
    response_id SERIAL PRIMARY KEY,
    query_id INT UNIQUE NOT NULL,
    generated_answer TEXT NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL
        CHECK (confidence_score >= 0 AND confidence_score <= 1),
    FOREIGN KEY (query_id)
        REFERENCES Query(query_id)
        ON DELETE CASCADE
);

-- =========================================================
-- 10. RETRIEVED_CHUNK (M:N)
-- Tracks retrieved chunks per query
-- =========================================================
CREATE TABLE Retrieved_Chunk (
    query_id INT NOT NULL,
    chunk_id INT NOT NULL,
    relevance_score DECIMAL(5,4) NOT NULL
        CHECK (relevance_score >= 0 AND relevance_score <= 1),
    PRIMARY KEY (query_id, chunk_id),
    FOREIGN KEY (query_id)
        REFERENCES Query(query_id)
        ON DELETE CASCADE,
    FOREIGN KEY (chunk_id)
        REFERENCES Chunk(chunk_id)
        ON DELETE CASCADE
);

-- =========================================================
-- 11. EVALUATION (1:1 with Response)
-- Stores quality metrics for responses
-- =========================================================
CREATE TABLE Evaluation (
    evaluation_id SERIAL PRIMARY KEY,
    response_id INT UNIQUE NOT NULL,
    factuality_score DECIMAL(3,2) NOT NULL
        CHECK (factuality_score >= 0 AND factuality_score <= 1),
    consistency_score DECIMAL(3,2) NOT NULL
        CHECK (consistency_score >= 0 AND consistency_score <= 1),
    notes TEXT,
    response_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (response_id)
        REFERENCES Response(response_id)
        ON DELETE CASCADE
);