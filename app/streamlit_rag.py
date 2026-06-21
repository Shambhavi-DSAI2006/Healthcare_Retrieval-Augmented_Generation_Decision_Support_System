import streamlit as st
import pandas as pd
import pyodbc
import numpy as np
import ast
import requests

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

SERVER = r"YASHU-PAVILION\SQLEXPRESS"
DATABASE = "healthcare_rag"

# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

@st.cache_resource
def get_connection():
    return pyodbc.connect(
        f"DRIVER={{SQL Server}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"Trusted_Connection=yes;"
    )

def save_user_query(question):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ISNULL(MAX(query_id), 0)
        FROM user_query
    """)

    new_query_id = cursor.fetchone()[0] + 1

    cursor.execute("""
        INSERT INTO user_query
        (
            query_id,
            query_text,
            query_timestamp
        )
        VALUES
        (
            ?, ?, GETDATE()
        )
    """, new_query_id, question)

    conn.commit()

    return new_query_id

def save_retrieved_chunks(query_id, results):

    conn = get_connection()
    cursor = conn.cursor()

    for item in results:

        cursor.execute("""
            INSERT INTO retrieved_chunk
            (
                query_id,
                chunk_id,
                relevance_score
            )
            VALUES
            (
                ?, ?, ?
            )
        """,
        query_id,
        int(item["chunk_id"]),
        float(item["score"]))

    conn.commit()

def save_response(query_id, answer, confidence_score):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ISNULL(MAX(response_id), 0)
        FROM response
    """)

    new_response_id = cursor.fetchone()[0] + 1

    cursor.execute("""
        INSERT INTO response
        (
            response_id,
            query_id,
            generated_answer,
            confidence_score
        )
        VALUES
        (
            ?, ?, ?, ?
        )
    """,
    new_response_id,
    query_id,
    answer,
    float(confidence_score))

    conn.commit()

    return new_response_id

def save_evaluation(response_id, results):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ISNULL(MAX(evaluation_id), 0)
        FROM evaluation
    """)

    new_evaluation_id = cursor.fetchone()[0] + 1

    factuality_score = sum(
        item["score"] for item in results
    ) / len(results)

    consistency_score = max(
        item["score"] for item in results
    )

    notes = (
        f"Automatically evaluated using "
        f"{len(results)} retrieved chunks."
    )

    cursor.execute("""
        INSERT INTO evaluation
        (
            evaluation_id,
            response_id,
            factuality_score,
            consistency_score,
            notes,
            response_timestamp
        )
        VALUES
        (
            ?, ?, ?, ?, ?, GETDATE()
        )
    """,
    new_evaluation_id,
    response_id,
    factuality_score,
    consistency_score,
    notes)

    conn.commit()

    return (
        new_evaluation_id,
        factuality_score,
        consistency_score
    )

# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------

@st.cache_resource
def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

# --------------------------------------------------
# LOAD EMBEDDINGS FROM SQL
# --------------------------------------------------

@st.cache_data
def load_embeddings():

    conn = get_connection()

    embeddings_df = pd.read_sql("""
        SELECT
            embedding_id,
            chunk_id,
            vector
        FROM embedding
    """, conn)

    chunks_df = pd.read_sql("""
        SELECT
            c.chunk_id,
            c.chunk_text,
            s.section_title,
            d.title AS document_title,
            src.source_name
        FROM chunk c
        JOIN section s
            ON c.section_id = s.section_id
        JOIN document d
            ON s.document_id = d.document_id
        JOIN source src
            ON d.source_id = src.source_id
    """, conn)

    embeddings_df["vector"] = embeddings_df["vector"].apply(ast.literal_eval)

    embedding_matrix = np.array(
        embeddings_df["vector"].tolist()
    )

    return embeddings_df, chunks_df, embedding_matrix

# --------------------------------------------------
# RETRIEVAL FUNCTION
# --------------------------------------------------

def semantic_search(question):

    model = load_model()

    embeddings_df, chunks_df, embedding_matrix = load_embeddings()

    query_embedding = model.encode([question])

    similarities = cosine_similarity(
        query_embedding,
        embedding_matrix
    )[0]

    top_indices = np.argsort(similarities)[::-1][:5]

    results = []

    for idx in top_indices:

        chunk_id = embeddings_df.iloc[idx]["chunk_id"]

        chunk_row = chunks_df[
            chunks_df["chunk_id"] == chunk_id
        ]

        if not chunk_row.empty:

            results.append({
                "chunk_id": chunk_id,
                "chunk_text": chunk_row.iloc[0]["chunk_text"],
                "section_title": chunk_row.iloc[0]["section_title"],
                "document_title": chunk_row.iloc[0]["document_title"],
                "source_name": chunk_row.iloc[0]["source_name"],
                "score": float(similarities[idx])
            })

    return results


def classify_severity(answer):

    answer = answer.lower()

    emergency_keywords = [
        "shock",
        "unconscious",
        "respiratory failure",
        "cardiac arrest",
        "heart attack",
        "stroke",
        "severe bleeding"
    ]

    high_keywords = [
        "severe dengue",
        "bleeding",
        "high fever",
        "pneumonia",
        "sepsis",
        "chest pain",
        "difficulty breathing"
    ]

    moderate_keywords = [
        "infection",
        "diabetes",
        "hypertension",
        "persistent fever",
        "malaria",
        "covid"
    ]

    for word in emergency_keywords:
        if word in answer:
            return (
                "🚨 Emergency",
                "Seek emergency medical attention immediately. Visit the nearest hospital or emergency care facility without delay."
            )

    for word in high_keywords:
        if word in answer:
            return (
                "🔴 High Risk",
                "Consult a qualified healthcare professional as soon as possible for proper diagnosis and treatment."
            )

    for word in moderate_keywords:
        if word in answer:
            return (
                "🟠 Moderate Risk",
                "Monitor symptoms and consult a healthcare professional if symptoms persist or worsen."
            )

    return (
        "🟢 Low Risk",
        "Maintain healthy practices and seek medical advice if new symptoms develop."
    )


fallback_hospitals = {

    "Zanzibar": [
        "Mnazi Mmoja Hospital",
        "Global Hospital",
        "Tawam Hospital"
    ],

    "Dar es Salaam": [
        "Muhimbili National Hospital",
        "Aga Khan Hospital",
        "Amana Hospital"
    ],

    "Nairobi": [
        "Kenyatta National Hospital",
        "Nairobi Hospital",
        "Aga Khan University Hospital"
    ],

    "Mombasa": [
        "Coast General Hospital",
        "Pandya Memorial Hospital",
        "Aga Khan Medical Centre"
    ]
}

def get_nearby_hospitals(city):
    
    try:

        url = (
            f"https://nominatim.openstreetmap.org/search"
            f"?q=hospital+in+{city}"
            f"&format=json"
            f"&limit=5"
        )

        headers = {
            "User-Agent": "HealthcareRAGProject"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=5
        )

        data = response.json()

        hospitals = []

        for item in data:
            hospitals.append({
                "name": item["display_name"],
                "lat": item["lat"],
                "lon": item["lon"]
            })

        if hospitals:
            return hospitals

    except:
        pass
    
    return None
    
# --------------------------------------------------
# UI
# --------------------------------------------------

st.set_page_config(
    page_title="Healthcare RAG",
    page_icon="🏥",
    layout="wide"
)

st.markdown("""
<style>

/* Main background */
.stApp {
    background: linear-gradient(
        180deg,
        #0f172a 0%,
        #111827 100%
    );
}

/* Title */
h1 {
    text-align: center;
    color: #38bdf8 !important;
    font-weight: 700;
}

/* Subheaders */
h3 {
    color: #60a5fa !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #0b1220;
}

/* Metric cards */
[data-testid="metric-container"] {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 15px;
    padding: 15px;
}

/* Expanders */
.streamlit-expanderHeader {
    background-color: #1e293b;
    border-radius: 10px;
}

/* Text input */
.stTextInput input {
    border-radius: 12px;
    border: 2px solid #38bdf8;
}

/* Search button */
.stButton > button {
    background: linear-gradient(
        90deg,
        #0284c7,
        #38bdf8
    );
    color: white;
    font-weight: bold;
    border-radius: 12px;
    height: 50px;
    width: 180px;
    border: none;
}

/* Search button hover */
.stButton > button:hover {
    transform: scale(1.03);
}

/* Success messages */
div[data-baseweb="notification"] {
    border-radius: 12px;
}

/* Progress bar */
.stProgress > div > div > div {
    background-color: #22c55e;
}

</style>
""", unsafe_allow_html=True)


with st.sidebar:

    st.header("Project Overview")

    st.markdown("""
    **Healthcare RAG Pipeline**

    - SQL Server Database
    - SentenceTransformers
    - Semantic Retrieval
    - Severity Classification
    - Hospital Recommendation
    - Self-Evaluation Metrics
    """)

    st.success("System Status: Online")

    st.divider()

    st.caption(
        "DBMS Project | IIT Madras Zanzibar"
    )

st.title(" Healthcare Intelligence Assistant")

st.markdown(
"""
<div style='text-align:center;
font-size:18px;
color:#94a3b8;
margin-bottom:20px;'>

Self-Reflective Retrieval-Augmented Healthcare Pipeline

</div>
""",
unsafe_allow_html=True
)

st.caption(
    "AI-Powered Retrieval-Augmented Healthcare Decision Support System"
)

st.info(
    "Ask a healthcare question and receive a generated answer along with severity classification, nearby hospital recommendations, and evaluation metrics."
)

with st.form("search_form"):

    question = st.text_input(
        "Enter your healthcare question",
        placeholder="What are symptoms of dengue?"
    )

    submitted = st.form_submit_button("Search")

if submitted:

    if not question.strip():
        st.warning("Please enter a question.")
        st.stop()

    query_id = save_user_query(question)

    with st.spinner("Generating embedding and retrieving relevant chunks..."):

        results = semantic_search(question)

        save_retrieved_chunks(
            query_id,
            results
        )



    # --------------------------------------------------
    # GENERATED ANSWER
    # --------------------------------------------------

    answer = " ".join(
        [x["chunk_text"] for x in results[:2]]
    )

    severity, recommendation = classify_severity(answer)

    confidence_score = results[0]["score"]

    response_id = save_response(
        query_id,
        answer,
        confidence_score
    )

    evaluation_id, factuality_score, consistency_score = save_evaluation(
        response_id,
        results
    )

    st.subheader("Generated Answer")

    st.success(answer)

    st.divider()

    st.subheader("Severity Classification")

    if "Emergency" in severity:
        st.error(severity)
        st.error(recommendation)

    elif "High Risk" in severity:
        st.error(severity)
        st.warning(recommendation)

    elif "Moderate Risk" in severity:
        st.warning(severity)
        st.info(recommendation)

    else:
        st.success(severity)
        st.info(recommendation)

    st.divider()


    if (
        "Emergency" in severity
        or
        "High Risk" in severity
    ):

        st.subheader("Nearby Hospitals")

        hospitals = get_nearby_hospitals("Zanzibar")

        if hospitals:

            st.success(
                "Nearby hospitals retrieved successfully."
            )

            for hospital in hospitals:

                map_link = (
                    f"https://www.google.com/maps?q="
                    f"{hospital['lat']},{hospital['lon']}"
                )

                st.markdown(
                    f"🏥 [{hospital['name']}]({map_link})"
                )

        else:

            st.warning(
                "Online hospital service unavailable. "
                "Please select your city."
            )

            city = st.selectbox(
                "Select Your City",
                [
                    "Zanzibar",
                    "Dar es Salaam",
                    "Nairobi",
                    "Mombasa"
                ]
            )

            for hospital in fallback_hospitals[city]:
                st.write("🏥", hospital)

    st.divider()


    # --------------------------------------------------
    # Evaluation Metrics
    # --------------------------------------------------

    st.subheader("Evaluation Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Confidence",
            f"{confidence_score:.4f}"
        )

    with col2:
        st.metric(
            "Factuality",
            f"{factuality_score:.4f}"
        )

    with col3:
        st.metric(
            "Consistency",
            f"{consistency_score:.4f}"
        )
    
    st.divider()

    st.write("Confidence Level")

    st.progress(
        min(
            int(confidence_score * 100),
            100
        )
    )

    # --------------------------------------------------
    # RETRIEVED CHUNKS
    # --------------------------------------------------

    st.subheader("Retrieved Evidence")

    for rank, item in enumerate(results, start=1):

        with st.expander(
            f"📄 Chunk #{rank} | Similarity Score: {item['score']:.4f}"
        ):

            st.write(
                f"**Document:** {item['document_title']}"
            )

            st.write(
                f"**Section:** {item['section_title']}"
            )

            st.write(
                f"**Source:** {item['source_name']}"
            )

            st.write(
                f"**Chunk ID:** {item['chunk_id']}"
            )

            st.markdown("---")

            st.write(item["chunk_text"])
    # --------------------------------------------------
    # QUERY INFORMATION
    # --------------------------------------------------

    st.subheader("Query Information")

    st.success( f"Query stored successfully" )
    

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Query ID", query_id)

    with col2:
        st.metric("Response ID", response_id)

    with col3:
        st.metric("Evaluation ID", evaluation_id)

    # --------------------------------------------------
    # METHOD USED
    # --------------------------------------------------

    with st.expander("System Workflow"):

        st.code("""
    User Question
        ↓
    Embedding Generation
        ↓
    Semantic Retrieval
        ↓
    Top Retrieved Chunks
        ↓
    Generated Answer
        ↓
    Severity Assessment
        ↓
    Hospital Recommendation
        ↓
    Self Evaluation
    """)
st.markdown("---")

st.caption(
    "Healthcare RAG Database Project | Semantic Retrieval using Embeddings"
)