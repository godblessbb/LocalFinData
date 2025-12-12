"""
CSV batch ingestion for financial news.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Generator, List, Optional

import pandas as pd

from .store import FinancialNewsStore, NewsDocument

logger = logging.getLogger(__name__)


class NewsIngester:
    """
    Batch ingestion of financial news from CSV files.

    Expected CSV format:
        symbol,news_date,source,news_title,news_content,price_change_1d,...

    Usage:
        ingester = NewsIngester(store)

        # Ingest single file
        ingester.ingest_file("./data/news/AAPL.csv")

        # Ingest entire directory
        ingester.ingest_directory("./data/news-yh-stock/")
    """

    def __init__(
        self,
        store: FinancialNewsStore,
        batch_size: int = 500,
    ):
        """
        Initialize the ingester.

        Args:
            store: FinancialNewsStore instance
            batch_size: Number of documents to process at once
        """
        self.store = store
        self.batch_size = batch_size

    def ingest_file(
        self,
        file_path: str,
        show_progress: bool = True,
    ) -> int:
        """
        Ingest news from a single CSV file.

        Args:
            file_path: Path to CSV file
            show_progress: Whether to show progress

        Returns:
            Number of documents ingested
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return 0

        logger.info(f"Ingesting {file_path}")

        total_added = 0

        for batch in self._read_csv_batches(file_path):
            documents = [NewsDocument.from_csv_row(row) for row in batch]
            # Filter out documents with empty content
            documents = [d for d in documents if d.content.strip()]
            added = self.store.add_documents(
                documents,
                show_progress=show_progress,
            )
            total_added += added

        logger.info(f"Completed {file_path}: {total_added} documents added")
        return total_added

    def ingest_directory(
        self,
        directory: str,
        pattern: str = "*.csv",
        show_progress: bool = True,
    ) -> dict:
        """
        Ingest all CSV files from a directory.

        Args:
            directory: Directory containing CSV files
            pattern: Glob pattern for CSV files
            show_progress: Whether to show progress

        Returns:
            Dict with ingestion statistics
        """
        directory = Path(directory)

        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return {"error": "Directory not found", "total": 0}

        csv_files = sorted(directory.glob(pattern))

        if not csv_files:
            logger.warning(f"No CSV files found matching {pattern} in {directory}")
            return {"files_processed": 0, "total_documents": 0}

        logger.info(f"Found {len(csv_files)} CSV files in {directory}")

        results = {
            "files_processed": 0,
            "files_failed": 0,
            "total_documents": 0,
            "by_file": {},
        }

        file_iterator = csv_files
        if show_progress:
            try:
                from tqdm import tqdm

                file_iterator = tqdm(csv_files, desc="Processing files")
            except ImportError:
                pass

        for csv_file in file_iterator:
            try:
                added = self.ingest_file(
                    str(csv_file),
                    show_progress=False,  # Avoid nested progress bars
                )
                results["files_processed"] += 1
                results["total_documents"] += added
                results["by_file"][csv_file.name] = added
            except Exception as e:
                logger.error(f"Failed to process {csv_file}: {e}")
                results["files_failed"] += 1
                results["by_file"][csv_file.name] = f"Error: {e}"

        logger.info(
            f"Ingestion complete: {results['files_processed']} files, "
            f"{results['total_documents']} documents"
        )
        return results

    def _read_csv_batches(
        self,
        file_path: Path,
    ) -> Generator[List[dict], None, None]:
        """Read CSV file in batches."""
        try:
            # Read CSV with proper handling
            for chunk in pd.read_csv(
                file_path,
                chunksize=self.batch_size,
                dtype=str,  # Read all as string to avoid type issues
                on_bad_lines="skip",
            ):
                # Convert to list of dicts
                yield chunk.to_dict("records")
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return


def ingest_from_csv(
    csv_path: str,
    persist_dir: str = "./data/vector_db",
    model_path: Optional[str] = None,
    use_4bit: bool = True,
    batch_size: int = 500,
) -> int:
    """
    Convenience function to ingest a single CSV file.

    Args:
        csv_path: Path to CSV file
        persist_dir: Vector DB persist directory
        model_path: Embedding model path
        use_4bit: Whether to use 4-bit quantization
        batch_size: Batch size for processing

    Returns:
        Number of documents ingested
    """
    store = FinancialNewsStore(
        persist_dir=persist_dir,
        model_path=model_path,
        use_4bit=use_4bit,
    )
    ingester = NewsIngester(store, batch_size=batch_size)
    return ingester.ingest_file(csv_path)


def ingest_from_directory(
    directory: str,
    persist_dir: str = "./data/vector_db",
    model_path: Optional[str] = None,
    use_4bit: bool = True,
    batch_size: int = 500,
) -> dict:
    """
    Convenience function to ingest all CSV files from a directory.

    Args:
        directory: Directory containing CSV files
        persist_dir: Vector DB persist directory
        model_path: Embedding model path
        use_4bit: Whether to use 4-bit quantization
        batch_size: Batch size for processing

    Returns:
        Ingestion statistics dict
    """
    store = FinancialNewsStore(
        persist_dir=persist_dir,
        model_path=model_path,
        use_4bit=use_4bit,
    )
    ingester = NewsIngester(store, batch_size=batch_size)
    return ingester.ingest_directory(directory)
