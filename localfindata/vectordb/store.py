"""
ChromaDB-based vector store for financial news.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from .embedder import BaseEmbedder, create_embedder

logger = logging.getLogger(__name__)


@dataclass
class NewsDocument:
    """Represents a financial news document."""

    news_id: str
    symbol: str
    news_date: str
    source: str
    title: str
    content: str
    price_change_1d: Optional[float] = None
    price_change_3d: Optional[float] = None
    price_change_5d: Optional[float] = None
    price_change_10d: Optional[float] = None
    sector: Optional[str] = None
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_text(self) -> str:
        """Convert to text for embedding."""
        return f"{self.title}\n{self.content}"

    def to_metadata(self) -> Dict[str, Any]:
        """Convert to metadata dict for storage."""
        metadata = {
            "symbol": self.symbol,
            "news_date": self.news_date,
            "source": self.source,
            "title": self.title,
        }

        # Add optional fields if present
        if self.price_change_1d is not None:
            metadata["price_change_1d"] = float(self.price_change_1d)
        if self.price_change_3d is not None:
            metadata["price_change_3d"] = float(self.price_change_3d)
        if self.price_change_5d is not None:
            metadata["price_change_5d"] = float(self.price_change_5d)
        if self.price_change_10d is not None:
            metadata["price_change_10d"] = float(self.price_change_10d)
        if self.sector:
            metadata["sector"] = self.sector

        # Add any extra metadata
        metadata.update(self.extra_metadata)

        return metadata

    @classmethod
    def from_csv_row(cls, row: Dict[str, Any]) -> "NewsDocument":
        """Create from a CSV row dict."""
        # Generate unique ID from content hash
        content = str(row.get("news_content", ""))
        title = str(row.get("news_title", ""))
        symbol = str(row.get("symbol", ""))
        date = str(row.get("news_date", ""))

        news_id = hashlib.md5(
            f"{symbol}_{date}_{title}_{content[:100]}".encode()
        ).hexdigest()

        def safe_float(val):
            try:
                if val is None or val == "" or str(val).lower() == "nan":
                    return None
                return float(val)
            except (ValueError, TypeError):
                return None

        return cls(
            news_id=news_id,
            symbol=symbol,
            news_date=date,
            source=str(row.get("source", "")),
            title=title,
            content=content,
            price_change_1d=safe_float(row.get("price_change_1d")),
            price_change_3d=safe_float(row.get("price_change_3d")),
            price_change_5d=safe_float(row.get("price_change_5d")),
            price_change_10d=safe_float(row.get("price_change_10d")),
            sector=row.get("sector"),
        )


class FinancialNewsStore:
    """
    ChromaDB-based vector store for financial news.

    Usage:
        # Initialize
        store = FinancialNewsStore(
            persist_dir="./data/vector_db",
            model_path="D:/models/Qwen3-Embedding-4B"
        )

        # Add documents
        store.add_documents([doc1, doc2, ...])

        # Search
        results = store.search(
            query="trade war impact on tech stocks",
            symbols=["AAPL", "MSFT"],
            top_k=10
        )
    """

    def __init__(
        self,
        persist_dir: str = "./data/vector_db",
        collection_name: str = "financial_news",
        embedder: Optional[BaseEmbedder] = None,
        model_path: Optional[str] = None,
        use_4bit: bool = True,
    ):
        """
        Initialize the vector store.

        Args:
            persist_dir: Directory to persist ChromaDB data
            collection_name: Name of the collection
            embedder: Optional pre-configured embedder
            model_path: Path to embedding model (if embedder not provided)
            use_4bit: Whether to use 4-bit quantization
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        # Initialize embedder
        if embedder:
            self._embedder = embedder
        else:
            self._embedder = create_embedder(
                model_path=model_path,
                use_4bit=use_4bit,
            )

        # Initialize ChromaDB
        self._client = None
        self._collection = None

    def _get_client(self):
        """Lazy load ChromaDB client."""
        if self._client is None:
            import chromadb

            self._client = chromadb.PersistentClient(path=str(self.persist_dir))
            logger.info(f"ChromaDB initialized at {self.persist_dir}")
        return self._client

    def _get_collection(self):
        """Get or create the collection."""
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},  # Use cosine similarity
            )
            logger.info(
                f"Collection '{self.collection_name}' ready. "
                f"Current count: {self._collection.count()}"
            )
        return self._collection

    @property
    def count(self) -> int:
        """Return the number of documents in the store."""
        return self._get_collection().count()

    def add_documents(
        self,
        documents: List[NewsDocument],
        batch_size: int = 100,
        show_progress: bool = True,
    ) -> int:
        """
        Add documents to the store.

        Args:
            documents: List of NewsDocument to add
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar

        Returns:
            Number of documents added
        """
        if not documents:
            return 0

        collection = self._get_collection()

        # Get existing IDs to avoid duplicates
        existing_ids = set()
        try:
            # Check in batches to avoid memory issues
            all_ids = [doc.news_id for doc in documents]
            for i in range(0, len(all_ids), 1000):
                batch_ids = all_ids[i : i + 1000]
                result = collection.get(ids=batch_ids)
                existing_ids.update(result["ids"])
        except Exception:
            pass

        # Filter out existing documents
        new_documents = [doc for doc in documents if doc.news_id not in existing_ids]

        if not new_documents:
            logger.info("No new documents to add")
            return 0

        logger.info(
            f"Adding {len(new_documents)} new documents "
            f"({len(documents) - len(new_documents)} duplicates skipped)"
        )

        # Process in batches
        added_count = 0
        iterator = range(0, len(new_documents), batch_size)

        if show_progress:
            try:
                from tqdm import tqdm

                iterator = tqdm(
                    iterator,
                    desc="Adding documents",
                    total=len(new_documents) // batch_size + 1,
                )
            except ImportError:
                pass

        for i in iterator:
            batch = new_documents[i : i + batch_size]

            # Prepare texts for embedding
            texts = [doc.to_text() for doc in batch]

            # Generate embeddings
            embeddings = self._embedder.encode(texts)

            # Prepare data for ChromaDB
            ids = [doc.news_id for doc in batch]
            metadatas = [doc.to_metadata() for doc in batch]
            documents_text = [doc.content for doc in batch]

            # Add to collection
            collection.add(
                ids=ids,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
                documents=documents_text,
            )

            added_count += len(batch)

        logger.info(f"Successfully added {added_count} documents")
        return added_count

    def search(
        self,
        query: str = "",
        symbols: Optional[List[str]] = None,
        sectors: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sources: Optional[List[str]] = None,
        min_price_change_1d: Optional[float] = None,
        max_price_change_1d: Optional[float] = None,
        top_k: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar news with optional filters.

        Args:
            query: Semantic search query (can be empty for filter-only search)
            symbols: Filter by stock symbols (e.g., ["AAPL", "MSFT"])
            sectors: Filter by sectors (e.g., ["Healthcare", "Technology"])
            date_from: Filter by date range start (YYYY-MM-DD)
            date_to: Filter by date range end (YYYY-MM-DD)
            sources: Filter by news sources
            min_price_change_1d: Minimum 1-day price change
            max_price_change_1d: Maximum 1-day price change
            top_k: Number of results to return

        Returns:
            List of search results with metadata and similarity scores
        """
        collection = self._get_collection()

        # Build where filter
        where_filter = self._build_where_filter(
            symbols=symbols,
            sectors=sectors,
            date_from=date_from,
            date_to=date_to,
            sources=sources,
            min_price_change_1d=min_price_change_1d,
            max_price_change_1d=max_price_change_1d,
        )

        # Execute search
        if query:
            # Semantic search
            query_embedding = self._embedder.encode(query)
            results = collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=top_k,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"],
            )
        else:
            # Filter-only search (no semantic query)
            results = collection.get(
                where=where_filter if where_filter else None,
                limit=top_k,
                include=["documents", "metadatas"],
            )
            # Convert to query result format
            results = {
                "ids": [results["ids"]],
                "documents": [results["documents"]],
                "metadatas": [results["metadatas"]],
                "distances": [None],
            }

        return self._format_results(results)

    def _build_where_filter(
        self,
        symbols: Optional[List[str]] = None,
        sectors: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sources: Optional[List[str]] = None,
        min_price_change_1d: Optional[float] = None,
        max_price_change_1d: Optional[float] = None,
    ) -> Optional[Dict]:
        """Build ChromaDB where filter from search parameters."""
        conditions = []

        # Symbol filter
        if symbols:
            if len(symbols) == 1:
                conditions.append({"symbol": {"$eq": symbols[0]}})
            else:
                conditions.append({"symbol": {"$in": symbols}})

        # Sector filter
        if sectors:
            if len(sectors) == 1:
                conditions.append({"sector": {"$eq": sectors[0]}})
            else:
                conditions.append({"sector": {"$in": sectors}})

        # Source filter
        if sources:
            if len(sources) == 1:
                conditions.append({"source": {"$eq": sources[0]}})
            else:
                conditions.append({"source": {"$in": sources}})

        # Date range filter
        if date_from:
            conditions.append({"news_date": {"$gte": date_from}})
        if date_to:
            conditions.append({"news_date": {"$lte": date_to}})

        # Price change filter
        if min_price_change_1d is not None:
            conditions.append({"price_change_1d": {"$gte": min_price_change_1d}})
        if max_price_change_1d is not None:
            conditions.append({"price_change_1d": {"$lte": max_price_change_1d}})

        if not conditions:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"$and": conditions}

    def _format_results(self, results: Dict) -> List[Dict[str, Any]]:
        """Format ChromaDB results into a clean list."""
        formatted = []

        ids = results["ids"][0] if results["ids"] else []
        documents = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        distances = results.get("distances", [[]])[0]

        for i, (doc_id, doc, meta) in enumerate(zip(ids, documents, metadatas)):
            result = {
                "id": doc_id,
                "content": doc,
                **meta,
            }

            # Add similarity score (convert distance to similarity)
            if distances and distances[i] is not None:
                # ChromaDB returns L2 distance for cosine space
                # similarity = 1 - distance for cosine
                result["similarity"] = 1 - distances[i]

            formatted.append(result)

        return formatted

    def delete_by_symbol(self, symbol: str) -> int:
        """Delete all documents for a specific symbol."""
        collection = self._get_collection()

        # Get IDs to delete
        results = collection.get(
            where={"symbol": {"$eq": symbol}},
            include=[],
        )

        if not results["ids"]:
            return 0

        collection.delete(ids=results["ids"])
        logger.info(f"Deleted {len(results['ids'])} documents for {symbol}")
        return len(results["ids"])

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the store."""
        collection = self._get_collection()

        # Get sample to analyze
        sample = collection.get(limit=1000, include=["metadatas"])

        symbols = set()
        sources = set()
        date_range = [None, None]

        for meta in sample["metadatas"]:
            if meta.get("symbol"):
                symbols.add(meta["symbol"])
            if meta.get("source"):
                sources.add(meta["source"])
            if meta.get("news_date"):
                date = meta["news_date"]
                if date_range[0] is None or date < date_range[0]:
                    date_range[0] = date
                if date_range[1] is None or date > date_range[1]:
                    date_range[1] = date

        return {
            "total_documents": collection.count(),
            "unique_symbols_sample": len(symbols),
            "unique_sources_sample": len(sources),
            "date_range_sample": date_range,
            "persist_dir": str(self.persist_dir),
            "collection_name": self.collection_name,
        }
