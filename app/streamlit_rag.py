import streamlit as st
import pandas as pd
import numpy as np
import ast
import math
import requests
import urllib.parse

from dotenv import load_dotenv
load_dotenv()

import os
import psycopg2

from rag_pipeline import run_pipeline, classify_severity, check_faithfulness
from streamlit_geolocation import streamlit_geolocation

# --------------------------------------------------
# DB CONNECTION (with liveness check for Neon auto-suspend)
# --------------------------------------------------

@st.cache_resource
def _get_cached_connection():
    return psycopg2.connect(
        host=os.environ["PG_HOST"],
        database=os.environ.get("PG_DATABASE", "healthcare_rag"),
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        port=os.environ.get("PG_PORT", "5432"),
        sslmode="require"
    )

def get_pg_connection():
    conn = _get_cached_connection()
    try:
        test_cursor = conn.cursor()
        test_cursor.execute("SELECT 1")
        test_cursor.close()
    except Exception:
        st.cache_resource.clear()
        conn = _get_cached_connection()
    return conn

# --------------------------------------------------
# QUERY / RESPONSE / EVALUATION LOGGING
# --------------------------------------------------

def save_user_query(question):
    for attempt in range(2):
        try:
            conn = get_pg_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_query (query_text, query_timestamp)
                VALUES (%s, CURRENT_TIMESTAMP)
                RETURNING query_id
            """, (question,))
            new_query_id = cursor.fetchone()[0]
            conn.commit()
            return new_query_id
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            if attempt == 1:
                raise
            st.cache_resource.clear()
            continue

def save_retrieved_chunks(query_id, results):
    for attempt in range(2):
        try:
            conn = get_pg_connection()
            cursor = conn.cursor()
            for item in results:
                cursor.execute("""
                    INSERT INTO retrieved_chunk (query_id, chunk_id, relevance_score)
                    VALUES (%s, %s, %s)
                """, (query_id, int(item["chunk_id"]), float(item["score"])))
            conn.commit()
            return
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            if attempt == 1:
                raise
            st.cache_resource.clear()
            continue

def save_response(query_id, answer, confidence_score):
    for attempt in range(2):
        try:
            conn = get_pg_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO response (query_id, generated_answer, confidence_score)
                VALUES (%s, %s, %s)
                RETURNING response_id
            """, (query_id, answer, float(confidence_score)))
            new_response_id = cursor.fetchone()[0]
            conn.commit()
            return new_response_id
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            if attempt == 1:
                raise
            st.cache_resource.clear()
            continue

def save_evaluation(response_id, factuality_score, consistency_score, notes):
    for attempt in range(2):
        try:
            conn = get_pg_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO evaluation
                    (response_id, factuality_score, consistency_score, notes, response_timestamp)
                VALUES
                    (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING evaluation_id
            """, (response_id, factuality_score, consistency_score, notes))
            new_evaluation_id = cursor.fetchone()[0]
            conn.commit()
            return new_evaluation_id
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            if attempt == 1:
                raise
            st.cache_resource.clear()
            continue
# --------------------------------------------------
# CHUNK METADATA
# --------------------------------------------------

@st.cache_data
def load_chunk_metadata():
    for attempt in range(2):
        try:
            conn = get_pg_connection()
            chunks_df = pd.read_sql("""
                SELECT
                    c.chunk_id,
                    s.section_title,
                    d.title AS document_title,
                    src.source_name
                FROM chunk c
                JOIN section s ON c.section_id = s.section_id
                JOIN document d ON s.document_id = d.document_id
                JOIN source src ON d.source_id = src.source_id
            """, conn)
            return chunks_df
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            if attempt == 1:
                raise
            st.cache_resource.clear()
            continue


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def enrich_chunks(pipeline_chunks, metadata_df):
    enriched = []
    for c in pipeline_chunks:
        meta_row = metadata_df[metadata_df["chunk_id"] == c["chunk_id"]]
        enriched.append({
            "chunk_id": c["chunk_id"],
            "chunk_text": c["chunk_text"],
            "section_title": meta_row.iloc[0]["section_title"] if not meta_row.empty else "Unknown",
            "document_title": meta_row.iloc[0]["document_title"] if not meta_row.empty else "Unknown",
            "source_name": meta_row.iloc[0]["source_name"] if not meta_row.empty else "Unknown",
            "score": sigmoid(c["rerank_score"])
        })
    return enriched

# --------------------------------------------------
# HOSPITAL LOCATING (geolocation + Overpass, real distances)
# --------------------------------------------------

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def geocode_location(place_name, retries=2):
    for attempt in range(retries):
        try:
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": place_name, "format": "json", "limit": 1},
                headers={"User-Agent": "HealthcareRAGProject"},
                timeout=8
            )
            data = response.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception:
            if attempt == retries - 1:
                return None
            continue
    return None


def get_hospitals_near(lat, lon, radius_km=10, limit=5, retries=2):
    radius_m = radius_km * 1000
    overpass_query = f"""
    [out:json][timeout:15];
    (
      node["amenity"="hospital"](around:{radius_m},{lat},{lon});
      way["amenity"="hospital"](around:{radius_m},{lat},{lon});
    );
    out center;
    """
    for attempt in range(retries):
        try:
            response = requests.post(
                "https://overpass-api.de/api/interpreter",
                data={"data": overpass_query},
                headers={"User-Agent": "HealthcareRAGProject"},
                timeout=25
            )
            data = response.json()

            hospitals = []
            for element in data.get("elements", []):
                if element["type"] == "node":
                    h_lat, h_lon = element["lat"], element["lon"]
                elif "center" in element:
                    h_lat, h_lon = element["center"]["lat"], element["center"]["lon"]
                else:
                    continue

                name = element.get("tags", {}).get("name", "Unnamed Hospital")
                distance = haversine_distance(lat, lon, h_lat, h_lon)
                hospitals.append({"name": name, "lat": h_lat, "lon": h_lon, "distance_km": distance})

            hospitals.sort(key=lambda h: h["distance_km"])
            return hospitals[:limit]
        except Exception:
            if attempt == retries - 1:
                return None
            continue
    return None


fallback_hospitals = {
    "Hyderabad": ["Apollo Hospitals Jubilee Hills", "Yashoda Hospitals", "NIMS (Nizam's Institute of Medical Sciences)"],
    "Zanzibar": ["Mnazi Mmoja Hospital", "Global Hospital", "Tawam Hospital"],
    "Bengaluru": ["Manipal Hospital", "Fortis Hospital", "St. John's Medical College Hospital"],
    "Delhi": ["AIIMS Delhi", "Apollo Hospital Delhi", "Max Super Speciality Hospital"],
    "Chennai": ["Apollo Hospitals Chennai", "MIOT International", "Sri Ramachandra Medical Centre"],
    "Mumbai": ["Lilavati Hospital", "Kokilaben Dhirubhai Ambani Hospital", "Tata Memorial Hospital"]
}

# --------------------------------------------------
# UI SETUP
# --------------------------------------------------

st.set_page_config(page_title="Healthcare RAG", page_icon="🏥", layout="wide")

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">

<style>

:root {
    --bg: #0a0e14;
    --bg-panel: #121922;
    --bg-panel-alt: #182029;
    --border: #253140;
    --text-primary: #eaf0f5;
    --text-muted: #7c8b9a;
    --accent: #2dd4bf;
    --accent-dim: #1a8f80;
    --risk-low: #34d399;
    --risk-moderate: #fbbf24;
    --risk-high: #f87171;
    --risk-emergency: #ef4444;
}

.stApp {
    background: var(--bg);
    font-family: 'IBM Plex Sans', sans-serif;
}

h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: -0.01em;
}

h1 {
    text-align: center;
    color: var(--text-primary) !important;
    font-weight: 700 !important;
}

h3 {
    color: var(--accent) !important;
    font-weight: 600 !important;
}

p, span, label, div {
    color: var(--text-primary);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: var(--bg-panel);
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--text-primary) !important;
}

/* Metric cards -- panel with a teal top accent, monospace numbers */
[data-testid="stMetric"] {
    background-color: var(--bg-panel);
    border: 1px solid var(--border);
    border-top: 2px solid var(--accent);
    border-radius: 8px;
    padding: 16px;
}

[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    color: var(--accent) !important;
    font-weight: 600 !important;
}

[data-testid="stMetricLabel"] {
    font-family: 'IBM Plex Mono', monospace !important;
    color: var(--text-muted) !important;
    text-transform: uppercase;
    font-size: 0.75rem !important;
    letter-spacing: 0.05em;
}
            
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px;
}            

/* Expanders (retrieved evidence, system workflow) */
.streamlit-expanderHeader {
    background-color: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-family: 'IBM Plex Mono', monospace;
}

[data-testid="stExpander"] {
    border: 1px solid var(--border);
    border-radius: 8px;
    background-color: var(--bg-panel);
}

/* Text input */
.stTextInput input {
    background-color: var(--bg-panel-alt);
    border-radius: 8px;
    border: 1px solid var(--border);
    color: var(--text-primary);
    font-family: 'IBM Plex Sans', sans-serif;
}

.stTextInput input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 1px var(--accent);
}

/* Search button */
.stButton > button {
    background: var(--accent);
    color: #04120f;
    font-weight: 600;
    font-family: 'Space Grotesk', sans-serif;
    border-radius: 8px;
    height: 48px;
    width: 180px;
    border: none;
    transition: transform 0.15s ease, background 0.15s ease;
}

.stButton > button:hover {
    background: var(--accent-dim);
    transform: translateY(-1px);
}

/* Notification/alert boxes */
div[data-baseweb="notification"] {
    border-radius: 8px;
    font-family: 'IBM Plex Sans', sans-serif;
}

/* Progress bar -- monitor-teal trace */
.stProgress > div > div > div {
    background-color: var(--accent);
}

/* Dividers */
hr {
    border-color: var(--border) !important;
}

/* Code blocks (System Workflow) */
code, pre {
    font-family: 'IBM Plex Mono', monospace !important;
}

/* Links (hospital results) */
a {
    color: var(--accent) !important;
}

/* Caption text */
[data-testid="stCaptionContainer"] {
    font-family: 'IBM Plex Mono', monospace;
    color: var(--text-muted) !important;
}

/* --- Signature element: ECG pulse trace --- */
.pulse-trace-wrapper {
    width: 100%;
    max-width: 500px;
    margin: -8px auto 24px auto;
    opacity: 0.85;
}

.pulse-trace-wrapper svg {
    width: 100%;
    height: 40px;
    display: block;
}

.pulse-line {
    fill: none;
    stroke: var(--accent);
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-dasharray: 1000;
    stroke-dashoffset: 1000;
    animation: draw-pulse 2.2s ease-out forwards;
}

@keyframes draw-pulse {
    to {
        stroke-dashoffset: 0;
    }
}

@media (prefers-reduced-motion: reduce) {
    .pulse-line {
        animation: none;
        stroke-dashoffset: 0;
    }
}

</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Project Overview")
    st.markdown("""
    **Healthcare RAG Pipeline**

    - PostgreSQL (Neon) + pgvector
    - Hybrid Search (Dense + BM25) with RRF
    - Cross-Encoder Reranking
    - Query Rewriting (Groq)
    - Corrective Retrieval Grading
    - Grounded Generation (Groq)
    - LLM Severity Classification
    - Geolocation-Based Hospital Search
    """)
    st.success("System Status: Online")
    st.divider()
    st.caption("DBMS Project | IIT Madras Zanzibar")

st.title(" Healthcare Intelligence Assistant")

st.markdown("""
<div class="pulse-trace-wrapper">
<svg viewBox="0 0 500 40" xmlns="http://www.w3.org/2000/svg">
  <path class="pulse-line" d="M0,20 L140,20 L155,20 L165,5 L178,35 L190,20 L210,20 L500,20" />
</svg>
</div>
""", unsafe_allow_html=True)

st.caption("AI-Powered Retrieval-Augmented Healthcare Decision Support System")

st.info(
    "Ask a healthcare question and receive a generated answer along with severity classification, "
    "nearby hospital recommendations, and evaluation metrics."
)

with st.form("search_form"):
    question = st.text_input("Enter your healthcare question", placeholder="What are symptoms of dengue?")
    submitted = st.form_submit_button("Search")

# --------------------------------------------------
# ON SUBMIT: run the pipeline once, store everything needed
# for display into session_state. This runs ONLY on the exact
# rerun triggered by clicking Search.
# --------------------------------------------------

if submitted:

    if not question.strip():
        st.warning("Please enter a question.")
        st.stop()

    query_id = save_user_query(question)

    with st.spinner("Rewriting query, retrieving evidence, and generating a grounded answer..."):
        pipeline_result = run_pipeline(question)
        metadata_df = load_chunk_metadata()
        results = enrich_chunks(pipeline_result["chunks"], metadata_df)
        save_retrieved_chunks(query_id, results)

    answer = pipeline_result["answer"]
    grading = pipeline_result["grading"]
    attempt_count = pipeline_result["attempt"]

    severity, recommendation, severity_reasoning = classify_severity(question, answer)

    confidence_score = grading["confidence"]

    response_id = save_response(query_id, answer, confidence_score)

    factuality_score, unsupported_claims = check_faithfulness(
        answer,
        [r["chunk_text"] for r in results]
    )
    consistency_score = sum(r["score"] for r in results) / len(results)

    notes = (
        f"Corrective RAG pipeline: {attempt_count} retrieval attempt(s), "
        f"final query '{pipeline_result['current_query']}'. "
        f"Retrieval grading feedback: {grading['feedback']}"
    )

    evaluation_id = save_evaluation(response_id, factuality_score, consistency_score, notes)

    # Store everything needed for display -- this is what survives
    # later reruns triggered by the geolocation button / city input
    # widgets further down the page.
    st.session_state["last_result"] = {
        "answer": answer,
        "severity": severity,
        "recommendation": recommendation,
        "severity_reasoning": severity_reasoning,
        "results": results,
        "confidence_score": confidence_score,
        "factuality_score": factuality_score,
        "consistency_score": consistency_score,
        "unsupported_claims": unsupported_claims,
        "query_id": query_id,
        "response_id": response_id,
        "evaluation_id": evaluation_id,
        "attempt_count": attempt_count,
    }

# --------------------------------------------------
# DISPLAY: reads from session_state, NOT from `submitted`.
# This means it survives reruns caused by any widget on the
# page, including the hospital-locating ones below.
# --------------------------------------------------

if "last_result" in st.session_state:

    r = st.session_state["last_result"]
    answer = r["answer"]
    severity = r["severity"]
    recommendation = r["recommendation"]
    severity_reasoning = r["severity_reasoning"]
    results = r["results"]
    confidence_score = r["confidence_score"]
    factuality_score = r["factuality_score"]
    consistency_score = r["consistency_score"]
    query_id = r["query_id"]
    unsupported_claims = r["unsupported_claims"]
    response_id = r["response_id"]
    evaluation_id = r["evaluation_id"]
    attempt_count = r["attempt_count"]

    st.subheader("Generated Answer")
    st.success(answer)

    if attempt_count > 1:
        st.caption(f"ℹ️ Query was automatically rewritten and retried {attempt_count} times to improve retrieval quality.")

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

    st.caption(f"Reasoning: {severity_reasoning}")

    st.divider()

    if "Emergency" in severity or "High Risk" in severity:

        st.subheader("Nearby Hospitals")

        with st.container(border=True):
            st.write("📍 Share your location to find nearby hospitals:")
            location = streamlit_geolocation()

        lat, lon = None, None

        if location and location.get("latitude") and location.get("longitude"):
            lat = location["latitude"]
            lon = location["longitude"]
            st.success("Location detected.")
        else:
            st.info("Click the location button above, or enter your city manually below.")
            manual_city = st.text_input("Enter your city", key=f"manual_city_input_{query_id}")
            if manual_city:
                geocoded = geocode_location(manual_city)
                if geocoded:
                    lat, lon = geocoded
                else:
                    st.warning("Could not find that location. Try a more specific city name.")

        if lat and lon:
            hospitals = get_hospitals_near(lat, lon)

            if hospitals:
                st.success(f"Found {len(hospitals)} nearby hospitals.")
                for hospital in hospitals:
                    map_link = f"https://www.google.com/maps?q={hospital['lat']},{hospital['lon']}"
                    st.markdown(f"🏥 [{hospital['name']}]({map_link}) — {hospital['distance_km']:.1f} km away")
            else:
                st.warning("No hospitals found nearby via OpenStreetMap. Showing fallback list.")
                city_fallback = st.selectbox("Select your city", ["Bengaluru" , "Zanzibar", "Hyderabad",  "Delhi", "Chennai", "Mumbai"])
                for hospital in fallback_hospitals[city_fallback]:
                    search_query = urllib.parse.quote_plus(f"{hospital} {city_fallback}")
                    map_link = f"https://www.google.com/maps/search/?api=1&query={search_query}"
                    st.markdown(f"🏥 [{hospital}]({map_link})")

    st.divider()

    st.subheader("Evaluation Metrics")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Confidence", f"{confidence_score:.4f}")
    with col2:
        st.metric("Factuality", f"{factuality_score:.4f}")
    with col3:
        st.metric("Consistency", f"{consistency_score:.4f}")
    if unsupported_claims:
        st.caption(f"⚠️ Claims not directly supported by evidence: {', '.join(unsupported_claims)}")

    st.divider()

    st.write("Confidence Level")
    st.progress(min(int(confidence_score * 100), 100))

    st.subheader("Retrieved Evidence")

    for rank, item in enumerate(results, start=1):
        with st.expander(f"📄 Chunk #{rank} | Relevance Score: {item['score']:.4f}"):
            st.write(f"**Document:** {item['document_title']}")
            st.write(f"**Section:** {item['section_title']}")
            st.write(f"**Source:** {item['source_name']}")
            st.write(f"**Chunk ID:** {item['chunk_id']}")
            st.markdown("---")
            st.write(item["chunk_text"])

    st.subheader("Query Information")
    st.success("Query stored successfully")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Query ID", query_id)
    with col2:
        st.metric("Response ID", response_id)
    with col3:
        st.metric("Evaluation ID", evaluation_id)

    with st.expander("System Workflow"):
        st.code("""
    User Question
        ↓
    Query Rewriting (Groq LLM)
        ↓
    Hybrid Retrieval (Dense pgvector + BM25, fused via RRF)
        ↓
    Cross-Encoder Reranking
        ↓
    Retrieval Quality Grading (Groq LLM)
        ↓
    [Retry rewrite + retrieval once if grading is insufficient]
        ↓
    Grounded Answer Generation (Groq LLM)
        ↓
    LLM-Based Severity Classification (with hard safety-net)
        ↓
    Geolocation-Based Hospital Recommendation
        ↓
    Evaluation Logging
    """)

st.markdown("---")
st.caption("Healthcare RAG Database Project | Corrective RAG with Hybrid Search")
