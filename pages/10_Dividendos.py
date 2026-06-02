import pandas as pd
import plotly.express as px
import streamlit as st

from utils.market_data import get_dividendos_ativo, get_proximo_dividendo
from utils.portfolio import fmt_brl, get_ativos_por_classe


def _brl(v: float) -> str:
    return fmt_brl(v).replace("$", r"\$")


st.title("Calendário de Dividendos")
st.caption("Acompanhe os dividendos e rendimentos da sua carteira.")

acoes = get_ativos_por_classe("Ações")
fiis  = get_ativos_por_classe("FIIs")
ativos_div = [(a, "Ações") for a in acoes] + [(a, "FIIs") for a in fiis]

if not ativos_div:
    st.info("Nenhuma ação ou FII cadastrado. Acesse 'Carteira' para adicionar ativos.")
    st.stop()

# ── Busca dados de dividendos ─────────────────────────────────────────────────
with st.spinner("Carregando dados de dividendos..."):
    dados_prox = {}
    for ativo, classe in ativos_div:
        ticker = ativo["ticker"]
        dados_prox[ticker] = get_proximo_dividendo(ticker, classe)

# ── Seção 1 — Resumo de Renda Passiva ─────────────────────────────────────────
st.subheader("Renda Passiva Estimada")

renda_mensal = 0.0
soma_dy_ponderado = 0.0
soma_valor_posicao = 0.0

for ativo, classe in ativos_div:
    ticker = ativo["ticker"]
    qtd    = ativo["quantidade"]
    prox   = dados_prox.get(ticker)
    if not prox:
        continue

    freq = prox["frequencia"]
    media = prox["media_pagamento"]
    if freq == "Mensal":
        renda_mensal += media * qtd
    elif freq == "Trimestral":
        renda_mensal += (media * qtd) / 3
    elif freq == "Semestral":
        renda_mensal += (media * qtd) / 6

    dy = prox.get("dy_ultimos_12m")
    valor_posicao = qtd * ativo["preco_medio"]
    if dy is not None:
        soma_dy_ponderado += dy * valor_posicao
        soma_valor_posicao += valor_posicao

dy_medio = (soma_dy_ponderado / soma_valor_posicao) if soma_valor_posicao > 0 else 0.0

m1, m2, m3 = st.columns(3)
m1.metric("Renda Mensal Estimada",  fmt_brl(renda_mensal))
m2.metric("Renda Anual Estimada",   fmt_brl(renda_mensal * 12))
m3.metric("DY Médio da Carteira",   f"{dy_medio:.1f}%" if dy_medio else "—")

st.caption(
    "Valores estimados com base no histórico de pagamentos. "
    "Dividendos futuros não são garantidos."
)

tem_baixa_confiabilidade = any(
    dados_prox.get(a["ticker"], {}) and
    dados_prox[a["ticker"]].get("confiabilidade_label") in ("Baixa", "Sem dados")
    for a, _ in ativos_div
)
if tem_baixa_confiabilidade:
    st.caption(
        ":orange[Atenção: alguns ativos têm estimativas de baixa confiabilidade. "
        "Consulte os detalhes abaixo.]"
    )

# ── Seção 2 — Próximos Pagamentos ─────────────────────────────────────────────
st.subheader("Próximos Pagamentos Estimados")

proximos = []
for ativo, classe in ativos_div:
    ticker = ativo["ticker"]
    qtd    = ativo["quantidade"]
    prox   = dados_prox.get(ticker)
    if not prox:
        continue
    proximos.append({
        "Ativo":                   ticker,
        "Classe":                  classe,
        "Data Estimada":           prox["proxima_data_estimada"],
        "Valor Estimado por Cota": prox["media_pagamento"],
        "Valor Total Estimado":    prox["media_pagamento"] * qtd,
        "Frequência":              prox["frequencia"],
        "quantidade":              qtd,
        "confiabilidade_label":    prox.get("confiabilidade_label", "Sem dados"),
        "confiabilidade_cor":      prox.get("confiabilidade_cor", "gray"),
        "confiabilidade_motivo":   prox.get("confiabilidade_motivo", ""),
    })

proximos.sort(key=lambda x: x["Data Estimada"])

if not proximos:
    st.info("Não há estimativas de pagamento disponíveis para os ativos cadastrados.")
else:
    for p in proximos:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"**{p['Ativo']}**")
                st.caption(p["Classe"])
            with c2:
                st.write(p["Data Estimada"].strftime("%d/%m/%Y"))
                st.caption("Estimada")
            with c3:
                st.write(fmt_brl(p["Valor Estimado por Cota"]))
                st.caption("por cota")
            with c4:
                st.markdown(f"**{fmt_brl(p['Valor Total Estimado'])}**")
                st.caption(f"{p['quantidade']} cotas · {p['Frequência']}")

            col_conf, col_motivo = st.columns([1, 4])
            with col_conf:
                cor   = p["confiabilidade_cor"]
                label = p["confiabilidade_label"]
                st.markdown(
                    f'<span style="color:{cor}">● </span>**Confiabilidade: {label}**',
                    unsafe_allow_html=True,
                )
            with col_motivo:
                st.caption(p["confiabilidade_motivo"])

# ── Seção 3 — Histórico por Ativo ─────────────────────────────────────────────
st.subheader("Histórico de Dividendos")

for ativo, classe in ativos_div:
    ticker = ativo["ticker"]
    qtd    = ativo["quantidade"]

    with st.expander(ticker, expanded=False):
        hist = get_dividendos_ativo(ticker, classe)

        if hist.empty:
            st.info("Sem histórico disponível para os últimos 24 meses.")
            continue

        corte_12m = pd.Timestamp.today() - pd.DateOffset(months=12)
        hist_12m  = hist[hist.index >= corte_12m]["Dividendo"]

        ultimo     = float(hist["Dividendo"].iloc[-1])
        media_12m  = float(hist_12m.mean()) if not hist_12m.empty else 0.0
        total_12m  = float(hist_12m.sum() * qtd) if not hist_12m.empty else 0.0

        h1, h2, h3 = st.columns(3)
        h1.metric("Último Pagamento",      fmt_brl(ultimo))
        h2.metric("Média últimos 12m",     fmt_brl(media_12m))
        h3.metric("Total últimos 12m",     fmt_brl(total_12m))

        hist_reset = hist.reset_index()
        fig = px.bar(
            hist_reset,
            x="Data",
            y="Dividendo",
            title=f"Histórico de dividendos — {ticker}",
            labels={"Data": "Data", "Dividendo": "Dividendo por cota (R$)"},
            color_discrete_sequence=["#00A878"],
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
