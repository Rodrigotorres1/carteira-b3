from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from utils.market_data import get_indices_renda_fixa
from utils.portfolio import (
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

# ── Prepara DataFrame ─────────────────────────────────────────────────────────
df = pd.DataFrame(historico)
df["data_dt"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
df["valor"]   = df["valor"].astype(float)
df = df.sort_values("data_dt").reset_index(drop=True)

primeiro = df.iloc[0]
ultimo   = df.iloc[-1]

# ── Seção 1 — Resumo ──────────────────────────────────────────────────────────
rendimento_total = float(ultimo.get("rendimento_pct", 0))
variacao_valor   = float(ultimo["valor"]) - float(primeiro["valor"])
dias             = (df["data_dt"].iloc[-1] - df["data_dt"].iloc[0]).days

m1, m2, m3, m4 = st.columns(4)
m1.metric("Patrimônio Atual", fmt_brl(float(ultimo["valor"])))
m2.metric(
    "Rendimento Total",
    f"{rendimento_total:+.2f}%",
    delta=f"{rendimento_total:+.2f}%",
    delta_color="normal" if rendimento_total >= 0 else "inverse",
)
m3.metric(
    "Variação em R$",
    fmt_brl(variacao_valor),
    delta=fmt_brl(variacao_valor),
    delta_color="normal" if variacao_valor >= 0 else "inverse",
)
m4.metric("Período", f"{dias} dias")

# ── Seção 2 — Gráfico comparativo ────────────────────────────────────────────
data_inicio   = df["data_dt"].iloc[0]
data_inicio_s = data_inicio.strftime("%Y-%m-%d")
valor_inicial = float(df["valor"].iloc[0])

df["carteira_base100"] = df["valor"] / valor_inicial * 100

indices    = get_indices_renda_fixa()
cdi_diario = (1 + indices["cdi"] / 100) ** (1 / 252) - 1

datas_cdi  = pd.date_range(start=data_inicio, end=date.today(), freq="B")
cdi_vals   = [100 * (1 + cdi_diario) ** i for i in range(len(datas_cdi))]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df["data_dt"], y=df["carteira_base100"],
    name="Minha Carteira",
    line={"color": "#00A878", "width": 3},
))
fig.add_trace(go.Scatter(
    x=datas_cdi, y=cdi_vals,
    name="CDI",
    line={"color": "#4A90D9", "dash": "dot"},
))

try:
    ibov = yf.Ticker("^BVSP").history(start=data_inicio_s)
    if not ibov.empty:
        ibov.index = ibov.index.tz_localize(None)
        fig.add_trace(go.Scatter(
            x=ibov.index, y=ibov["Close"] / ibov["Close"].iloc[0] * 100,
            name="Ibovespa",
            line={"color": "#F5A623", "dash": "dash"},
        ))
except Exception:
    pass

try:
    ifix = yf.Ticker("IFIX.SA").history(start=data_inicio_s)
    if not ifix.empty:
        ifix.index = ifix.index.tz_localize(None)
        fig.add_trace(go.Scatter(
            x=ifix.index, y=ifix["Close"] / ifix["Close"].iloc[0] * 100,
            name="IFIX",
            line={"color": "#9B59B6", "dash": "dash"},
        ))
except Exception:
    pass

try:
    btc = yf.Ticker("BTC-USD").history(start=data_inicio_s)
    if not btc.empty:
        btc.index = btc.index.tz_localize(None)
        fig.add_trace(go.Scatter(
            x=btc.index, y=btc["Close"] / btc["Close"].iloc[0] * 100,
            name="Bitcoin",
            line={"color": "#F7931A", "dash": "dash"},
        ))
except Exception:
    pass

fig.update_layout(
    title="Performance Comparativa (Base 100)",
    xaxis_title="Data",
    yaxis_title="Base 100",
    hovermode="x unified",
    legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    "⚠️ Possíveis imprecisões no gráfico: "
    "(1) Dias sem acesso ao app nos últimos 30 dias são preenchidos com dados históricos do yfinance "
    "para Ações, FIIs e Alternativos conhecidos. "
    "(2) Renda Fixa usa a taxa contratada cadastrada para estimar o valor diário. "
    "(3) Alternativos sem ticker reconhecido usam o preço médio como estimativa. "
    "(4) Finais de semana e feriados usam o último preço disponível."
)

# ── Seção 3 — Tabela de Registros ─────────────────────────────────────────────
st.subheader("Registros")

cols_disp = ["data", "valor"]
if "rendimento_pct" in df.columns:
    cols_disp.append("rendimento_pct")

df_exibir = df[cols_disp].copy()
df_exibir["valor"] = df_exibir["valor"].apply(fmt_brl)
rename = {"data": "Data", "valor": "Patrimônio"}
if "rendimento_pct" in df_exibir.columns:
    df_exibir["rendimento_pct"] = df_exibir["rendimento_pct"].apply(lambda x: f"{x:+.2f}%")
    rename["rendimento_pct"] = "Rendimento (%)"
df_exibir = df_exibir.rename(columns=rename).sort_values("Data", ascending=False)

st.dataframe(df_exibir, use_container_width=True, hide_index=True)
st.caption(f"Total de {len(historico)} registros. Atualizado automaticamente ao abrir o app.")
