from fastapi import FastAPI
import faiss
import numpy as np
import pickle
import os
from sqlalchemy import text

from sentence_transformers import SentenceTransformer
from rag import build_index
from db import SessionLocal

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_index = None
encoder = None
text_store = None


@app.on_event("startup")
def load_system():
    global vector_index, encoder, text_store
    print("Starting RAG API...")
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        print("Database connection failed:", e)
    if not os.path.exists("vector.index") and not os.path.exists("text_store.pkl"):
        print("Vector files not found. Creating them...")
        build_index()

    else:
        print("Vector files found.")
    vector_index = faiss.read_index("vector.index")
    with open("text_store.pkl", "rb") as f:
        text_store = pickle.load(f)

    encoder = SentenceTransformer("all-MiniLM-L6-v2")




@app.get("/")
def home():
    return {"message": "RAG API is running"}


@app.get("/ask")
def ask_question(query: str):

    query_embedding = encoder.encode([query])
    query_embedding = np.array(query_embedding).astype("float32")
    # cosine similarity
    faiss.normalize_L2(query_embedding)

    k = 1
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)