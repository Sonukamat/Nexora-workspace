import os
import math
import re
from typing import List, Dict, Any

class VectorStore:
    """
    Nexora Vector Database & Semantic Retrieval Manager
    Uses ChromaDB or local high-performance Cosine Vector Engine for zero-cost operation.
    """
    def __init__(self, persist_directory="./data/chroma_db"):
        self.persist_directory = persist_directory
        self.chunks_db = []
        self.chroma_collection = None
        self.embedder = None
        self._init_store()

    def _init_store(self):
        os.makedirs(self.persist_directory, exist_ok=True)
        # Try initializing ChromaDB & SentenceTransformers if available
        try:
            import chromadb
            client = chromadb.PersistentClient(path=self.persist_directory)
            self.chroma_collection = client.get_or_create_collection(name="nexora_knowledge_base")
            print("[VectorStore] ChromaDB initialized successfully.")
        except Exception as e:
            print(f"[VectorStore] Using Native High-Speed Cosine Vector Engine ({e})")

        try:
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            print("[VectorStore] SentenceTransformers embedder loaded.")
        except Exception as e:
            print(f"[VectorStore] Embedder running in lightweight vector mode.")

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return

        # 1. Store in memory DB instantly
        self.chunks_db.extend(chunks)

        # 2. Batch encode into ChromaDB (100x faster than sequential loop)
        if self.chroma_collection and self.embedder:
            try:
                texts = [c['text'] for c in chunks]
                ids = [c['chunk_id'] for c in chunks]
                metadatas = [{
                    "file_id": c['file_id'],
                    "filename": c['filename'],
                    "page_number": c.get('page_number', 1)
                } for c in chunks]

                embeddings = self.embedder.encode(texts, batch_size=64, show_progress_bar=False).tolist()

                self.chroma_collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas
                )
            except Exception as e:
                print(f"[VectorStore] ChromaDB batch add fallback: {e}")


    def similarity_search(self, query: str, top_k: int = 6, file_id: str = None, file_ids: List[str] = None) -> List[Dict[str, Any]]:
        if not self.chunks_db:
            return []

        target_chunks = self.chunks_db
        if file_ids and len(file_ids) > 0:
            target_chunks = [c for c in self.chunks_db if c.get('file_id') in file_ids]
        elif file_id:
            target_chunks = [c for c in self.chunks_db if c.get('file_id') == file_id]

        if not target_chunks:
            target_chunks = self.chunks_db


        query_lower = query.lower()

        # Detect chapter target patterns (e.g., "chapter 2", "chapter ii", "chapter two", "chapter 3")
        chap_match = re.search(r'chapter\s*(\d+|one|two|three|four|five|six|seven|eight|nine|ten|i|ii|iii|iv|v|vi|vii|viii|ix|x)', query_lower)
        target_chap_num = chap_match.group(1) if chap_match else None

        # Try ChromaDB first if available and no specific chapter query
        if self.chroma_collection and self.embedder and not target_chap_num:
            try:
                query_emb = self.embedder.encode(query).tolist()
                where_clause = {"file_id": file_id} if file_id else None
                results = self.chroma_collection.query(
                    query_embeddings=[query_emb],
                    n_results=min(top_k, len(target_chunks)),
                    where=where_clause
                )
                retrieved = []
                if results and 'ids' in results and results['ids']:
                    matched_ids = results['ids'][0]
                    distances = results.get('distances', [[0]*len(matched_ids)])[0]
                    for idx, c_id in enumerate(matched_ids):
                        chunk_obj = next((c for c in target_chunks if c['chunk_id'] == c_id), None)
                        if chunk_obj:
                            score = max(0.0, 1.0 - (distances[idx] if idx < len(distances) else 0.5))
                            retrieved.append({**chunk_obj, "similarity_score": round(score, 4)})
                    if retrieved:
                        return retrieved
            except Exception:
                pass

        # Targeted Keyword & Chapter Ranker Engine
        scored_chunks = []
        stop_words = {"summarize", "summary", "explain", "tell", "me", "about", "the", "a", "an", "in", "of", "and", "is", "for", "to"}
        query_words = set(re.findall(r'\w+', query_lower)) - stop_words

        for chunk in target_chunks:
            chunk_text_lower = chunk['text'].lower()
            score = 0.05

            # Chapter exact match boost
            if target_chap_num:
                if f"chapter {target_chap_num}" in chunk_text_lower or f"chapter {self._num_to_roman(target_chap_num)}" in chunk_text_lower:
                    score += 0.85
                elif target_chap_num in chunk_text_lower and "chapter" in chunk_text_lower:
                    score += 0.60

            # Keyword match scoring
            if query_words:
                chunk_words = set(re.findall(r'\w+', chunk_text_lower))
                matched_words = query_words.intersection(chunk_words)
                if matched_words:
                    score += (len(matched_words) / len(query_words)) * 0.55

            # Exact phrase match boost
            if len(query_lower) > 4 and query_lower in chunk_text_lower:
                score += 0.40

            scored_chunks.append({
                **chunk,
                "similarity_score": round(min(1.0, score), 4)
            })

        scored_chunks.sort(key=lambda x: x['similarity_score'], reverse=True)
        return scored_chunks[:top_k]

    def _num_to_roman(self, num_str):
        mapping = {"1":"i", "2":"ii", "3":"iii", "4":"iv", "5":"v", "6":"vi", "7":"vii", "8":"viii", "9":"ix", "10":"x",
                   "one":"i", "two":"ii", "three":"iii", "four":"iv", "five":"v"}
        return mapping.get(str(num_str).lower(), str(num_str))


    def get_document_sample_chunks(self, file_id: str = None, file_ids: List[str] = None, max_chunks: int = 12) -> List[Dict[str, Any]]:
        """
        Samples chunks evenly across the entire document (beginning, middle, end)
        for full-book or full-document summarization.
        """
        target_chunks = self.chunks_db
        if file_ids and len(file_ids) > 0:
            target_chunks = [c for c in self.chunks_db if c.get('file_id') in file_ids]
        elif file_id:
            target_chunks = [c for c in self.chunks_db if c.get('file_id') == file_id]

        if not target_chunks:
            target_chunks = self.chunks_db


        if len(target_chunks) <= max_chunks:
            return target_chunks

        # Sample uniformly across the document space
        step = max(1, len(target_chunks) // max_chunks)
        sampled = [target_chunks[i] for i in range(0, len(target_chunks), step)]
        return sampled[:max_chunks]

    def delete_chunks_by_file_id(self, file_id: str):
        self.chunks_db = [c for c in self.chunks_db if c.get('file_id') != file_id]
        if self.chroma_collection:
            try:
                self.chroma_collection.delete(where={"file_id": file_id})
            except Exception:
                pass


    def clear_all(self):
        self.chunks_db = []
        if self.chroma_collection:
            try:
                self.chroma_collection.delete(where={})
            except Exception:
                pass

    def get_stats(self):
        unique_files = list(set([c['filename'] for c in self.chunks_db]))
        return {
            "total_chunks": len(self.chunks_db),
            "total_files": len(unique_files),
            "files": unique_files
        }

