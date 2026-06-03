import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from utils.market_data import get_indices_renda_fixa
from utils.portfolio import (
    calcular_rentabilidade_historico,
    fmt_brl,
    get_historico_patrimonio,
    salvar_snapshot_patrimonio,
)

from utils.database import is_authenticated
if not is_authenticated():
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

st.title("Histórico de Patrimônio")
st.caption("Evolução real do seu patrimônio ao longo do tempo.")

salvar_snapshot_patrimonio()

historico = get_historico_patrimonio()

if len(historico) < 2:
    valor_atual = historico[-1]["valor"] if historico else None
    st.info(
        "Histórico insuficiente. O patrimônio é registrado automaticamente cada vez "
        "que você abre o app. Volte amanhã para ver a evolução."
    )
    if valor_atual:
        st.metric("Patrimônio Atual", fmt_brl(valor_atual))
    st.stop()

# ── Seção 1 — Resumo ──────────────────────────────────────────────────────────
rent = calcular_rentabilidade_historico(historico)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Patrimônio Atual",   fmt_brl(historico[-1]["valor"]))
m2.metric(
    "Patrimônio Inicial",
    fmt_brl(historico[0]["valor"]),
    delta=historico[0]["data"],
    delta_color="off",
)
if rent:
    m3.metric(
        "Rentabilidade Total",
        f"{rent['rentabilidade_total']:+.2f}%",
        delta=f"{rent['rentabilidade_total']:+.2f}%",
        delta_color="normal" if rent["rentabilidade_total"] >= 0 else "inverse",
    )
    m4.metric(
        "Período",
        f"{rent['dias']} dias",
        delta=f"~{rent['dias'] // 30} meses",
        delta_color="off",
    )

# ── Seção 2 — Gráfico ─────────────────────────────────────────────────────────
df = pd.DataFrame(historico)
df["data"]  = pd.to_datetime(df["data"], format="%d/%m/%Y")
df["valor"] = df["valor"].astype(float)
df = df.sort_values("data").reset_index(drop=True)

indices  = get_indices_renda_fixa()
cdi_diario = (1 + indices["cdi"] / 100) ** (1 / 252) - 1
valor_inicial = df["valor"].iloc[0]
df["CDI"] = [valor_inicial * (1 + cdi_diario) ** i for i in range(len(df))]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df["data"], y=df["valor"],
    name="Minha Carteira",
    line={"color": "#00A878", "width": 3},
    mode="lines+markers",
))
fig.add_trace(go.Scatter(
    x=df["data"], y=df["CDI"],
    name="CDI",
    line={"color": "#4A90D9", "width": 1, "dash": "dash"},
))

try:
    data_inicio = df["data"].iloc[0].strftime("%Y-%m-%d")
    ibov_ticker = yf.Ticker("^BVSP")
    hist_ibov = ibov_ticker.history(start=data_inicio)
    if not hist_ibov.empty:
        hist_ibov.index = hist_ibov.index.tz_localize(None)
        ibov_inicial = hist_ibov["Close"].iloc[0]
        ibov_norm = hist_ibov["Close"] / ibov_inicial * valor_inicial
        fig.add_trace(go.Scatter(
            x=ibov_norm.index, y=ibov_norm.values,
            name="Ibovespa",
            line={"color": "#F5A623", "width": 1, "dash": "dash"},
        ))
except Exception:
    pass

fig.update_layout(
    title="Evolução Patrimonial",
    xaxis_title="Data",
    yaxis_title="Valor (R$)",
    hovermode="x unified",
    legend={"orientation": "h", "y": -0.15},
)
st.plotly_chart(fig, use_container_width=True)

# ── Seção 3 — Tabela de Registros ─────────────────────────────────────────────
st.subheader("Registros")

df_exibir = df[["data", "valor"]].copy()
df_exibir["data"]  = df_exibir["data"].dt.strftime("%d/%m/%Y")
df_exibir["valor"] = df_exibir["valor"].apply(fmt_brl)
df_exibir.columns = ["Data", "Patrimônio"]
df_exibir = df_exibir.sort_values("Data", ascending=False)

st.dataframe(df_exibir, use_container_width=True, hide_index=True)
st.caption(
    f"Total de {len(historico)} registros. "
    "Atualizado automaticamente ao abrir o app."
)
