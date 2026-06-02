from datetime import date

import pandas as pd
import streamlit as st

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
        quantidade = st.number_input("Quantidade", min_value=1, step=1, value=1)
        preco_medio = st.number_input("Preço Médio por cota (R$)", min_value=0.01, format="%.2f", value=0.01)
        vencimento = None
        data_aplicacao = None
        taxa = None
        pvp = None

    elif classe == "FIIs":
        identificador = st.text_input("Ticker", placeholder="Ex: KNRI11")
        quantidade = st.number_input("Quantidade", min_value=1, step=1, value=1)
        preco_medio = st.number_input("Preço Médio por cota (R$)", min_value=0.01, format="%.2f", value=0.01)
        pvp = st.number_input(
            "P/VP atual",
            min_value=0.01, max_value=5.0, step=0.01, format="%.2f", value=1.0,
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
        vencimento = None
        data_aplicacao = None
        taxa = None

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
        quantidade = st.number_input(
            "Quantidade", min_value=0.00000001, format="%.8f", value=0.001,
            help="Para Bitcoin use decimais (ex: 0.01 BTC). Para Ouro use frações de onça (ex: 0.5). Tickers aceitos: BTC-USD, GC=F (Ouro), SI=F (Prata)",
        )
        preco_medio = st.number_input("Preço Médio (R$)", min_value=0.01, format="%.2f", value=0.01)
        vencimento = None
        data_aplicacao = None
        taxa = None
        pvp = None

    submitted = st.form_submit_button("Adicionar")

if submitted:
    nome = identificador.strip()
    if not nome:
        st.warning("Preencha o identificador do ativo.")
    elif ativo_existe(nome):
        st.warning(f"{nome.upper()} já está cadastrado na carteira.")
    else:
        add_ativo(
            nome, quantidade, preco_medio, classe,
            vencimento=vencimento,
            data_aplicacao=data_aplicacao,
            tipo_rentabilidade=tipo_rentabilidade,
            taxa=taxa,
            pvp=pvp,
        )
        st.success(f"{nome.upper()} adicionado com sucesso.")

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

    def _btn_editar(ticker: str) -> None:
        if st.button("Editar", key=f"edit_{ticker}", use_container_width=True):
            st.session_state["editando"] = ticker
            st.rerun()

    if acoes:
        st.subheader("Ações")
        for i, a in enumerate(acoes):
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
                if i == 0:
                    c1.caption("Ticker"); c2.caption("Quantidade")
                    c3.caption("Preço Médio"); c4.write("")
                c1.write(a["ticker"]); c2.write(str(a["quantidade"]))
                c3.write(fmt_brl(a["preco_medio"]))
                with c4: _btn_editar(a["ticker"])

    if fiis:
        st.subheader("FIIs")
        for i, a in enumerate(fiis):
            pvp_val = a.get("pvp")
            texto_pvp = f"{pvp_val:.2f}" if pvp_val is not None and float(pvp_val) > 0 else "—"
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([4, 2, 3, 2, 1])
                if i == 0:
                    c1.caption("Ticker"); c2.caption("Quantidade")
                    c3.caption("Preço Médio"); c4.caption("P/VP"); c5.write("")
                c1.write(a["ticker"]); c2.write(str(a["quantidade"]))
                c3.write(fmt_brl(a["preco_medio"]))
                c4.write(texto_pvp)
                with c5: _btn_editar(a["ticker"])

    if renda_fixa:
        st.subheader("Renda Fixa")
        for i, a in enumerate(renda_fixa):
            with st.container(border=True):
                l1, l2 = st.columns([5, 1])
                l1.write(a["ticker"])
                with l2: _btn_editar(a["ticker"])
                d1, d2, d3, d4 = st.columns(4)
                if i == 0:
                    d1.caption("Valor"); d2.caption("Tipo")
                    d3.caption("Taxa"); d4.caption("Vencimento")
                d1.write(fmt_brl(a["preco_medio"]))
                d2.write(a.get("tipo_rentabilidade") or "—")
                d3.write(f"{a['taxa']:.1f}%" if a.get("taxa") is not None else "—")
                d4.write(a.get("vencimento") or "—")

    if alternativos:
        st.subheader("Alternativo")
        for i, a in enumerate(alternativos):
            t = a["ticker"].upper()
            casas = 8 if ("BTC" in t or "ETH" in t) else 4
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([4, 3, 3, 1])
                if i == 0:
                    c1.caption("Ticker"); c2.caption("Quantidade")
                    c3.caption("Preço Médio"); c4.write("")
                c1.write(a["ticker"])
                c2.write(f"{a['quantidade']:.{casas}f}")
                c3.write(fmt_brl(a["preco_medio"]))
                with c4: _btn_editar(a["ticker"])

    # ── Formulário de edição ──────────────────────────────────────────────────
    ticker_editando = st.session_state["editando"]
    if ticker_editando:
        ativo_ed = next((a for a in ativos if a["ticker"] == ticker_editando), None)
        if ativo_ed:
            st.divider()
            classe_ed = ativo_ed["classe"]

            def _parse_data_str(s: str | None) -> date:
                try:
                    d, m, y = (s or "").split("/")
                    return date(int(y), int(m), int(d))
                except Exception:
                    return date.today()

            with st.container(border=True):
                st.subheader(f"Editando: {ticker_editando}")
                st.caption(f"Classe: {classe_ed} | Ticker: {ticker_editando}")
                st.divider()

                with st.form(f"form_edicao_{ticker_editando}"):
                    if classe_ed == "Ações":
                        nova_qtd   = st.number_input("Quantidade", min_value=1, step=1, value=int(ativo_ed["quantidade"]))
                        novo_preco = st.number_input("Preço Médio (R$)", min_value=0.01, format="%.2f", value=float(ativo_ed["preco_medio"]))

                    elif classe_ed == "FIIs":
                        nova_qtd   = st.number_input("Quantidade", min_value=1, step=1, value=int(ativo_ed["quantidade"]))
                        novo_preco = st.number_input("Preço Médio (R$)", min_value=0.01, format="%.2f", value=float(ativo_ed["preco_medio"]))
                        novo_pvp   = st.number_input("P/VP atual", min_value=0.01, max_value=5.0, step=0.01, format="%.2f",
                                                     value=float(ativo_ed.get("pvp") or 1.0))

                    elif classe_ed == "Renda Fixa":
                        novo_nome  = st.text_input("Nome do ativo", value=ativo_ed["ticker"])
                        novo_valor = st.number_input("Valor Investido (R$)", min_value=0.01, format="%.2f", value=float(ativo_ed["preco_medio"]))
                        _tipos     = ["Prefixado", "CDI+", "% do CDI", "IPCA+"]
                        _tipo_at   = ativo_ed.get("tipo_rentabilidade", "Prefixado")
                        novo_tipo  = st.selectbox("Tipo de Rentabilidade", _tipos,
                                                  index=_tipos.index(_tipo_at) if _tipo_at in _tipos else 0)
                        nova_taxa  = st.number_input("Taxa (% a.a.)", min_value=0.01, format="%.2f",
                                                     value=float(ativo_ed.get("taxa") or 10.0))
                        nova_aplic = st.date_input("Data de Aplicação", value=_parse_data_str(ativo_ed.get("data_aplicacao")))
                        novo_venc  = st.date_input("Data de Vencimento",  value=_parse_data_str(ativo_ed.get("vencimento")))

                    else:  # Alternativo
                        nova_qtd   = st.number_input("Quantidade", min_value=0.00000001, format="%.8f",
                                                     value=float(ativo_ed["quantidade"]))
                        novo_preco = st.number_input("Preço Médio (R$)", min_value=0.01, format="%.2f",
                                                     value=float(ativo_ed["preco_medio"]))

                    col_s, col_c = st.columns(2)
                    with col_s:
                        salvar   = st.form_submit_button("Salvar alterações", use_container_width=True)
                    with col_c:
                        cancelar = st.form_submit_button("Cancelar", use_container_width=True)
                    st.caption("As alterações são salvas localmente.")

            if salvar:
                if classe_ed == "Ações":
                    editar_ativo(ticker_editando, {"quantidade": nova_qtd, "preco_medio": novo_preco})
                elif classe_ed == "FIIs":
                    editar_ativo(ticker_editando, {"quantidade": nova_qtd, "preco_medio": novo_preco, "pvp": novo_pvp})
                elif classe_ed == "Renda Fixa":
                    editar_ativo(ticker_editando, {
                        "ticker": novo_nome.strip().upper(),
                        "preco_medio": novo_valor,
                        "tipo_rentabilidade": novo_tipo,
                        "taxa": nova_taxa,
                        "data_aplicacao": nova_aplic.strftime("%d/%m/%Y"),
                        "vencimento": novo_venc.strftime("%d/%m/%Y"),
                    })
                else:
                    editar_ativo(ticker_editando, {"quantidade": nova_qtd, "preco_medio": novo_preco})
                st.session_state["msg_edicao"] = f"{ticker_editando} atualizado com sucesso."
                st.session_state["editando"] = None
                st.rerun()

            if cancelar:
                st.session_state["editando"] = None
                st.rerun()

    st.divider()
    tickers_cadastrados = [a["ticker"] for a in ativos]
    ticker_remover = st.selectbox("Selecione o ativo para remover", tickers_cadastrados)
    if st.button("Remover"):
        remove_ativo(ticker_remover)
        st.session_state["msg_remocao"] = f"{ticker_remover} removido da carteira."
        st.rerun()

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
