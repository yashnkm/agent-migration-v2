"""
VectorStore Manager - Handles FAISS vectorstore creation and persistence
Uses Google Gemini Embedding (gemini-embedding-001) for embeddings
Falls back to local HuggingFace embeddings if Gemini fails/quota exceeded
"""
import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


class VectorStoreManager:
    """Manages FAISS vectorstore with Gemini embeddings (with local fallback)"""

    def __init__(self, output_dimensionality: int = 768, use_local: bool = False):
        """
        Initialize vectorstore manager

        Args:
            output_dimensionality: Embedding dimensions (768, 1536, or 3072)
                                  768 recommended for balance of quality/storage
            use_local: Force use of local embeddings (default: False, try Gemini first)
        """
        load_dotenv()

        self.use_local = use_local
        self.embedding_type = None

        # Try Gemini first, fallback to local if needed
        if not use_local:
            # Get API key
            self.api_key = (
                os.getenv('CODEBASE_GEMINI_KEY') or
                os.getenv('GOOGLE_GENAI_API_KEY') or
                os.getenv('GOOGLE_API_KEY')
            )

            if self.api_key:
                try:
                    print(f"Initializing Gemini embeddings (models/gemini-embedding-001, {output_dimensionality}d)...")
                    self.embeddings = GoogleGenerativeAIEmbeddings(
                        model="models/gemini-embedding-001",
                        google_api_key=self.api_key,
                        task_type="retrieval_document",
                        output_dimensionality=output_dimensionality
                    )
                    self.embedding_type = "gemini"
                    print("✓ Gemini embeddings initialized successfully")
                except Exception as e:
                    print(f"⚠ Gemini initialization failed: {e}")
                    print("→ Falling back to local embeddings...")
                    self._init_local_embeddings()
            else:
                print("⚠ No Gemini API key found")
                print("→ Using local embeddings...")
                self._init_local_embeddings()
        else:
            print("Using local embeddings (forced)...")
            self._init_local_embeddings()

        self.vectorstore: Optional[FAISS] = None
        self.index_path = Path("rag_index")
        self.index_path.mkdir(exist_ok=True)

    def _init_local_embeddings(self):
        """Initialize local HuggingFace embeddings as fallback"""
        print("Initializing local embeddings (all-MiniLM-L6-v2, 384d)...")
        print("This will download model on first use (~80MB)")

        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",  # Fast, good quality, 384 dimensions
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        self.embedding_type = "local"
        print("✓ Local embeddings initialized successfully")

    def create_vectorstore(self, documents: List[Document], repo_name: str = "default") -> FAISS:
        """
        Create FAISS vectorstore from documents

        Args:
            documents: List of LangChain Document objects
            repo_name: Repository name for saving index

        Returns:
            FAISS vectorstore
        """
        if not documents:
            raise ValueError("No documents provided")

        print(f"Creating vectorstore from {len(documents)} documents...")
        print(f"Using {self.embedding_type} embeddings...")
        print(f"This may take a moment (embedding generation)...")

        try:
            # Create FAISS vectorstore
            self.vectorstore = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )

            print(f"✓ Vectorstore created successfully with {self.embedding_type} embeddings!")

        except Exception as e:
            # If Gemini fails (quota exceeded), fallback to local
            if self.embedding_type == "gemini":
                print(f"⚠ Gemini embedding failed: {e}")
                print("→ Quota may be exceeded. Switching to local embeddings...")

                self._init_local_embeddings()

                # Retry with local embeddings
                print(f"Retrying with local embeddings...")
                self.vectorstore = FAISS.from_documents(
                    documents=documents,
                    embedding=self.embeddings
                )
                print(f"✓ Vectorstore created successfully with local embeddings!")
            else:
                raise

        # Save to disk
        self.save_vectorstore(repo_name)

        return self.vectorstore

    def save_vectorstore(self, repo_name: str = "default"):
        """Save vectorstore to disk"""
        if not self.vectorstore:
            raise ValueError("No vectorstore to save")

        save_path = self.index_path / repo_name
        save_path.mkdir(exist_ok=True)

        print(f"Saving vectorstore to {save_path}...")
        self.vectorstore.save_local(str(save_path))
        print(f"Vectorstore saved!")

    def load_vectorstore(self, repo_name: str = "default") -> Optional[FAISS]:
        """
        Load vectorstore from disk

        Args:
            repo_name: Repository name

        Returns:
            FAISS vectorstore or None if not found
        """
        load_path = self.index_path / repo_name

        if not load_path.exists():
            print(f"No saved vectorstore found at {load_path}")
            return None

        print(f"Loading vectorstore from {load_path}...")
        try:
            self.vectorstore = FAISS.load_local(
                str(load_path),
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True  # Required for loading FAISS
            )
            print(f"Vectorstore loaded successfully!")
            return self.vectorstore
        except Exception as e:
            print(f"Error loading vectorstore: {e}")
            return None

    def get_retriever(self, search_kwargs: Optional[dict] = None):
        """
        Get retriever from vectorstore

        Args:
            search_kwargs: Search parameters (e.g., {"k": 5} for top 5 results)

        Returns:
            LangChain retriever
        """
        if not self.vectorstore:
            raise ValueError("No vectorstore available. Create or load one first.")

        if search_kwargs is None:
            search_kwargs = {"k": 5}  # Default: return top 5 results

        return self.vectorstore.as_retriever(search_kwargs=search_kwargs)

    def search(self, query: str, k: int = 5) -> List[Document]:
        """
        Search vectorstore directly

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of most relevant documents
        """
        if not self.vectorstore:
            raise ValueError("No vectorstore available. Create or load one first.")

        results = self.vectorstore.similarity_search(query, k=k)
        return results

    def search_with_scores(self, query: str, k: int = 5) -> List[tuple]:
        """
        Search with similarity scores

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of (document, score) tuples
        """
        if not self.vectorstore:
            raise ValueError("No vectorstore available. Create or load one first.")

        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return results


# Convenience functions

def create_rag_index(documents: List[Document], repo_name: str = "default", dimensionality: int = 768) -> FAISS:
    """
    Convenience function to create RAG index

    Args:
        documents: List of documents
        repo_name: Repository name for saving
        dimensionality: Embedding dimensions (768, 1536, or 3072)

    Returns:
        FAISS vectorstore
    """
    manager = VectorStoreManager(output_dimensionality=dimensionality)
    return manager.create_vectorstore(documents, repo_name)


def load_rag_index(repo_name: str = "default", dimensionality: int = 768) -> Optional[FAISS]:
    """
    Convenience function to load RAG index

    Args:
        repo_name: Repository name
        dimensionality: Embedding dimensions used during creation

    Returns:
        FAISS vectorstore or None
    """
    manager = VectorStoreManager(output_dimensionality=dimensionality)
    return manager.load_vectorstore(repo_name)
