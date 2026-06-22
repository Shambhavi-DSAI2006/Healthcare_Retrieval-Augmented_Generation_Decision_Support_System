# 🏥 Healthcare Intelligence Assistant

## Project Information

**Course:** Z2004 – Database Management Systems
**Institution:** IIT Madras Zanzibar
**Project:** Healthcare Retrieval-Augmented Generation (Healthcare RAG) System
**Authors:** Shambhavi, Yashash

---

## Project Overview

Healthcare Intelligence Assistant is a Retrieval-Augmented Generation (RAG) based Healthcare Decision Support System developed using Microsoft SQL Server, PostgreSQL (Supabase pgvector), Sentence Transformers, and Streamlit.

The system retrieves semantically relevant healthcare information, generates evidence-based responses, classifies severity levels, recommends nearby hospitals, and evaluates response quality.

The architecture combines relational database storage with vector-based semantic retrieval to improve the relevance and accuracy of healthcare information retrieval.

---

## Features

* Semantic healthcare question answering
* Microsoft SQL Server relational database
* PostgreSQL (Supabase pgvector) vector retrieval
* Severity classification
* Hospital recommendation system
* Query logging and retrieval analytics
* Response evaluation metrics
* Streamlit web interface

---

## Prerequisites

Install the following software before running the project:

* Python 3.10 or higher
* Microsoft SQL Server Express
* SQL Server Management Studio (SSMS)

Verify Python installation:

```bash
python --version
```

---

## Step 1: Restore SQL Server Database

The project database is provided as:

```text
healthcare_rag.bak
```

### Restore Procedure

1. Open SQL Server Management Studio (SSMS)
2. Connect to your SQL Server instance
3. Right-click **Databases**
4. Select **Restore Database**
5. Choose **Device**
6. Browse and select:

```text
healthcare_rag.bak
```

7. Click **OK**
8. Wait for the restore process to complete

---

## Step 2: Verify Database Restoration

Run:

```sql
SELECT name
FROM sys.tables;
```

Expected tables:

```text
source
document
section
chunk
embedding
topic
chunk_topic
user_query
retrieved_chunk
response
evaluation
```

---

## Step 3: Configure SQL Server Connection

Open:

```python
app.py
```

Locate:

```python
SERVER = r"YOUR_PC_NAME\SQLEXPRESS"
DATABASE = "healthcare_rag"
```

Replace the server name with your local SQL Server instance.

Example:

```python
SERVER = r"DESKTOP-ABC123\SQLEXPRESS"
```

To find your SQL Server name:

```sql
SELECT @@SERVERNAME;
```

---

## Step 4: Install Python Dependencies

Open a terminal in the project folder and run:

```bash
python -m pip install streamlit pandas numpy pyodbc sentence-transformers scikit-learn requests torch torchvision psycopg2-binary pgvector
```

---

## Step 5: Run the Application

Launch Streamlit:

```bash
streamlit run streamlit_rag.py
```

Open:

```text
http://localhost:8501
```

in your browser.

---

## Example Queries

```text
What are symptoms of dengue?

What causes malaria?

What is hypertension?

How can diabetes be managed?

What are symptoms of pneumonia?
```

---

## Database Architecture

### Microsoft SQL Server

Stores:

* Documents
* Sections
* Chunks
* Topics
* Query Logs
* Responses
* Evaluations

### PostgreSQL (Supabase pgvector)

Stores:

* Vector Embeddings

Used for:

* Semantic Similarity Search
* Top-k Chunk Retrieval

---

## Performance Optimization

Indexes used:

```text
idx_chunk_section
idx_embedding_chunk
idx_retrieved_query
idx_response_query

IX_Chunk_ChunkID
IX_Document_Speciality
IX_RetrievedChunk_QueryID_Cover
```

Performance testing queries are provided in:

```text
performance.sql
```

---

## Authors

Shambhavi

Yashash

IIT Madras Zanzibar

Database Management Systems Project

---

## Notes

This project uses a hybrid database architecture:

* Microsoft SQL Server for relational healthcare data
* PostgreSQL (Supabase pgvector) for vector embeddings and semantic retrieval
* Streamlit for the user interface

Ensure SQL Server is running before launching the application.
