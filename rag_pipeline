"""
Full Corrective RAG pipeline: rewrite -> hybrid retrieve -> rerank -> grade
-> (retry once if weak) -> generate.

This consolidates the 4 standalone test scripts into one LangGraph state
machine. Import run_pipeline(question) from this file elsewhere (e.g.
streamlit_rag.py) rather than copy-pasting the logic.
"""

import os
import json
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from typing import TypedDict, Optional

from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

load_dotenv()

# --------------------------------------------------
# SHARED RESOURCES (loaded once, reused across calls)
# --------------------------------------------------

def get_pg_connection():
    return psycopg2.connect(
        host=os.environ["PG_HOST"],
        database=os.environ.get("PG_DATABASE", "healthcare_rag"),
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        port=os.environ.get("PG_PORT", "5432"),
        sslmode="require"
    )

def _create_connection():
    return psycopg2.connect(
        host=os.environ["PG_HOST"],
        database=os.environ.get("PG_DATABASE", "healthcare_rag"),
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        port=os.environ.get("PG_PORT", "5432"),
        sslmode="require"
    )

_conn = _create_connection()

def get_live_connection():
    global _conn
    try:
        if _conn.closed:
            _conn = _create_connection()
    except Exception:
        _conn = _create_connection()
    return _conn
_chunks_df = pd.read_sql("SELECT chunk_id, chunk_text FROM chunk", _conn)
_tokenized_corpus = [text.lower().split() for text in _chunks_df["chunk_text"]]
_bm25 = BM25Okapi(_tokenized_corpus)
_embed_model = SentenceTransformer("all-MiniLM-L6-v2")
_reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

_llm = ChatGroq(
    groq_api_key=os.environ["GROQ_API_KEY"],
    model="llama-3.3-70b-versatile",
    temperature=0
)

_llm_generation = ChatGroq(
    groq_api_key=os.environ["GROQ_API_KEY"],
    model="llama-3.3-70b-versatile",
    temperature=0.2
)

# --------------------------------------------------
# PROMPTS
# --------------------------------------------------

REWRITE_SYSTEM_PROMPT = (
    "You rewrite healthcare questions into short search queries for a "
    "medical document retrieval system.\n\n"
    "Rules:\n"
    "- Output a SHORT PHRASE (3-8 words), never a full sentence or question\n"
    "- Expand abbreviations and shorthand (e.g. 'temp' -> 'fever/temperature')\n"
    "- Do NOT invent or add specific symptoms, causes, or facts not implied by the original question\n"
    "- Do NOT change the core intent of the question\n"
    "- Output ONLY the rewritten phrase, nothing else -- no preamble, no explanation, no punctuation at the end\n\n"
    "Example:\n"
    "Original: whats dengue fever symptoms\n"
    "Rewritten: dengue fever symptoms\n\n"
    "Example:\n"
    "Original: temp and headache what could it be\n"
    "Rewritten: fever headache possible causes"
)

GRADE_SYSTEM_PROMPT = (
    "You judge whether retrieved document chunks are sufficient to answer "
    "a healthcare question, with a CALIBRATED confidence score.\n\n"
    "Respond ONLY with valid JSON in exactly this format, nothing else:\n"
    '{"reasoning": "1-2 sentences on what the chunks cover vs what the question needs", '
    '"sufficient": true or false, '
    '"confidence": a number from 0.0 to 1.0}\n\n'
    "CONFIDENCE CALIBRATION -- use the full range, do not default to a 'safe' middle value:\n"
    "- 0.90-1.00: chunks directly and completely answer the exact question asked\n"
    "- 0.70-0.89: chunks answer the general topic well, but miss a specific detail the question asked for\n"
    "- 0.40-0.69: chunks are related to the topic but only partially relevant, "
    "or answer a nearby but different question\n"
    "- 0.10-0.39: chunks barely touch the topic, mostly irrelevant to what was asked\n"
    "- 0.00-0.09: chunks are essentially unrelated to the question\n\n"
    "Write your reasoning FIRST, then decide confidence based on that reasoning -- "
    "do not just pick a number and justify it afterward. Be honest and strict: "
    "most real retrievals are NOT a perfect 0.9+ match, so use the lower bands "
    "whenever the chunks only partially address the question."
)

GENERATION_SYSTEM_PROMPT = (
    "You are a healthcare information assistant. Answer the user's question "
    "using ONLY the information in the provided document chunks.\n\n"
    "Rules:\n"
    "- Do NOT use any medical knowledge beyond what's in the chunks\n"
    "- Do NOT speculate, diagnose, or add caveats not present in the chunks\n"
    "- If the chunks don't fully answer the question, say what they DO cover "
    "and clearly note what's missing -- don't fill the gap yourself\n"
    "- Keep the answer concise and directly grounded in the chunk text\n"
    "- Do not mention 'chunks' or 'documents' to the user -- just answer naturally\n"
    "- This is informational only, not a substitute for professional medical advice\n\n"
    "IMPORTANT -- personal/diagnostic questions (e.g. 'Do I have X?', 'Is this "
    "dangerous for me?'): you cannot determine anything about this specific "
    "person. But do NOT respond with just a refusal or near-empty answer. "
    "Instead: clearly explain the general symptoms, risk factors, or "
    "diagnostic criteria for the condition AS COVERED IN THE CHUNKS, then "
    "explicitly state that only a healthcare professional can determine "
    "whether this applies to them, and recommend they get evaluated. The "
    "general information is still valuable even though you can't diagnose."
)

SEVERITY_SYSTEM_PROMPT = (
    "You classify the urgency of a healthcare question based on the "
    "question itself and the information available to answer it.\n\n"
    "Respond ONLY with valid JSON in exactly this format:\n"
    '{"severity": "Emergency" or "High Risk" or "Moderate Risk" or "Low Risk", '
    '"reasoning": "one short sentence explaining why"}\n\n'
    "Guidelines:\n"
    "- Emergency: symptoms suggesting immediate life-threatening danger "
    "(e.g. difficulty breathing, chest pain, unconsciousness, severe bleeding, signs of shock)\n"
    "- High Risk: serious symptoms needing prompt medical attention, but not immediately life-threatening\n"
    "- Moderate Risk: symptoms worth monitoring and consulting a doctor if they persist/worsen\n"
    "- Low Risk: general information seeking, mild or no symptoms described\n"
    "- Base this on what the USER ASKED, not just words that happen to "
    "appear in the answer text"
)

HARD_EMERGENCY_TRIGGERS = [
    "can't breathe", "cant breathe", "difficulty breathing",
    "unconscious", "passed out", "not breathing",
    "severe bleeding", "won't stop bleeding",
    "chest pain", "crushing pain",
]

RECOMMENDATIONS = {
    "Emergency": "Seek emergency medical attention immediately. Visit the nearest hospital or emergency care facility without delay.",
    "High Risk": "Consult a qualified healthcare professional as soon as possible for proper diagnosis and treatment.",
    "Moderate Risk": "Monitor symptoms and consult a healthcare professional if symptoms persist or worsen.",
    "Low Risk": "Maintain healthy practices and seek medical advice if new symptoms develop.",
}

ICONS = {
    "Emergency": "🚨 Emergency",
    "High Risk": "🔴 High Risk",
    "Moderate Risk": "🟠 Moderate Risk",
    "Low Risk": "🟢 Low Risk",
}

def classify_severity(question, answer):

    question_lower = question.lower()
    for trigger in HARD_EMERGENCY_TRIGGERS:
        if trigger in question_lower:
            return (
                ICONS["Emergency"],
                RECOMMENDATIONS["Emergency"],
                f"Hard safety-net trigger matched: '{trigger}'"
            )

    user_content = f"Question: {question}\n\nAnswer provided: {answer}"

    response = _llm.invoke([
        ("system", SEVERITY_SYSTEM_PROMPT),
        ("user", user_content)
    ])

    try:
        result = json.loads(response.content.strip())
        severity = result["severity"]
        reasoning = result.get("reasoning", "")
    except (json.JSONDecodeError, KeyError):
        severity = "High Risk"
        reasoning = "Could not parse severity classification; defaulted to High Risk as a safe fallback."

    return (
        ICONS.get(severity, ICONS["Moderate Risk"]),
        RECOMMENDATIONS.get(severity, RECOMMENDATIONS["Moderate Risk"]),
        reasoning
    )

FAITHFULNESS_SYSTEM_PROMPT = (
    "You check whether a generated answer's claims are actually supported "
    "by the provided source chunks.\n\n"
    "Break the answer down into individual factual claims. For each claim, "
    "determine if it is directly supported by the source chunks.\n\n"
    "Respond ONLY with valid JSON in exactly this format:\n"
    '{"total_claims": <int>, "supported_claims": <int>, '
    '"unsupported_claims": ["claim text", ...]}\n\n'
    "Be strict: a claim only counts as supported if the source chunks "
    "actually state it, not if it's merely plausible or related."
)

def check_faithfulness(answer, chunks):
    chunk_text = "\n\n".join(f"[Source {i+1}]: {c}" for i, c in enumerate(chunks))
    user_content = f"Generated answer:\n{answer}\n\nSource chunks:\n{chunk_text}"

    response = _llm.invoke([
        ("system", FAITHFULNESS_SYSTEM_PROMPT),
        ("user", user_content)
    ])

    try:
        result = json.loads(response.content.strip())
        total = result["total_claims"]
        supported = result["supported_claims"]
        score = supported / total if total > 0 else 1.0
        return score, result["unsupported_claims"]
    except (json.JSONDecodeError, KeyError, ZeroDivisionError):
        return 0.0, ["Could not parse faithfulness check."]


# --------------------------------------------------
# PIPELINE STATE
# --------------------------------------------------

class RAGState(TypedDict):
    original_question: str
    current_query: str
    chunks: list
    grading: dict
    attempt: int
    answer: str

# --------------------------------------------------
# NODES
# --------------------------------------------------

def node_rewrite(state: RAGState) -> RAGState:
    feedback = None
    if state.get("grading"):
        feedback = state["grading"].get("feedback")

    user_content = "Original question: " + state["original_question"]
    if feedback:
        user_content += (
            "\n\nFeedback from a failed retrieval attempt: " + feedback +
            "\nRewrite the query taking this into account."
        )

    response = _llm.invoke([
        ("system", REWRITE_SYSTEM_PROMPT),
        ("user", user_content)
    ])

    state["current_query"] = response.content.strip()
    return state


def node_retrieve(state: RAGState) -> RAGState:
    question = state["current_query"]

    query_embedding = _embed_model.encode(question).tolist()

    dense_ranked_ids = None
    for attempt in range(2):
        try:
            pg_cursor = get_live_connection().cursor()
            pg_cursor.execute("""
                SELECT chunk_id
                FROM embedding_pg
                ORDER BY vector <=> %s::vector
                LIMIT 20
            """, (str(query_embedding),))
            dense_ranked_ids = [row[0] for row in pg_cursor.fetchall()]
            break
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            if attempt == 1:
                raise
            global _conn
            _conn = _create_connection()
            continue

    tokenized_query = question.lower().split()
    bm25_scores = _bm25.get_scores(tokenized_query)
    bm25_ranked_indices = sorted(
        range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
    )[:20]
    sparse_ranked_ids = [_chunks_df.iloc[i]["chunk_id"] for i in bm25_ranked_indices]

    rrf_k = 60
    fused_scores = {}
    for rank, chunk_id in enumerate(dense_ranked_ids):
        fused_scores[chunk_id] = fused_scores.get(chunk_id, 0) + 1 / (rrf_k + rank + 1)
    for rank, chunk_id in enumerate(sparse_ranked_ids):
        fused_scores[chunk_id] = fused_scores.get(chunk_id, 0) + 1 / (rrf_k + rank + 1)

    candidate_pool = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[:15]
    candidates = []
    for chunk_id, rrf_score in candidate_pool:
        text = _chunks_df[_chunks_df["chunk_id"] == chunk_id].iloc[0]["chunk_text"]
        candidates.append({"chunk_id": chunk_id, "rrf_score": rrf_score, "chunk_text": text})

    pairs = [(question, c["chunk_text"]) for c in candidates]
    rerank_scores = _reranker.predict(pairs)
    for c, score in zip(candidates, rerank_scores):
        c["rerank_score"] = float(score)

    state["chunks"] = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)[:5]
    return state


def node_grade(state: RAGState) -> RAGState:
    chunk_text = "\n\n".join(
        f"[Chunk {c['chunk_id']}]: {c['chunk_text']}" for c in state["chunks"]
    )
    user_content = f"Question: {state['original_question']}\n\nRetrieved chunks:\n{chunk_text}"

    response = _llm.invoke([
        ("system", GRADE_SYSTEM_PROMPT),
        ("user", user_content)
    ])

    try:
        grading = json.loads(response.content.strip())
        grading.setdefault("feedback", grading.get("reasoning", ""))
    except json.JSONDecodeError:
        grading = {"sufficient": False, "confidence": 0.0, "reasoning": "Could not parse.", "feedback": "Could not parse grading response."}

    state["grading"] = grading
    state["attempt"] = state.get("attempt", 0) + 1
    return state


def node_generate(state: RAGState) -> RAGState:
    chunk_text = "\n\n".join(
        f"[Source {i+1}]: {c['chunk_text']}" for i, c in enumerate(state["chunks"])
    )
    user_content = f"Question: {state['original_question']}\n\nAvailable information:\n{chunk_text}"

    response = _llm_generation.invoke([
        ("system", GENERATION_SYSTEM_PROMPT),
        ("user", user_content)
    ])

    answer = response.content.strip()

    if state["grading"]["confidence"] < 0.5:
        answer = (
            "⚠️ *Low confidence: the available information may not fully address your question.*\n\n"
            + answer
        )

    state["answer"] = answer
    return state


def route_after_grade(state: RAGState) -> str:
    if state["grading"]["sufficient"] or state["attempt"] >= 2:
        return "generate"
    return "rewrite"


# --------------------------------------------------
# BUILD GRAPH
# --------------------------------------------------

_graph = StateGraph(RAGState)
_graph.add_node("rewrite", node_rewrite)
_graph.add_node("retrieve", node_retrieve)
_graph.add_node("grade", node_grade)
_graph.add_node("generate", node_generate)

_graph.set_entry_point("rewrite")
_graph.add_edge("rewrite", "retrieve")
_graph.add_edge("retrieve", "grade")
_graph.add_conditional_edges("grade", route_after_grade, {"rewrite": "rewrite", "generate": "generate"})
_graph.add_edge("generate", END)

_compiled_graph = _graph.compile()

# --------------------------------------------------
# PUBLIC ENTRY POINT
# --------------------------------------------------

def run_pipeline(question: str) -> dict:
    initial_state: RAGState = {
        "original_question": question,
        "current_query": "",
        "chunks": [],
        "grading": {},
        "attempt": 0,
        "answer": ""
    }

    final_state = _compiled_graph.invoke(initial_state)
    return final_state


if __name__ == "__main__":
    result = run_pipeline("What are the symptoms of dengue fever?")
    print("Attempts used:", result["attempt"])
    print("Final query used:", result["current_query"])
    print("Grading:", result["grading"])
    print("\nAnswer:\n", result["answer"])
