import streamlit as st

from utils.market_data import (
    get_contexto_macro,
    get_dados_fundamentus,
    get_dados_yfinance_fii,
    get_indices_renda_fixa,
    get_preco_atual,
    get_preco_entrada_saida,
)
from utils.portfolio import (
    add_watchlist,
    calcular_score_radar,
    classificar_estilo,
    fmt_brl,
    get_ativos,
)
from utils.profile import get_profile

from utils.database import is_authenticated
if not is_authenticated():
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

st.title("Sugestões de Ativos")
st.caption("Análise de ativos em tempo real com dados públicos.")

perfil = get_profile()

# ── Contexto Macro ────────────────────────────────────────────────────────────
macro = get_contexto_macro()
selic = macro["selic"]
vix = macro["vix"]
ibov_no_ano = macro["ibov_no_ano"]
dolar = macro["dolar"]

st.subheader("Contexto Macroeconômico Atual")

m1, m2, m3, m4 = st.columns(4)
m1.metric(
    "Selic a.a.",
    f"{selic:.2f}%",
    delta="Renda fixa atrativa" if selic > 13 else "Renda fixa menos atrativa",
    delta_color="normal" if selic > 13 else "inverse",
)
m2.metric(
    "Risco Global (VIX)",
    f"{vix:.1f}",
    delta=macro["nivel_risco"],
    delta_color="inverse" if macro["nivel_risco"] == "Alto" else "normal",
)
m3.metric(
    "Ibovespa no ano",
    f"{ibov_no_ano:+.1f}%",
    delta=macro["momento_bolsa"],
    delta_color="normal" if ibov_no_ano >= 0 else "inverse",
)
m4.metric("Dólar", f"R$ {dolar:.2f}")

st.info(macro["resumo_macro"])

impactos = []
if selic > 13 and perfil == "conservador":
    impactos.append("Selic elevada favorece sua alocação em renda fixa. Momento adequado para o seu perfil.")
if selic > 13 and perfil in ("moderado", "arrojado"):
    impactos.append("Selic elevada aumenta o custo de oportunidade de ações. Seja seletivo nas escolhas.")
if vix > 25:
    impactos.append("VIX elevado indica instabilidade global. Considere aumentar posição em renda fixa ou ouro.")
if ibov_no_ano < 0:
    impactos.append("Ibovespa negativo no ano pode indicar oportunidade de entrada em ações a preços mais baixos.")
if ibov_no_ano > 15:
    impactos.append("Bolsa em alta no ano. Avalie se os preços atuais ainda oferecem margem de segurança.")
if dolar > 5.5:
    impactos.append("Dólar alto beneficia exportadoras (VALE3, PRIO3) e ativos dolarizados como Bitcoin e Ouro.")

if impactos:
    for msg in impactos:
        st.warning(f"⚠️ {msg}")
else:
    st.success("Cenário macro sem alertas relevantes para o seu perfil no momento.")

st.divider()

# ── Busca livre ───────────────────────────────────────────────────────────────
st.subheader("Analisar Qualquer Ativo")

col_tk, col_cl, col_bt = st.columns([3, 2, 1])
with col_tk:
    ticker_busca = st.text_input(
        "Digite o ticker",
        placeholder="Ex: PETR4, VALE3, MXRF11",
        help="Digite qualquer ticker da B3 para análise completa instantânea.",
    ).upper().strip()
with col_cl:
    classe_busca = st.selectbox("Classe", ["Ações", "FIIs", "Alternativo"], key="classe_busca")
with col_bt:
    st.write("")
    buscar = st.button("Analisar", use_container_width=True, type="primary")

if buscar and ticker_busca:
    with st.spinner(f"Analisando {ticker_busca}..."):
        preco = get_preco_atual(ticker_busca, classe_busca)

    if preco is None:
        st.error(f"Ticker {ticker_busca} não encontrado. Verifique se o ticker está correto.")
    else:
        pl = dy = pvp = roe = None

        if classe_busca == "Ações":
            fund = get_dados_fundamentus(ticker_busca)
            if fund:
                pl  = fund.get("pl")
                dy  = fund.get("dy")
                pvp = fund.get("pvp")
                roe = fund.get("roe")
        elif classe_busca == "FIIs":
            fii = get_dados_yfinance_fii(ticker_busca)
            if fii:
                dy  = fii.get("dy_anual")
                pvp = fii.get("pvp")

        entrada_saida = get_preco_entrada_saida(ticker_busca, classe_busca)
        upside = entrada_saida.get("upside") if entrada_saida else None

        selic_busca = get_indices_renda_fixa()["selic"]
        estilo = classificar_estilo(pl, dy, roe, pvp, selic_busca)
        score_data = calcular_score_radar(
            {"pl": pl, "dy": dy, "pvp": pvp, "roe": roe, "upside": upside, "estilo": estilo},
            selic_busca,
        )

        st.divider()
        _COR_ESTILO = {"Valor": "blue", "Crescimento": "orange", "Híbrido": "gray"}

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"**{ticker_busca}**")
            c1.caption(classe_busca)
            c2.write(fmt_brl(preco))
            if dy is not None:
                c3.write(f"DY: {dy:.1f}%")
            if upside is not None:
                cor_up = "#00A878" if upside >= 0 else "#FF4B4B"
                c4.markdown(
                    f"<span style='color:{cor_up};font-weight:bold'>Upside: {upside:+.1f}%</span>",
                    unsafe_allow_html=True,
                )

            cor_est = _COR_ESTILO.get(estilo, "gray")
            st.markdown(
                f"<span style='background-color:{cor_est};color:white;"
                f"padding:2px 8px;border-radius:10px;font-size:0.75rem'>{estilo}</span>",
                unsafe_allow_html=True,
            )
            st.metric("Score", f"{score_data['score_oportunidade']}/10")

            if entrada_saida:
                e1, e2 = st.columns(2)
                with e1:
                    st.caption("Comprar até")
                    st.markdown(f"**{entrada_saida['entrada_texto']}**")
                with e2:
                    st.caption("Alvo de saída")
                    st.markdown(f"**{entrada_saida['saida_texto']}**")

            if score_data.get("justificativas"):
                st.markdown("**Pontos positivos:**")
                for j in score_data["justificativas"]:
                    st.success(f"✓ {j}")

            if score_data.get("penalidades"):
                st.markdown("**Pontos de atenção:**")
                for p in score_data["penalidades"]:
                    st.warning(f"⚠️ {p}")

            st.divider()

            ativos_carteira_busca = [a["ticker"] for a in get_ativos()]
            if ticker_busca in ativos_carteira_busca:
                st.success("Você já tem esse ativo na carteira.")
            else:
                col_watch, _ = st.columns([1, 3])
                with col_watch:
                    if st.button("Adicionar à watchlist", key="watch_busca"):
                        add_watchlist(
                            ticker_busca, classe_busca,
                            entrada_saida.get("preco_atual") if entrada_saida else None,
                            "Adicionado via busca",
                        )
                        st.toast(f"{ticker_busca} adicionado à watchlist!")

            st.caption(
                "Análise baseada em dados públicos do Fundamentus e yfinance. "
                "Não é recomendação de investimento."
            )
