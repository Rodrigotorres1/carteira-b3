import pandas as pd
import plotly.express as px
import streamlit as st

from utils.market_data import get_dados_acao
from utils.portfolio import calcular_score_acao, get_ativos_por_classe
from utils.profile import get_profile


def _fmt_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


st.title("Painel de Ações")

acoes = get_ativos_por_classe("Ações")

if not acoes:
    st.info("Nenhuma ação cadastrada. Acesse 'Carteira' para adicionar ações.")
    st.stop()

perfil = get_profile()
resumo = []

for ativo in acoes:
    ticker = ativo["ticker"]
    dados = get_dados_acao(ticker)

    with st.expander(f"{ticker}" + (f" — {dados['nome']}" if dados else ""), expanded=False):
        if dados is None:
            st.warning(f"Não foi possível obter dados para {ticker}.")
            resumo.append({
                "Ticker": ticker,
                "Preço Atual": "—",
                "Variação %": "—",
                "DY %": "—",
                "P/L": "—",
                "Score": "—",
            })
            continue

        hist = dados["historico"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Preço atual", _fmt_brl(dados["preco_atual"]))
        col2.metric(
            "Variação diária",
            f"{dados['variacao_pct']:+.2f}%",
            delta=f"{dados['variacao_pct']:.2f}%",
        )
        col3.metric("Dividend Yield", f"{dados['dividend_yield']:.2f}%")
        col4.metric("P/L", f"{dados['pl']:.1f}" if dados["pl"] else "—")

        resultado = calcular_score_acao(
            ticker,
            dados["preco_atual"],
            ativo["preco_medio"],
            perfil,
        )

        cor = resultado["cor"]
        label = resultado["label"]
        if cor == "success":
            st.success(f"Score: **{label}** ({resultado['score']:+d} pontos)")
        elif cor == "warning":
            st.warning(f"Score: **{label}** ({resultado['score']:+d} pontos)")
        else:
            st.info(f"Score: **{label}** ({resultado['score']:+d} pontos)")

        with st.popover("Por que esse score?"):
            st.markdown(f"**{resultado['resumo']}**")
            st.divider()
            for fator in resultado["fatores"]:
                c1, c2, c3 = st.columns([2, 1, 5])
                c1.write(fator["nome"])
                sinal = f"{fator['pontos']:+d}" if fator["pontos"] != 0 else "0"
                c2.write(f"`{sinal}`")
                c3.write(fator["explicacao"])
            st.caption(
                "Score baseado em recomendações de analistas, dados fundamentalistas "
                "e sua posição na carteira. Não é recomendação de investimento."
            )

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
            "Score": label,
        })

st.header("Resumo")
if resumo:
    st.dataframe(pd.DataFrame(resumo), use_container_width=True, hide_index=True)
