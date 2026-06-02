import pandas as pd
import streamlit as st

from utils.email import enviar_email_vencimentos
from utils.market_data import get_indices_renda_fixa
from utils.portfolio import calcular_renda_fixa, fmt_brl as _brl

from utils.database import is_authenticated
if not is_authenticated():
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

def _cor_status(status: str) -> str:
    if status == "Vencido":
        return "color: #FF4B4B"
    if "dias" in status:
        return "color: #FF8C00"
    if "meses" in status:
        return "color: #FFC107"
    if "ano" in status:
        return "color: #00A878"
    return ""


def _taxa_label(a: dict) -> str:
    tipo = a.get("tipo_rentabilidade")
    taxa = a.get("taxa")
    if not tipo or taxa is None:
        return "—"
    if tipo == "Prefixado":
        return f"Prefixado {taxa:.2f}% a.a."
    if tipo == "% do CDI":
        return f"{taxa:.0f}% do CDI"
    if tipo == "CDI+":
        return f"CDI + {taxa:.2f}%"
    if tipo == "IPCA+":
        return f"IPCA + {taxa:.2f}%"
    return "—"


st.title("Renda Fixa")

ativos = calcular_renda_fixa()
indices = get_indices_renda_fixa()

# ── Notificações por Email ────────────────────────────────────────────────────
user_email = st.session_state.get("user").email if st.session_state.get("user") else None

ativos_vencidos  = [a for a in ativos if a.get("status_vencimento") == "Vencido"]
ativos_vencendo  = [a for a in ativos if "dias" in a.get("status_vencimento", "") or "meses" in a.get("status_vencimento", "")]

if user_email and (ativos_vencidos or ativos_vencendo):
    st.subheader("Notificações")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(f"Enviar resumo de vencimentos para **{user_email}**")
    with col2:
        if st.button("Enviar por email", use_container_width=True, type="primary"):
            with st.spinner("Enviando email..."):
                result = enviar_email_vencimentos(user_email, ativos_vencendo, ativos_vencidos)
            if result["success"]:
                st.success("Email enviado com sucesso! Verifique sua caixa de entrada.")
            else:
                st.error(f"Erro ao enviar: {result['error']}")

# ── Alertas de Vencimento (topo) ──────────────────────────────────────────────
alertas_criticos = [a for a in ativos if a["status_vencimento"] == "Vencido" or "dias" in a["status_vencimento"]]
if alertas_criticos:
    st.header("Alertas de Vencimento")
    for a in alertas_criticos:
        if a["status_vencimento"] == "Vencido":
            st.error(f"{a['ticker']}: ativo vencido em {a.get('vencimento', '?')}. Verifique o resgate.")
        else:
            st.warning(
                f"{a['ticker']}: vence em {a['dias_para_vencer']} dia(s) "
                f"({a.get('vencimento', '?')}). Planeje o resgate ou reinvestimento."
            )

# ── Índices Atuais ────────────────────────────────────────────────────────────
st.header("Índices Atuais")
col1, col2, col3 = st.columns(3)
col1.metric("Selic", f"{indices['selic']:.2f}% a.a.")
col2.metric("CDI", f"{indices['cdi']:.2f}% a.a.")
col3.metric("IPCA", f"{indices['ipca']:.2f}% a.m.")
st.caption(
    f"Fonte: Banco Central do Brasil. Atualizado em {indices['data_atualizacao']}."
)

# ── Minha Renda Fixa ──────────────────────────────────────────────────────────
st.header("Minha Renda Fixa")

if not ativos:
    st.info("Nenhum ativo de renda fixa cadastrado. Acesse 'Carteira' para adicionar.")
else:
    for a in ativos:
        with st.expander(a["ticker"], expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Valor Investido", _brl(a["preco_medio"]))
            c2.metric(
                "Valor Atual Estimado",
                _brl(a["valor_atual_estimado"]),
                delta=f"{_brl(a['rendimento_acumulado_rs'])}" if a["rendimento_acumulado_rs"] else None,
            )
            c3.metric(
                "Rentabilidade Acumulada",
                f"{a['rendimento_acumulado_pct']:.2f}%" if a["rendimento_acumulado_pct"] is not None else "—",
            )
            c4.metric(
                "Valor no Vencimento",
                _brl(a["valor_no_vencimento"]) if a["valor_no_vencimento"] else "—",
            )

            st.divider()

            i1, i2, i3 = st.columns(3)
            i1.write(f"**Taxa contratada**\n\n{_taxa_label(a)}")
            i2.write(f"**Data de aplicação**\n\n{a.get('data_aplicacao', '—')}")
            venc_txt = a.get("vencimento", "—")
            dias_pv = a["dias_para_vencer"]
            i3.write(
                f"**Vencimento**\n\n{venc_txt}"
                + (f" ({dias_pv} dias)" if dias_pv is not None and dias_pv > 0 else "")
            )

            dias_aplic = a["dias_aplicado"]
            if dias_aplic is not None and dias_pv is not None and dias_pv > 0:
                dias_total = dias_aplic + dias_pv
                progresso = min(dias_aplic / dias_total, 1.0)
                st.progress(progresso)
                st.caption(f"{dias_aplic} dias aplicado de {dias_total} dias totais.")

    st.subheader("Resumo")
    linhas = []
    for a in ativos:
        linhas.append({
            "Ativo": a["ticker"],
            "Valor Investido": _brl(a["preco_medio"]),
            "Valor Atual Est.": _brl(a["valor_atual_estimado"]),
            "Rend. Acum. %": f"{a['rendimento_acumulado_pct']:.2f}%" if a["rendimento_acumulado_pct"] is not None else "—",
            "Taxa Efetiva a.a.": f"{a['taxa_efetiva_anual']:.2f}%",
            "Vencimento": a.get("vencimento", "—"),
            "Dias para Vencer": a["dias_para_vencer"] if a["dias_para_vencer"] is not None else "—",
            "Status": a["status_vencimento"],
        })

    df = pd.DataFrame(linhas)

    def _estilo(row: pd.Series) -> list[str]:
        cor = _cor_status(row["Status"])
        return [""] * (len(row) - 1) + [cor]

    st.dataframe(df.style.apply(_estilo, axis=1), use_container_width=True, hide_index=True)

    if not alertas_criticos:
        st.success("Nenhum vencimento próximo.")

    st.header("Comparativo com Benchmarks")
    st.write(
        f"Seu capital em renda fixa rende aproximadamente **{indices['selic']:.2f}%** ao ano. "
        f"Comparando: Selic **{indices['selic']:.2f}%**, "
        f"CDI **{indices['cdi']:.2f}%**, "
        f"IPCA **{indices['ipca']:.2f}%** ao mês."
    )
