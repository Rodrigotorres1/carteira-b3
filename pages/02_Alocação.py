import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.portfolio import calcular_alocacao_atual, calcular_carteira
from utils.profile import get_alocacao_alvo, get_profile

CLASSES_PADRAO = ["Ações", "FIIs", "Renda Fixa", "Alternativo"]

_CLASSE_PARA_CHAVE = {
    "Ações": "acoes",
    "FIIs": "fiis",
    "Renda Fixa": "renda_fixa",
    "Alternativo": "alternativos",
}

st.title("Alocação da Carteira")

carteira = calcular_carteira()

if not carteira:
    st.info("Nenhum ativo cadastrado. Acesse 'Minha Carteira' para adicionar ativos.")
    st.stop()

alocacao_atual = calcular_alocacao_atual()
alocacao_alvo_raw = get_alocacao_alvo()
alocacao_alvo = {
    "Ações": alocacao_alvo_raw.get("acoes", 0),
    "FIIs": alocacao_alvo_raw.get("fiis", 0),
    "Renda Fixa": alocacao_alvo_raw.get("renda_fixa", 0),
    "Alternativo": alocacao_alvo_raw.get("alternativos", 0),
}

valor_total = sum(a["valor_atual"] for a in carteira)
num_ativos = len(carteira)
perfil = get_profile()

st.header("Visão Geral")
col1, col2, col3 = st.columns(3)
col1.metric("Valor total", f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col2.metric("Número de ativos", num_ativos)
col3.metric("Perfil do investidor", perfil.capitalize())

st.header("Alocação Atual vs. Alvo")


def _cor_diferenca(diff: float) -> str:
    """Retorna cor CSS conforme distância da alocação alvo."""
    diff_abs = abs(diff)
    if diff_abs <= 3:
        return "color: #00A878"
    if diff_abs <= 8:
        return "color: #FFC107"
    return "color: #FF4B4B"


linhas = []
for classe in CLASSES_PADRAO:
    atual = alocacao_atual.get(classe, 0.0)
    alvo = alocacao_alvo.get(classe, 0.0)
    linhas.append({
        "Classe": classe,
        "Atual (%)": round(atual, 1),
        "Alvo (%)": round(alvo, 1),
        "Diferença (%)": round(atual - alvo, 1),
    })

df = pd.DataFrame(linhas)


def _estilo_linha(row: pd.Series) -> list[str]:
    cor = _cor_diferenca(row["Diferença (%)"])
    return ["", "", "", cor]


st.dataframe(
    df.style.apply(_estilo_linha, axis=1),
    use_container_width=True,
    hide_index=True,
)

st.header("Alertas de Rebalanceamento")
alertas = False
for _, row in df.iterrows():
    diff_abs = abs(row["Diferença (%)"])
    if diff_abs > 8:
        st.error(
            f"{row['Classe']}: diferença de {row['Diferença (%)']:+.1f}% em relação ao alvo "
            f"({row['Atual (%)']:.1f}% atual vs {row['Alvo (%)']:.1f}% alvo)."
        )
        alertas = True
    elif diff_abs > 3:
        st.warning(
            f"{row['Classe']}: diferença de {row['Diferença (%)']:+.1f}% em relação ao alvo "
            f"({row['Atual (%)']:.1f}% atual vs {row['Alvo (%)']:.1f}% alvo)."
        )
        alertas = True

if not alertas:
    st.success("Carteira equilibrada — todas as classes dentro da faixa de 3% do alvo.")

st.header("Gráfico")
col_esq, col_dir = st.columns(2)

with col_esq:
    fig_atual = go.Figure(go.Pie(
        labels=list(alocacao_atual.keys()),
        values=list(alocacao_atual.values()),
        hole=0.35,
        textinfo="label+percent",
    ))
    fig_atual.update_layout(title_text="Alocação Atual", showlegend=False)
    st.plotly_chart(fig_atual, use_container_width=True)

with col_dir:
    fig_alvo = go.Figure(go.Pie(
        labels=list(alocacao_alvo.keys()),
        values=list(alocacao_alvo.values()),
        hole=0.35,
        textinfo="label+percent",
    ))
    fig_alvo.update_layout(title_text="Alocação Alvo", showlegend=False)
    st.plotly_chart(fig_alvo, use_container_width=True)
