"""Local semantic search over policy clauses already eligible for a project."""

import hashlib
import json
from threading import Lock

from . import storage

MAX_DISTANCE = 0.40
MODEL = "all-MiniLM-L6-v2"
_index_lock = Lock()


class SearchUnavailable(RuntimeError):
    """A local model or index failed before the review could be saved."""


def search(policies, requirements):
    """Return candidate cosine distances keyed by (policy ID, requirement ID)."""
    if not policies or not requirements:
        return {}
    try:
        return _search(policies, requirements)
    except Exception as exc:
        raise SearchUnavailable(
            "Policy vector search is unavailable. Check the local index directory and "
            "run python -m backend.retrieval in the project environment to prepare the model, then retry."
        ) from exc


def _search(policies, requirements):
    import chromadb
    from chromadb.config import Settings

    # Immutable collections prevent concurrent reviews or changed clauses from mixing evidence.
    documents = sorted((p["id"], p["text"]) for p in policies)
    fingerprint = hashlib.sha256(json.dumps([MODEL, documents]).encode()).hexdigest()
    with _index_lock:
        client = chromadb.PersistentClient(
            path=str(storage.database_path().parent / "policy_vectors"),
            settings=Settings(anonymized_telemetry=False),
        )
        collection = client.get_or_create_collection(
            name="policy-" + fingerprint[:32], configuration={"hnsw": {"space": "cosine"}}
        )
        if collection.count() != len(documents):
            collection.upsert(ids=[d[0] for d in documents], documents=[d[1] for d in documents])

    distances = {}
    for offset in range(0, len(requirements), 32):
        batch = requirements[offset : offset + 32]
        result = collection.query(
            query_texts=[r["statement"] for r in batch],
            n_results=min(2, len(documents)),
            include=["distances"],
        )
        for requirement, ids, scores in zip(batch, result["ids"], result["distances"], strict=True):
            for policy_id, distance in zip(ids, scores, strict=True):
                if distance <= MAX_DISTANCE:
                    distances[policy_id, requirement["id"]] = round(max(0.0, distance), 4)
    return distances


if __name__ == "__main__":
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

    vector = DefaultEmbeddingFunction()(["Loan application policy"])[0]
    print(f"{MODEL} ready locally ({len(vector)} dimensions).")
