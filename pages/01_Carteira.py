from datetime import date

import pandas as pd
import streamlit as st

from utils.database import deletar_compra, get_compras, salvar_compra
from utils.market_data import get_preco_atual
from utils.portfolio import add_ativo, ativo_existe, editar_ativo, fmt_brl, get_ativos, get_watchlist, remove_ativo, remove_watchlist

from utils.database import is_authenticated
if not is_authenticated():
    st.warning("Você precisa estar logado para acessar esta página.")
    st.stop()

# ── Mensagens de feedback ────────────────────────────────────────────────────
if "msg_remocao" in st.session_state:
    st.success(st.session_state.pop("msg_remocao"))
if "msg_edicao" in st.session_state:
    st.success(st.session_state.pop("msg_edicao"))

if "editando" not in st.session_state:
    st.session_state["editando"] = None

st.title("Minha Carteira")

# ── Formulário de adição ─────────────────────────────────────────────────────
st.header("Adicionar Ativo")

classe = st.selectbox(
    "Classe",
    ["Ações", "FIIs", "Renda Fixa", "Alternativo"],
    key="classe_selecionada",
)

tipo_rentabilidade = None
if classe == "Renda Fixa":
    tipo_rentabilidade = st.selectbox(
        "Tipo de Rentabilidade",
        ["Prefixado", "CDI+", "% do CDI", "IPCA+"],
        key="tipo_rentabilidade_selecionado",
    )

with st.form("form_add_ativo", clear_on_submit=True):
    if classe == "Ações":
        identificador = st.text_input("Ticker", placeholder="Ex: BBAS3")
        f1, f2, f3 = st.columns(3)
        with f1:
            quantidade  = st.number_input("Quantidade", min_value=0.01, step=1.0, value=1.0)
        with f2:
            data_compra_form = st.date_input("Data da compra", value=date.today())
        with f3:
            preco_compra_form = st.number_input("Preço de compra (R$)", min_value=0.01, format="%.2f", value=0.01)
        preco_medio = preco_compra_form
        vencimento = None; data_aplicacao = None; taxa = None; pvp = None

    elif classe == "FIIs":
        identificador = st.text_input("Ticker", placeholder="Ex: KNRI11")
        f1, f2, f3 = st.columns(3)
        with f1:
            quantidade  = st.number_input("Quantidade", min_value=0.01, step=1.0, value=1.0)
        with f2:
            data_compra_form = st.date_input("Data da compra", value=date.today())
        with f3:
            preco_compra_form = st.number_input("Preço de compra (R$)", min_value=0.01, format="%.2f", value=0.01)
        pvp = st.number_input(
            "P/VP atual", min_value=0.01, max_value=5.0, step=0.01, format="%.2f", value=1.0,
            help="Valor Patrimonial por Cota. Consulte na sua corretora ou no Funds Explorer.",
        )
        if pvp < 0.95:
            _pvp_cor, _pvp_txt = "#00A878", "Abaixo do patrimônio: desconto interessante"
        elif pvp <= 1.05:
            _pvp_cor, _pvp_txt = "#888888", "Próximo do valor patrimonial: preço justo"
        elif pvp <= 1.20:
            _pvp_cor, _pvp_txt = "#FFC107", "Acima do patrimônio: atenção ao preço de entrada"
        else:
            _pvp_cor, _pvp_txt = "#FF4B4B", "Prêmio elevado sobre o patrimônio: risco de sobrepreço"
        st.markdown(f"<span style='color:{_pvp_cor};font-size:0.85rem'>{_pvp_txt}</span>",
                    unsafe_allow_html=True)
        preco_medio = preco_compra_form
        vencimento = None; data_aplicacao = None; taxa = None

    elif classe == "Renda Fixa":
        identificador = st.text_input("Nome do ativo", placeholder="Ex: Tesouro Prefixado 2032")
        valor_investido = st.number_input("Valor Investido (R$)", min_value=0.01, format="%.2f", value=0.01)
        data_aplic = st.date_input("Data de Aplicação", value=date.today())
        data_venc = st.date_input("Data de Vencimento")

        if tipo_rentabilidade == "Prefixado":
            taxa = st.number_input("Taxa prefixada (% a.a.)", min_value=0.01, format="%.2f", value=13.5)
            st.caption("Exemplos: 13.5%, 14.0%, 15.25%")
            leitura = f"Rende {taxa:.2f}% ao ano independente do mercado."
        elif tipo_rentabilidade == "% do CDI":
            taxa = st.number_input("Percentual do CDI (%)", min_value=80.0, max_value=200.0, step=5.0, format="%.1f", value=100.0)
            st.caption("Exemplos: 100% do CDI, 110%, 120%")
            if taxa == 100.0:
                leitura = "Rende o equivalente a 100% do CDI."
            elif taxa > 100.0:
                leitura = f"Rende {taxa - 100:.0f}% a mais que o CDI."
            else:
                leitura = f"Rende {taxa:.0f}% do CDI."
        elif tipo_rentabilidade == "CDI+":
            taxa = st.number_input("Spread sobre o CDI (% a.a.)", min_value=0.01, format="%.2f", value=1.5)
            st.caption("Exemplos: CDI + 1.5%, CDI + 2.0%")
            leitura = f"Rende o CDI mais {taxa:.2f}% ao ano."
        else:  # IPCA+
            taxa = st.number_input("Spread sobre o IPCA (% a.a.)", min_value=0.01, format="%.2f", value=6.5)
            st.caption("Exemplos: IPCA + 5.0%, IPCA + 6.5%, IPCA + 7.5%")
            leitura = f"Rende a inflação mais {taxa:.2f}% ao ano: protege o poder de compra."

        st.info(leitura)

        quantidade = 1
        preco_medio = valor_investido
        vencimento = data_venc.strftime("%d/%m/%Y")
        data_aplicacao = data_aplic.strftime("%d/%m/%Y")
        pvp = None

    else:  # Alternativo
        identificador = st.text_input("Ticker", placeholder="Ex: BTC-USD")
        st.info(
            "Tickers suportados: BTC-USD (Bitcoin), GC=F (Ouro), SI=F (Prata). "
            "Para ETFs brasileiros use o código sem sufixo .SA: GOLD11, BOVA11."
        )
        f1, f2, f3 = st.columns(3)
        with f1:
            quantidade = st.number_input(
                "Quantidade", min_value=0.00000001, format="%.8f", value=0.001,
                help="Para Bitcoin use decimais (ex: 0.01 BTC).",
            )
        with f2:
            data_compra_form = st.date_input("Data da compra", value=date.today())
        with f3:
            preco_compra_form = st.number_input("Preço de compra (R$)", min_value=0.01, format="%.2f", value=0.01)
        preco_medio = preco_compra_form
        vencimento = None; data_aplicacao = None; taxa = None; pvp = None

    submitted = st.form_submit_button("Adicionar")

if submitted:
    nome = identificador.strip().upper()
    if not nome:
        st.warning("Preencha o identificador do ativo.")
    elif classe in ("Ações", "FIIs", "Alternativo"):
        # Compra-first: registra a compra e recalcula o ativo
        salvar_compra(nome, data_compra_form.strftime("%Y-%m-%d"), quantidade, preco_compra_form)
        if ativo_existe(nome):
            _pvp_val = pvp if classe == "FIIs" else None
            # _recalcular_ativo_por_compras não está disponível fora do else ativos,
            # então recalculamos inline
            todas = get_compras(nome)
            qtd_t = sum(float(c["quantidade"]) for c in todas)
            pm_t  = sum(float(c["quantidade"]) * float(c["preco_compra"]) for c in todas) / qtd_t
            upd: dict = {"quantidade": qtd_t, "preco_medio": round(pm_t, 4)}
            if _pvp_val is not None:
                upd["pvp"] = _pvp_val
            editar_ativo(nome, upd)
        else:
            add_ativo(nome, quantidade, round(preco_compra_form, 4), classe,
                      pvp=pvp if classe == "FIIs" else None)
        st.success(f"{nome} adicionado com sucesso. Preco médio calculado pela compra registrada.")
    else:
        # Renda Fixa: fluxo original
        if ativo_existe(nome):
            st.warning(f"{nome} já está cadastrado na carteira.")
        else:
            add_ativo(
                nome, quantidade, preco_medio, classe,
                vencimento=vencimento,
                data_aplicacao=data_aplicacao,
                tipo_rentabilidade=tipo_rentabilidade,
                taxa=taxa,
                pvp=pvp,
            )
            st.success(f"{nome} adicionado com sucesso.")

# ── CSS hover para lixeiras de compra ────────────────────────────────────────
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] button[data-testid="baseButton-secondary"] {
    opacity: 0;
    transition: opacity 0.15s;
    background: none !important;
    border: none !important;
    color: #888 !important;
    padding: 0 4px !important;
    min-height: 0 !important;
    box-shadow: none !important;
}
div[data-testid="stHorizontalBlock"]:hover button[data-testid="baseButton-secondary"] {
    opacity: 1 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Ativos Cadastrados ────────────────────────────────────────────────────────
st.header("Ativos Cadastrados")
ativos = get_ativos()

if not ativos:
    st.info("Nenhum ativo cadastrado ainda.")
else:
    acoes        = [a for a in ativos if a["classe"] == "Ações"]
    fiis         = [a for a in ativos if a["classe"] == "FIIs"]
    renda_fixa   = [a for a in ativos if a["classe"] == "Renda Fixa"]
    alternativos = [a for a in ativos if a["classe"] == "Alternativo"]

    def _btn_remover(ticker: str) -> None:
        """Lixeira inline: remove ativo e todas as suas compras."""
        if st.button("🗑️", key=f"del_ativo_{ticker}", help=f"Remover {ticker}"):
            for c in get_compras(ticker):
                deletar_compra(str(c["id"]))
            remove_ativo(ticker)
            st.session_state["msg_remocao"] = f"{ticker} removido da carteira."
            st.rerun()

    def _recalcular_ativo_por_compras(ticker: str, classe: str, pvp: float | None = None) -> None:
        """Recalcula preco_medio e quantidade_total a partir das compras e atualiza o ativo."""
        compras = get_compras(ticker)
        if not compras:
            remove_ativo(ticker)
            return
        qtd_total = sum(float(c["quantidade"]) for c in compras)
        pm = sum(float(c["quantidade"]) * float(c["preco_compra"]) for c in compras) / qtd_total
        if ativo_existe(ticker):
            update: dict = {"quantidade": qtd_total, "preco_medio": round(pm, 4)}
            if pvp is not None:
                update["pvp"] = pvp
            editar_ativo(ticker, update)
        else:
            add_ativo(ticker, qtd_total, round(pm, 4), classe, pvp=pvp)

    def _secao_compras(ticker: str, classe: str) -> None:
        """Exibe tabela de compras e formulário de registro para um ativo."""
        preco_atual = get_preco_atual(ticker, classe)
        compras = get_compras(ticker)

        st.divider()
        st.caption("**Histórico de Compras**")

        if compras:
            cab1, cab2, cab3, cab4, cab5, cab6 = st.columns([2, 2, 2, 2, 2, 1])
            cab1.caption("Data"); cab2.caption("Preço pago")
            cab3.caption("Qtd."); cab4.caption("Ganho (R$)")
            cab5.caption("Valor atual"); cab6.write("")

            for c in compras:
                qtd   = float(c["quantidade"])
                p_pago = float(c["preco_compra"])
                pa    = preco_atual or p_pago
                ganho = (pa - p_pago) * qtd
                v_at  = pa * qtd
                cor   = "#00C896" if ganho >= 0 else "#FF4B4B"

                r1, r2, r3, r4, r5, r6 = st.columns([2, 2, 2, 2, 2, 1])
                r1.write(c["data_compra"])
                r2.write(fmt_brl(p_pago))
                r3.write(str(qtd))
                r4.markdown(
                    f"<span style='color:{cor};font-weight:600;'>{fmt_brl(ganho)}</span>",
                    unsafe_allow_html=True,
                )
                r5.write(fmt_brl(v_at))
                with r6:
                    if st.button("🗑", key=f"del_compra_{c['id']}", help="Remover", type="secondary"):
                        deletar_compra(str(c["id"]))
                        _recalcular_ativo_por_compras(ticker, classe)
                        st.rerun()

        key_form = f"show_form_compra_{ticker}"
        if st.button("+ Registrar compra", key=f"btn_reg_{ticker}"):
            st.session_state[key_form] = True

        if st.session_state.get(key_form):
            with st.form(f"form_compra_{ticker}"):
                fc1, fc2, fc3 = st.columns(3)
                with fc1:
                    qtd_c = st.number_input("Quantidade", min_value=0.01, step=1.0, value=1.0,
                                            key=f"qtd_c_{ticker}")
                with fc2:
                    data_c = st.date_input("Data da compra", value=date.today(),
                                           key=f"data_c_{ticker}")
                with fc3:
                    preco_c = st.number_input("Preço de compra (R$)", min_value=0.01,
                                              format="%.2f", value=preco_atual or 0.01,
                                              key=f"preco_c_{ticker}")
                sb, cb = st.columns(2)
                salvar   = sb.form_submit_button("Salvar",   use_container_width=True, type="primary")
                cancelar = cb.form_submit_button("Cancelar", use_container_width=True)

                if salvar:
                    salvar_compra(ticker, data_c.strftime("%Y-%m-%d"), qtd_c, preco_c)
                    _recalcular_ativo_por_compras(ticker, classe)
                    st.session_state[key_form] = False
                    st.rerun()
                if cancelar:
                    st.session_state[key_form] = False
                    st.rerun()

    def _cabecalho_ativo(ticker: str, classe: str, preco_medio: float, quantidade: float) -> None:
        """Exibe métricas do ativo estilo Google Finanças."""
        pa        = get_preco_atual(ticker, classe) or preco_medio
        ganho_rs  = (pa - preco_medio) * quantidade
        ganho_pct = (pa / preco_medio - 1) * 100 if preco_medio > 0 else 0.0
        valor_tot = pa * quantidade

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Preço atual",  fmt_brl(pa))
        m2.metric("Quantidade",   str(quantidade))
        m3.metric("Ganho (R$)",   fmt_brl(ganho_rs))
        m4.metric("Ganho (%)",    f"{ganho_pct:+.2f}%")
        m5.metric("Valor total",  fmt_brl(valor_tot))

    def _menu_excluir(ticker: str, classe: str) -> None:
        """Popover ⋮ com opção de excluir o ativo e todas as suas compras."""
        with st.popover("⋮"):
            if st.button("Excluir ativo", key=f"excluir_{ticker}",
                         type="primary", use_container_width=True):
                for c in get_compras(ticker):
                    deletar_compra(str(c["id"]))
                remove_ativo(ticker)
                st.session_state["msg_remocao"] = f"{ticker} removido da carteira."
                st.rerun()

    if acoes:
        st.subheader("Ações")
        for a in acoes:
            with st.expander(a["ticker"], expanded=False):
                h1, h2 = st.columns([9, 1])
                h1.caption(f"PM: {fmt_brl(float(a['preco_medio']))}")
                with h2:
                    _menu_excluir(a["ticker"], "Ações")
                _cabecalho_ativo(a["ticker"], "Ações", float(a["preco_medio"]), float(a["quantidade"]))
                _secao_compras(a["ticker"], "Ações")

    if fiis:
        st.subheader("FIIs")
        for a in fiis:
            with st.expander(a["ticker"], expanded=False):
                h1, h2 = st.columns([9, 1])
                h1.caption(f"PM: {fmt_brl(float(a['preco_medio']))}")
                with h2:
                    _menu_excluir(a["ticker"], "FIIs")
                _cabecalho_ativo(a["ticker"], "FIIs", float(a["preco_medio"]), float(a["quantidade"]))
                _secao_compras(a["ticker"], "FIIs")

    if renda_fixa:
        st.subheader("Renda Fixa")
        for a in renda_fixa:
            with st.container(border=True):
                h1, h2 = st.columns([9, 1])
                h1.markdown(f"**{a['ticker']}**")
                with h2:
                    with st.popover("⋮"):
                        if st.button("Excluir", key=f"excluir_rf_{a['ticker']}",
                                     type="primary", use_container_width=True):
                            remove_ativo(a["ticker"])
                            st.session_state["msg_remocao"] = f"{a['ticker']} removido."
                            st.rerun()
                d1, d2, d3, d4 = st.columns(4)
                d1.caption("Valor");      d1.write(fmt_brl(a["preco_medio"]))
                d2.caption("Tipo");       d2.write(a.get("tipo_rentabilidade") or "—")
                d3.caption("Taxa");       d3.write(f"{a['taxa']:.1f}%" if a.get("taxa") is not None else "—")
                d4.caption("Vencimento"); d4.write(a.get("vencimento") or "—")

    if alternativos:
        st.subheader("Alternativo")
        for a in alternativos:
            with st.expander(a["ticker"], expanded=False):
                h1, h2 = st.columns([9, 1])
                h1.caption(f"PM: {fmt_brl(float(a['preco_medio']))}")
                with h2:
                    _menu_excluir(a["ticker"], "Alternativo")
                _cabecalho_ativo(a["ticker"], "Alternativo",
                                 float(a["preco_medio"]), float(a["quantidade"]))
                _secao_compras(a["ticker"], "Alternativo")

    # ── Watchlist ─────────────────────────────────────────────────────────────

# ── Watchlist ─────────────────────────────────────────────────────────────────
st.divider()
st.header("Watchlist")

watchlist = get_watchlist()

if not watchlist:
    st.info("Sua watchlist está vazia. Adicione ativos pelas Sugestões.")
else:
    alertas_wl = []

    for item in watchlist:
        ticker_wl     = item["ticker"]
        classe_wl     = item["classe"]
        preco_na_ad   = item.get("preco_na_adicao")
        preco_ent_alvo = item.get("preco_entrada_alvo")
        motivo_wl     = item.get("motivo", "")
        data_adicao   = item.get("data_adicao", "—")

        preco_atual_wl = get_preco_atual(ticker_wl, classe_wl)

        var_wl = None
        if preco_na_ad and preco_atual_wl:
            var_wl = ((preco_atual_wl - preco_na_ad) / preco_na_ad) * 100

        dist_wl = None
        if preco_ent_alvo and preco_atual_wl:
            dist_wl = ((preco_atual_wl - preco_ent_alvo) / preco_ent_alvo) * 100

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.markdown(f"**{ticker_wl}**")
                st.caption(classe_wl)
                st.caption(f"Adicionado: {data_adicao}")

            with c2:
                st.write(fmt_brl(preco_atual_wl) if preco_atual_wl else "—")
                if preco_na_ad:
                    st.caption(f"Na adição: {fmt_brl(preco_na_ad)}")

            with c3:
                if var_wl is not None:
                    st.metric(
                        "Variação",
                        f"{var_wl:+.1f}%",
                        delta=f"{var_wl:+.1f}%",
                        delta_color="normal" if var_wl < 0 else "inverse",
                    )
                else:
                    st.caption("Variação indisponível")

            with c4:
                if dist_wl is not None:
                    if dist_wl <= 0:
                        st.success("No preço alvo!")
                    elif dist_wl <= 5:
                        st.warning(f"A {dist_wl:.1f}% do alvo")
                    else:
                        st.info(f"{dist_wl:.1f}% acima do alvo")
                else:
                    st.caption("Sem alvo definido")

            if motivo_wl:
                st.caption(f"Motivo: {motivo_wl}")

            col_rem, col_add = st.columns([1, 4])
            with col_rem:
                if st.button("Remover", key=f"rem_watch_{ticker_wl}"):
                    remove_watchlist(ticker_wl)
                    st.rerun()
            with col_add:
                st.caption("Para adicionar à carteira, use o formulário acima.")

            if dist_wl is not None and dist_wl <= 2:
                alertas_wl.append(f"{ticker_wl} atingiu o preço de entrada alvo!")
            if var_wl is not None and var_wl <= -10:
                alertas_wl.append(f"{ticker_wl} caiu {abs(var_wl):.1f}% desde que foi adicionado. Pode ser oportunidade.")

    if alertas_wl:
        st.subheader("Alertas da Watchlist")
        for msg in alertas_wl:
            st.warning(f"⚠️ {msg}")
