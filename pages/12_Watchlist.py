import streamlit as st

from utils.market_data import get_preco_atual
from utils.portfolio import fmt_brl, get_watchlist, remove_watchlist

st.title("Watchlist")
st.caption("Ativos que você está monitorando antes de investir.")

watchlist = get_watchlist()

if not watchlist:
    st.info("Sua watchlist está vazia. Adicione ativos pelo Radar ou pelas Sugestões.")
    st.stop()

alertas = []

for item in watchlist:
    ticker         = item["ticker"]
    classe         = item["classe"]
    preco_na_ad    = item.get("preco_na_adicao")
    preco_ent_alvo = item.get("preco_entrada_alvo")
    motivo         = item.get("motivo", "")
    data_adicao    = item.get("data_adicao", "—")

    preco_atual = get_preco_atual(ticker, classe)

    var = None
    if preco_na_ad and preco_atual:
        var = ((preco_atual - preco_na_ad) / preco_na_ad) * 100

    dist = None
    if preco_ent_alvo and preco_atual:
        dist = ((preco_atual - preco_ent_alvo) / preco_ent_alvo) * 100

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown(f"**{ticker}**")
            st.caption(classe)
            st.caption(f"Adicionado: {data_adicao}")

        with c2:
            st.write(fmt_brl(preco_atual) if preco_atual else "—")
            if preco_na_ad:
                st.caption(f"Na adição: {fmt_brl(preco_na_ad)}")

        with c3:
            if var is not None:
                st.metric(
                    "Variação",
                    f"{var:+.1f}%",
                    delta=f"{var:+.1f}%",
                    delta_color="normal" if var < 0 else "inverse",
                )
            else:
                st.caption("Variação indisponível")

        with c4:
            if dist is not None:
                if dist <= 0:
                    st.success("No preço alvo!")
                elif dist <= 5:
                    st.warning(f"A {dist:.1f}% do alvo")
                else:
                    st.info(f"{dist:.1f}% acima do alvo")
            else:
                st.caption("Sem alvo definido")

        if motivo:
            st.caption(f"Motivo: {motivo}")

        col_rem, col_add = st.columns([1, 4])
        with col_rem:
            if st.button("Remover", key=f"rem_watch_{ticker}"):
                remove_watchlist(ticker)
                st.rerun()
        with col_add:
            if st.button("Mover para carteira", key=f"move_watch_{ticker}"):
                st.session_state["mover_para_carteira"] = ticker
                st.switch_page("pages/01_Carteira.py")

        # Acumula alertas
        if dist is not None and dist <= 2:
            alertas.append(f"{ticker} atingiu o preço de entrada alvo!")
        if var is not None and var <= -10:
            alertas.append(f"{ticker} caiu {abs(var):.1f}% desde que você adicionou. Pode ser oportunidade.")

# ── Alertas ───────────────────────────────────────────────────────────────────
st.subheader("Alertas")
if alertas:
    for msg in alertas:
        st.warning(f"⚠️ {msg}")
else:
    st.success("Nenhum alerta no momento.")
