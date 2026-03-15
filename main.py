from fastapi import FastAPI
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

app = FastAPI()

vector_index = None
encoder = None
text_store = None


@app.on_event("startup")
def load_vector_db():
    global vector_index, encoder, text_store

    # load FAISS index
    vector_index = faiss.read_index("vector.index")

    # load embedding model
    encoder = SentenceTransformer("all-MiniLM-L6-v2")
    
    # load text store
    with open("text_store.pkl", "rb") as f:
        text_store = pickle.load(f)


@app.get("/")
def home():
    return {"message": "RAG API is running"}


@app.get("/ask")
def ask_question(query: str):

    query_embedding = encoder.encode([query])
    query_embedding = np.array(query_embedding).astype("float32")
    # cosine similarity
    faiss.normalize_L2(query_embedding)

    k = 5
    limit = 0.40

    D, I = vector_index.search(query_embedding, k)

    results = []

    for i, id_ in enumerate(I[0]):
        score = float(D[0][i])
        if id_ == -1:
            continue
        if score < limit:
            continue
        data = text_store.get(id_)
        if data:
            results.append({
                "question": data["question"],
                "answer": data["answer"],
                "score": score
            })

    return {
        "query": query,
        "results": results
    }