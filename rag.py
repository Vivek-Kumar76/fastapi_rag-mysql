import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from db import SessionLocal
from model import QAData

db = SessionLocal()
rows = db.query(QAData.id, QAData.question, QAData.answer).all()
ids = []
texts = []
text_store = {}


for row in rows:
    ids.append(row.id)
    text = row.question + " " + row.answer
    texts.append(text)
    text_store[row.id] = {
        "question": row.question,
        "answer": row.answer
    }

encoder = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = encoder.encode(texts)
embeddings = np.array(embeddings).astype("float32")
faiss.normalize_L2(embeddings)
dimension = embeddings.shape[1]
index = faiss.IndexIDMap(faiss.IndexFlatIP(dimension))

index.add_with_ids(embeddings, np.array(ids))
faiss.write_index(index, "vector.index")    # save FAISS index
with open("text_store.pkl", "wb") as f:     # save text store
    pickle.dump(text_store, f)

print("Vector index and text store saved successfully")