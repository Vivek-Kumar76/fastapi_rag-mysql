from fastapi import FastAPI, requests
from fastapi import Request
from fastapi.responses import FileResponse
import hashlib
import faiss
import numpy as np
import pickle
import os
import requests
from jose import jwt
from datetime import datetime, timedelta
from sqlalchemy import text

from sentence_transformers import SentenceTransformer
from rag import build_index
from db import SessionLocal

from google import genai
from google.genai import types

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

API_KEY = "your_openweathermap_api_key_here"

client = genai.Client(api_key="your_google_genai_api_key_here")

SECRET_KEY ="fastapi_rag-mysql"
ALGORITHM ="HS256"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
    
        if not result:
            return {"message":"Invalid email or password"}
        
        expire= datetime.utcnow()+timedelta(hours=2)
        token= jwt.encode({"sub":email,"exp":expire},
                          SECRET_KEY,
                          algorithm=ALGORITHM)


        db.execute(
                text("INSERT INTO SESSION (user_id, session_id) VALUES (:user_id, :session_id)"),
                {"user_id": result._mapping["id"], "session_id": token}
            )
        db.commit()
        return {"message": "Login successful!", "token":token}
    
    except Exception as e:
        return {"message": "An error occurred during login. Please try again.",
                "error":str(e)}
    
        
    finally:
        db.close()

def gemini_response(query:str):
    system= "Answer the query in short and precisely with refrennce of source of data. Do not answer, irrelevant question. In case of irrelevant question, just tell the user to ask question in context of digilocker and govt doc only. "
    response= client.models.generate_content(
        model="gemini-3-flash-preview",
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0,
        ),
        contents=query
    )
    answer = "No answer from Gemini"
    if hasattr(response, "text") and response.text:
        answer = response.text
    elif hasattr(response, "candidates") and response.candidates:
        parts = response.candidates[0].content.parts
        if parts and hasattr(parts[0], "text"):
            answer = parts[0].text
    return {"answer":answer}


def router(query:str):
    router_prompt= """ You are arouting assistant.
    decide which function to call based on the query:
      -if the query is about the weather,temperature or location, return "weather"
      -if the query is about digilocker, govt doc retuen "gemini"
      -if irrelevant retuen please relavant question only.
    only output one word: weather, gemini or reject.

"""
    response= client.models.generate_content(
        model="gemini-3-flash-preview",
        config=types.GenerateContentConfig(
            system_instruction=router_prompt,
            temperature=0,
        ),
        contents=query
    )
    return response.text.strip().lower()

def extract_city(query:str):
    prompt="Extract the city name from the query. If the city name is not found in the query, return 'Location not found'."
    response= client.models.generate_content(
        model= "gemini-3-flash-preview",
        config = types.GenerateContentConfig(
            system_instruction=prompt,
            temperature=0,
        ),
        contents=query
    )
    return response.text.strip()

def getweather(city:str):
    url= f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response= requests.get(url)

    if response.status_code!=200:
        return {"error":f"Failed to fetch weather data for {city}"}
    data=response.json()

    prompt= f"take this {data} of weather data and give me weather information in a paragraph describing the current weather conditions in {city} including temperature and weather description."
    system_prompt= "You are a helpful weather broadcaster assistant for providing weather information based on the given data. Answer the query in short and precise manner."
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0,
        ),
        contents=prompt
    )
    return {"answer":response.text.strip()}

def weather(city:str):
    return getweather(city)


@app.get("/ask")
def ask_question(request:Request, query: str):
    session_id = request.headers.get("token")
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
    limit = 0.80

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
                #"question": data["question"],
                "answer": data["answer"],
               # "score": score
            })
    if (len(results)==0):
        decision = router(query)
        if decision == "weather":
            city= extract_city(query)
            if city.lower() == "location not found":
                return {"message":"Could not extract location from the query. Please specify the city name."}
            else:
                results.append(getweather(city))
        elif decision == "gemini":
            results.append(gemini_response(query))
    return {
        "query": query,
        "results": results
    }

@app.get("/logout")
def logout(request:Request):
    session_id = request.headers.get("token")
    db= SessionLocal()


    db.execute(
        text("update session set is_active = 0 where session_id = :sid"),
        {"sid" :  session_id}
    )

    db.commit()
    return {"message":"Logout Successfully"}


#def weather(city:str):
#    return getweather(city)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)