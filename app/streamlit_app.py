import streamlit as st

st.set_page_config(page_title="Shivank | AI/ML Portfolio Starter", layout="wide")
st.title("👋 Welcome to Shivank's AI/ML Portfolio Starter")
with st.sidebar:
    st.header("Controls")
    name = st.text_input("Your name", "Shivank")
st.success(f"Hello, {name}! 🚀 Your portfolio starter is live.")
