"""
app.py — Interfaccia web locale per l'assistente KBE Turbojet
Avvio: streamlit run app.py
"""

from dotenv import load_dotenv
load_dotenv()

import os
import sys
import streamlit as st
import chromadb
from google import genai
from sentence_transformers import SentenceTransformer
from ask import SYSTEM_PROMPT, detect_intent, retrieve_context

# ---------------------------------------------------------------------------
# CONFIGURAZIONE
# ---------------------------------------------------------------------------

CHROMA_DIR  = "./chroma_db"
EMBED_MODEL = "all-mpnet-base-v2"
N_RESULTS   = 5

# ---------------------------------------------------------------------------
# SETUP (cached — caricato una volta sola)
# ---------------------------------------------------------------------------

@st.cache_resource
def load_resources():
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    collections = {}
    for name in ["physics", "codebase", "multall"]:
        try:
            collections[name] = chroma_client.get_collection(name)
        except Exception:
            pass
    embedder = SentenceTransformer(EMBED_MODEL)
    gemini   = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return collections, embedder, gemini

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.set_page_config(page_title="KBE Turbojet Assistant", page_icon="✈️", layout="wide")
st.title("✈️ KBE Turbojet Assistant")
st.caption("Team 23 — TU Delft AE4314 | Parapy · Multall · Aero Engine")

collections, embedder, gemini_client = load_resources()

# mostra stato collezioni nella sidebar
with st.sidebar:
    st.header("Knowledge base")
    for name, col in collections.items():
        st.metric(name, f"{col.count()} chunks")
    st.divider()
    st.markdown("**Esempi di query:**")
    examples = [
        "sviluppa l'attributo compute_area in FlowStation",
        "come viene gestita mass_flow in FlowStation?",
        "aggiungi il metodo surge_margin a Compressor",
        "come funziona il ciclo Brayton nel progetto?",
        "scrivi l'attributo n_stages in Turbomachine",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state["query_input"] = ex

# cronologia messaggi
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Fonti recuperate"):
                st.text(msg["sources"])

# input utente
query = st.chat_input("Chiedi qualcosa sul progetto KBE...")

# se è stato premuto un esempio dalla sidebar, usalo come query
if "query_input" in st.session_state and st.session_state["query_input"]:
    query = st.session_state.pop("query_input")

if query:
    # mostra messaggio utente
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # retrieval
    intent_cols = detect_intent(query)

    # embedding della query
    query_embedding = embedder.encode([query]).tolist()[0]

    context_parts = []
    for col_name in intent_cols:
        if col_name not in collections:
            continue
        col = collections[col_name]
        if col.count() == 0:
            continue
        results = col.query(
            query_embeddings=[query_embedding],
            n_results=min(N_RESULTS, col.count())
        )
        if not results["documents"] or not results["documents"][0]:
            continue
        context_parts.append(f"--- [{col_name}] ---")
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            source = meta.get("source", "?")
            chunk_type = meta.get("type", "")
            context_parts.append(f"[{source} | {chunk_type}]\n{doc}\n")

    context = "\n".join(context_parts) if context_parts else "Nessun contesto trovato."

    user_prompt = f"""CONTESTO RECUPERATO DALLA KNOWLEDGE BASE:
{context}

RICHIESTA:
{query}

Rispondi usando il contesto recuperato e le tue conoscenze del progetto.
Se generi codice Parapy, usa le convenzioni del progetto (Input/Attribute/Part/metodi semplici).
Cita la fonte del contesto quando rilevante.
"""

    # generazione risposta
    with st.chat_message("assistant"):
        with st.spinner("Sto cercando nella knowledge base..."):
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=user_prompt,
                config={"system_instruction": SYSTEM_PROMPT}
            )
            answer = response.text

        st.markdown(answer)
        with st.expander("Fonti recuperate"):
            st.text(context[:2000])

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": context[:2000]
    })
