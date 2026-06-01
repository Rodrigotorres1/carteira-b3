import pandas as pd
import streamlit as st

from utils.portfolio import add_ativo, ativo_existe, get_ativos, remove_ativo

st.title("Minha Carteira")

st.header("Adicionar Ativo")
with st.form("form_add_ativo", clear_on_submit=True):
    ticker = st.text_input("Ticker", placeholder="Ex: BBAS3")
    quantidade = st.number_input("Quantidade", min_value=1, step=1, value=1)
    preco_medio = st.number_input("Preço Médio (R$)", min_value=0.01, format="%.2f", value=0.01)
    classe = st.selectbox("Classe", ["Ações", "FIIs", "Renda Fixa", "Alternativo"])
    submitted = st.form_submit_button("Adicionar")

if submitted:
    if not ticker.strip():
        st.warning("Informe o ticker do ativo.")
    elif ativo_existe(ticker):
        st.warning(f"{ticker.upper()} já está cadastrado na carteira.")
    else:
        add_ativo(ticker, quantidade, preco_medio, classe)
        st.success(f"{ticker.upper()} adicionado com sucesso.")

st.header("Ativos Cadastrados")
ativos = get_ativos()

if not ativos:
    st.info("Nenhum ativo cadastrado. Adicione seu primeiro ativo acima.")
else:
    df = pd.DataFrame(ativos)[["ticker", "classe", "quantidade", "preco_medio"]]
    df.columns = ["Ticker", "Classe", "Quantidade", "Preço Médio"]
    st.dataframe(df, use_container_width=True, hide_index=True)

    tickers_cadastrados = [a["ticker"] for a in ativos]
    ticker_remover = st.selectbox("Selecione o ativo para remover", tickers_cadastrados)
    if st.button("Remover"):
        remove_ativo(ticker_remover)
        st.success(f"{ticker_remover} removido da carteira.")
        st.rerun()
