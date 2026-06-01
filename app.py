import pandas as pd
import streamlit as st

from utils.profile import get_alocacao_alvo, get_profile, profile_exists, save_profile

st.set_page_config(
    page_title="Carteira B3",
    page_icon="📊",
    layout="wide",
)

with st.sidebar:
    st.title("📊 Carteira B3")
    st.caption("v0.1.0")
    if profile_exists():
        st.divider()
        st.subheader("Perfil do investidor")
        st.write(get_profile().capitalize())
        alocacao = get_alocacao_alvo()
        df = pd.DataFrame(
            {"Classe": list(alocacao.keys()), "%": list(alocacao.values())}
        ).set_index("Classe")
        st.table(df)

if not profile_exists():
    st.title("Bem-vindo ao Carteira B3")
    st.write(
        "Seu perfil de investidor define as sugestões de alocação e os alertas "
        "exibidos ao longo do app. Escolha o perfil que melhor representa sua "
        "tolerância ao risco."
    )
    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Conservador", use_container_width=True):
            save_profile("conservador")
            st.rerun()
        st.caption("Prioriza segurança e estabilidade.\nMaior parte em renda fixa.")

    with col2:
        if st.button("Moderado", use_container_width=True):
            save_profile("moderado")
            st.rerun()
        st.caption("Equilíbrio entre risco e retorno.\nMix diversificado de ativos.")

    with col3:
        if st.button("Arrojado", use_container_width=True):
            save_profile("arrojado")
            st.rerun()
        st.caption("Aceita maior volatilidade.\nFoco em crescimento de longo prazo.")
else:
    st.title("Carteira B3")
    st.write("Selecione uma opção no menu lateral para começar.")
