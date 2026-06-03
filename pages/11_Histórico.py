from datetime import date, timedelta

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

st.title("Rentabilidade e Evolução Patrimonial")
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

# ── Prepara DataFrame base ────────────────────────────────────────────────────
df_base = pd.DataFrame(historico)
df_base["data_dt"] = pd.to_datetime(df_base["data"], format="%d/%m/%Y")
df_base["valor"]   = df_base["valor"].astype(float)
df_base = df_base.sort_values("data_dt").reset_index(drop=True)

_HOJE = date.today()

_COR_BENCHMARK = {
    "CDI":      "#4A90D9",
    "Ibovespa": "#F5A623",
    "IFIX":     "#9B59B6",
    "Bitcoin":  "#F7931A",
}


def _filtrar(df: pd.DataFrame, periodo: str) -> pd.DataFrame:
    hoje_ts = pd.Timestamp(_HOJE)
    if periodo == "No ano":
        corte = pd.Timestamp(f"{_HOJE.year}-01-01")
    elif periodo == "6 meses":
        corte = hoje_ts - pd.DateOffset(days=180)
    elif periodo == "3 meses":
        corte = hoje_ts - pd.DateOffset(days=90)
    elif periodo == "1 mês":
        corte = hoje_ts - pd.DateOffset(days=30)
    else:
        return df
    return df[df["data_dt"] >= corte].reset_index(drop=True)


def _buscar_benchmark_pct(nome: str, data_inicio: pd.Timestamp, indices: dict) -> tuple:
    """Retorna (datas, valores_pct) do benchmark. None se falhar."""
    inicio_s = data_inicio.strftime("%Y-%m-%d")
    try:
        if nome == "CDI":
            cdi_diario = (1 + indices["cdi"] / 100) ** (1 / 252) - 1
            datas = pd.date_range(start=data_inicio, end=_HOJE, freq="B")
            vals  = [(1 + cdi_diario) ** i * 100 - 100 for i in range(len(datas))]
            return datas, vals
        tickers = {"Ibovespa": "^BVSP", "IFIX": "IFIX.SA", "Bitcoin": "BTC-USD"}
        t = tickers[nome]
        hist = yf.Ticker(t).history(start=inicio_s)
        if hist.empty:
            return None, None
        hist.index = hist.index.tz_localize(None)
        pct = (hist["Close"] / hist["Close"].iloc[0] - 1) * 100
        return hist.index, pct.values
    except Exception:
        return None, None


tab_rent, tab_patr = st.tabs(["Rentabilidade", "Patrimônio"])

indices = get_indices_renda_fixa()

# ── Tab: Rentabilidade ────────────────────────────────────────────────────────
with tab_rent:
    c1, c2 = st.columns(2)
    with c1:
        periodo_r = st.selectbox(
            "Período", ["Máximo", "No ano", "6 meses", "3 meses", "1 mês"], key="periodo_r"
        )
    with c2:
        benchmark = st.selectbox(
            "Comparar com", ["Nenhum", "CDI", "Ibovespa", "IFIX", "Bitcoin"], key="bench_r"
        )

    df_r = _filtrar(df_base, periodo_r)

    if len(df_r) < 2:
        st.info("Sem dados suficientes para o período selecionado.")
    else:
        v0 = float(df_r["valor"].iloc[0])
        v1 = float(df_r["valor"].iloc[-1])
        rendimento_rs  = v1 - v0
        rendimento_pct = (rendimento_rs / v0 * 100) if v0 > 0 else 0.0
        data_ini_str   = df_r["data_dt"].iloc[0].strftime("%d/%m/%Y")
        data_fim_str   = df_r["data_dt"].iloc[-1].strftime("%d/%m/%Y")

        # ── Métricas estilo Rico ──────────────────────────────────────────────
        seta   = "↑" if rendimento_pct >= 0 else "↓"
        cor_pct = "#4CAF50" if rendimento_pct >= 0 else "#F44336"

        bench_html = ""
        bench_pct_val = None
        if benchmark != "Nenhum":
            datas_b, vals_b = _buscar_benchmark_pct(benchmark, df_r["data_dt"].iloc[0], indices)
            if vals_b is not None and len(vals_b) > 0:
                bench_pct_val = float(vals_b[-1])
                cor_b = "#4CAF50" if bench_pct_val >= 0 else "#F44336"
                bench_html = (
                    f"&nbsp;&nbsp;<span style='color:#7EB8F7;font-size:1rem;'>●</span>"
                    f"&nbsp;<span style='color:#AAAAAA;font-size:0.95rem;'>{benchmark}"
                    f" <span style='color:{cor_b};'>{bench_pct_val:+.2f}%</span></span>"
                )

        st.markdown(
            f"<div style='padding: 8px 0 4px 0;'>"
            f"<span style='color:#FFFFFF;font-size:2rem;font-weight:700;'>"
            f"{fmt_brl(rendimento_rs)}</span>"
            f"&nbsp;&nbsp;"
            f"<span style='color:{cor_pct};font-size:1.2rem;font-weight:600;'>"
            f"{seta} {abs(rendimento_pct):.2f}%</span>"
            f"{bench_html}"
            f"</div>",
            unsafe_allow_html=True,
        )

        # ── Gráfico estilo Rico ───────────────────────────────────────────────
        df_r = df_r.copy()
        df_r["rent_pct"] = (df_r["valor"] / v0 - 1) * 100

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_r["data_dt"], y=df_r["rent_pct"],
            showlegend=False,
            fill="tozeroy",
            fillcolor="rgba(255, 255, 255, 0.10)",
            line={"color": "#FFFFFF", "width": 2},
            hovertemplate="%{y:.2f}%<extra></extra>",
        ))

        if benchmark != "Nenhum" and bench_pct_val is not None:
            fig.add_trace(go.Scatter(
                x=datas_b, y=vals_b,
                showlegend=False,
                line={"color": "#7EB8F7", "dash": "dot", "width": 1.5},
                hovertemplate=f"%{{y:.2f}}%<extra>{benchmark}</extra>",
            ))

        fig.update_layout(
            hovermode="x unified",
            showlegend=False,
            plot_bgcolor="#0D1B3E",
            paper_bgcolor="rgba(0,0,0,0)",
            margin={"t": 10, "b": 10, "l": 10, "r": 10},
            xaxis={
                "showgrid": False,
                "zeroline": False,
                "tickfont": {"color": "rgba(255,255,255,0.4)"},
                "linecolor": "rgba(255,255,255,0.1)",
            },
            yaxis={
                "showgrid": False,
                "zeroline": False,
                "tickformat": ".1f",
                "ticksuffix": "%",
                "tickfont": {"color": "rgba(255,255,255,0.4)"},
                "linecolor": "rgba(255,255,255,0.1)",
            },
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── Detalhes da rentabilidade ─────────────────────────────────────────
        st.markdown("### Detalhes da rentabilidade")
        st.divider()

        cor_rend = "#4CAF50" if rendimento_rs >= 0 else "#F44336"
        seta_rend = "↑" if rendimento_rs >= 0 else "↓"

        col_a, col_b = st.columns([3, 1])
        col_a.write("Rendimento")
        col_b.markdown(
            f"<span style='color:{cor_rend};font-weight:600;'>"
            f"{seta_rend} {fmt_brl(abs(rendimento_rs))}</span>",
            unsafe_allow_html=True,
        )
        st.divider()

        col_c, col_d = st.columns([3, 1])
        col_c.write("Data de referência")
        col_d.write(f"De {data_ini_str} Até {data_fim_str}")
        st.divider()

        st.caption(
            "⚠️ Possíveis imprecisões: dias sem acesso ao app são preenchidos com dados históricos do yfinance "
            "para Ações/FIIs/Alternativos. Renda Fixa usa a taxa contratada. "
            "Alternativos sem ticker reconhecido usam o preço médio. Finais de semana usam o último preço disponível."
        )

# ── Tab: Patrimônio ───────────────────────────────────────────────────────────
with tab_patr:
    periodo_p = st.selectbox(
        "Período", ["Máximo", "No ano", "6 meses", "3 meses", "1 mês"], key="periodo_p"
    )

    df_p = _filtrar(df_base, periodo_p)

    if len(df_p) < 2:
        st.info("Sem dados suficientes para o período selecionado.")
    else:
        vp0 = float(df_p["valor"].iloc[0])
        vp1 = float(df_p["valor"].iloc[-1])
        var_p = vp1 - vp0

        m1, m2, m3 = st.columns(3)
        m1.metric("Patrimônio Atual",    fmt_brl(vp1))
        m2.metric("Patrimônio Inicial",  fmt_brl(vp0))
        m3.metric(
            "Variação", fmt_brl(var_p),
            delta=fmt_brl(var_p),
            delta_color="normal" if var_p >= 0 else "inverse",
        )

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df_p["data_dt"], y=df_p["valor"],
            name="Patrimônio",
            fill="tozeroy",
            fillcolor="rgba(0, 168, 120, 0.15)",
            line={"color": "#00A878", "width": 2},
            hovertemplate="R$ %{y:,.2f}<extra></extra>",
        ))
        fig2.update_layout(
            yaxis_title="Valor (R$)",
            xaxis_title="",
            hovermode="x unified",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis={"tickprefix": "R$ "},
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Tabela de registros
    st.subheader("Registros")
    cols_tab = ["data", "valor"]
    if "rendimento_pct" in df_base.columns:
        cols_tab.append("rendimento_pct")
    df_tab = df_base[cols_tab].copy().sort_values("data", ascending=False)
    df_tab["valor"] = df_tab["valor"].apply(fmt_brl)
    rename = {"data": "Data", "valor": "Patrimônio"}
    if "rendimento_pct" in df_tab.columns:
        df_tab["rendimento_pct"] = df_tab["rendimento_pct"].apply(lambda x: f"{x:+.2f}%")
        rename["rendimento_pct"] = "Rendimento (%)"
    st.dataframe(df_tab.rename(columns=rename), use_container_width=True, hide_index=True)
    st.caption(f"Total de {len(historico)} registros. Atualizado automaticamente ao abrir o app.")
