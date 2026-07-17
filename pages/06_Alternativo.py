import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.market_data import (
    detectar_casas_decimais,
    detectar_moeda,
    get_correlacao_com_ibov,
    get_cotacao_dolar,
    get_dados_alternativos,
    get_dados_ativo_alternativo,
)
from utils.portfolio import fmt_brl as _fmt_brl, get_ativos_por_classe

from utils.database import is_authenticated
if not is_authenticated():
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()


def _fmt_usd(v: float) -> str:
    return f"$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _cor_var(v: float) -> str:
    return "color: #00A878" if v >= 0 else "color: #FF4B4B"


def _metric_cor(col, label: str, texto: str, positivo: bool) -> None:
    cor  = "#00C896" if positivo else "#FF4B4B"
    seta = "↑" if positivo else "↓"
    col.markdown(
        f"<div style='font-size:13px;color:#888;margin-bottom:4px'>{label}</div>"
        f"<div style='font-size:24px;font-weight:700;color:{cor}'>{seta} {texto}</div>",
        unsafe_allow_html=True,
    )


st.title("Alternativos")

cotacao_dolar = get_cotacao_dolar()
ativos = get_ativos_por_classe("Alternativo")

if not ativos:
    st.info("Nenhum ativo alternativo cadastrado. Acesse 'Carteira' para adicionar.")
else:
    st.header("Minha Posição")

    for ativo in ativos:
        ticker = ativo["ticker"]
        moeda = detectar_moeda(ticker)
        casas = detectar_casas_decimais(ticker)
        dados = get_dados_ativo_alternativo(ticker)

        with st.expander(ticker, expanded=False):
            if dados is None:
                st.warning(f"Não foi possível obter dados para {ticker}.")
                continue

            preco_atual = dados["preco_atual"]
            preco_brl = preco_atual * cotacao_dolar if moeda == "USD" else preco_atual

            # ── Preço Atual ──
            c1, c2, c3, c4 = st.columns(4)
            if moeda == "USD":
                c1.metric("Preço (USD)", _fmt_usd(preco_atual),
                          delta=f"{dados['variacao_diaria_pct']:+.2f}%")
                c2.metric("Preço (BRL)", _fmt_brl(preco_brl),
                          delta=f"{dados['variacao_diaria_pct']:+.2f}%")
            else:
                c1.metric("Preço (BRL)", _fmt_brl(preco_atual),
                          delta=f"{dados['variacao_diaria_pct']:+.2f}%")
                c2.metric("Cotação (BRL)", "—")
            if dados["variacao_7d_pct"] is not None:
                _metric_cor(c3, "Variação 7 dias", f"{abs(dados['variacao_7d_pct']):.2f}%", dados["variacao_7d_pct"] >= 0)
            else:
                c3.metric("Variação 7 dias", "—")
            if dados["variacao_30d_pct"] is not None:
                _metric_cor(c4, "Variação 30 dias", f"{abs(dados['variacao_30d_pct']):.2f}%", dados["variacao_30d_pct"] >= 0)
            else:
                c4.metric("Variação 30 dias", "—")

            # ── Posição do usuário ──
            quantidade = ativo["quantidade"]
            preco_medio_orig = ativo["preco_medio"]
            valor_atual_brl = quantidade * preco_brl

            if moeda == "USD":
                preco_medio_usd = preco_medio_orig / cotacao_dolar
                resultado_usd = (preco_atual - preco_medio_usd) * quantidade
                resultado_brl = valor_atual_brl - quantidade * preco_medio_orig
                resultado_pct = ((preco_atual - preco_medio_usd) / preco_medio_usd) * 100

                st.divider()
                p1, p2, p3, p4 = st.columns(4)
                p1.metric("Quantidade", f"{quantidade:.{casas}f}")
                p2.metric("Valor Atual (BRL)", _fmt_brl(valor_atual_brl))
                _metric_cor(p3, "Resultado (BRL)", _fmt_brl(abs(resultado_brl)), resultado_brl >= 0)
                p4.metric("Preço Médio (BRL)", _fmt_brl(preco_medio_orig))
                st.caption("Preço cadastrado na carteira")

                r1, r2, r3 = st.columns(3)
                r1.metric("Preço Médio (USD)", _fmt_usd(preco_medio_usd))
                _metric_cor(r2, "Resultado (USD)", _fmt_usd(abs(resultado_usd)), resultado_usd >= 0)
                _metric_cor(r3, "Resultado (%)", f"{abs(resultado_pct):.2f}%", resultado_pct >= 0)
            else:
                resultado_brl = valor_atual_brl - quantidade * preco_medio_orig
                resultado_pct = ((preco_atual - preco_medio_orig) / preco_medio_orig) * 100

                st.divider()
                p1, p2, p3 = st.columns(3)
                p1.metric("Quantidade", f"{quantidade:.{casas}f}")
                p2.metric("Valor Atual (BRL)", _fmt_brl(valor_atual_brl))
                _metric_cor(p3, "Resultado (%)", f"{abs(resultado_pct):.2f}%", resultado_pct >= 0)

            # ── Histórico ──
            hist = dados["historico"].reset_index()
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist["Date"], y=hist["Close"],
                name=f"Preço ({'USD' if moeda == 'USD' else 'BRL'})",
                line={"color": "#00A878"}, yaxis="y1",
            ))
            fig.add_trace(go.Bar(
                x=hist["Date"], y=hist["Volume"],
                name="Volume", marker_color="rgba(150,150,150,0.3)", yaxis="y2",
            ))
            fig.update_layout(
                title=f"{ticker} - Histórico 12 meses ({'USD' if moeda == 'USD' else 'BRL'})",
                yaxis={"title": f"Preço ({'USD' if moeda == 'USD' else 'BRL'})", "side": "left"},
                yaxis2={"title": "Volume", "side": "right", "overlaying": "y", "showgrid": False},
                legend={"orientation": "h", "y": -0.15},
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)

            # ── Correlação com Ibovespa ──
            corr_dados = get_correlacao_com_ibov(ticker)
            if corr_dados:
                st.subheader("Correlação com Ibovespa")
                corr = corr_dados["correlacao"]
                st.metric(f"Correlação {ticker} × IBOV (12m)", f"{corr:.2f}")

                if corr > 0.7:
                    st.warning("Alta correlação: ativo e IBOV estão se movendo juntos. "
                               "Diversificação limitada entre os dois ativos.")
                elif corr >= 0.3:
                    st.info("Correlação moderada: ativo oferece diversificação "
                            "parcial em relação à bolsa brasileira.")
                else:
                    st.success("Baixa correlação: ativo está se comportando de forma "
                               "independente do Ibovespa. Boa diversificação.")

                hist_norm = corr_dados["historico_normalizado"].reset_index()
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=hist_norm["Date"], y=hist_norm["Ativo"],
                                          name=ticker, line={"color": "#F7931A"}))
                fig2.add_trace(go.Scatter(x=hist_norm["Date"], y=hist_norm["IBOV"],
                                          name="Ibovespa", line={"color": "#00A878"}))
                fig2.update_layout(title=f"Performance comparada - Base 100 (12m)",
                                   yaxis_title="Base 100", hovermode="x unified")
                st.plotly_chart(fig2, use_container_width=True)

                r1, r2 = st.columns(2)
                r1.metric(f"Performance {ticker} 12m", f"{corr_dados['perf_ativo_12m']:+.1f}%")
                r2.metric("Performance IBOV 12m", f"{corr_dados['perf_ibov_12m']:+.1f}%")

# ── Comparativo com Alternativos ─────────────────────────────────────────────
st.header("Comparativo com Outros Alternativos")
if not ativos:
    st.info("Cadastre um ativo alternativo para ver o comparativo de mercado.")
    alt = None
else:
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
            "Var. 30d %": f"{d['variacao_30d']:+.2f}%" if d["variacao_30d"] is not None else "—",
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
            x=serie.iloc[:, 0], y=serie.iloc[:, 1],
            name=nome, line={"color": _CORES.get(nome, "#FFFFFF")},
        ))
    fig3.update_layout(
        title="Performance comparativa 12 meses (base 100)",
        yaxis_title="Base 100",
        hovermode="x unified",
    )
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("GC=F (Ouro Futuro), SI=F (Prata Futuro), BTC-USD. Preços em USD.")
