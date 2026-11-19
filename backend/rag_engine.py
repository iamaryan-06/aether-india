"""
rag_engine.py — ChromaDB RAG engine for AETHER INDIA brand knowledge.

Embedding strategy (100% free / offline):
  Primary:  chromadb built-in SentenceTransformerEmbeddingFunction
            (uses sentence-transformers/all-MiniLM-L6-v2 locally)
  Fallback: chromadb DefaultEmbeddingFunction
            (uses ONNX all-MiniLM-L6-v2 — no extra packages needed)

Documents indexed (from backend/knowledge_base/):
  • return_policy.md
  • size_and_fit_guide.md
  • fabric_care_manual.md
  • shipping_sla.md

Public API:
  query_brand_knowledge_rag(query, n_results) -> str
  get_collection()                            -> chromadb.Collection
  rebuild_index()                             -> chromadb.Collection
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────
CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
KNOWLEDGE_BASE_DIR: Path = Path(__file__).parent / "knowledge_base"
COLLECTION_NAME: str = "aether_brand_knowledge"

# ── Chunking config ───────────────────────────────────────────────────────────
CHUNK_SIZE: int = 700      # characters per chunk
CHUNK_OVERLAP_LINES: int = 3  # lines to repeat for context continuity
N_RESULTS_DEFAULT: int = 4


# ─────────────────────────────────────────────────────────────────────────────
# Embedding function factory
# ─────────────────────────────────────────────────────────────────────────────

def _get_embedding_function():
    """
    Return the best available local embedding function.

    Preference order:
        1. SentenceTransformerEmbeddingFunction (all-MiniLM-L6-v2)
           — needs sentence-transformers (in requirements.txt)
        2. DefaultEmbeddingFunction
           — uses chromadb's bundled ONNX all-MiniLM-L6-v2
    Both are 100% free and run fully offline after the first model download.
    """
    try:
        from chromadb.utils.embedding_functions import (
            SentenceTransformerEmbeddingFunction,
        )
        ef = SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2",
            device="cpu",
        )
        print("[RAG] Embedding: SentenceTransformer all-MiniLM-L6-v2 (local)")
        return ef
    except Exception as e:
        print(f"[RAG] SentenceTransformer unavailable ({e}), falling back to DefaultEmbeddingFunction")
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        return DefaultEmbeddingFunction()


# ─────────────────────────────────────────────────────────────────────────────
# Document chunking
# ─────────────────────────────────────────────────────────────────────────────

def _chunk_markdown(text: str, source: str) -> list[dict]:
    """
    Split a markdown document into overlapping text chunks.

    Strategy:
      • Split by newlines, tracking the current section heading.
      • When a chunk reaches CHUNK_SIZE characters, flush it and start a new
        one with CHUNK_OVERLAP_LINES lines of overlap so context is preserved
        across chunk boundaries.
      • Empty / whitespace-only chunks are discarded.

    Returns a list of dicts: {"text", "source", "section"}
    """
    lines = text.split("\n")
    chunks: list[dict] = []
    current_lines: list[str] = []
    current_chars: int = 0
    current_section: str = ""

    for line in lines:
        # Track the nearest heading for metadata
        stripped = line.strip()
        if stripped.startswith("#"):
            current_section = stripped.lstrip("#").strip()

        line_len = len(line) + 1  # +1 for the newline

        # Flush when chunk is full
        if current_chars + line_len > CHUNK_SIZE and current_lines:
            chunk_text = "\n".join(current_lines).strip()
            if chunk_text:
                chunks.append(
                    {"text": chunk_text, "source": source, "section": current_section}
                )
            # Keep the last few lines as overlap
            overlap = current_lines[-CHUNK_OVERLAP_LINES:]
            current_lines = overlap + [line]
            current_chars = sum(len(l) + 1 for l in current_lines)
        else:
            current_lines.append(line)
            current_chars += line_len

    # Flush remaining lines
    if current_lines:
        chunk_text = "\n".join(current_lines).strip()
        if chunk_text:
            chunks.append(
                {"text": chunk_text, "source": source, "section": current_section}
            )

    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# Index builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_index(client, embedding_fn) -> "chromadb.Collection":
    """
    Read all markdown files from KNOWLEDGE_BASE_DIR, chunk them, and
    upsert into a new ChromaDB collection.
    """
    md_files = sorted(KNOWLEDGE_BASE_DIR.glob("*.md"))
    if not md_files:
        raise FileNotFoundError(
            f"No .md files found in {KNOWLEDGE_BASE_DIR}. "
            "Please verify knowledge_base/ directory exists."
        )

    all_ids: list[str] = []
    all_texts: list[str] = []
    all_metas: list[dict] = []

    for md_path in md_files:
        text = md_path.read_text(encoding="utf-8")
        source = md_path.name
        chunks = _chunk_markdown(text, source)
        for i, chunk in enumerate(chunks):
            all_ids.append(f"{source}__c{i:04d}")
            all_texts.append(chunk["text"])
            all_metas.append(
                {"source": chunk["source"], "section": chunk["section"]}
            )
        print(f"[RAG]   {source}: {len(chunks)} chunks")

    # Create collection
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    # Upsert in batches of 64 (safe for memory and ChromaDB limits)
    BATCH = 64
    for start in range(0, len(all_ids), BATCH):
        end = start + BATCH
        collection.add(
            ids=all_ids[start:end],
            documents=all_texts[start:end],
            metadatas=all_metas[start:end],
        )

    print(
        f"[RAG] Index built: {collection.count()} chunks "
        f"from {len(md_files)} documents → {CHROMA_PERSIST_DIR}"
    )
    return collection


# ─────────────────────────────────────────────────────────────────────────────
# Singleton collection
# ─────────────────────────────────────────────────────────────────────────────

_collection: Optional["chromadb.Collection"] = None


def rebuild_index() -> "chromadb.Collection":
    """
    Delete any existing collection and rebuild from scratch.
    Useful after updating knowledge_base/ markdown files.
    """
    global _collection
    import chromadb

    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    embedding_fn = _get_embedding_function()

    # Delete existing collection if present
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"[RAG] Deleted existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    _collection = _build_index(client, embedding_fn)
    return _collection


def get_collection() -> "chromadb.Collection":
    """
    Return the singleton ChromaDB collection, building it on first call.
    Subsequent calls return the cached instance (no re-embedding cost).
    """
    global _collection
    if _collection is not None:
        return _collection

    import chromadb

    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    embedding_fn = _get_embedding_function()

    # Check whether a populated collection already exists on disk
    existing_names = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing_names:
        col = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn,
        )
        if col.count() > 0:
            print(
                f"[RAG] Loaded existing index: {col.count()} chunks "
                f"in '{COLLECTION_NAME}'"
            )
            _collection = col
            return _collection
        else:
            # Empty collection — rebuild
            client.delete_collection(COLLECTION_NAME)

    # Build fresh
    print(f"[RAG] Building index from {KNOWLEDGE_BASE_DIR} …")
    _collection = _build_index(client, embedding_fn)
    return _collection


# ─────────────────────────────────────────────────────────────────────────────
# Public query function
# ─────────────────────────────────────────────────────────────────────────────

def query_brand_knowledge_rag(query: str, n_results: int = N_RESULTS_DEFAULT) -> str:
    """
    Semantic search over the AETHER INDIA brand knowledge base.

    Args:
        query:     Natural-language question / search string.
        n_results: Number of top chunks to return (default 4).

    Returns:
        A formatted string of the most relevant knowledge chunks with
        source file and section attribution, ready for the LLM to use
        as context.  Returns a clear "not found" message if no results.
    """
    collection = get_collection()
    count = collection.count()
    if count == 0:
        return (
            "The brand knowledge base is empty. "
            "Please run the RAG index builder first."
        )

    n = min(n_results, count)
    results = collection.query(
        query_texts=[query],
        n_results=n,
        include=["documents", "metadatas", "distances"],
    )

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    if not docs:
        return (
            "No relevant information found in the AETHER INDIA brand "
            "knowledge base for this query."
        )

    parts: list[str] = []
    for doc, meta, dist in zip(docs, metas, dists):
        # Cosine distance → similarity (0 = identical, 2 = opposite)
        similarity = max(0.0, 1.0 - dist)
        source = meta.get("source", "unknown")
        section = meta.get("section", "")
        header = f"📄 [{source}]"
        if section:
            header += f" — {section}"
        header += f"  (relevance: {similarity:.0%})"
        parts.append(f"{header}\n{doc}")

    return "\n\n" + ("\n\n---\n\n".join(parts))
