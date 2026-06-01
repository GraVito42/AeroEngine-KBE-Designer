"""
setup_kb.py — Inizializzazione knowledge base KBE Turbojet
Crea tre collezioni ChromaDB separate:
  · physics    — contenuto estratto dai PDF + note .md (testo + descrizioni immagini)
  · codebase   — classi e metodi Parapy estratti via AST
  · multall    — sezioni dei file .dat e output Multall

Rieseguibile senza duplicati — gli ID sono basati su nome file e posizione.
Per aggiungere le immagini in seguito: decommentare il blocco IMMAGINI e il time.sleep.
"""

from dotenv import load_dotenv
load_dotenv()

import os
import ast
import re
import io
import time
import chromadb
import fitz  # pymupdf
import PIL.Image
from google import genai
from pathlib import Path
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# CONFIGURAZIONE
# ---------------------------------------------------------------------------

PDF_DIR     = "./docs/pdf"
NOTES_DIR   = "./docs/notes"
PARAPY_DIR  = "./src"
MULTALL_DIR = "./multall"
CHROMA_DIR  = "./chroma_db"

EMBED_MODEL = "all-mpnet-base-v2"

# ---------------------------------------------------------------------------
# SETUP CLIENT
# ---------------------------------------------------------------------------

client        = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
embedder      = SentenceTransformer(EMBED_MODEL)

def embed(texts: list[str]) -> list[list[float]]:
    return embedder.encode(texts, show_progress_bar=False).tolist()

def add_to_collection(collection, docs, metas, ids):
    """Aggiunge chunks in batch da 500. Ignora ID già esistenti."""
    batch = 500
    for i in range(0, len(docs), batch):
        try:
            collection.add(
                documents=docs[i:i+batch],
                embeddings=embed(docs[i:i+batch]),
                metadatas=metas[i:i+batch],
                ids=ids[i:i+batch]
            )
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"  [INFO] alcuni chunks già presenti, saltati")
            else:
                raise

# ---------------------------------------------------------------------------
# COLLEZIONE 1 — PHYSICS (PDF + note .md)
# ---------------------------------------------------------------------------

def describe_image(image_bytes: bytes, page_context: str) -> str:
    time.sleep(4)  # rate limiter: max ~15 chiamate/minuto
    image = PIL.Image.open(io.BytesIO(image_bytes))
    prompt = f"""Sei un esperto di motori turbojet e turbomacchine.
Analizza questa immagine estratta da documentazione tecnica.
Il testo attorno nella stessa pagina dice:
\"\"\"{page_context[:500]}\"\"\"

Fornisci una descrizione tecnica strutturata:
1. Tipo di schema (meridional view / triangolo di velocità / mappa prestazione /
   diagramma architetturale / tabella / altro)
2. Componente o concetto rappresentato
3. Grandezze fisiche visibili (angoli, pressioni, velocità, efficienze...)
4. Relazioni geometriche o fisiche chiave leggibili dallo schema
5. Come questo schema si collega al codice Parapy o ai parametri Multall

Sii conciso ma tecnico. Usa terminologia aerospaziale precisa."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, image]
    )
    return response.text


def ingest_pdfs(collection):
    pdf_dir = Path(PDF_DIR)
    if not pdf_dir.exists():
        print(f"  [SKIP] cartella PDF non trovata: {PDF_DIR}")
        return

    docs, metas, ids = [], [], []

    for pdf_path in pdf_dir.rglob("*.pdf"):
        print(f"  Processo: {pdf_path.name}")
        doc = fitz.open(str(pdf_path))

        for page_num, page in enumerate(doc):

            # --- TESTO ---
            text = page.get_text().strip()
            if len(text) > 80:
                docs.append(text)
                metas.append({"source": pdf_path.name,
                               "page": page_num + 1,
                               "type": "text"})
                ids.append(f"pdf_{pdf_path.stem}_p{page_num}_t")

            # --- IMMAGINI --- (commentato per ora, decommentare quando hai più quota)
            # for img_index, img_ref in enumerate(page.get_images(full=True)):
            #     xref = img_ref[0]
            #     img_data = doc.extract_image(xref)
            #     if img_data["width"] < 100 or img_data["height"] < 100:
            #         continue
            #     try:
            #         description = describe_image(img_data["image"], text)
            #         docs.append(description)
            #         metas.append({"source": pdf_path.name,
            #                        "page": page_num + 1,
            #                        "type": "image",
            #                        "img_index": img_index})
            #         ids.append(f"pdf_{pdf_path.stem}_p{page_num}_i{img_index}")
            #     except Exception as e:
            #         print(f"    [WARN] immagine saltata ({e})")

        doc.close()

    if docs:
        add_to_collection(collection, docs, metas, ids)
        print(f"  → {len(docs)} chunks caricati dai PDF")


def ingest_notes(collection):
    notes_dir = Path(NOTES_DIR)
    if not notes_dir.exists():
        print(f"  [SKIP] cartella note non trovata: {NOTES_DIR}")
        return

    docs, metas, ids = [], [], []

    for md_path in notes_dir.rglob("*.md"):
        print(f"  Processo: {md_path.name}")
        text = md_path.read_text(encoding="utf-8", errors="ignore")
        sections = re.split(r'\n(?=#+ )', text)

        for sec_index, section in enumerate(sections):
            section = section.strip()
            if len(section) < 40:
                continue
            first_line = section.splitlines()[0].lstrip("#").strip()
            docs.append(section)
            metas.append({"source": md_path.name,
                           "type": "note",
                           "section": first_line})
            ids.append(f"note_{md_path.stem}_s{sec_index}")

    if docs:
        add_to_collection(collection, docs, metas, ids)
        print(f"  → {len(docs)} chunks caricati dalle note .md")

# ---------------------------------------------------------------------------
# COLLEZIONE 2 — CODEBASE (Parapy .py)
# ---------------------------------------------------------------------------

def extract_parapy_chunks(filepath: Path) -> list[dict]:
    source = filepath.read_text(encoding="utf-8", errors="ignore")
    chunks = []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        for i, line in enumerate(source.splitlines(keepends=True)):
            if line.strip():
                chunks.append({
                    "text": line,
                    "meta": {"source": filepath.name, "type": "raw_line",
                              "line": i + 1},
                    "id": f"code_{filepath.stem}_l{i}"
                })
        return chunks

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [n.name for n in ast.walk(node)
                       if isinstance(n, ast.FunctionDef)]
            assigns = [n.targets[0].id for n in ast.walk(node)
                       if isinstance(n, ast.Assign)
                       and isinstance(n.targets[0], ast.Name)]
            docstring = ast.get_docstring(node) or ""
            bases = [getattr(b, 'id', '') for b in node.bases]

            text = (f"Classe: {node.name}\n"
                    f"Eredita da: {', '.join(bases) or 'object'}\n"
                    f"Metodi: {', '.join(methods)}\n"
                    f"Attributi: {', '.join(assigns)}\n"
                    f"Docstring: {docstring}")
            chunks.append({
                "text": text,
                "meta": {"source": filepath.name, "type": "class",
                          "name": node.name, "line": node.lineno},
                "id": f"code_{filepath.stem}_class_{node.name}"
            })

        elif isinstance(node, ast.FunctionDef):
            docstring = ast.get_docstring(node) or ""
            args = [a.arg for a in node.args.args]
            try:
                body_lines = source.splitlines()[
                    node.lineno - 1: node.end_lineno
                ]
                body = "\n".join(body_lines[:40])
            except Exception:
                body = ""

            text = (f"Metodo: {node.name}\n"
                    f"Argomenti: {', '.join(args)}\n"
                    f"Docstring: {docstring}\n"
                    f"Corpo:\n{body}")
            chunks.append({
                "text": text,
                "meta": {"source": filepath.name, "type": "method",
                          "name": node.name, "line": node.lineno},
                "id": f"code_{filepath.stem}_fn_{node.name}_l{node.lineno}"
            })

    return chunks


def ingest_codebase(collection):
    src_dir = Path(PARAPY_DIR)
    if not src_dir.exists():
        print(f"  [SKIP] cartella codebase non trovata: {PARAPY_DIR}")
        return

    docs, metas, ids = [], [], []

    for py_path in src_dir.rglob("*.py"):
        print(f"  Processo: {py_path.name}")
        for c in extract_parapy_chunks(py_path):
            docs.append(c["text"])
            metas.append(c["meta"])
            ids.append(c["id"])

    if docs:
        add_to_collection(collection, docs, metas, ids)
        print(f"  → {len(docs)} chunks caricati nella collezione 'codebase'")

# ---------------------------------------------------------------------------
# COLLEZIONE 3 — MULTALL (.dat e output)
# ---------------------------------------------------------------------------

def chunk_multall_file(filepath: Path) -> list[dict]:
    SECTION_PATTERN = re.compile(
        r"^\s*(BLADE|INLET|OUTLET|HUB|CASING|ROTOR|STATOR|"
        r"NROWS|NSTREAM|NPASS|TITLE|END|\d{1,4}\s+\d)",
        re.IGNORECASE
    )

    text = filepath.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    sections, current_title, current_lines = [], "header", []
    for line in lines:
        if SECTION_PATTERN.match(line) and current_lines:
            sections.append((current_title, "\n".join(current_lines)))
            current_title = line.strip()[:60]
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_title, "\n".join(current_lines)))

    return [
        {"text": f"File: {filepath.name}\nSezione: {title}\n\n{body}",
         "meta": {"source": filepath.name,
                  "type": "dat" if filepath.suffix == ".dat" else "output",
                  "section": title},
         "id": f"multall_{filepath.stem}_{re.sub(r'[^a-z0-9]', '_', title.lower())[:40]}"}
        for title, body in sections if body.strip()
    ]


def ingest_multall(collection):
    m_dir = Path(MULTALL_DIR)
    if not m_dir.exists():
        print(f"  [SKIP] cartella Multall non trovata: {MULTALL_DIR}")
        return

    docs, metas, ids = [], [], []

    extensions = {".dat", ".out", ".res", ".txt"}
    for f in m_dir.rglob("*"):
        if f.suffix.lower() not in extensions:
            continue
        print(f"  Processo: {f.name}")
        for c in chunk_multall_file(f):
            docs.append(c["text"])
            metas.append(c["meta"])
            ids.append(c["id"])

    if docs:
        add_to_collection(collection, docs, metas, ids)
        print(f"  → {len(docs)} chunks caricati nella collezione 'multall'")

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Setup Knowledge Base KBE Turbojet ===\n")

    physics_col  = chroma_client.get_or_create_collection("physics")
    codebase_col = chroma_client.get_or_create_collection("codebase")
    multall_col  = chroma_client.get_or_create_collection("multall")

    print("[1/4] Ingestione PDF (solo testo per ora)...")
    ingest_pdfs(physics_col)

    print("\n[2/4] Ingestione note .md...")
    ingest_notes(physics_col)

    print("\n[3/4] Ingestione codebase Parapy...")
    ingest_codebase(codebase_col)

    print("\n[4/4] Ingestione file Multall...")
    ingest_multall(multall_col)

    print("\n=== Fatto. Collezioni create in:", CHROMA_DIR, "===")
    print("Chunks totali:")
    print(f"  physics:  {physics_col.count()}")
    print(f"  codebase: {codebase_col.count()}")
    print(f"  multall:  {multall_col.count()}")