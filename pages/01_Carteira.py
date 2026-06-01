import pandas as pd
import streamlit as st

from utils.portfolio import add_ativo, ativo_existe, get_ativos, remove_ativo

st.title("Minha Carteira")

st.header("Adicionar Ativo")

classe = st.selectbox(
    "Classe",
    ["Ações", "FIIs", "Renda Fixa", "Alternativo"],
    key="classe_selecionada",
)

with st.form("form_add_ativo", clear_on_submit=True):
    if classe in ("Ações", "FIIs"):
        identificador = st.text_input("Ticker", placeholder="Ex: BBAS3")
        quantidade = st.number_input("Quantidade", min_value=1, step=1, value=1)
        preco_medio = st.number_input("Preço Médio por cota (R$)", min_value=0.01, format="%.2f", value=0.01)
        vencimento = None

    elif classe == "Renda Fixa":
        identificador = st.text_input("Nome do ativo", placeholder="Ex: Tesouro Prefixado 2032")
        valor_investido = st.number_input("Valor Investido (R$)", min_value=0.01, format="%.2f", value=0.01)
        data_venc = st.date_input("Data de Vencimento")
        quantidade = 1
        preco_medio = valor_investido
        vencimento = data_venc.strftime("%d/%m/%Y")

    else:  # Alternativo
        identificador = st.text_input("Ticker", placeholder="Ex: BTC-USD")
        quantidade = st.number_input("Quantidade", min_value=0.00000001, format="%.8f", value=0.00000001)
        preco_medio = st.number_input("Preço Médio (R$)", min_value=0.01, format="%.2f", value=0.01)
        vencimento = None

    submitted = st.form_submit_button("Adicionar")

if submitted:
    nome = identificador.strip()
    if not nome:
        st.warning("Preencha o identificador do ativo.")
    elif ativo_existe(nome):
        st.warning(f"{nome.upper()} já está cadastrado na carteira.")
    else:
        add_ativo(nome, quantidade, preco_medio, classe, vencimento)
        st.success(f"{nome.upper()} adicionado com sucesso.")

st.header("Ativos Cadastrados")
ativos = get_ativos()

if not ativos:
    st.info("Nenhum ativo cadastrado. Adicione seu primeiro ativo acima.")
else:
    linhas = []
    for a in ativos:
        linhas.append({
            "Ticker": a["ticker"],
            "Classe": a["classe"],
            "Quantidade": a["quantidade"],
            "Preço Médio": a["preco_medio"],
            "Vencimento": a.get("vencimento", "-"),
        })
    st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)

    tickers_cadastrados = [a["ticker"] for a in ativos]
    ticker_remover = st.selectbox("Selecione o ativo para remover", tickers_cadastrados)
    if st.button("Remover"):
        remove_ativo(ticker_remover)
        st.success(f"{ticker_remover} removido da carteira.")
        st.rerun()
