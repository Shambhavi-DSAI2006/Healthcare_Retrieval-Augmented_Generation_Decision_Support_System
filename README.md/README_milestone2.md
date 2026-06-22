# Healthcare RAG Pipeline Dataset
https://github.com/Yashash-Yallapragada/Healthcare-RAG
## Project Overview

This project implements a Retrieval-Augmented Generation (RAG) healthcare question-answering dataset using structured relational data and semantic embeddings.

The system simulates:
- healthcare document storage
- chunk-based retrieval
- semantic embeddings
- AI-generated responses
- reliability evaluation

The dataset is designed for Track A requirements.




# Dataset Structure

## Tables

### source.csv
Stores healthcare organizations and information sources.

### document.csv
Stores healthcare documents and reports.

### section.csv
Stores sections belonging to documents.

### chunk.csv
Stores text chunks generated from healthcare documents.

### embedding.csv
Stores semantic vector embeddings generated using sentence-transformers.

### topic.csv
Stores healthcare topics.

### chunk_topic.csv
Maps chunks to topics.

### query.csv
Stores simulated user healthcare queries.

### response.csv
Stores generated AI responses.

### retrieved_chunk.csv
Stores retrieved chunks associated with queries.

### evaluation.csv
Stores factuality and consistency evaluation scores.



# Embedding Model

Embeddings were generated using:

- sentence-transformers
- all-MiniLM-L6-v2

# Data Dictionary

## source.csv

| Column | Description | Data Type | Allowed Values / Notes |
|---|---|---|---|
| source_id | Unique identifier for healthcare source | INT | Positive integer |
| source_name | Name of healthcare organization | VARCHAR | WHO, CDC, NIH, etc. |
| organization_type | Type of organization | VARCHAR | Government, Research, Public Health |
| source_url | Official source website URL | VARCHAR | Valid URL |
| source_reliability | Reliability/confidence metadata for source | VARCHAR | Typically 0.00–1.00 |

---

## document.csv

| Column | Description | Data Type | Allowed Values / Notes |
|---|---|---|---|
| document_id | Unique identifier for document | INT | Positive integer |
| title | Title of healthcare document | VARCHAR | Medical document titles |
| publication_date | Publication date of document | VARCHAR | DD-MM-YYYY |
| source_id | References source table | INT | Existing source_id |
| document_type | Type of document | VARCHAR | Guideline, Report, Article |
| medical_speciality | Medical domain/category | VARCHAR | Cardiology, Infectious Disease, etc. |

---

## section.csv

| Column | Description | Data Type | Allowed Values / Notes |
|---|---|---|---|
| section_id | Unique identifier for section | INT | Positive integer |
| document_id | References document table | INT | Existing document_id |
| section_title | Section heading/title | VARCHAR | Symptoms, Prevention, Treatment |

---

## chunk.csv

| Column | Description | Data Type | Allowed Values / Notes |
|---|---|---|---|
| chunk_id | Unique identifier for semantic chunk | SMALLINT | Positive integer |
| chunk_text | Semantic healthcare text chunk | VARCHAR(MAX) | Natural language healthcare text |
| chunk_index | Positional order of chunk within section | INT | Positive integer |
| section_id | References section table | INT | Existing section_id |

---

## embedding.csv

| Column | Description | Data Type | Allowed Values / Notes |
|---|---|---|---|
| embedding_id | Unique embedding identifier | INT | Positive integer |
| chunk_id | References chunk table | SMALLINT | Existing chunk_id |
| embedding_model | Embedding model used | VARCHAR | all-MiniLM-L6-v2 |
| embedding_vector | Semantic embedding vector | VARCHAR(MAX) | Vector representation of chunk |

---

## topic.csv

| Column | Description | Data Type | Allowed Values / Notes |
|---|---|---|---|
| topic_id | Unique topic identifier | SMALLINT | Positive integer |
| topic_name | Healthcare topic name | VARCHAR | Dengue, Diabetes, Asthma |
| topic_category | Topic classification category | VARCHAR | Infectious Disease, Mental Health |

---

## chunk_topic.csv

| Column | Description | Data Type | Allowed Values / Notes |
|---|---|---|---|
| chunk_id | References chunk table | SMALLINT | Existing chunk_id |
| topic_id | References topic table | SMALLINT | Existing topic_id |

---

## user_query.csv

| Column | Description | Data Type | Allowed Values / Notes |
|---|---|---|---|
| query_id | Unique query identifier | INT | Positive integer |
| query_text | Realistic healthcare user query | VARCHAR(MAX) | Natural language query |
| query_timestamp | Timestamp of query | DATETIME | DD-MM-YYYY HH:MM:SS |

---

## retrieved_chunk.csv

| Column | Description | Data Type | Allowed Values / Notes |
|---|---|---|---|
| query_id | References user_query table | INT | Existing query_id |
| chunk_id | References chunk table | SMALLINT | Existing chunk_id |
| relevance_score | Semantic retrieval relevance score | DECIMAL(4,3) | 0.000–1.000 |

---

## response.csv

| Column | Description | Data Type | Allowed Values / Notes |
|---|---|---|---|
| response_id | Unique response identifier | INT | Positive integer |
| query_id | References user_query table | INT | Existing query_id |
| generated_answer | AI-generated healthcare response | NVARCHAR(MAX) | Natural language answer |
| confidence_score | Confidence score for response | DECIMAL(4,3) | 0.000–1.000 |

---

## evaluation.csv

| Column | Description | Data Type | Allowed Values / Notes |
|---|---|---|---|
| evaluation_id | Unique evaluation identifier | INT | Positive integer |
| response_id | References response table | INT | Existing response_id |
| factuality_score | Factual correctness score | DECIMAL(4,3) | 0.000–1.000 |
| consistency_score | Logical consistency score | DECIMAL(4,3) | 0.000–1.000 |
| notes | Reliability evaluation notes | VARCHAR(MAX) | Natural language evaluation |
| response_timestamp | Timestamp of evaluation | DATETIME | DD-MM-YYYY HH:MM:SS |

---

# Dataset Notes

- The dataset contains 1183+ semantic healthcare chunks.
- User queries were expanded from 15 to 70 realistic healthcare queries to improve behavioral realism.
- AI-generated responses and evaluation metrics were similarly expanded to simulate realistic RAG system interaction.
- Semantic embeddings were generated using sentence-transformers (`all-MiniLM-L6-v2`).
- Retrieval mappings simulate semantic top-k chunk retrieval behavior in a healthcare RAG pipeline.



# Dataset Statistics

- Total chunks: 1183+
- Total embeddings: 1183+
- Healthcare topics included:
  - dengue
  - malaria
  - diabetes
  - hypertension
  - asthma
  - nutrition
  - mental health
  - cardiovascular diseases




# Data Sources

Healthcare information was collected from publicly available trusted sources including:

- WHO
- CDC
- Mayo Clinic
- NIH / MedlinePlus




# Query Coverage

The SQL queries include:

- aggregation queries
- join queries
- subqueries
- CTE queries
- window function queries




# Import Instructions

## Step 1: Create PostgreSQL Database

CREATE DATABASE healthcare_rag;

Connect to the database:

\c healthcare_rag




## Step 2: Execute Schema

\i queries/schema.sql




## Step 3: Import CSV Files

COPY source
FROM 'data/source.csv'
DELIMITER ','
CSV HEADER;

COPY document
FROM 'data/document.csv'
DELIMITER ','
CSV HEADER;

COPY section
FROM 'data/section.csv'
DELIMITER ','
CSV HEADER;

COPY chunk
FROM 'data/chunk.csv'
DELIMITER ','
CSV HEADER;

COPY embedding
FROM 'data/embedding.csv'
DELIMITER ','
CSV HEADER;

COPY topic
FROM 'data/topic.csv'
DELIMITER ','
CSV HEADER;

COPY chunk_topic
FROM 'data/chunk_topic.csv'
DELIMITER ','
CSV HEADER;

COPY query
FROM 'data/query.csv'
DELIMITER ','
CSV HEADER;

COPY retrieved_chunk
FROM 'data/retrieved_chunk.csv'
DELIMITER ','
CSV HEADER;

COPY response
FROM 'data/response.csv'
DELIMITER ','
CSV HEADER;

COPY evaluation
FROM 'data/evaluation.csv'
DELIMITER ','
CSV HEADER;




## Step 4: Execute SQL Queries

\i queries/queries.sql




# AI Usage Disclosure

AI assistance was used for:
- dataset planning
- SQL query drafting
- documentation support
- embedding workflow guidance

All generated data and project structure were reviewed and validated manually.
