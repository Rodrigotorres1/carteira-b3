from datetime import datetime

import pandas as pd
import streamlit as st

from utils.market_data import get_dados_radar
from utils.portfolio import fmt_brl, get_ativos
from utils.sugestoes import UNIVERSO_ACOES, UNIVERSO_FIIS

st.title("Radar de Oportunidades")
st.caption("Varredura automática do mercado em busca de ativos com bom potencial.")

# ── Filtros ───────────────────────────────────────────────────────────────────
f1, f2, f3 = st.columns(3)
with f1:
    filtro_classe = st.selectbox("Classe", ["Ações", "FIIs", "Ambos"])
with f2:
    criterio = st.selectbox(
        "Critério principal",
        [
            "Melhor oportunidade geral",
            "Maior dividend yield",
            "Mais barato (P/L)",
            "Maior upside",
            "P/VP abaixo de 1",
        ],
    )
with f3:
    minimo_dados = st.selectbox(
        "Mínimo de dados",
        ["Mostrar todos", "Apenas com DY disponível", "Apenas com upside disponível"],
    )

st.info(
    "A varredura busca dados em tempo real para todos os ativos. "
    "Pode levar alguns segundos."
)

if st.button("Executar Radar", type="primary"):
    tickers_varrer = []
    if filtro_classe in ("Ações", "Ambos"):
        tickers_varrer += [(t, "Ações") for t in UNIVERSO_ACOES]
    if filtro_classe in ("FIIs", "Ambos"):
        tickers_varrer += [(t, "FIIs") for t in UNIVERSO_FIIS]

    resultados = []
    with st.spinner(f"Varrendo {len(tickers_varrer)} ativos..."):
        for ticker, cls in tickers_varrer:
            dados = get_dados_radar(ticker, cls)
            if dados:
                resultados.append(dados)

    st.session_state["radar_resultados"] = resultados
    st.session_state["radar_ts"] = datetime.now().strftime("%d/%m/%Y %H:%M")

# ── Resultados ────────────────────────────────────────────────────────────────
if "radar_resultados" not in st.session_state:
    st.stop()

st.caption(f"Última atualização: {st.session_state['radar_ts']}")

todos = st.session_state["radar_resultados"]

# Aplicar filtro de mínimo de dados
if minimo_dados == "Apenas com DY disponível":
    todos = [r for r in todos if r["dy"] is not None]
elif minimo_dados == "Apenas com upside disponível":
    todos = [r for r in todos if r["upside"] is not None]

# Aplicar filtro de classe (pode ter mudado após execução)
if filtro_classe != "Ambos":
    todos = [r for r in todos if r["classe"] == filtro_classe]

# Ordenar por critério
_SORT_KEY = {
    "Melhor oportunidade geral": lambda r: r["score_oportunidade"],
    "Maior dividend yield":      lambda r: r["dy"] or 0,
    "Mais barato (P/L)":         lambda r: -(r["pl"] or 999) if (r["pl"] and r["pl"] > 0) else -999,
    "Maior upside":              lambda r: r["upside"] or 0,
    "P/VP abaixo de 1":          lambda r: -(r["pvp"] or 999),
}
resultados_ord = sorted(todos, key=_SORT_KEY[criterio], reverse=True)

if not resultados_ord:
    st.warning("Nenhum ativo encontrado com os filtros selecionados.")
    st.stop()

ativos_carteira = {a["ticker"] for a in get_ativos()}
top3 = resultados_ord[:3]

st.subheader(f"{len(resultados_ord)} ativos encontrados")

# Top 3 destaques
cols_top = st.columns(3)
for col, r in zip(cols_top, top3):
    with col:
        with st.container(border=True):
            na_carteira = r["ticker"] in ativos_carteira
            st.metric(
                r["ticker"],
                f"Score: {r['score_oportunidade']}/10",
                delta="Na carteira" if na_carteira else None,
                delta_color="normal" if na_carteira else "off",
            )
            st.write(fmt_brl(r["preco_atual"]))
            if criterio == "Maior dividend yield" and r["dy"]:
                st.caption(f"DY: {r['dy']:.1f}%")
            elif criterio == "Mais barato (P/L)" and r["pl"]:
                st.caption(f"P/L: {r['pl']:.1f}")
            elif criterio in ("P/VP abaixo de 1", "Melhor oportunidade geral") and r["pvp"]:
                st.caption(f"P/VP: {r['pvp']:.2f}")
            elif r["upside"] is not None:
                st.caption(f"Upside: {r['upside']:+.1f}%")

# Tabela completa
top3_tickers = {r["ticker"] for r in top3}

linhas = []
for r in resultados_ord:
    linhas.append({
        "Ticker":    r["ticker"],
        "Classe":    r["classe"],
        "Preço":     fmt_brl(r["preco_atual"]),
        "DY %":      f"{r['dy']:.1f}%" if r["dy"] is not None else "—",
        "P/L":       f"{r['pl']:.1f}"  if r["pl"]  is not None else "—",
        "P/VP":      f"{r['pvp']:.2f}" if r["pvp"] is not None else "—",
        "Upside %":  f"{r['upside']:+.1f}%" if r["upside"] is not None else "—",
        "Score":     r["score_oportunidade"],
        "_carteira": r["ticker"] in ativos_carteira,
        "_top3":     r["ticker"] in top3_tickers,
    })

df = pd.DataFrame(linhas)
df_exibir = df.drop(columns=["_carteira", "_top3"]).copy()


def _highlight(row: pd.Series) -> list[str]:
    orig = df.loc[row.name]
    if orig["_carteira"]:
        return ["background-color: #1a3a2a"] * len(row)
    if orig["_top3"]:
        return ["background-color: #1a2a3a"] * len(row)
    return [""] * len(row)


st.dataframe(
    df_exibir.style.apply(_highlight, axis=1),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Scores baseados em dados públicos. "
    "Não constituem recomendação de investimento."
)
