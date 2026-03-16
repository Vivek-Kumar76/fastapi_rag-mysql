# FastAPI RAG System (MySQL + FAISS)

A **Retrieval Augmented Generation (RAG) API** built using **FastAPI, FAISS, Sentence Transformers, and MySQL**.
The system retrieves the most relevant question–answer pairs using **semantic vector search** instead of traditional keyword search.

This project demonstrates how to build a **low-latency AI retrieval system** where embeddings are stored in a vector database and queried through a REST API.

# Architecture

User Query
↓
Sentence Transformer → Convert query to vector
↓
FAISS Vector Search
↓
Retrieve Top-K Similar IDs
↓
Fetch corresponding Q/A data
↓
Return results via FastAPI API

# Features

• Semantic search using Sentence Transformers
• Fast vector similarity search using FAISS
• REST API using FastAPI
• MySQL for structured data storage
• Low latency retrieval
• Easily extendable to full RAG with LLMs


# Project Structure

fastapi_rag-mysql/
│
├── main.py            # FastAPI server and query endpoint
├── rag.py             # Builds FAISS vector index
├── db.py              # Database connection
├── model.py           # SQLAlchemy models
│
├── requirements.txt   # Python dependencies
├── vector.index       # FAISS vector index (generated)
├── text_store.pkl     # Stored text mapping (generated)
│
└── README.md


# Installation

Clone the repository:

git clone https://github.com/Vivek-Kumar76/fastapi_rag-mysql.git
Move into the project directory:
cd fastapi_rag-mysql

# Create Virtual Environment
Windows:

python -m venv venv
venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt

# Build Vector Index
Run the RAG indexing script:
python rag.py

This will create:
vector.index
text_store.pkl

These files store the vector embeddings and retrieved text.

# Run the API Server

Start FastAPI:

```
uvicorn main:app --reload
```

Server will start at:

```
http://127.0.0.1:8000
```

---

# API Endpoints

## Home

```
GET /
```

Response:

```
{
 "message": "RAG API is running"
}
```

---

## Ask Question

```
GET /ask?query=your question
```

Example:

```
http://127.0.0.1:8000/ask?query=What is machine learning?
```

Example Response:

```
{
 "query": "What is machine learning?",
 "results": [
   {
     "question": "...",
     "answer": "...",
     "score": 0.78
   }
 ]
}
```

---

# Technologies Used

• FastAPI
• FAISS (Facebook AI Similarity Search)
• Sentence Transformers
• SQLAlchemy
• MySQL
• NumPy

---

# Future Improvements

• Add LLM for answer generation
• Add reranking using Cross-Encoder
• Implement hybrid search (BM25 + vector search)
• Add caching with Redis
• Deploy with Docker


# Author

Vivek Kumar

AI / ML Developer interested in building scalable **RAG systems, AI agents, and intelligent search systems**.


