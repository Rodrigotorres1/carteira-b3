import pandas as pd
import plotly.express as px
import streamlit as st

from utils.market_data import get_dados_acao
from utils.portfolio import get_ativos_por_classe

DY_COMPRA = 5.0
PL_COMPRA = 15.0
PL_VENDA = 30.0
VARIACAO_QUEDA = -5.0
VARIACAO_ALTA = 15.0


def calcular_score(dados: dict, variacao_30d: float) -> str:
    """Retorna recomendação com base em DY, P/L e variação de 30 dias."""
    dy = dados.get("dividend_yield") or 0
    pl = dados.get("pl")

    if dy >= DY_COMPRA and pl is not None and pl <= PL_COMPRA:
        return "Comprar"
    if pl is not None and pl >= PL_VENDA and variacao_30d >= VARIACAO_ALTA:
        return "Vender"
    return "Manter"


def _fmt_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


st.title("Painel de Ações")

acoes = get_ativos_por_classe("Ações")

if not acoes:
    st.info("Nenhuma ação cadastrada. Acesse 'Carteira' para adicionar ações.")
    st.stop()

resumo = []

for ativo in acoes:
    ticker = ativo["ticker"]
    dados = get_dados_acao(ticker)

    with st.expander(f"{ticker}" + (f" — {dados['nome']}" if dados else ""), expanded=False):
        if dados is None:
            st.warning(f"Não foi possível obter dados para {ticker}.")
            resumo.append({
                "Ticker": ticker,
                "Preço Atual": None,
                "Variação %": None,
                "DY %": None,
                "P/L": None,
                "Score": "—",
            })
            continue

        hist = dados["historico"]
        variacao_30d = 0.0
        if hist is not None and len(hist) >= 30:
            preco_30d_atras = float(hist["Close"].iloc[-30])
            variacao_30d = ((dados["preco_atual"] - preco_30d_atras) / preco_30d_atras) * 100

        score = calcular_score(dados, variacao_30d)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Preço atual", _fmt_brl(dados["preco_atual"]))
        col2.metric(
            "Variação diária",
            f"{dados['variacao_pct']:+.2f}%",
            delta=f"{dados['variacao_pct']:.2f}%",
        )
        col3.metric("Dividend Yield", f"{dados['dividend_yield']:.2f}%")
        col4.metric("P/L", f"{dados['pl']:.1f}" if dados["pl"] else "—")

        if score == "Comprar":
            st.success(f"Score: **Comprar**")
        elif score == "Vender":
            st.warning(f"Score: **Vender**")
        else:
            st.info(f"Score: **Manter**")

        if hist is not None and not hist.empty:
            hist_reset = hist.reset_index()
            fig = px.line(
                hist_reset,
                x="Date",
                y="Close",
                title=f"Histórico 12 meses — {ticker}",
                labels={"Date": "Data", "Close": "Preço (R$)"},
                color_discrete_sequence=["#00A878"],
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        resumo.append({
            "Ticker": ticker,
            "Preço Atual": f"R$ {dados['preco_atual']:.2f}",
            "Variação %": f"{dados['variacao_pct']:+.2f}%",
            "DY %": f"{dados['dividend_yield']:.2f}%",
            "P/L": f"{dados['pl']:.1f}" if dados["pl"] else "—",
            "Score": score,
        })

st.header("Resumo")
if resumo:
    st.dataframe(pd.DataFrame(resumo), use_container_width=True, hide_index=True)
