"""
src/rag.py — RAG (Retrieval-Augmented Generation) pipeline.

Flow:
  1. Load documents from data/docs/ (.md, .txt, .pdf)
  2. Split into small chunks (so retrieval is precise, not full-doc)
  3. Embed each chunk with Ollama (nomic-embed-text model)
  4. Store in ChromaDB (local vector database)
  5. On query: embed the question → find closest chunks → return them

The vector store is persisted to disk — only rebuilt when you add new docs.
"""

from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from src.config import settings


def _get_embeddings() -> OllamaEmbeddings:
    """Local embeddings via Ollama. Run: ollama pull nomic-embed-text"""
    return OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=settings.ollama_base_url,
    )


def build_vector_store(force_rebuild: bool = False) -> Chroma:
    """
    Build or load the ChromaDB vector store.

    - First run: loads all docs → splits → embeds → saves to disk
    - Later runs: just loads from disk (fast)
    - force_rebuild=True: re-ingests everything (use after adding new docs)
    """
    embeddings = _get_embeddings()
    chroma_path = Path(settings.chroma_dir)

    if chroma_path.exists() and not force_rebuild:
        print(f"[RAG] Loading existing vector store from {settings.chroma_dir}")
        return Chroma(
            collection_name="business_docs",
            embedding_function=embeddings,
            persist_directory=settings.chroma_dir,
        )

    print(f"[RAG] Building vector store from {settings.docs_dir} ...")

    # Python glob doesn't support {md,txt} brace syntax — one loader per extension
    docs = []
    for pattern in ("**/*.md", "**/*.txt"):
        loader = DirectoryLoader(
            settings.docs_dir,
            glob=pattern,
            loader_cls=TextLoader,
            show_progress=True,
        )
        docs.extend(loader.load())

    if not docs:
        print(f"[RAG] ⚠️  No documents found in {settings.docs_dir}/")
        return Chroma(
            collection_name="business_docs",
            embedding_function=embeddings,
            persist_directory=settings.chroma_dir,
        )

    # 2. Split into chunks
    # Why chunk? LLMs have context limits + smaller chunks = more precise retrieval
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,        # ~800 chars per chunk
        chunk_overlap=settings.chunk_overlap,  # 100 chars overlap so context isn't lost
        separators=["\n\n", "\n", ".", " "],   # split on paragraphs first, then lines
    )
    chunks = splitter.split_documents(docs)
    print(f"[RAG] {len(docs)} docs → {len(chunks)} chunks")

    # 3. Embed + store
    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name="business_docs",
        persist_directory=settings.chroma_dir,
    )


def get_retriever():
    """Returns a retriever ready to use as a LangChain tool."""
    store = build_vector_store()
    return store.as_retriever(search_kwargs={"k": settings.rag_top_k})