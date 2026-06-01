import pandas as pd
import streamlit as st

from utils.profile import get_alocacao_alvo, get_profile, profile_exists, save_profile

st.set_page_config(
    page_title="Carteira B3",
    page_icon="📊",
    layout="wide",
)

if "trocando_perfil" not in st.session_state:
    st.session_state.trocando_perfil = False

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
        if st.button("Trocar perfil", use_container_width=True):
            st.session_state.trocando_perfil = True
            st.rerun()


def _tela_selecao_perfil(titulo: str, subtitulo: str) -> None:
    st.title(titulo)
    st.write(subtitulo)
    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Conservador", use_container_width=True):
            save_profile("conservador")
            st.session_state.trocando_perfil = False
            st.rerun()
        st.caption("Prioriza segurança e estabilidade.\nMaior parte em renda fixa.")

    with col2:
        if st.button("Moderado", use_container_width=True):
            save_profile("moderado")
            st.session_state.trocando_perfil = False
            st.rerun()
        st.caption("Equilíbrio entre risco e retorno.\nMix diversificado de ativos.")

    with col3:
        if st.button("Arrojado", use_container_width=True):
            save_profile("arrojado")
            st.session_state.trocando_perfil = False
            st.rerun()
        st.caption("Aceita maior volatilidade.\nFoco em crescimento de longo prazo.")


if not profile_exists():
    _tela_selecao_perfil(
        "Bem-vindo ao Carteira B3",
        "Seu perfil de investidor define as sugestões de alocação e os alertas "
        "exibidos ao longo do app. Escolha o perfil que melhor representa sua "
        "tolerância ao risco.",
    )
elif st.session_state.trocando_perfil:
    _tela_selecao_perfil(
        "Trocar perfil de investidor",
        f"Perfil atual: **{get_profile().capitalize()}**. "
        "Selecione o novo perfil abaixo.",
    )
else:
    st.title("Carteira B3")
    st.write("Selecione uma opção no menu lateral para começar.")
