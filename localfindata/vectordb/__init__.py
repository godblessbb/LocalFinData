"""
Financial News Vector Database Module

A lightweight vector search system for financial news-futu-stock with:
- Local embedding model support (Qwen3-Embedding-4B with 4-bit quantization)
- ChromaDB for vector storage
- Structured filtering (symbol, date, sector, price change)
- Designed as a data API for external agents

Quick Start:
    from localfindata.vectordb import SearchAPI, NewsIngester, FinancialNewsStore

    # Initialize API
    api = SearchAPI(persist_dir="./data/vector_db")

    # Search
    results = api.search("trade war impact on tech stocks", top_k=10)
    for r in results:
        print(r.summary())

    # Ingest new data
    store = FinancialNewsStore(persist_dir="./data/vector_db")
    ingester = NewsIngester(store)
    ingester.ingest_directory("./data/news-futu-stock-yh-stock/")
"""

from .store import FinancialNewsStore, NewsDocument
from .search import SearchResult, SearchAPI, quick_search
from .embedder import QwenEmbedder, SentenceTransformerEmbedder, OpenAIEmbedder, create_embedder
from .ingest import NewsIngester, ingest_from_csv, ingest_from_directory

__all__ = [
    # Main classes
    "FinancialNewsStore",
    "SearchAPI",
    "NewsIngester",
    # Data classes
    "NewsDocument",
    "SearchResult",
    # Embedders
    "QwenEmbedder",
    "SentenceTransformerEmbedder",
    "OpenAIEmbedder",
    "create_embedder",
    # Convenience functions
    "quick_search",
    "ingest_from_csv",
    "ingest_from_directory",
]
