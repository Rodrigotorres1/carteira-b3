import streamlit as st

from utils.market_data import (
    get_contexto_macro,
    get_dados_fundamentus,
    get_preco_atual,
    get_preco_entrada_saida,
)
from utils.portfolio import get_ativos
from utils.profile import get_profile
from utils.sugestoes import agrupar_por_classe, get_objetivo_combinado, get_sugestoes

_OBJETIVO_MAP = {
    "Geração de renda": "renda",
    "Crescimento de patrimônio": "crescimento",
    "Combinado (Renda + Crescimento)": "combinado",
}
_ORDEM_CLASSES = ["Ações", "FIIs", "Renda Fixa", "Alternativos"]
_ATIVOS_DOLAR = {"VALE3", "PRIO3", "BTC-USD", "GC=F", "SMTO3"}

st.title("Sugestões de Ativos")

st.warning(
    "As sugestões abaixo são baseadas no perfil e objetivo selecionado. "
    "Não constituem recomendação de investimento. "
    "Consulte um assessor de investimentos certificado (AAI)."
)

perfil = get_profile()

col_obj, col_perf = st.columns(2)
with col_obj:
    objetivo_label = st.selectbox("Objetivo", list(_OBJETIVO_MAP.keys()))
with col_perf:
    st.metric("Seu perfil", perfil.capitalize())

objetivo_chave = _OBJETIVO_MAP[objetivo_label]

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

# ── Sugestões ─────────────────────────────────────────────────────────────────
if objetivo_chave == "combinado":
    sugestoes = get_objetivo_combinado(perfil)
else:
    sugestoes = [{**s, "objetivos": objetivo_chave.capitalize()} for s in get_sugestoes(perfil, objetivo_chave)]

agrupado = agrupar_por_classe(sugestoes)
ativos_carteira = {a["ticker"] for a in get_ativos()}

_COR_OBJETIVO = {
    "Renda e Crescimento": "green",
    "Renda": "blue",
    "Crescimento": "orange",
}

for i, classe in enumerate(_ORDEM_CLASSES):
    itens = agrupado.get(classe)
    if not itens:
        continue

    if i > 0:
        st.divider()

    st.subheader(classe)

    for ativo in itens:
        ticker = ativo["ticker"]
        nome = ativo["nome"]
        motivo = ativo["motivo"]
        objetivos = ativo.get("objetivos", "")

        precos = get_preco_entrada_saida(ticker, classe) if classe != "Renda Fixa" else None

        with st.container(border=True):
            # Linha 1 — identificação + preço + DY + upside
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.markdown(f"**{ticker}**")
                st.caption(nome)
                if objetivos:
                    cor = _COR_OBJETIVO.get(objetivos, "gray")
                    st.markdown(
                        f"<span style='background-color:{cor};color:white;"
                        f"padding:2px 8px;border-radius:10px;font-size:0.75rem'>"
                        f"{objetivos}</span>",
                        unsafe_allow_html=True,
                    )

            with c2:
                if classe == "Renda Fixa":
                    st.write("Ver na corretora")
                elif precos and precos["preco_atual"]:
                    brl = f"R$ {precos['preco_atual']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    st.write(brl)
                else:
                    st.write("Preço indisponível")

            with c3:
                if classe in ("Ações", "FIIs"):
                    fund = get_dados_fundamentus(ticker)
                    dy = fund.get("dy") if fund else None
                    if dy:
                        st.write(f"DY: {dy:.1f}%")

            with c4:
                if precos and precos.get("upside") is not None:
                    upside = precos["upside"]
                    cor_up = "#00A878" if upside >= 0 else "#FF4B4B"
                    st.markdown(
                        f"<span style='color:{cor_up};font-weight:bold'>"
                        f"Upside: {upside:+.1f}%</span>",
                        unsafe_allow_html=True,
                    )

            # Linha 2 — entrada/saída (exceto renda fixa)
            if classe != "Renda Fixa" and precos:
                e1, e2 = st.columns(2)
                with e1:
                    st.caption("Comprar até")
                    st.markdown(f"**{precos['entrada_texto']}**")
                with e2:
                    st.caption("Alvo de saída")
                    st.markdown(f"**{precos['saida_texto']}**")

            # Linha 3 — motivo + contexto macro
            st.caption(motivo)

            if dolar > 5.5 and ticker in _ATIVOS_DOLAR:
                st.caption("💵 Dólar forte favorece este ativo.")
            if selic > 13 and classe == "Renda Fixa":
                st.caption("📈 Selic elevada aumenta a atratividade deste título.")
            if vix > 25 and ticker == "GC=F":
                st.caption("🛡️ Instabilidade global tende a valorizar o ouro.")

            # Linha 4 — carteira / watchlist
            if ticker in ativos_carteira:
                st.success("Você já tem esse ativo na carteira.")
            else:
                if st.button("Adicionar à watchlist", key=f"add_{ticker}_{objetivo_chave}"):
                    st.toast("Em breve: funcionalidade de watchlist")
