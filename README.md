RAG based QA system with Database:
Retrieval Augmented Generation (RAG) API built using FastAPI, FAISS, Sentence Transformers, and MySQL. The system retrieves the most relevant question–answer pairs using semantic vector search instead of traditional keyword search.This project demonstrates how to build a low-latency AI retrieval system where embeddings are stored in a vector database.

## To clone the project :

  1. ## create virtual environment
   .RUN: python -m venv task
   .RUN: task\Scripts\activate

  2. ## for installation of dependencies
    .Run: pip install -r requirement.txt


  3. ##  setup database :
    db.py

  4. ## Run server:
      .Run:  uvicorn main:app --reload
  
  5. ## Query 
    You can directly check it by "http://127.0.0.1:8000/docs". Here you will see you two end points. Go to ask question and click on try it out. Paste your question and now you will get your answer.
