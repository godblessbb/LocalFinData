"""
Embedding model wrapper with support for local models and 4-bit quantization.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Union

import numpy as np

logger = logging.getLogger(__name__)


class BaseEmbedder(ABC):
    """Abstract base class for embedding models."""

    @abstractmethod
    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Encode text(s) into embeddings."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        pass


class QwenEmbedder(BaseEmbedder):
    """
    Qwen3-Embedding model with optional 4-bit quantization.

    Usage:
        # With 4-bit quantization (recommended for large models)
        embedder = QwenEmbedder(
            model_path="D:/models/Qwen3-Embedding-4B",
            use_4bit=True
        )

        # Without quantization
        embedder = QwenEmbedder(model_path="path/to/model", use_4bit=False)

        # Encode texts
        embeddings = embedder.encode(["Hello world", "Financial news-futu-stock"])
    """

    def __init__(
        self,
        model_path: str,
        use_4bit: bool = True,
        device: str = "auto",
        max_length: int = 8192,
        batch_size: int = 32,
    ):
        """
        Initialize the Qwen embedding model.

        Args:
            model_path: Path to the local model or HuggingFace model ID
            use_4bit: Whether to use 4-bit quantization (reduces VRAM ~4x)
            device: Device to use ('auto', 'cuda', 'cpu')
            max_length: Maximum sequence length
            batch_size: Batch size for encoding
        """
        self.model_path = model_path
        self.use_4bit = use_4bit
        self.device = device
        self.max_length = max_length
        self.batch_size = batch_size
        self._model = None
        self._tokenizer = None
        self._dimension = None

    def _load_model(self):
        """Lazy load the model on first use."""
        if self._model is not None:
            return

        import torch
        from transformers import AutoModel, AutoTokenizer

        logger.info(f"Loading embedding model from {self.model_path}")
        logger.info(f"4-bit quantization: {self.use_4bit}")

        # Tokenizer
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=True
        )

        # Model with optional quantization
        if self.use_4bit:
            try:
                from transformers import BitsAndBytesConfig

                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                )
                self._model = AutoModel.from_pretrained(
                    self.model_path,
                    quantization_config=quantization_config,
                    device_map=self.device,
                    trust_remote_code=True,
                )
                logger.info("Model loaded with 4-bit quantization")
            except ImportError:
                logger.warning(
                    "bitsandbytes not installed, falling back to fp16. "
                    "Install with: pip install bitsandbytes"
                )
                self._model = AutoModel.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.float16,
                    device_map=self.device,
                    trust_remote_code=True,
                )
        else:
            self._model = AutoModel.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16,
                device_map=self.device,
                trust_remote_code=True,
            )

        self._model.eval()

        # Get embedding dimension from model config
        self._dimension = self._model.config.hidden_size
        logger.info(f"Model loaded. Embedding dimension: {self._dimension}")

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        if self._dimension is None:
            self._load_model()
        return self._dimension

    def encode(
        self,
        texts: Union[str, List[str]],
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Encode text(s) into embeddings.

        Args:
            texts: Single text or list of texts to encode
            show_progress: Whether to show progress bar for batch encoding

        Returns:
            numpy array of shape (n_texts, dimension)
        """
        import torch

        self._load_model()

        # Handle single text
        if isinstance(texts, str):
            texts = [texts]

        all_embeddings = []

        # Process in batches
        iterator = range(0, len(texts), self.batch_size)
        if show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(iterator, desc="Encoding", unit="batch")
            except ImportError:
                pass

        for i in iterator:
            batch_texts = texts[i : i + self.batch_size]

            # Tokenize
            inputs = self._tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            )

            # Move to device
            inputs = {k: v.to(self._model.device) for k, v in inputs.items()}

            # Encode
            with torch.no_grad():
                outputs = self._model(**inputs)
                # Use last hidden state with mean pooling
                embeddings = self._mean_pooling(
                    outputs.last_hidden_state, inputs["attention_mask"]
                )
                # Normalize
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
                all_embeddings.append(embeddings.cpu().numpy())

        return np.vstack(all_embeddings)

    def _mean_pooling(self, last_hidden_state, attention_mask):
        """Apply mean pooling to get sentence embeddings."""
        import torch

        input_mask_expanded = (
            attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
        )
        sum_embeddings = torch.sum(last_hidden_state * input_mask_expanded, dim=1)
        sum_mask = torch.clamp(input_mask_expanded.sum(dim=1), min=1e-9)
        return sum_embeddings / sum_mask


class OpenAIEmbedder(BaseEmbedder):
    """
    OpenAI Embedding API wrapper.

    Fast and cost-effective for large-scale embedding.
    Price: $0.02/1M tokens (text-embedding-3-small)

    Usage:
        embedder = OpenAIEmbedder(api_key="sk-xxx")
        embeddings = embedder.encode(["Hello world", "Financial news-futu-stock"])

    Environment variable:
        Set OPENAI_API_KEY to avoid passing api_key explicitly.
    """

    # Embedding dimensions for each model
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        batch_size: int = 100,  # OpenAI recommends batches of ~100
        max_retries: int = 3,
    ):
        """
        Initialize OpenAI embedder.

        Args:
            model: Model name (text-embedding-3-small recommended)
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            batch_size: Batch size for API calls
            max_retries: Number of retries on API errors
        """
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self._client = None
        self._api_key = api_key

    def _get_client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            import os
            from pathlib import Path

            # Try to load from .env file
            try:
                from dotenv import load_dotenv
                # Look for .env in project root
                env_path = Path(__file__).resolve().parent.parent.parent / ".env"
                if env_path.exists():
                    load_dotenv(env_path)
                    logger.info(f"Loaded environment from {env_path}")
            except ImportError:
                pass  # dotenv not installed, use system env vars

            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "openai package not installed. Install with: pip install openai"
                )

            api_key = self._api_key or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OpenAI API key not provided. Set OPENAI_API_KEY in .env file "
                    "or pass api_key parameter."
                )

            # Support custom base URL (for proxies)
            base_url = os.environ.get("OPENAI_BASE_URL")
            self._client = OpenAI(api_key=api_key, base_url=base_url)
            logger.info(f"OpenAI client initialized. Model: {self.model}")

        return self._client

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self.MODEL_DIMENSIONS.get(self.model, 1536)

    def encode(
        self,
        texts: Union[str, List[str]],
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Encode text(s) into embeddings using OpenAI API.

        Args:
            texts: Single text or list of texts to encode
            show_progress: Whether to show progress bar

        Returns:
            numpy array of shape (n_texts, dimension)
        """
        import time

        client = self._get_client()

        if isinstance(texts, str):
            texts = [texts]

        all_embeddings = []

        # Process in batches
        iterator = range(0, len(texts), self.batch_size)
        if show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(
                    iterator,
                    desc="OpenAI Embedding",
                    total=(len(texts) + self.batch_size - 1) // self.batch_size,
                )
            except ImportError:
                pass

        for i in iterator:
            batch_texts = texts[i : i + self.batch_size]

            # Retry logic
            for attempt in range(self.max_retries):
                try:
                    response = client.embeddings.create(
                        model=self.model,
                        input=batch_texts,
                    )

                    # Extract embeddings in correct order
                    batch_embeddings = [None] * len(batch_texts)
                    for item in response.data:
                        batch_embeddings[item.index] = item.embedding

                    all_embeddings.extend(batch_embeddings)
                    break

                except Exception as e:
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(
                            f"OpenAI API error: {e}. Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        raise

        return np.array(all_embeddings)


class SentenceTransformerEmbedder(BaseEmbedder):
    """
    Fallback embedder using sentence-transformers library.
    Useful for smaller models or when transformers setup is complex.

    Usage:
        embedder = SentenceTransformerEmbedder("BAAI/bge-small-zh-v1.5")
        embeddings = embedder.encode(["Hello world"])
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-zh-v1.5",
        device: str = "cuda",
        batch_size: int = 64,
    ):
        """
        Initialize sentence-transformers model.

        Args:
            model_name: Model name or path
            device: Device to use
            batch_size: Batch size for encoding
        """
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self._model = None
        self._dimension = None

    def _load_model(self):
        """Lazy load the model."""
        if self._model is not None:
            return

        from sentence_transformers import SentenceTransformer

        logger.info(f"Loading SentenceTransformer model: {self.model_name}")
        self._model = SentenceTransformer(self.model_name, device=self.device)
        self._dimension = self._model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self._dimension}")

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        if self._dimension is None:
            self._load_model()
        return self._dimension

    def encode(
        self,
        texts: Union[str, List[str]],
        show_progress: bool = False,
    ) -> np.ndarray:
        """Encode text(s) into embeddings."""
        self._load_model()

        if isinstance(texts, str):
            texts = [texts]

        embeddings = self._model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=True,
        )
        return np.array(embeddings)


def create_embedder(
    model_path: Optional[str] = None,
    use_4bit: bool = True,
    fallback_model: str = "BAAI/bge-small-zh-v1.5",
) -> BaseEmbedder:
    """
    Factory function to create an embedder.

    Args:
        model_path: Path to Qwen model. If None, uses fallback model.
        use_4bit: Whether to use 4-bit quantization for Qwen model.
        fallback_model: Fallback model if Qwen is not available.

    Returns:
        BaseEmbedder instance
    """
    if model_path:
        try:
            return QwenEmbedder(model_path=model_path, use_4bit=use_4bit)
        except Exception as e:
            logger.warning(f"Failed to load Qwen model: {e}")
            logger.warning(f"Falling back to {fallback_model}")

    return SentenceTransformerEmbedder(model_name=fallback_model)
