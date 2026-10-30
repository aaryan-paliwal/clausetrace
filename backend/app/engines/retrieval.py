"""Hybrid BM25 + dense hashing retrieval engine with 1-hop deontic graph expansion."""
import hashlib
import json
import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional
import numpy as np

from app.db.database import get_db_context
from app.db.repository import Repository

EMBEDDING_DIM = 256

# High-salience domain terms with extra weight in the hashing vector
DOMAIN_WEIGHTS = {
    "terminate": 2.5,
    "termination": 2.5,
    "cause": 2.0,
    "notice": 2.2,
    "cure": 2.2,
    "days": 1.5,
    "inventions": 2.5,
    "patent": 2.2,
    "copyright": 2.0,
    "software": 2.0,
    "ownership": 2.5,
    "confidential": 2.2,
    "confidentiality": 2.2,
    "survival": 2.0,
    "notwithstanding": 3.0,
    "supersedes": 3.0,
    "override": 3.0,
    "must": 2.0,
    "shall": 2.0,
    "must not": 2.5,
    "prohibited": 2.5,
    "may": 1.5,
    "attendance": 2.2,
    "grade": 2.0,
    "refund": 2.2,
    "financial": 2.0,
    "delaware": 2.0,
    "california": 2.0,
}


def _tokenize(text: str) -> List[str]:
    """Tokenize and normalize text."""
    return re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text.lower())


def compute_embedding(text: str) -> List[float]:
    """
    Deterministic 256-dimensional semantic + lexical embedding vector.
    Zero external dependencies, fast, reproducible, and normalized.
    """
    tokens = _tokenize(text)
    if not tokens:
        return [0.0] * EMBEDDING_DIM

    vec = np.zeros(EMBEDDING_DIM, dtype=np.float32)

    # 1. Unigram feature hashing with domain weights
    for token in tokens:
        weight = DOMAIN_WEIGHTS.get(token, 1.0)
        h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        idx = h % EMBEDDING_DIM
        sign = 1.0 if (h // EMBEDDING_DIM) % 2 == 0 else -1.0
        vec[idx] += sign * weight

    # 2. Bigram feature hashing
    for i in range(len(tokens) - 1):
        bigram = f"{tokens[i]}_{tokens[i + 1]}"
        weight = 1.5 if bigram in DOMAIN_WEIGHTS else 1.0
        h = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16)
        idx = h % EMBEDDING_DIM
        sign = 1.0 if (h // EMBEDDING_DIM) % 2 == 0 else -1.0
        vec[idx] += sign * weight

    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


class BM25Index:
    """In-memory BM25 index over documents/clauses."""

    def __init__(self, corpus: List[Dict[str, Any]]):
        self.corpus = corpus
        self.k1 = 1.5
        self.b = 0.75
        self.doc_lens = [len(_tokenize(item["text"])) for item in corpus]
        self.avg_dl = sum(self.doc_lens) / max(len(self.doc_lens), 1)
        self.doc_freqs: Counter = Counter()
        self.tokenized_corpus = [_tokenize(item["text"]) for item in corpus]

        for doc_tokens in self.tokenized_corpus:
            unique_tokens = set(doc_tokens)
            for token in unique_tokens:
                self.doc_freqs[token] += 1

    def score(self, query: str) -> List[float]:
        q_tokens = _tokenize(query)
        scores = []
        n_docs = len(self.corpus)

        for i, doc_tokens in enumerate(self.tokenized_corpus):
            doc_len = self.doc_lens[i]
            tf_counter = Counter(doc_tokens)
            score = 0.0

            for q in q_tokens:
                tf = tf_counter.get(q, 0)
                df = self.doc_freqs.get(q, 0)
                if df == 0:
                    continue
                # IDF calculation with smoothing
                idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1.0)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / max(self.avg_dl, 1)))
                score += idf * (numerator / max(denominator, 1e-6))
            scores.append(score)
        return scores


class HybridGraphRetriever:
    """Hybrid BM25 + dense retriever with 1-hop deontic graph expansion."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def retrieve(
        self,
        workspace_id: str,
        query: str,
        top_k: int = 5,
        enable_graph_expansion: bool = True,
    ) -> List[Dict[str, Any]]:
        with get_db_context(self.db_path) as conn:
            repo = Repository(conn)
            clauses = repo.list_clauses(workspace_id=workspace_id)
            if not clauses:
                return []

            # 1. Compute BM25 scores
            bm25 = BM25Index(clauses)
            bm25_scores = bm25.score(query)
            max_bm25 = max(bm25_scores) if bm25_scores and max(bm25_scores) > 0 else 1.0
            norm_bm25 = [s / max_bm25 for s in bm25_scores]

            # 2. Compute Dense Cosine Scores
            q_emb = compute_embedding(query)
            dense_scores = []
            for clause in clauses:
                emb = None
                if clause.get("embedding_json"):
                    try:
                        emb = json.loads(clause["embedding_json"])
                    except Exception:
                        pass
                if not emb:
                    emb = compute_embedding(clause["text"])
                sim = _cosine_similarity(q_emb, emb)
                dense_scores.append(sim)

            # 3. Combine with hybrid weights (0.5 BM25 + 0.5 Dense)
            scored_clauses = []
            for i, clause in enumerate(clauses):
                hybrid_score = 0.5 * norm_bm25[i] + 0.5 * dense_scores[i]
                c_copy = dict(clause)
                c_copy["score"] = round(hybrid_score, 4)
                scored_clauses.append(c_copy)

            # Sort by hybrid score
            scored_clauses.sort(key=lambda x: x["score"], reverse=True)
            top_results = scored_clauses[:top_k]

            if not enable_graph_expansion:
                return top_results

            # 4. 1-Hop Deontic Graph Expansion
            expanded_clause_ids = set(c["id"] for c in top_results)
            top_categories = set()

            # Find categories and conflicts connected to top clauses
            rules = repo.list_deontic_rules(workspace_id=workspace_id)
            clause_to_rules: Dict[str, List[Dict[str, Any]]] = {}
            for r in rules:
                clause_to_rules.setdefault(r["clause_id"], []).append(r)
                if r["clause_id"] in expanded_clause_ids:
                    top_categories.add(r["action_category"])

            conflicts = repo.list_conflicts(workspace_id=workspace_id)
            additional_clauses = []

            # (A) Expand clauses connected by active conflicts
            for conf in conflicts:
                a_id = conf["clause_a_id"]
                b_id = conf["clause_b_id"]
                if a_id in expanded_clause_ids and b_id not in expanded_clause_ids:
                    cl_b = repo.get_clause(b_id)
                    if cl_b:
                        c_dict = dict(cl_b)
                        c_dict["score"] = 0.999
                        c_dict["expansion_reason"] = f"Conflict-linked to {a_id} ({conf['conflict_type']})"
                        additional_clauses.append(c_dict)
                        expanded_clause_ids.add(b_id)
                elif b_id in expanded_clause_ids and a_id not in expanded_clause_ids:
                    cl_a = repo.get_clause(a_id)
                    if cl_a:
                        c_dict = dict(cl_a)
                        c_dict["score"] = 0.999
                        c_dict["expansion_reason"] = f"Conflict-linked to {b_id} ({conf['conflict_type']})"
                        additional_clauses.append(c_dict)
                        expanded_clause_ids.add(a_id)

            # (B) Expand any clause marked with is_override=True in the same category
            for r in rules:
                if r["is_override"] and r["action_category"] in top_categories:
                    if r["clause_id"] not in expanded_clause_ids:
                        cl_override = repo.get_clause(r["clause_id"])
                        if cl_override:
                            c_dict = dict(cl_override)
                            c_dict["score"] = 0.995
                            c_dict["expansion_reason"] = f"Supremacy override rule in {r['action_category']}"
                            additional_clauses.append(c_dict)
                            expanded_clause_ids.add(r["clause_id"])

            return top_results + additional_clauses
