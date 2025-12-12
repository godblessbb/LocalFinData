"""
Search API for external agents.

This module provides a clean interface for agents to search financial news
with semantic queries and structured filters.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from .store import FinancialNewsStore

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """
    A single search result.

    Attributes:
        id: Unique document ID
        symbol: Stock symbol (e.g., "AAPL")
        news_date: Publication date (YYYY-MM-DD)
        source: News source
        title: News title
        content: News content
        similarity: Similarity score (0-1, higher is better)
        price_change_1d: 1-day price change after news
        price_change_3d: 3-day price change after news
        price_change_5d: 5-day price change after news
        price_change_10d: 10-day price change after news
    """

    id: str
    symbol: str
    news_date: str
    source: str
    title: str
    content: str
    similarity: Optional[float] = None
    price_change_1d: Optional[float] = None
    price_change_3d: Optional[float] = None
    price_change_5d: Optional[float] = None
    price_change_10d: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def summary(self) -> str:
        """Return a brief summary string."""
        sim_str = f" (similarity: {self.similarity:.3f})" if self.similarity else ""
        price_str = ""
        if self.price_change_1d is not None:
            price_str = f" | 1d: {self.price_change_1d:+.2%}"
        if self.price_change_5d is not None:
            price_str += f", 5d: {self.price_change_5d:+.2%}"
        return f"[{self.news_date}] [{self.symbol}] {self.title}{sim_str}{price_str}"


class SearchAPI:
    """
    High-level search API for external agents.

    This class provides a clean, agent-friendly interface for searching
    financial news. It's designed to be called by AI agents that need
    to find relevant historical news events.

    Usage:
        api = SearchAPI(persist_dir="./data/vector_db")

        # Semantic search
        results = api.search("trade war impact on Apple")

        # Search with filters
        results = api.search(
            query="earnings report",
            symbols=["AAPL", "MSFT"],
            date_from="2024-01-01",
            top_k=10
        )

        # Filter-only search (no semantic query)
        results = api.search_by_filters(
            symbols=["NVDA"],
            min_price_change=0.05,  # 5%+ moves
            top_k=20
        )

        # Find similar historical events
        results = api.find_similar_events(
            reference_text="Apple stock drops 5% on China tariff concerns",
            top_k=10
        )
    """

    def __init__(
        self,
        persist_dir: str = "./data/vector_db",
        model_path: Optional[str] = None,
        use_4bit: bool = True,
    ):
        """
        Initialize the Search API.

        Args:
            persist_dir: Path to ChromaDB persist directory
            model_path: Path to embedding model (optional)
            use_4bit: Whether to use 4-bit quantization
        """
        self._store = FinancialNewsStore(
            persist_dir=persist_dir,
            model_path=model_path,
            use_4bit=use_4bit,
        )

    @property
    def document_count(self) -> int:
        """Return total number of documents in the store."""
        return self._store.count

    def search(
        self,
        query: str,
        symbols: Optional[List[str]] = None,
        sectors: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sources: Optional[List[str]] = None,
        min_price_change: Optional[float] = None,
        max_price_change: Optional[float] = None,
        top_k: int = 20,
    ) -> List[SearchResult]:
        """
        Search for similar news with optional filters.

        This is the main search method that combines semantic similarity
        with structured filters.

        Args:
            query: Natural language search query
            symbols: Filter by stock symbols (e.g., ["AAPL", "MSFT"])
            sectors: Filter by sectors (e.g., ["Healthcare"])
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            sources: Filter by news sources
            min_price_change: Minimum 1-day price change (e.g., 0.05 for 5%)
            max_price_change: Maximum 1-day price change
            top_k: Number of results to return

        Returns:
            List of SearchResult objects, sorted by relevance

        Example:
            # Find news about trade tensions affecting tech stocks
            results = api.search(
                query="US China trade war technology semiconductor",
                symbols=["NVDA", "AMD", "INTC"],
                date_from="2024-01-01",
                top_k=15
            )
        """
        raw_results = self._store.search(
            query=query,
            symbols=symbols,
            sectors=sectors,
            date_from=date_from,
            date_to=date_to,
            sources=sources,
            min_price_change_1d=min_price_change,
            max_price_change_1d=max_price_change,
            top_k=top_k,
        )
        return self._convert_results(raw_results)

    def search_by_filters(
        self,
        symbols: Optional[List[str]] = None,
        sectors: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sources: Optional[List[str]] = None,
        min_price_change: Optional[float] = None,
        max_price_change: Optional[float] = None,
        top_k: int = 20,
    ) -> List[SearchResult]:
        """
        Search using only filters, without semantic query.

        Useful when you want to retrieve news based purely on
        structured criteria without semantic matching.

        Args:
            symbols: Filter by stock symbols
            sectors: Filter by sectors
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            sources: Filter by news sources
            min_price_change: Minimum 1-day price change
            max_price_change: Maximum 1-day price change
            top_k: Number of results to return

        Returns:
            List of SearchResult objects

        Example:
            # Get all major news events (5%+ price move) for healthcare sector
            results = api.search_by_filters(
                sectors=["Healthcare", "Biotech"],
                min_price_change=0.05,
                date_from="2024-01-01",
                top_k=50
            )
        """
        raw_results = self._store.search(
            query="",  # Empty query for filter-only search
            symbols=symbols,
            sectors=sectors,
            date_from=date_from,
            date_to=date_to,
            sources=sources,
            min_price_change_1d=min_price_change,
            max_price_change_1d=max_price_change,
            top_k=top_k,
        )
        return self._convert_results(raw_results)

    def find_similar_events(
        self,
        reference_text: str,
        exclude_symbols: Optional[List[str]] = None,
        include_symbols: Optional[List[str]] = None,
        date_before: Optional[str] = None,
        top_k: int = 10,
    ) -> List[SearchResult]:
        """
        Find historically similar news events.

        Given a reference news text, find similar events from the past.
        This is useful for analyzing "what happened last time when
        similar news occurred".

        Args:
            reference_text: The reference news content to find similar events for
            exclude_symbols: Symbols to exclude (e.g., exclude the same stock)
            include_symbols: Only include these symbols
            date_before: Only return events before this date
            top_k: Number of results to return

        Returns:
            List of historically similar news events

        Example:
            # Find what happened historically when Apple had tariff concerns
            results = api.find_similar_events(
                reference_text="Apple stock drops on China tariff concerns",
                exclude_symbols=["AAPL"],  # Find similar events for OTHER stocks
                top_k=10
            )
        """
        raw_results = self._store.search(
            query=reference_text,
            symbols=include_symbols,
            date_to=date_before,
            top_k=top_k * 2,  # Get more to filter
        )

        # Filter out excluded symbols
        if exclude_symbols:
            exclude_set = set(exclude_symbols)
            raw_results = [
                r for r in raw_results if r.get("symbol") not in exclude_set
            ]

        return self._convert_results(raw_results[:top_k])

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.

        Returns:
            Dictionary with store statistics
        """
        return self._store.get_stats()

    def _convert_results(self, raw_results: List[Dict]) -> List[SearchResult]:
        """Convert raw dict results to SearchResult objects."""
        results = []
        for r in raw_results:
            results.append(
                SearchResult(
                    id=r.get("id", ""),
                    symbol=r.get("symbol", ""),
                    news_date=r.get("news_date", ""),
                    source=r.get("source", ""),
                    title=r.get("title", ""),
                    content=r.get("content", ""),
                    similarity=r.get("similarity"),
                    price_change_1d=r.get("price_change_1d"),
                    price_change_3d=r.get("price_change_3d"),
                    price_change_5d=r.get("price_change_5d"),
                    price_change_10d=r.get("price_change_10d"),
                )
            )
        return results


# Convenience function for quick searches
def quick_search(
    query: str,
    persist_dir: str = "./data/vector_db",
    top_k: int = 10,
    **filters,
) -> List[SearchResult]:
    """
    Quick search without initializing a full API object.

    Args:
        query: Search query
        persist_dir: Vector DB path
        top_k: Number of results
        **filters: Additional filters (symbols, date_from, etc.)

    Returns:
        List of SearchResult objects
    """
    api = SearchAPI(persist_dir=persist_dir)
    return api.search(query=query, top_k=top_k, **filters)
