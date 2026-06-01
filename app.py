import streamlit as st

st.set_page_config(
    page_title="Carteira B3",
    page_icon="📊",
    layout="wide",
)

with st.sidebar:
    st.title("📊 Carteira B3")
    st.caption("v0.1.0")

st.title("Bem-vindo à Carteira B3")
st.write("Gerencie e acompanhe seus investimentos na bolsa de valores brasileira.")
