import math

import streamlit as st

from utils.market_data import get_preco_atual
from utils.portfolio import fmt_brl, get_ativos


def _brl(v: float) -> str:
    """fmt_brl com $ escapado para uso em contextos markdown do Streamlit."""
    return fmt_brl(v).replace("$", r"\$")

st.title("Calculadora de Preço Médio")
st.caption("Simule aportes e descubra como otimizar seu preço médio.")

_CLASSES_CALC = ("Ações", "FIIs", "Alternativo")

ativos_carteira = [a for a in get_ativos() if a["classe"] in _CLASSES_CALC]
opcoes_ticker = [a["ticker"] for a in ativos_carteira] + ["Digitar manualmente"]

# ── Seção 1 — Simular Aporte ──────────────────────────────────────────────────
st.subheader("Simular Novo Aporte")

sel1 = st.selectbox(
    "Selecionar ativo da carteira",
    opcoes_ticker,
    key="calc_sel1",
)

if sel1 != "Digitar manualmente":
    ativo1 = next(a for a in ativos_carteira if a["ticker"] == sel1)
    qtd_atual_def   = int(ativo1["quantidade"])
    pm_atual_def    = float(ativo1["preco_medio"])
    preco_mkt       = get_preco_atual(sel1, ativo1["classe"])
    preco_compra_def = float(preco_mkt) if preco_mkt else pm_atual_def
else:
    qtd_atual_def    = 1
    pm_atual_def     = 0.01
    preco_compra_def = 0.01

col_a, col_b = st.columns(2)
with col_a:
    qtd_atual1   = st.number_input("Quantidade atual",        min_value=1,    step=1,     value=qtd_atual_def,    key="c1_qtd_atual")
    pm_atual1    = st.number_input("Preço médio atual (R$)",  min_value=0.01, format="%.2f", value=pm_atual_def,  key="c1_pm_atual")
with col_b:
    qtd_comprar1 = st.number_input("Quantidade a comprar",    min_value=1,    step=1,     value=1,                key="c1_qtd_comprar")
    preco_comp1  = st.number_input("Preço de compra (R$)",    min_value=0.01, format="%.2f", value=preco_compra_def, key="c1_preco_compra")

novo_pm1 = (qtd_atual1 * pm_atual1 + qtd_comprar1 * preco_comp1) / (qtd_atual1 + qtd_comprar1)
diff_pm1 = novo_pm1 - pm_atual1
var_pct1 = (diff_pm1 / pm_atual1) * 100

with st.container(border=True):
    m1, m2, m3 = st.columns(3)
    m1.metric("PM Atual",    fmt_brl(pm_atual1))
    delta_text = fmt_brl(abs(diff_pm1))
    if diff_pm1 < 0:
        m2.metric("Novo PM", fmt_brl(novo_pm1), delta=f"-{delta_text}", delta_color="normal")
    elif diff_pm1 > 0:
        m2.metric("Novo PM", fmt_brl(novo_pm1), delta=f"+{delta_text}", delta_color="inverse")
    else:
        m2.metric("Novo PM", fmt_brl(novo_pm1))
    m3.metric("Variação do PM", f"{var_pct1:+.2f}%")

    st.divider()

    v1, v2 = st.columns(2)
    v1.write(f"**Valor do aporte:** {_brl(qtd_comprar1 * preco_comp1)}")
    v2.write(f"**Nova quantidade total:** {qtd_atual1 + qtd_comprar1}")

    if novo_pm1 < pm_atual1:
        st.success(f"Aporte reduz seu preço médio em {_brl(abs(diff_pm1))} por cota.")
    elif novo_pm1 > pm_atual1:
        st.warning(f"Aporte aumenta seu preço médio em {_brl(abs(diff_pm1))} por cota.")
    else:
        st.info("Aporte não altera o preço médio.")

# ── Seção 2 — Atingir PM Alvo ─────────────────────────────────────────────────
st.divider()
st.subheader("Quantas Cotas para Atingir um PM Alvo?")

sel2 = st.selectbox(
    "Selecionar ativo da carteira",
    opcoes_ticker,
    key="calc_sel2",
)

if sel2 != "Digitar manualmente":
    ativo2 = next(a for a in ativos_carteira if a["ticker"] == sel2)
    qtd_atual2_def   = int(ativo2["quantidade"])
    pm_atual2_def    = float(ativo2["preco_medio"])
    preco_mkt2       = get_preco_atual(sel2, ativo2["classe"])
    preco_comp2_def  = float(preco_mkt2) if preco_mkt2 else pm_atual2_def
else:
    qtd_atual2_def   = 1
    pm_atual2_def    = 0.01
    preco_comp2_def  = 0.01

col_c, col_d = st.columns(2)
with col_c:
    qtd_atual2  = st.number_input("Quantidade atual",          min_value=1,    step=1,     value=qtd_atual2_def,   key="c2_qtd_atual")
    pm_atual2   = st.number_input("Preço médio atual (R$)",    min_value=0.01, format="%.2f", value=pm_atual2_def, key="c2_pm_atual")
with col_d:
    pm_alvo2    = st.number_input("PM alvo desejado (R$)",     min_value=0.01, format="%.2f", value=max(pm_atual2_def * 0.9, 0.01), key="c2_pm_alvo")
    preco_comp2 = st.number_input("Preço de compra (R$)",      min_value=0.01, format="%.2f", value=preco_comp2_def, key="c2_preco_compra")

if preco_comp2 >= pm_atual2:
    st.error(
        f"Impossível atingir um PM menor comprando acima do seu preço médio atual. "
        f"O preço de compra precisa ser menor que {_brl(pm_atual2)}."
    )
elif pm_alvo2 >= pm_atual2:
    st.warning("O PM alvo precisa ser menor que o PM atual para fazer sentido como estratégia de redução.")
else:
    qtd_nec2     = math.ceil(
        (pm_alvo2 * qtd_atual2 - pm_atual2 * qtd_atual2) / (preco_comp2 - pm_alvo2)
    )
    valor_total2 = qtd_nec2 * preco_comp2
    pm_result2   = (qtd_atual2 * pm_atual2 + qtd_nec2 * preco_comp2) / (qtd_atual2 + qtd_nec2)

    with st.container(border=True):
        r1, r2, r3 = st.columns(3)
        r1.metric("Cotas necessárias",   qtd_nec2)
        r2.metric("Valor total do aporte", fmt_brl(valor_total2))
        r3.metric(
            "PM resultante",
            fmt_brl(pm_result2),
            delta=f"-{fmt_brl(pm_atual2 - pm_result2)}",
            delta_color="normal",
        )

        st.divider()

        st.write(
            f"Comprando **{qtd_nec2} cotas** a "
            f"**{_brl(preco_comp2)}**, seu PM cairá de "
            f"**{_brl(pm_atual2)}** para "
            f"**{_brl(pm_result2)}**."
        )
        st.caption(
            f"O PM resultante é ligeiramente menor que o alvo "
            f"({_brl(pm_alvo2)}) pois não é possível comprar "
            f"frações de cota. O cálculo arredonda para cima "
            f"garantindo que o alvo seja atingido ou superado."
        )
