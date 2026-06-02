from datetime import date

import pandas as pd
import streamlit as st

from utils.portfolio import add_ativo, ativo_existe, get_ativos, remove_ativo

st.title("Minha Carteira")

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
        quantidade = st.number_input("Quantidade", min_value=0.00000001, format="%.8f", value=0.00000001)
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

st.header("Ativos Cadastrados")
ativos = get_ativos()

if not ativos:
    st.info("Nenhum ativo cadastrado. Adicione seu primeiro ativo acima.")
else:
    linhas = []
    for a in ativos:
        linhas.append({
            "Ticker": a["ticker"],
            "Classe": a["classe"],
            "Quantidade": a["quantidade"],
            "Preço Médio": a["preco_medio"],
            "P/VP": f"{a['pvp']:.2f}" if a.get("pvp") is not None else "-",
            "Vencimento": a.get("vencimento", "-"),
            "Data Aplicação": a.get("data_aplicacao", "-"),
            "Tipo": a.get("tipo_rentabilidade", "-"),
            "Taxa (% a.a.)": a["taxa"] if a.get("taxa") is not None else "-",
        })
    st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)

    tickers_cadastrados = [a["ticker"] for a in ativos]
    ticker_remover = st.selectbox("Selecione o ativo para remover", tickers_cadastrados)
    if st.button("Remover"):
        remove_ativo(ticker_remover)
        st.success(f"{ticker_remover} removido da carteira.")
        st.rerun()
