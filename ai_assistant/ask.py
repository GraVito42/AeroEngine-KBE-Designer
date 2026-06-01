"""
ask.py — Assistente KBE Turbojet
Uso:
    python ask.py "aggiungi il metodo compute_area alla classe Duct"
    python ask.py "come viene gestita la variabile mass_flow in FlowStation?"
    python ask.py "sviluppa l'attributo n_stages in Turbomachine"
"""

from dotenv import load_dotenv
load_dotenv()

import os
import sys
import chromadb
from google import genai
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# CONFIGURAZIONE
# ---------------------------------------------------------------------------

CHROMA_DIR  = "./chroma_db"
EMBED_MODEL = "all-mpnet-base-v2"
N_RESULTS   = 5   # chunks recuperati per collezione

# ---------------------------------------------------------------------------
# SYSTEM PROMPT — calibrato sul progetto Team 23
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Sei un assistente esperto di Knowledge Based Engineering (KBE) specializzato 
nel progetto di modellazione di motori turbojet del Team 23 (TU Delft, corso AE4314).

ARCHITETTURA DEL PROGETTO:
Il codebase Parapy è strutturato attorno a queste classi principali e relazioni:

- AeroEngine (top-level orchestratore)
    - contiene: EngineFrame, Combustor, Spool, InputParser, ReportWriter
    - attributi: engine_architecture, design_flight_conditions, engine_features, thermodynamic_cycle
    - metodi: total_weight(), preliminary_performance()

- Spool (coordina le turbomacchine)
    - contiene: 1 Turbine, 1 Compressor (entrambi sottoclassi di Turbomachine)
    - attributi: shaft_radius, shaft_length, turbine_position, compressor_position
    - metodi: power_balance()

- Turbomachine (classe astratta, parent di Turbine e Compressor)
    - attributi: n_stages, detailed_features
    - metodi: build_geometry(), weight(), multall_analysis()
    - contiene: n_stages istanze di Stage

- Turbine(Turbomachine)
    - attributi propri: inlet_temperature, loading_factor, degree_of_reaction

- Compressor(Turbomachine)
    - attributi propri: stage_pressure_ratio, polytropic_efficiency
    - metodi propri: surge_margin()

- Stage (contenuto in Turbomachine)
    - attributi: inflow_conditions, type, n_blades
    - metodi: meangen_analysis(), weight()
    - contiene: 2*n_blades istanze di Blade (stator+rotor)

- Blade
    - attributi: type, chords, radius, twist, section_coords
    - metodi: weight()

- EngineComponent (classe astratta, parent di Duct e Turbomachine)
    - attributi: inflow_conditions, pressure_ratio, isos_efficiency, station_in, station_out

- Duct (classe astratta, parent di Inlet e Nozzle, figlia di EngineComponent)
    - attributi: Mach_design, pressure_drop
    - metodi: is_choked()

- Inlet(Duct)
    - attributi propri: lip_geometry, highlight_profile, ram_recovery_factor

- Nozzle(Duct)
    - attributi propri: is_convergent_divergent, thrust_coefficient
    - metodi propri: is_choked()

- EngineFrame
    - attributi: Mach_design, flow_properties
    - metodi: weight(), blade_off_analysis()

- FlowStation (usata da tutti i componenti per le condizioni di flusso)
    - attributi: Mach, pressure_total, temperature_total, mass_flow, isos_efficiency, area_section, station_number
    - metodi: isos_transformation(), compute_area()

- Combustor
    - attributi: internal_radius, external_radius, length

- InputParser — legge file .xlsx di input
- ReportWriter — genera PDF, CSV e file STEP

CONVENZIONI PARAPY DEL PROGETTO:
- Input semplici: dichiarati come attributi di classe con tipo e default
  Esempio: length: float = Input(24.0)
- @Input decorator: per input il cui default dipende da una funzione
  Esempio:
    @Input
    def n_stages(self):
        return self._estimate_stages()
- @Attribute decorator: per attributi calcolati (lazy evaluation)
  Esempio:
    @Attribute
    def compute_area(self):
        return math.pi * self.radius**2
- @Part decorator: per parti geometriche figlie
  Esempio:
    @Part
    def blades(self):
        return QuantityList(Blade(...) for i in range(self.n_blades))
- Metodi semplici: definiti senza decorator
  Esempio:
    def weight(self):
        return self.volume * self.density

INTEGRAZIONE MULTALL:
- Il solver Multall viene chiamato tramite file .in, .dat e .out
- Meangen e Stagen generano la geometria 3D delle pale
- L'integrazione avviene leggendo/scrivendo file di testo da Stage e Turbomachine
- multall_analysis() in Turbomachine gestisce l'intera pipeline

FISICA DEL DOMINIO:
- Ciclo termodinamico Brayton: stazioni di flusso numerate dall'ingresso all'uscita
- FlowStation lega condizioni di flusso (P_tot, T_tot, Mach, mdot) alla geometria locale
- Triangoli di velocità: componenti assiali e tangenziali delle velocità in ogni stadio
- Efficienza isoentropica: usata da compressore e turbina per le trasformazioni
- Rapporto di pressione (PR): parametro chiave che guida il sizing dei componenti
- Blade-off containment: E_k (energia cinetica frammenti) < E_s (energia di deformazione casing)

REGOLE DI RISPOSTA:
1. Quando generi codice Parapy, usa SEMPRE le convenzioni del progetto (Input/Attribute/Part/metodi)
2. Rispetta la gerarchia di classi — non aggiungere attributi in classi sbagliate
3. Cita sempre la fisica sottostante quando definisci un attributo o metodo
4. Se un attributo dipende da FlowStation, mostra come recuperare i dati dalla stazione corretta
5. Mantieni la coerenza con i metodi già esistenti nelle classi (weight, build_geometry, ecc.)
6. Per metodi che coinvolgono Multall, indica chiaramente quali file vengono letti/scritti
"""

# ---------------------------------------------------------------------------
# ROUTER — decide quali collezioni interrogare
# ---------------------------------------------------------------------------

def detect_intent(query: str) -> list[str]:
    """
    Classifica la query e restituisce le collezioni da interrogare.
    - "sviluppa/aggiungi/implementa/crea/scrivi" → tutte e tre
    - "come viene gestita/traccia/analizza/spiega" → codebase + physics
    - "multall/meangen/stagen/.dat/.in/.out" → multall + physics
    """
    q = query.lower()

    dev_keywords = ["aggiungi", "sviluppa", "implementa", "crea", "scrivi",
                    "definisci", "costruisci", "genera", "add", "implement", "create"]
    trace_keywords = ["come viene", "traccia", "analizza", "spiega", "dove",
                      "how is", "where is", "explain", "gestita", "usata"]
    multall_keywords = ["multall", "meangen", "stagen", ".dat", ".in", ".out",
                        "cfd", "blade geometry", "mesh"]

    if any(k in q for k in multall_keywords):
        return ["physics", "multall"]
    if any(k in q for k in trace_keywords):
        return ["codebase", "physics"]
    if any(k in q for k in dev_keywords):
        return ["physics", "codebase", "multall"]

    # default: tutte e tre
    return ["physics", "codebase", "multall"]

# ---------------------------------------------------------------------------
# RETRIEVAL
# ---------------------------------------------------------------------------

def retrieve_context(query: str, collections: dict, intent_cols: list[str]) -> str:
    embedder = SentenceTransformer(EMBED_MODEL)
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

        context_parts.append(f"\n--- Contesto da [{col_name}] ---")
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            source = meta.get("source", "?")
            chunk_type = meta.get("type", "")
            context_parts.append(f"[{source} | {chunk_type}]\n{doc}\n")

    return "\n".join(context_parts) if context_parts else "Nessun contesto trovato."

# ---------------------------------------------------------------------------
# GENERAZIONE
# ---------------------------------------------------------------------------

def ask(query: str):
    # connetti a ChromaDB
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

    collections = {}
    for name in ["physics", "codebase", "multall"]:
        try:
            collections[name] = chroma_client.get_collection(name)
        except Exception:
            pass  # collezione non ancora creata (es. multall vuota)

    if not collections:
        print("ERRORE: nessuna collezione trovata. Esegui prima setup_kb.py")
        return

    # router
    intent_cols = detect_intent(query)
    print(f"\n[Retrieval da: {', '.join(intent_cols)}]")

    # retrieval
    context = retrieve_context(query, collections, intent_cols)

    # costruisci il prompt
    user_prompt = f"""CONTESTO RECUPERATO DALLA KNOWLEDGE BASE:
{context}

RICHIESTA:
{query}

Rispondi usando il contesto recuperato e le tue conoscenze del progetto.
Se generi codice Parapy, usa le convenzioni del progetto (Input/Attribute/Part/metodi semplici).
Cita la fonte del contesto quando rilevante (es. "come indicato in FlowStation...").
"""

    # chiamata Gemini
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=user_prompt,
        config={"system_instruction": SYSTEM_PROMPT}
    )

    print("\n" + "="*60)
    print(response.text)
    print("="*60)

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python ask.py \"la tua domanda qui\"")
        print("Esempi:")
        print('  python ask.py "aggiungi il metodo compute_area alla classe Duct"')
        print('  python ask.py "come viene gestita mass_flow in FlowStation?"')
        print('  python ask.py "sviluppa l\'attributo n_stages in Turbomachine"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    ask(query)
