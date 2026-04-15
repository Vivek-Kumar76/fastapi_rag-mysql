from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import FileResponse
import hashlib
import faiss
import numpy as np
import pickle
import os
import secrets
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
    return FileResponse("static_page/login.html")

@app.get("/registeration.html")
def register_page():
    return FileResponse("static_page/registeration.html")


@app.get("/index.html")
def main():
    return FileResponse("static_page/index.html")




@app.post("/register")
async def register_user(request: Request):
    db = SessionLocal()
    try:
        data= await request.json()
        name= data.get("name")
        username = data.get("username")
        email = data.get("email")
        password1 = data.get("password")
        password = hashlib.sha256(password1.encode()).hexdigest()

        db.execute(text("INSERT INTO users (name, username, email, password) VALUES (:name, :username, :email, :password)"),
                {"name":name, "username": username, "email": email, "password": password})
    
        db.commit()

        return {"message": "User registered successfully!"}
    except Exception as e:
        db.rollback()
        print("Error during registration:", e)
        return {"message": "An error occurred during registration. Please try again."}
    
        
    finally:
        db.close()


@app.post("/login")
async def login_user(request: Request):
    db = SessionLocal()
    try:
        data= await request.json()
        email = data.get("email")
        password1 = data.get("password")
        password = hashlib.sha256(password1.encode()).hexdigest()

        result = db.execute(text("SELECT * FROM users WHERE email = :email AND password = :password"),
                {"email": email, "password": password}).fetchone()
    
        if result:
            session_id = secrets.token_hex(5)
            db.execute(
                text("INSERT INTO SESSION (user_id, session_id) VALUES (:user_id, :session_id)"),
                {"user_id": result.id, "session_id": session_id}
            )
            db.commit()
            return {"message": "Login successful!", "session_id":session_id}
        
        else:
            return {"message": "Invalid email or password."}
    except Exception as e:
        print("Error during login:", e)
        return {"message": "An error occurred during login. Please try again."}
    
        
    finally:
        db.close()

@app.get("/ask")
def ask_question(request:Request, query: str):
    session_id = request.headers.get("session_id")
    if not session_id:
        return {"message":"Unauthorized"}
    
    db = SessionLocal()
    session = db.execute(
        text("select * from session where session_id = :sid"),
        {"sid":session_id}
    ).fetchone()

    if not session:
        return{"message":"invalid session"}

    query_embedding = encoder.encode([query])
    query_embedding = np.array(query_embedding).astype("float32")
    # cosine similarity
    faiss.normalize_L2(query_embedding)

    k = 3
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
               # "score": score
            })

    return {
        "query": query,
        "results": results
    }

@app.get("/logout")
def logout(request:Request):
    session_id = request.headers.get("session_id")
    db= SessionLocal()


    db.execute(
        text("update session set is_active = 0 where session_id = :sid"),
        {"sid" :  session_id}
    )

    db.commit()
    return {"message":"Logout Successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)