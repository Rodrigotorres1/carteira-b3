UNIVERSO_ACOES = [
    "BBAS3", "BBSE3", "ITUB4", "BRADESCO4", "SANB11",
    "PETR4", "VALE3", "PRIO3", "CSAN3",
    "WEGE3", "EQTL3", "CPFE3", "EGIE3", "TAEE11",
    "RENT3", "RADL3", "LREN3", "MGLU3",
    "VIVT3", "TOTS3", "INTB3", "SMTO3",
]

UNIVERSO_FIIS = [
    "HGLG11", "KNRI11", "XPML11", "HGBS11",
    "GGRC11", "ALZR11", "RBVA11", "CPTS11",
    "BTLG11", "VILG11", "MXRF11", "KNCR11",
]

SUGESTOES = {
    "conservador": {
        "renda": [
            {"ticker": "TAEE11", "nome": "Taesa", "classe": "Ações",
             "motivo": "Transmissão de energia, setor regulado, dividendos consistentes acima de 8% ao ano"},
            {"ticker": "BBSE3", "nome": "BB Seguridade", "classe": "Ações",
             "motivo": "Distribui quase todo lucro como dividendo, negócio previsível e defensivo"},
            {"ticker": "KNRI11", "nome": "Kinea Renda Imobiliária", "classe": "FIIs",
             "motivo": "FII híbrido diversificado, um dos maiores do Brasil"},
            {"ticker": "HGLG11", "nome": "CSHG Logística", "classe": "FIIs",
             "motivo": "Galpões logísticos com contratos longos e gestão Credit Suisse"},
            {"ticker": "Tesouro Selic 2028", "nome": "Tesouro Selic", "classe": "Renda Fixa",
             "motivo": "Liquidez diária, acompanha a Selic, ideal para reserva de emergência"},
            {"ticker": "CDB 100% CDI", "nome": "CDB CDI", "classe": "Renda Fixa",
             "motivo": "Retorno atrelado ao CDI com proteção do FGC até R$ 250 mil"},
        ],
        "crescimento": [
            {"ticker": "CPFE3", "nome": "CPFL Energia", "classe": "Ações",
             "motivo": "Distribuição de energia, setor defensivo com crescimento estável"},
            {"ticker": "EGIE3", "nome": "Engie Brasil", "classe": "Ações",
             "motivo": "Geração de energia renovável, uma das melhores gestões do setor elétrico"},
            {"ticker": "BBAS3", "nome": "Banco do Brasil", "classe": "Ações",
             "motivo": "Banco sólido com P/L baixo e bons fundamentos"},
            {"ticker": "ALZR11", "nome": "Alianza Trust", "classe": "FIIs",
             "motivo": "Ativos urbanos com contratos atípicos de longo prazo"},
            {"ticker": "Tesouro IPCA+ 2035", "nome": "Tesouro IPCA+", "classe": "Renda Fixa",
             "motivo": "Proteção contra inflação no longo prazo"},
        ],
    },
    "moderado": {
        "renda": [
            {"ticker": "BBAS3", "nome": "Banco do Brasil", "classe": "Ações",
             "motivo": "Dividend yield acima de 8%, P/L baixo historicamente"},
            {"ticker": "BBSE3", "nome": "BB Seguridade", "classe": "Ações",
             "motivo": "Payout elevado, negócio previsível, baixa volatilidade"},
            {"ticker": "TAEE11", "nome": "Taesa", "classe": "Ações",
             "motivo": "Dividendos semestrais elevados, setor regulado"},
            {"ticker": "HGBS11", "nome": "Hedge Brasil Shopping", "classe": "FIIs",
             "motivo": "FII de shoppings consolidado com renda mensal"},
            {"ticker": "RBVA11", "nome": "Rio Bravo Renda Varejo", "classe": "FIIs",
             "motivo": "Imóveis bancários com contratos de longo prazo"},
            {"ticker": "CPTS11", "nome": "Capitânia Securities", "classe": "FIIs",
             "motivo": "FII de papel com rendimentos mensais acima da média"},
        ],
        "crescimento": [
            {"ticker": "WEGE3", "nome": "WEG", "classe": "Ações",
             "motivo": "Crescimento de receita e lucro por mais de 20 anos consecutivos"},
            {"ticker": "EQTL3", "nome": "Equatorial", "classe": "Ações",
             "motivo": "Melhor gestora de distribuidoras do Brasil, expansão consistente"},
            {"ticker": "RENT3", "nome": "Localiza", "classe": "Ações",
             "motivo": "Líder em aluguel de veículos, consolidação do mercado de mobilidade"},
            {"ticker": "RADL3", "nome": "Raia Drogasil", "classe": "Ações",
             "motivo": "Crescimento secular do setor farmacêutico, expansão de lojas"},
            {"ticker": "GGRC11", "nome": "GGR Covipça", "classe": "FIIs",
             "motivo": "Expansão do portfólio logístico com demanda crescente"},
            {"ticker": "BTC-USD", "nome": "Bitcoin", "classe": "Alternativo",
             "motivo": "Reserva de valor digital, descorrelacionado do IBOV, alocação sugerida de até 5%"},
        ],
    },
    "arrojado": {
        "renda": [
            {"ticker": "BBAS3", "nome": "Banco do Brasil", "classe": "Ações",
             "motivo": "Alto DY com P/L historicamente baixo"},
            {"ticker": "PETR4", "nome": "Petrobras", "classe": "Ações",
             "motivo": "Dividendos extraordinários nos ciclos de alta do petróleo"},
            {"ticker": "VALE3", "nome": "Vale", "classe": "Ações",
             "motivo": "Dividendos elevados em ciclos favoráveis de commodities"},
            {"ticker": "CPTS11", "nome": "Capitânia Securities", "classe": "FIIs",
             "motivo": "Rendimentos mensais acima de 1% com carteira de CRIs"},
            {"ticker": "HGBS11", "nome": "Hedge Brasil Shopping", "classe": "FIIs",
             "motivo": "Shoppings premium com boa recuperação"},
        ],
        "crescimento": [
            {"ticker": "WEGE3", "nome": "WEG", "classe": "Ações",
             "motivo": "Compounding machine brasileira, segure por décadas"},
            {"ticker": "PRIO3", "nome": "PetroRio", "classe": "Ações",
             "motivo": "Produção de petróleo offshore com gestão de custos eficiente"},
            {"ticker": "SMTO3", "nome": "São Martinho", "classe": "Ações",
             "motivo": "Sucroenegético com ciclo favorável e gestão sólida"},
            {"ticker": "INTB3", "nome": "Intelbras", "classe": "Ações",
             "motivo": "Crescimento em segurança eletrônica e conectividade"},
            {"ticker": "BTC-USD", "nome": "Bitcoin", "classe": "Alternativo",
             "motivo": "Alocação de até 10-15% para perfil arrojado, maior potencial de valorização no longo prazo"},
            {"ticker": "GC=F", "nome": "Ouro", "classe": "Alternativo",
             "motivo": "Proteção em cenários de crise e dólar forte, descorrelacionado da bolsa"},
        ],
    },
}


def get_sugestoes(perfil: str, objetivo: str) -> list:
    """Retorna lista de sugestões para o perfil e objetivo informados."""
    return SUGESTOES.get(perfil, {}).get(objetivo, [])


def get_objetivo_combinado(perfil: str) -> list:
    """Retorna sugestões combinadas de renda e crescimento sem duplicatas.

    Ativos presentes nos dois objetivos aparecem primeiro com
    o campo 'objetivos' = 'Renda e Crescimento'.
    """
    renda = {s["ticker"]: s for s in SUGESTOES.get(perfil, {}).get("renda", [])}
    crescimento = {s["ticker"]: s for s in SUGESTOES.get(perfil, {}).get("crescimento", [])}

    resultado = []
    vistos = set()

    for ticker in renda:
        if ticker in crescimento:
            item = {**renda[ticker], "objetivos": "Renda e Crescimento"}
            resultado.append(item)
            vistos.add(ticker)

    for ticker, ativo in renda.items():
        if ticker not in vistos:
            resultado.append({**ativo, "objetivos": "Renda"})
            vistos.add(ticker)

    for ticker, ativo in crescimento.items():
        if ticker not in vistos:
            resultado.append({**ativo, "objetivos": "Crescimento"})
            vistos.add(ticker)

    return resultado


def agrupar_por_classe(sugestoes: list) -> dict:
    """Agrupa lista de sugestões por classe de ativo."""
    grupos: dict[str, list] = {}
    for s in sugestoes:
        grupos.setdefault(s["classe"], []).append(s)
    return grupos
