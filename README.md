# Healthcare Intelligence Assistant  
### Retrieval-Augmented Generation Based Healthcare Decision Support System  

---

## Overview

The Healthcare Intelligence Assistant is a Retrieval-Augmented Generation (RAG) based healthcare decision support system designed to deliver evidence-based responses for medical queries using structured databases and semantic search techniques.

The system integrates relational database management, vector similarity search, and transformer-based embeddings to enable intelligent healthcare question answering with transparency, evaluation, and decision support capabilities.

It enhances traditional healthcare information retrieval by combining structured storage in SQL databases with semantic retrieval using vector embeddings, supported by an interactive web application.

---

## Academic Information

- Course: Database Management Systems  
- Institution: IIT Madras Zanzibar Campus  
- Project Type: Database Systems and Artificial Intelligence Integration  

---

## Authors

- Shambhavi Srivastava  
- Yashash Yallapragada  

---

## Key Features

- Semantic healthcare question answering system  
- Retrieval-Augmented Generation pipeline  
- Hybrid database architecture using SQL Server and PostgreSQL (pgvector)  
- Sentence transformer-based embeddings (all-MiniLM-L6-v2)  
- Rule-based severity classification system  
- Hospital recommendation using OpenStreetMap API  
- Response evaluation framework with multiple metrics  
- Interactive Streamlit-based web interface  
- Query logging and audit trail for analysis  

---

## System Architecture

The system is built on a hybrid architecture that combines relational databases with vector-based semantic search.

### Core Components

- Microsoft SQL Server  
  Stores structured healthcare data including documents, chunks, queries, responses, and evaluation records.

- PostgreSQL (pgvector)  
  Stores high-dimensional embeddings and performs semantic similarity search.

- Sentence Transformers  
  Converts healthcare text into dense vector representations for semantic matching.

- Streamlit  
  Provides an interactive user interface for querying and displaying results.

- OpenStreetMap API  
  Provides hospital location search and recommendation services.

---

## System Workflow

User Query  
→ Embedding Generation using Sentence Transformer  
→ Vector Similarity Search using pgvector  
→ Retrieval of Top-K Relevant Chunks  
→ Metadata Fetch from SQL Server  
→ Response Generation  
→ Severity Classification  
→ Hospital Recommendation (if required)  
→ Evaluation Metric Computation  
→ Display through Streamlit Interface  

---

## Database Design

The system uses 11 relational tables organized into structured categories.

### Core Entities

- Source  
- Document  
- Section  
- Chunk  
- Embedding  
- Topic  

### Relationship Tables

- Chunk_Topic (many-to-many relationship)  
- Retrieved_Chunk (many-to-many relationship between queries and chunks)  

### Transactional Tables

- User_Query  
- Response  
- Evaluation  

---

## Database Relationships

- Source → Document (1:N)  
- Document → Section (1:N)  
- Section → Chunk (1:N)  
- Chunk → Embedding (1:1)  
- Chunk ↔ Topic (M:N via Chunk_Topic)  
- Query ↔ Chunk (M:N via Retrieved_Chunk)  
- Query → Response (1:1)  
- Response → Evaluation (1:1)  

---

## Normalization

The database design follows Third Normal Form (3NF):

- No repeating groups (1NF)  
- No partial dependencies (2NF)  
- No transitive dependencies (3NF)  

This ensures data consistency, reduced redundancy, and efficient relational operations.

---

## Dataset Overview

- 1183+ healthcare text chunks  
- 1183+ embeddings  
- Approximately 70 user queries  
- Approximately 70 generated responses  
- Approximately 70 evaluation records  

### Data Sources

- World Health Organization (WHO)  
- Centers for Disease Control and Prevention (CDC)  
- Mayo Clinic  
- NIH / MedlinePlus  

---

## Chunk Generation

Healthcare documents are divided into semantic chunks to improve retrieval accuracy and reduce context complexity.

Each chunk contains:
- chunk identifier  
- chunk text  
- chunk index  
- section reference  

Chunking improves:
- retrieval precision  
- semantic matching quality  
- response relevance  
- computational efficiency  

---

## Embedding Generation

The system uses Sentence Transformers with the model all-MiniLM-L6-v2.

Each chunk is converted into a dense vector representation that preserves semantic meaning, enabling similarity-based retrieval instead of keyword matching.

---

## Hybrid Database Architecture

### SQL Server Responsibilities

- Structured healthcare data storage  
- Document and chunk management  
- Query logging  
- Response storage  
- Evaluation storage  

### PostgreSQL (pgvector) Responsibilities

- Storage of embeddings  
- Vector similarity search  
- Semantic ranking of chunks  

This hybrid approach combines relational integrity with high-performance semantic search capabilities.

---

## Semantic Retrieval Pipeline

1. User submits a healthcare query  
2. Query is converted into an embedding vector  
3. Vector similarity search is performed in pgvector  
4. Top-K relevant chunks are retrieved  
5. Metadata is fetched from SQL Server  
6. Response is generated  
7. Severity classification is applied  
8. Evaluation metrics are computed  

---

## Interactive Application

The system is deployed using Streamlit and provides the following functionalities:

- Healthcare question answering interface  
- Evidence-based retrieved chunk display  
- Confidence score visualization  
- Severity classification output  
- Hospital recommendation system  
- Evaluation metrics dashboard  
- Query tracking and logging  

---

## Severity Classification System

The system categorizes medical conditions into four risk levels:

- Emergency  
- High Risk  
- Moderate Risk  
- Low Risk  

Examples include:

Emergency cases: stroke, cardiac arrest, respiratory failure  
High risk cases: pneumonia, severe dengue, chest pain  
Moderate risk cases: diabetes, hypertension, malaria  

---

## Hospital Recommendation System

Hospital recommendations are generated using the OpenStreetMap Nominatim API.

If online retrieval fails, fallback city-based hospital lists are used for:

- Zanzibar  
- Dar es Salaam  
- Nairobi  
- Mombasa  

---

## Evaluation Framework

The system computes the following metrics:

- Confidence Score based on retrieval similarity  
- Factuality Score based on evidence strength  
- Consistency Score based on agreement among retrieved chunks  

All evaluation results are stored in the database for analysis and auditing.

---

## Key Results

- Improved retrieval accuracy using semantic embeddings  
- Reduced query execution time using optimized indexing  
- End-to-end explainable healthcare response generation  
- Fully integrated relational and vector database architecture  

---

## Limitations

- Rule-based severity classification limits medical reasoning capability  
- System depends on embedding model quality  
- Dataset size is limited to curated healthcare sources  
- External API dependency for hospital recommendations  

---

## Future Work

- Integration of large language models for improved response generation  
- Expansion of healthcare knowledge base  
- Advanced medical reasoning and diagnosis support  
- Improved recommendation and ranking systems  
- Real-time healthcare data integration  

---

## Conclusion

The Healthcare Intelligence Assistant demonstrates a complete implementation of a Retrieval-Augmented Generation system integrated with database management principles.

The project combines relational databases, semantic vector search, and machine learning embeddings to build an intelligent and explainable healthcare decision-support system.

It highlights the practical integration of database systems with modern AI techniques for real-world applications.

---

## Technology Stack

- Microsoft SQL Server  
- PostgreSQL (pgvector)  
- Python  
- Sentence Transformers  
- Streamlit  
- OpenStreetMap API  
