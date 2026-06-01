import pandas as pd
import streamlit as st

from utils.market_data import get_indices_renda_fixa
from utils.portfolio import calcular_renda_fixa

_COR_STATUS = {
    "Vencido":        "color: #FF4B4B",
    "Vence em breve": "color: #FF8C00",
    "Vence em 1 ano": "color: #FFC107",
    "Longo prazo":    "color: #00A878",
    "Sem vencimento": "",
}

st.title("Renda Fixa")

indices = get_indices_renda_fixa()

st.header("Índices Atuais")
col1, col2, col3 = st.columns(3)
col1.metric("Selic", f"{indices['selic']:.2f}% a.a.")
col2.metric("CDI", f"{indices['cdi']:.2f}% a.a.")
col3.metric("IPCA", f"{indices['ipca']:.2f}% a.m.")
st.caption(
    f"Fonte: Banco Central do Brasil. Atualizado em {indices['data_atualizacao']}."
)

st.header("Minha Renda Fixa")
ativos = calcular_renda_fixa()

if not ativos:
    st.info("Nenhum ativo de renda fixa cadastrado. Acesse 'Carteira' para adicionar.")
else:
    linhas = []
    for a in ativos:
        linhas.append({
            "Ativo": a["ticker"],
            "Valor Investido": f"R$ {a['preco_medio']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "Vencimento": a.get("vencimento", "—"),
            "Dias para Vencer": a["dias_para_vencer"] if a["dias_para_vencer"] is not None else "—",
            "Status": a["status_vencimento"],
            "Rentabilidade Est. a.a.": f"{a['rentabilidade_estimada_anual']:.2f}%",
        })

    df = pd.DataFrame(linhas)

    def _estilo(row: pd.Series) -> list[str]:
        cor = _COR_STATUS.get(row["Status"], "")
        return [""] * (len(row) - 2) + [cor, ""]

    st.dataframe(
        df.style.apply(_estilo, axis=1),
        use_container_width=True,
        hide_index=True,
    )

    st.header("Alertas de Vencimento")
    alertas = False
    for a in ativos:
        if a["status_vencimento"] == "Vencido":
            st.error(f"{a['ticker']}: ativo vencido em {a.get('vencimento', '?')}. Verifique o resgate.")
            alertas = True
        elif a["status_vencimento"] == "Vence em breve":
            dias = a["dias_para_vencer"]
            st.warning(f"{a['ticker']}: vence em {dias} dia(s) ({a.get('vencimento', '?')}). Planeje o resgate ou reinvestimento.")
            alertas = True
    if not alertas:
        st.success("Nenhum vencimento próximo.")

    st.header("Comparativo com Benchmarks")
    st.write(
        f"Seu capital em renda fixa rende aproximadamente **{indices['selic']:.2f}%** ao ano. "
        f"Comparando: Selic **{indices['selic']:.2f}%**, "
        f"CDI **{indices['cdi']:.2f}%**, "
        f"IPCA **{indices['ipca']:.2f}%** ao mês."
    )
