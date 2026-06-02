import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.market_data import get_indices_renda_fixa
from utils.portfolio import calcular_carteira, fmt_brl


def _brl(v: float) -> str:
    """fmt_brl com $ escapado para contextos markdown do Streamlit."""
    return fmt_brl(v).replace("$", r"\$")


st.title("Simulador de Aportes")
st.caption("Projete o crescimento do seu patrimônio com aportes regulares.")

# ── Parâmetros ────────────────────────────────────────────────────────────────
st.subheader("Configurar Simulação")

carteira = calcular_carteira()
patrimonio_carteira = sum(a["valor_atual"] for a in carteira) if carteira else 0.0

indices = get_indices_renda_fixa()
cdi = indices["cdi"]

col_esq, col_dir = st.columns(2)

with col_esq:
    patrimonio_inicial = st.number_input(
        "Patrimônio atual (R$)", min_value=0.0, format="%.2f", value=float(patrimonio_carteira),
    )
    aporte_mensal = st.number_input(
        "Aporte mensal (R$)", min_value=0.0, format="%.2f", value=500.0,
    )
    anos = st.number_input("Período (anos)", min_value=1, max_value=50, step=1, value=10)

with col_dir:
    st.subheader("Rentabilidade esperada")
    perfil_retorno = st.selectbox(
        "Perfil de retorno",
        ["Conservador (CDI)", "Moderado (CDI + 2%)", "Arrojado (CDI + 5%)", "Personalizado"],
    )

    if perfil_retorno == "Personalizado":
        taxa_anual = st.number_input(
            "Taxa anual esperada (%)", min_value=0.1, max_value=50.0, format="%.1f", value=12.0,
        )
    elif perfil_retorno == "Conservador (CDI)":
        taxa_anual = cdi
    elif perfil_retorno == "Moderado (CDI + 2%)":
        taxa_anual = cdi + 2
    else:  # Arrojado
        taxa_anual = cdi + 5

    taxa_mensal = ((1 + taxa_anual / 100) ** (1 / 12) - 1) * 100
    st.info(f"Taxa anual: {taxa_anual:.1f}% | Taxa mensal: {taxa_mensal:.2f}%")

# ── Meta ──────────────────────────────────────────────────────────────────────
st.subheader("Definir Meta (opcional)")

tipo_meta = st.radio(
    "Tipo de meta",
    ["Patrimônio alvo (R$)", "Renda passiva mensal (R$)", "Sem meta definida"],
    horizontal=True,
)

meta_patrimonio = None
if tipo_meta == "Patrimônio alvo (R$)":
    meta_patrimonio = st.number_input(
        "Patrimônio desejado (R$)", min_value=0.01, format="%.2f", value=1_000_000.0,
    )
elif tipo_meta == "Renda passiva mensal (R$)":
    renda_desejada = st.number_input(
        "Renda mensal desejada (R$)", min_value=0.01, format="%.2f", value=5_000.0,
    )
    taxa_retirada = st.number_input(
        "Taxa de retirada segura (% ao ano)", min_value=0.1, max_value=20.0,
        format="%.1f", value=4.0,
        help="Regra dos 4%: você pode retirar 4% do patrimônio por ano sem esgotá-lo. "
             "Ajuste conforme sua estratégia.",
    )
    meta_patrimonio = (renda_desejada * 12) / (taxa_retirada / 100)
    st.caption(f"Patrimônio necessário: {_brl(meta_patrimonio)}")

# ── Simulação ─────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Projeção")

taxa_m = (1 + taxa_anual / 100) ** (1 / 12) - 1
total_meses = int(anos) * 12

historico_anual = []
patrimonio = patrimonio_inicial
mes_meta = None

for mes in range(1, total_meses + 1):
    patrimonio = patrimonio * (1 + taxa_m) + aporte_mensal
    aportes_acum = patrimonio_inicial + aporte_mensal * mes
    juros_acum = patrimonio - aportes_acum

    if meta_patrimonio and mes_meta is None and patrimonio >= meta_patrimonio:
        mes_meta = mes

    if mes % 12 == 0:
        historico_anual.append({
            "Ano": mes // 12,
            "Patrimônio": patrimonio,
            "Aportes acumulados": aportes_acum,
            "Juros acumulados": juros_acum,
        })

patrimonio_final = historico_anual[-1]["Patrimônio"]
total_aportado = patrimonio_inicial + aporte_mensal * total_meses
total_juros = patrimonio_final - total_aportado

m1, m2, m3 = st.columns(3)
m1.metric("Patrimônio Final", fmt_brl(patrimonio_final))
m2.metric("Total Aportado", fmt_brl(total_aportado))
m3.metric(
    "Juros Gerados",
    fmt_brl(total_juros),
    delta=f"{(total_juros / total_aportado * 100):.1f}% do total aportado" if total_aportado > 0 else None,
    delta_color="normal",
)

if meta_patrimonio:
    if mes_meta is not None:
        anos_meta = mes_meta / 12
        st.success(f"Meta de {_brl(meta_patrimonio)} atingida em {anos_meta:.1f} anos.")
    else:
        patrimonio_iter = patrimonio_inicial
        mes_extra = total_meses
        while patrimonio_iter < meta_patrimonio and mes_extra < total_meses + 600:
            patrimonio_iter = patrimonio_iter * (1 + taxa_m) + aporte_mensal
            mes_extra += 1
        anos_extras = (mes_extra - total_meses) / 12
        st.warning(
            f"Meta de {_brl(meta_patrimonio)} não atingida no período simulado. "
            f"Seria necessário aportar por mais {anos_extras:.1f} anos."
        )

df_hist = pd.DataFrame(historico_anual)
fig = go.Figure()
fig.add_trace(go.Bar(
    x=df_hist["Ano"], y=df_hist["Aportes acumulados"],
    name="Aportes acumulados", marker_color="#4C9BE8",
))
fig.add_trace(go.Bar(
    x=df_hist["Ano"], y=df_hist["Juros acumulados"],
    name="Juros acumulados", marker_color="#00A878",
))
fig.update_layout(
    title="Evolução Patrimonial",
    xaxis_title="Ano",
    yaxis_title="Valor (R$)",
    barmode="stack",
    hovermode="x unified",
    legend={"orientation": "h", "y": -0.15},
)
st.plotly_chart(fig, use_container_width=True)

# ── Comparativo de Estratégias ────────────────────────────────────────────────
st.subheader("Comparativo de Estratégias")

_ESTRATEGIAS = {
    "Conservador (CDI)": cdi,
    "Moderado (CDI + 2%)": cdi + 2,
    "Arrojado (CDI + 5%)": cdi + 5,
}

linhas_comp = []
for nome, taxa in _ESTRATEGIAS.items():
    tm = (1 + taxa / 100) ** (1 / 12) - 1
    p = patrimonio_inicial
    for _ in range(total_meses):
        p = p * (1 + tm) + aporte_mensal
    juros = p - total_aportado
    multiplicador = p / total_aportado if total_aportado > 0 else 0
    linhas_comp.append({
        "Estratégia": nome,
        "Taxa a.a.": f"{taxa:.1f}%",
        "Patrimônio Final": fmt_brl(p),
        "Total Juros": fmt_brl(juros),
        "Multiplicador": f"{multiplicador:.2f}x",
        "_selecionada": nome == perfil_retorno,
    })

df_comp = pd.DataFrame(linhas_comp)
df_exibir = df_comp.drop(columns=["_selecionada"]).copy()


def highlight_selecionada(row: pd.Series) -> list[str]:
    selecionada = df_comp.loc[row.name, "_selecionada"] if row.name in df_comp.index else False
    if selecionada:
        return ["background-color: #1a3a2a"] * len(row)
    return [""] * len(row)


st.dataframe(
    df_exibir.style.apply(highlight_selecionada, axis=1),
    use_container_width=True,
    hide_index=True,
)
