import pandas as pd
import plotly.express as px
import streamlit as st

from utils.market_data import get_dados_fii, get_dados_yfinance_fii
from utils.portfolio import calcular_score_fii, fmt_brl, get_ativos_por_classe
from utils.profile import get_profile

st.title("Painel de FIIs")

fiis = get_ativos_por_classe("FIIs")

if not fiis:
    st.info("Nenhum FII cadastrado. Acesse 'Carteira' para adicionar FIIs.")
    st.stop()

perfil = get_profile()

with st.spinner("Carregando dados de mercado..."):
    dados_mercado = {a["ticker"]: get_dados_fii(a["ticker"]) for a in fiis}
    dados_fund = {
        a["ticker"]: get_dados_yfinance_fii(a["ticker"], pvp_cadastrado=a.get("pvp"))
        for a in fiis
    }

resumo = []

for ativo in fiis:
    ticker = ativo["ticker"]
    dados = dados_mercado[ticker]
    fund = dados_fund[ticker]

    with st.expander(f"{ticker}" + (f" — {dados['nome']}" if dados else ""), expanded=False):
        if dados is None:
            st.warning(f"Não foi possível obter dados para {ticker}.")
            resumo.append({
                "Ticker": ticker,
                "Preço Atual": "—",
                "Variação %": "—",
                "DY Mensal %": "—",
                "Mín. / Máx. 52s": "—",
                "Score": "—",
            })
            continue

        p_min = fund["preco_52s_min"]
        p_max = fund["preco_52s_max"]
        range_52s = (
            f"{fmt_brl(p_min)} / {fmt_brl(p_max)}"
            if p_min and p_max else "—"
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Preço atual", fmt_brl(dados["preco_atual"]))
        col2.metric("Variação diária", f"{dados['variacao_pct']:+.2f}%")
        col3.metric(
            "DY mensal",
            f"{fund['dy_mensal']:.2f}%" if fund["dy_mensal"] else "—",
        )
        col4.metric("Mín. / Máx. 52s", range_52s)

        resultado = calcular_score_fii(
            ticker,
            dados["preco_atual"],
            ativo["preco_medio"],
            perfil,
            fund_data=fund,
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
                "Score baseado em dados de mercado e sua posição na carteira. "
                "Não é recomendação de investimento."
            )

        hist = dados["historico"]
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
            "Preço Atual": fmt_brl(dados["preco_atual"]),
            "Variação %": f"{dados['variacao_pct']:+.2f}%",
            "DY Mensal %": f"{fund['dy_mensal']:.2f}%" if fund["dy_mensal"] else "—",
            "Mín. / Máx. 52s": range_52s,
            "Score": label,
        })

st.header("Resumo")
if resumo:
    st.dataframe(pd.DataFrame(resumo), use_container_width=True, hide_index=True)
