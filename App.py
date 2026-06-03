from datetime import datetime

import pandas as pd
import streamlit as st

from components.auth import render_login
from utils.database import is_authenticated, logout
from utils.pdf_generator import gerar_pdf_carteira
from utils.market_data import get_contexto_macro
from utils.market_data import get_preco_atual
from utils.portfolio import (
    calcular_alocacao_atual,
    calcular_carteira,
    calcular_renda_fixa,
    get_ativos,
    get_historico_patrimonio,
    get_watchlist,
    salvar_snapshot_patrimonio,
)
from utils.profile import get_alocacao_alvo, get_profile, profile_exists, save_profile

# ── Callback de recuperação de senha ─────────────────────────────────────────
params = st.query_params

if "type" in params and params["type"] == "recovery":
    st.session_state["recovery_mode"] = True
    st.query_params.clear()

if "access_token" in params:
    try:
        from utils.database import get_supabase_client
        supabase = get_supabase_client()
        supabase.auth.set_session(
            params["access_token"],
            params.get("refresh_token", ""),
        )
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state["user"]    = session.user
            st.session_state["session"] = session.session
            if params.get("type") == "recovery":
                st.session_state["recovery_mode"] = True
        st.query_params.clear()
        st.rerun()
    except Exception:
        pass

if st.session_state.get("recovery_mode"):
    from components.auth import render_nova_senha
    st.set_page_config(page_title="Carteira B3", page_icon="📊", layout="wide",
                       initial_sidebar_state="collapsed")
    render_nova_senha()
    st.stop()

# ── Autenticação normal ───────────────────────────────────────────────────────
_autenticado = is_authenticated()

st.set_page_config(
    page_title="Carteira B3",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed" if not _autenticado else "auto",
)

if not _autenticado:
    render_login()
    st.stop()

if "trocando_perfil" not in st.session_state:
    st.session_state.trocando_perfil = False

with st.sidebar:
    st.title("📊 Carteira B3")
    st.caption("v0.1.0")
    user = st.session_state.get("user")
    st.caption(f"Logado como: {user.email if user else ''}")
    if st.button("Sair", use_container_width=True):
        logout()
        st.rerun()
    if profile_exists():
        st.divider()
        st.subheader("Perfil do investidor")
        st.write(get_profile().capitalize())
        alocacao = get_alocacao_alvo()
        NOMES_CLASSES = {
            "acoes": "Ações", "fiis": "FIIs",
            "renda_fixa": "Renda Fixa", "alternativos": "Alternativo",
        }
        df = pd.DataFrame(
            {"Classe": list(alocacao.keys()), "%": list(alocacao.values())}
        )
        df["Classe"] = df["Classe"].map(NOMES_CLASSES)
        st.table(df.set_index("Classe"))
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


salvar_snapshot_patrimonio()

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

    macro = get_contexto_macro()
    ativos = get_ativos()
    alocacao_atual = calcular_alocacao_atual()
    alocacao_alvo = get_alocacao_alvo()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Ativos cadastrados", len(ativos))
    m2.metric("Selic a.a.", f"{macro['selic']:.2f}%")
    m3.metric("IBOV no ano", f"{macro['ibov_no_ano']:+.1f}%")
    m4.metric("Dólar", f"R$ {macro['dolar']:.2f}")

    st.divider()

    col_aloc, col_alertas = st.columns(2)

    with col_aloc:
        st.subheader("Alocação Atual")
        if alocacao_atual:
            for classe, pct in alocacao_atual.items():
                st.write(f"{classe}: **{pct:.1f}%**")
        else:
            st.info("Cadastre seus ativos para ver a alocação.")

    with col_alertas:
        st.subheader("Alertas")
        alertas = []

        _chave_para_classe = {
            "acoes": "Ações", "fiis": "FIIs",
            "renda_fixa": "Renda Fixa", "alternativos": "Alternativo",
        }
        for chave, classe in _chave_para_classe.items():
            alvo = alocacao_alvo.get(chave, 0)
            atual = alocacao_atual.get(classe, 0.0)
            if abs(atual - alvo) > 5:
                alertas.append(
                    f"{classe}: {atual:.1f}% (alvo {alvo:.0f}%), diferença de {atual - alvo:+.1f}%"
                )

        try:
            for a in calcular_renda_fixa():
                dias = a.get("dias_para_vencer")
                if dias is not None and dias <= 0:
                    alertas.append(f"Renda Fixa: **{a['ticker']}** venceu. Verifique o resgate.")
                elif dias is not None and dias <= 90:
                    alertas.append(f"Renda Fixa: **{a['ticker']}** vence em {dias} dias.")
        except Exception:
            pass

        try:
            for w in get_watchlist():
                alvo = w.get("preco_entrada_alvo")
                if not alvo:
                    continue
                pa = get_preco_atual(w["ticker"], w["classe"])
                if pa and pa <= alvo * 1.02:
                    alertas.append(f"{w['ticker']} atingiu o preço alvo na watchlist")
        except Exception:
            pass

        if alertas:
            for msg in alertas:
                st.warning(msg)
        else:
            st.success("Tudo em ordem.")

    st.divider()
    st.caption("Navegue pelo menu lateral para acessar cada painel. Dados atualizados em tempo real.")

    ativos_pdf = calcular_carteira()
    if ativos_pdf:
        st.divider()
        col_pdf, _ = st.columns([1, 3])
        with col_pdf:
            if st.button("Exportar relatório PDF", use_container_width=True):
                with st.spinner("Gerando PDF..."):
                    pdf_bytes = gerar_pdf_carteira(
                        ativos=ativos_pdf,
                        alocacao_atual=alocacao_atual,
                        alocacao_alvo=alocacao_alvo,
                        perfil=get_profile(),
                        historico=get_historico_patrimonio(),
                        user_email=st.session_state.get("user").email,
                    )
                st.download_button(
                    label="Baixar PDF",
                    data=pdf_bytes,
                    file_name=f"carteira_b3_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
