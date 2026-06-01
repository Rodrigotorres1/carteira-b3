import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.market_data import (
    get_correlacao_btc_ibov,
    get_cotacao_dolar,
    get_dados_alternativos,
    get_dados_bitcoin,
)
from utils.portfolio import get_ativos_por_classe


def _fmt_usd(v: float) -> str:
    return f"$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _cor_var(v: float) -> str:
    return "color: #00A878" if v >= 0 else "color: #FF4B4B"


st.title("Bitcoin")

dados = get_dados_bitcoin()
cotacao_dolar = get_cotacao_dolar()

if dados is None:
    st.error("Não foi possível obter dados do Bitcoin. Verifique sua conexão.")
    st.stop()

btc_carteira = get_ativos_por_classe("Alternativo")
btc_posicao = next((a for a in btc_carteira if a["ticker"] == "BTC-USD"), None)

if btc_posicao is None:
    st.info("Você não tem Bitcoin cadastrado na carteira. Acesse 'Carteira' para adicionar.")

preco_brl = dados["preco_atual_usd"] * cotacao_dolar

# ── Preço Atual ──────────────────────────────────────────────────────────────
st.header("Preço Atual")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Preço (USD)", _fmt_usd(dados["preco_atual_usd"]),
          delta=f"{dados['variacao_diaria_pct']:+.2f}%")
c2.metric("Preço (BRL)", _fmt_brl(preco_brl),
          delta=f"{dados['variacao_diaria_pct']:+.2f}%")
c3.metric("Variação 7 dias",
          f"{dados['variacao_7d_pct']:+.2f}%" if dados["variacao_7d_pct"] else "—")
c4.metric("Variação 30 dias",
          f"{dados['variacao_30d_pct']:+.2f}%" if dados["variacao_30d_pct"] else "—")

# ── Minha Posição ─────────────────────────────────────────────────────────────
if btc_posicao:
    st.header("Minha Posição")
    quantidade = btc_posicao["quantidade"]
    preco_medio_brl = btc_posicao["preco_medio"]
    preco_medio_usd = preco_medio_brl / cotacao_dolar
    valor_atual_brl = quantidade * preco_brl
    resultado_brl = valor_atual_brl - quantidade * preco_medio_brl
    resultado_usd = (dados["preco_atual_usd"] - preco_medio_usd) * quantidade
    resultado_pct = ((dados["preco_atual_usd"] - preco_medio_usd) / preco_medio_usd) * 100

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Quantidade", f"{quantidade:.8f} BTC")
    p2.metric("Valor Atual (BRL)", _fmt_brl(valor_atual_brl))
    p3.metric("Resultado (BRL)", _fmt_brl(resultado_brl),
              delta=f"{_fmt_brl(resultado_brl)}")
    p4.metric("Preço Médio (BRL)", _fmt_brl(preco_medio_brl))
    st.caption("Preço cadastrado na carteira")

    r1, r2, r3 = st.columns(3)
    r1.metric("Preço Médio (USD)", _fmt_usd(preco_medio_usd))
    r2.metric("Resultado (USD)", _fmt_usd(resultado_usd),
              delta=f"{_fmt_usd(resultado_usd)}")
    r3.metric("Resultado (%)", f"{resultado_pct:+.2f}%",
              delta=f"{resultado_pct:+.2f}%")

# ── Histórico de Preços ───────────────────────────────────────────────────────
st.header("Histórico de Preços")
hist = dados["historico"].reset_index()

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=hist["Date"], y=hist["Close"],
    name="Preço (USD)", line={"color": "#00A878"}, yaxis="y1",
))
fig.add_trace(go.Bar(
    x=hist["Date"], y=hist["Volume"],
    name="Volume", marker_color="rgba(150,150,150,0.3)", yaxis="y2",
))
fig.update_layout(
    title="Bitcoin - Histórico 12 meses (USD)",
    yaxis={"title": "Preço (USD)", "side": "left"},
    yaxis2={"title": "Volume", "side": "right", "overlaying": "y", "showgrid": False},
    legend={"orientation": "h", "y": -0.15},
    hovermode="x unified",
)
st.plotly_chart(fig, use_container_width=True)

# ── Correlação com Ibovespa ───────────────────────────────────────────────────
st.header("Correlação com Ibovespa")
corr_dados = get_correlacao_btc_ibov()

if corr_dados is None:
    st.warning("Não foi possível calcular a correlação com o Ibovespa.")
else:
    corr = corr_dados["correlacao"]
    st.metric("Correlação BTC × IBOV (12m)", f"{corr:.2f}")

    if corr > 0.7:
        st.warning("Alta correlação: BTC e IBOV estão se movendo juntos. "
                   "Diversificação limitada entre os dois ativos.")
    elif corr >= 0.3:
        st.info("Correlação moderada: BTC oferece diversificação "
                "parcial em relação à bolsa brasileira.")
    else:
        st.success("Baixa correlação: BTC está se comportando de forma "
                   "independente do Ibovespa. Boa diversificação.")

    hist_norm = corr_dados["historico_normalizado"].reset_index()
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=hist_norm["Date"], y=hist_norm["BTC"],
                              name="Bitcoin", line={"color": "#F7931A"}))
    fig2.add_trace(go.Scatter(x=hist_norm["Date"], y=hist_norm["IBOV"],
                              name="Ibovespa", line={"color": "#00A878"}))
    fig2.update_layout(title="Performance comparada - Base 100 (12 meses)",
                       yaxis_title="Base 100", hovermode="x unified")
    st.plotly_chart(fig2, use_container_width=True)

    r1, r2 = st.columns(2)
    r1.metric("Performance BTC 12m", f"{corr_dados['perf_btc_12m']:+.1f}%")
    r2.metric("Performance IBOV 12m", f"{corr_dados['perf_ibov_12m']:+.1f}%")

# ── Comparativo com Alternativos ──────────────────────────────────────────────
st.header("Comparativo com Outros Alternativos")
alt = get_dados_alternativos()

if alt is None:
    st.warning("Não foi possível obter dados comparativos.")
else:
    _CORES = {"Bitcoin": "#00A878", "Ouro": "#FFD700", "Prata": "#C0C0C0"}
    _COLS_VAR = ["Var. 1d %", "Var. 7d %", "Var. 30d %", "Var. 12m %"]

    linhas = []
    for nome, d in alt.items():
        linhas.append({
            "Ativo": nome,
            "Preço Atual (USD)": f"$ {d['preco_atual']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "Var. 1d %":  f"{d['variacao_1d']:+.2f}%"  if d["variacao_1d"]  is not None else "—",
            "Var. 7d %":  f"{d['variacao_7d']:+.2f}%"  if d["variacao_7d"]  is not None else "—",
            "Var. 30d %": f"{d['variacao_30d']:+.2f}%"  if d["variacao_30d"] is not None else "—",
            "Var. 12m %": f"{d['variacao_12m']:+.2f}%",
        })

    df_alt = pd.DataFrame(linhas)

    def _estilo_var(row: pd.Series) -> list[str]:
        estilos = ["", ""]
        for col in _COLS_VAR:
            val_str = row.get(col, "—")
            try:
                val = float(val_str.replace("%", "").replace("+", ""))
                estilos.append(_cor_var(val))
            except Exception:
                estilos.append("")
        return estilos

    st.dataframe(
        df_alt.style.apply(_estilo_var, axis=1),
        use_container_width=True,
        hide_index=True,
    )

    fig3 = go.Figure()
    for nome, d in alt.items():
        serie = d["historico_normalizado"].reset_index()
        fig3.add_trace(go.Scatter(
            x=serie.iloc[:, 0],
            y=serie.iloc[:, 1],
            name=nome,
            line={"color": _CORES.get(nome, "#FFFFFF")},
        ))
    fig3.update_layout(
        title="Performance comparativa 12 meses (base 100)",
        yaxis_title="Base 100",
        hovermode="x unified",
    )
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("GC=F (Ouro Futuro), SI=F (Prata Futuro), BTC-USD. Preços em USD.")
