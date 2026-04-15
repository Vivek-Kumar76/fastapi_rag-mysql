import streamlit as st
import requests

user_input = st.text_input("Ask:")

if st.button("Submit"):
    r = requests.get("http://localhost:8000/ask", params={"query": user_input})
    data=r.json()
    if data.get("results"):
        st.write(data["results"][0])   
    else:
        st.write("No results found.") 