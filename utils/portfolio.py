from datetime import date

from utils.database import carregar_dados, salvar_dados
from utils.market_data import (
    get_dados_fundamentus,
    get_dados_yfinance_fii,
    get_indices_renda_fixa,
    get_preco_atual,
    get_recomendacoes_analistas,
)

# ── Constantes de módulo ──────────────────────────────────────────────────────
SELIC_FALLBACK = 10.5
PVP_OTIMO = 0.95
PVP_BOM = 1.05
PVP_CARO = 1.20
DY_MENSAL_BOM = 0.8
DY_MENSAL_MINIMO = 0.5


def fmt_brl(valor: float | None) -> str:
    """Formata valor em reais com separadores brasileiros (1.234,56)."""
    if valor is None:
        return "-"
    return f"R$ {valor:_.2f}".replace(".", ",").replace("_", ".")


def _load() -> dict:
    return carregar_dados()


def _dump(data: dict) -> None:
    salvar_dados(data)


def get_ativos() -> list:
    return _load().get("ativos", [])


def ativo_existe(ticker: str) -> bool:
    return any(a["ticker"] == ticker.upper() for a in get_ativos())


def add_ativo(
    ticker: str,
    quantidade: float,
    preco_medio: float,
    classe: str,
    vencimento: str | None = None,
    data_aplicacao: str | None = None,
    tipo_rentabilidade: str | None = None,
    taxa: float | None = None,
    pvp: float | None = None,
) -> None:
    """Adiciona ativo à carteira. Campos opcionais conforme classe."""
    ativo = {
        "ticker": ticker.upper(),
        "quantidade": quantidade,
        "preco_medio": preco_medio,
        "classe": classe,
    }
    for chave, valor in [
        ("vencimento", vencimento),
        ("data_aplicacao", data_aplicacao),
        ("tipo_rentabilidade", tipo_rentabilidade),
        ("taxa", taxa),
        ("pvp", pvp),
    ]:
        if valor is not None:
            ativo[chave] = valor
    data = _load()
    data.setdefault("ativos", []).append(ativo)
    _dump(data)


def editar_ativo(ticker: str, dados: dict) -> bool:
    """Atualiza campos de um ativo existente. Retorna True se encontrado."""
    data = _load()
    for ativo in data.get("ativos", []):
        if ativo["ticker"] == ticker.upper():
            ativo.update(dados)
            _dump(data)
            return True
    return False


def remove_ativo(ticker: str) -> None:
    data = _load()
    data["ativos"] = [a for a in data.get("ativos", []) if a["ticker"] != ticker.upper()]
    _dump(data)


def get_watchlist() -> list:
    return _load().get("watchlist", [])


def ticker_na_watchlist(ticker: str) -> bool:
    return any(w["ticker"] == ticker.upper() for w in get_watchlist())


def add_watchlist(
    ticker: str,
    classe: str,
    preco_entrada: float | None = None,
    motivo: str | None = None,
) -> bool:
    """Adiciona ativo à watchlist. Retorna False se já existia."""
    ticker = ticker.upper()
    data = _load()
    watchlist = data.setdefault("watchlist", [])
    if any(w["ticker"] == ticker for w in watchlist):
        return False
    preco_atual = get_preco_atual(ticker, classe)
    watchlist.append({
        "ticker":             ticker,
        "classe":             classe,
        "preco_entrada_alvo": preco_entrada,
        "motivo":             motivo or "",
        "preco_na_adicao":    preco_atual,
        "data_adicao":        date.today().strftime("%d/%m/%Y"),
    })
    _dump(data)
    return True


def remove_watchlist(ticker: str) -> None:
    data = _load()
    data["watchlist"] = [w for w in data.get("watchlist", []) if w["ticker"] != ticker.upper()]
    _dump(data)


def calcular_carteira() -> list[dict]:
    """Retorna lista de ativos com preço atual e valor atual calculados."""
    resultado = []
    for ativo in get_ativos():
        preco_atual = get_preco_atual(ativo["ticker"], ativo["classe"])
        valor_atual = ativo["quantidade"] * (preco_atual if preco_atual else ativo["preco_medio"])
        resultado.append({
            "ticker": ativo["ticker"],
            "classe": ativo["classe"],
            "quantidade": ativo["quantidade"],
            "preco_medio": ativo["preco_medio"],
            "preco_atual": preco_atual,
            "valor_atual": valor_atual,
        })
    return resultado


def get_ativos_por_classe(classe: str) -> list:
    """Retorna lista de ativos filtrados pela classe informada."""
    return [a for a in get_ativos() if a["classe"] == classe]


def _fator_posicao(preco_atual: float, preco_medio_usuario: float) -> dict:
    """Calcula fator de posição do usuário, reutilizado em ações e FIIs."""
    var_pos = ((preco_atual - preco_medio_usuario) / preco_medio_usuario) * 100
    if var_pos < -10:
        pts = 1
        explicacao = (
            f"Seu preço médio é R$ {preco_medio_usuario:.2f}. "
            f"O ativo está {abs(var_pos):.1f}% abaixo do seu custo médio: "
            f"possível oportunidade de aporte."
        )
    elif var_pos <= 20:
        pts = 0
        direcao = "acima" if var_pos >= 0 else "abaixo"
        explicacao = (
            f"Seu preço médio é R$ {preco_medio_usuario:.2f}. "
            f"O ativo está {abs(var_pos):.1f}% {direcao} do seu custo médio."
        )
    else:
        pts = -1
        explicacao = (
            f"Seu preço médio é R$ {preco_medio_usuario:.2f}. "
            f"O ativo está {var_pos:.1f}% acima do seu custo médio: "
            f"considere realizar parte do lucro."
        )
    return {"nome": "Sua posição na carteira", "pontos": pts, "explicacao": explicacao}


def _fator_perfil(perfil: str) -> dict | None:
    """Retorna fator modificador de perfil, ou None se moderado."""
    if perfil == "conservador":
        return {
            "nome": "Modificador de perfil",
            "pontos": -1,
            "explicacao": "Perfil conservador: recomendação ajustada para maior cautela.",
        }
    if perfil == "arrojado":
        return {
            "nome": "Modificador de perfil",
            "pontos": 1,
            "explicacao": "Perfil arrojado: recomendação ajustada para maior tolerância a risco.",
        }
    return None


def _score_label(total: int) -> tuple[str, str]:
    if total >= 4:
        return "Comprar", "success"
    if total >= 1:
        return "Manter", "info"
    return "Vender", "warning"


def calcular_score_fii(
    ticker: str,
    preco_atual: float,
    preco_medio_usuario: float,
    perfil: str,
    fund_data: dict | None = None,
) -> dict:
    """Calcula score de decisão para um FII com base em DY mensal, range 52s e posição."""
    fatores = []
    total = 0

    if fund_data is not None:
        fund = fund_data
    else:
        pvp_cadastrado = next(
            (a.get("pvp") for a in get_ativos() if a["ticker"] == ticker.upper()),
            None,
        )
        fund = get_dados_yfinance_fii(ticker, pvp_cadastrado=pvp_cadastrado)

    # Fator 1 — Dividend Yield mensal (peso 2)
    dy_mensal = fund["dy_mensal"]
    if dy_mensal is not None:
        if dy_mensal >= DY_MENSAL_BOM:
            pts_dy, nivel_dy = 2, "acima"
        elif dy_mensal >= DY_MENSAL_MINIMO:
            pts_dy, nivel_dy = 1, "acima"
        else:
            pts_dy, nivel_dy = -1, "abaixo"
        explicacao_dy = (
            f"DY mensal de {dy_mensal:.2f}% "
            f"({nivel_dy} do benchmark de {DY_MENSAL_BOM}%)."
        )
    else:
        pts_dy = 0
        explicacao_dy = "Dividend yield mensal não disponível para este FII."
    total += pts_dy
    fatores.append({"nome": "Dividend Yield mensal", "pontos": pts_dy, "explicacao": explicacao_dy})

    # Fator 2 — Posição no range de 52 semanas (peso 1)
    p_min = fund["preco_52s_min"]
    p_max = fund["preco_52s_max"]
    if p_min is not None and p_max is not None and p_max > p_min:
        posicao_range = (preco_atual - p_min) / (p_max - p_min) * 100
        range_txt = f"R$ {p_min:.2f} a R$ {p_max:.2f}"
        if posicao_range <= 30:
            pts_52s = 1
            explicacao_52s = (
                f"Cota próxima da mínima do range de 52 semanas ({range_txt}): "
                f"oportunidade de entrada."
            )
        elif posicao_range <= 70:
            pts_52s = 0
            explicacao_52s = f"Cota na metade do range de 52 semanas ({range_txt})."
        else:
            pts_52s = -1
            explicacao_52s = (
                f"Cota próxima da máxima do range de 52 semanas ({range_txt}): "
                f"atenção ao preço de entrada."
            )
    else:
        pts_52s = 0
        explicacao_52s = "Range de 52 semanas não disponível para este FII."
    total += pts_52s
    fatores.append({"nome": "Range de 52 semanas", "pontos": pts_52s, "explicacao": explicacao_52s})

    # Fator 3 — P/VP do usuário (peso 1, quando disponível)
    pvp = fund.get("pvp")
    if pvp is not None:
        fonte_pvp = "informado pelo usuário"
        if pvp <= PVP_OTIMO:
            pts_pvp = 1
            explicacao_pvp = (
                f"P/VP de {pvp:.2f} ({fonte_pvp}): cota negociada com desconto "
                f"sobre o patrimônio líquido."
            )
        elif pvp <= PVP_BOM:
            pts_pvp = 0
            explicacao_pvp = f"P/VP de {pvp:.2f} ({fonte_pvp}): cota próxima do valor patrimonial."
        elif pvp <= PVP_CARO:
            pts_pvp = 0
            explicacao_pvp = (
                f"P/VP de {pvp:.2f} ({fonte_pvp}): cota acima do patrimônio. "
                f"Atenção ao preço."
            )
        else:
            pts_pvp = -1
            explicacao_pvp = f"P/VP de {pvp:.2f} ({fonte_pvp}): prêmio elevado sobre o patrimônio."
        total += pts_pvp
        fatores.append({"nome": "P/VP", "pontos": pts_pvp, "explicacao": explicacao_pvp})

    # Fator 4 — Posição do usuário (peso 1)
    fpos = _fator_posicao(preco_atual, preco_medio_usuario)
    total += fpos["pontos"]
    fatores.append(fpos)

    # Fator 5 — Modificador por perfil
    fperfil = _fator_perfil(perfil)
    if fperfil:
        total += fperfil["pontos"]
        fatores.append(fperfil)

    label, cor = _score_label(total)
    fator_principal = max(fatores, key=lambda f: abs(f["pontos"]))
    resumo = (
        f"Score total: {total:+d} → **{label}**. "
        f"Fator de maior peso: {fator_principal['nome']} ({fator_principal['pontos']:+d} pts). "
        f"{fator_principal['explicacao']}"
    )

    return {"score": total, "label": label, "cor": cor, "fatores": fatores, "resumo": resumo}


def calcular_score_acao(
    ticker: str,
    preco_atual: float,
    preco_medio_usuario: float,
    perfil: str,
    fund_data: dict | None = None,
) -> dict:
    """Calcula score de decisão para uma ação com base em múltiplos fatores."""
    try:
        selic = get_indices_renda_fixa()["selic"]
    except Exception:
        selic = SELIC_FALLBACK

    fatores = []
    total = 0

    # Fator 1 — Consenso dos analistas (peso 2)
    rec = get_recomendacoes_analistas(ticker)
    consenso = rec["consenso"]
    num_analistas = rec["num_analistas"]
    _mapa_consenso = {
        "strongBuy": ("Forte compra", 2),
        "buy": ("Compra", 2),
        "hold": ("Neutro", 0),
        "sell": ("Venda", -2),
        "strongSell": ("Forte venda", -2),
    }
    if consenso and consenso in _mapa_consenso:
        label_con, pts_con = _mapa_consenso[consenso]
        explicacao_con = (
            f"Analistas recomendam {label_con} para este ativo "
            f"({num_analistas} analistas cobrindo)."
        )
    else:
        pts_con = 0
        explicacao_con = "Sem cobertura de analistas para este ativo."
    total += pts_con
    fatores.append({"nome": "Consenso dos analistas", "pontos": pts_con, "explicacao": explicacao_con})

    # Fator 2 — Preço atual vs preço alvo (peso 2)
    preco_alvo = rec["preco_alvo_medio"]
    if preco_alvo:
        upside = ((preco_alvo - preco_atual) / preco_atual) * 100
        if upside > 15:
            pts_alvo = 2
        elif upside >= 5:
            pts_alvo = 1
        elif upside >= -5:
            pts_alvo = 0
        else:
            pts_alvo = -2
        direcao = "upside" if upside >= 0 else "downside"
        explicacao_alvo = (
            f"Preço alvo médio dos analistas é R$ {preco_alvo:.2f} "
            f"({upside:+.1f}% de {direcao} em relação ao preço atual)."
        )
    else:
        pts_alvo = 0
        explicacao_alvo = "Preço alvo não disponível para este ativo."
    total += pts_alvo
    fatores.append({"nome": "Preço alvo dos analistas", "pontos": pts_alvo, "explicacao": explicacao_alvo})

    # Fator 3 — P/L (peso 1)
    fund = fund_data if fund_data is not None else get_dados_fundamentus(ticker)
    pl = fund["pl"]
    if pl is not None and pl > 0:
        if pl < 10:
            pts_pl, nivel_pl = 1, "Barato"
        elif pl <= 25:
            pts_pl, nivel_pl = 0, "Neutro"
        else:
            pts_pl, nivel_pl = -1, "Caro"
        explicacao_pl = (
            f"P/L de {pl:.1f}: o mercado paga R$ {pl:.2f} para cada R$ 1,00 de lucro. "
            f"{nivel_pl} em relação ao mercado geral."
        )
    else:
        pts_pl = 0
        explicacao_pl = "P/L não disponível para este ativo."
    total += pts_pl
    fatores.append({"nome": "P/L (Preço/Lucro)", "pontos": pts_pl, "explicacao": explicacao_pl})

    # Fator 4 — Dividend Yield vs Selic (peso 1)
    dy = fund["dy"]
    if dy is not None:
        if dy >= selic:
            pts_dy = 1
            nivel_dy = "supera"
        elif dy >= selic * 0.7:
            pts_dy = 0
            nivel_dy = "está próximo da"
        else:
            pts_dy = -1
            nivel_dy = "está abaixo da"
        explicacao_dy = f"Dividend yield de {dy:.2f}% {nivel_dy} Selic atual de {selic:.1f}%."
    else:
        pts_dy = 0
        explicacao_dy = "Dividend yield não disponível para este ativo."
    total += pts_dy
    fatores.append({"nome": "Dividend Yield vs Selic", "pontos": pts_dy, "explicacao": explicacao_dy})

    # Fator 5 — Posição do usuário (peso 1)
    fpos = _fator_posicao(preco_atual, preco_medio_usuario)
    total += fpos["pontos"]
    fatores.append(fpos)

    # Fator 6 — Modificador por perfil
    fperfil = _fator_perfil(perfil)
    if fperfil:
        total += fperfil["pontos"]
        fatores.append(fperfil)

    label, cor = _score_label(total)
    fator_principal = max(fatores, key=lambda f: abs(f["pontos"]))
    resumo = (
        f"Score total: {total:+d} → **{label}**. "
        f"Fator de maior peso: {fator_principal['nome']} ({fator_principal['pontos']:+d} pts). "
        f"{fator_principal['explicacao']}"
    )

    return {"score": total, "label": label, "cor": cor, "fatores": fatores, "resumo": resumo}


def _parse_data(data_str: str | None) -> date | None:
    """Converte string DD/MM/AAAA para date. Retorna None se inválido."""
    if not data_str:
        return None
    try:
        dia, mes, ano = data_str.split("/")
        return date(int(ano), int(mes), int(dia))
    except Exception:
        return None


def calcular_renda_fixa() -> list[dict]:
    """Retorna ativos de renda fixa com cálculos de rentabilidade e vencimento."""
    indices = get_indices_renda_fixa()
    ipca_anual = ((1 + indices["ipca"] / 100) ** 12 - 1) * 100
    hoje = date.today()
    resultado = []

    for ativo in get_ativos_por_classe("Renda Fixa"):
        # --- Vencimento ---
        venc = _parse_data(ativo.get("vencimento"))
        dias_para_vencer = (venc - hoje).days if venc else None
        if dias_para_vencer is None:
            status = "Sem vencimento"
        elif dias_para_vencer <= 0:
            status = "Vencido"
        elif dias_para_vencer <= 90:
            status = "Vence em breve"
        elif dias_para_vencer <= 365:
            status = "Vence em 1 ano"
        else:
            status = "Longo prazo"

        # --- Dias aplicado ---
        aplic = _parse_data(ativo.get("data_aplicacao"))
        dias_aplicado = (hoje - aplic).days if aplic else None

        # --- Taxa efetiva anual ---
        tipo = ativo.get("tipo_rentabilidade")
        taxa = ativo.get("taxa")
        if tipo == "Prefixado" and taxa is not None:
            taxa_efetiva = taxa
        elif tipo == "% do CDI" and taxa is not None:
            taxa_efetiva = (taxa / 100) * indices["cdi"]
        elif tipo == "CDI+" and taxa is not None:
            taxa_efetiva = indices["cdi"] + taxa
        elif tipo == "IPCA+" and taxa is not None:
            taxa_efetiva = ipca_anual + taxa
        else:
            taxa_efetiva = indices["selic"]

        # --- Rentabilidade acumulada ---
        valor_investido = ativo["preco_medio"]
        if dias_aplicado is not None and dias_aplicado > 0:
            rendimento_pct = ((1 + taxa_efetiva / 100) ** (dias_aplicado / 365) - 1) * 100
        else:
            rendimento_pct = None

        valor_atual = (
            valor_investido * (1 + rendimento_pct / 100)
            if rendimento_pct is not None else valor_investido
        )
        rendimento_rs = valor_atual - valor_investido

        # --- Valor no vencimento ---
        if dias_para_vencer is not None and dias_para_vencer <= 0:
            valor_vencimento = valor_atual
        elif dias_aplicado is not None and dias_para_vencer is not None:
            dias_total = dias_aplicado + dias_para_vencer
            valor_vencimento = valor_investido * (1 + taxa_efetiva / 100) ** (dias_total / 365)
        else:
            valor_vencimento = None

        resultado.append({
            **ativo,
            "dias_para_vencer": dias_para_vencer,
            "status_vencimento": status,
            "dias_aplicado": dias_aplicado,
            "taxa_efetiva_anual": taxa_efetiva,
            "rendimento_acumulado_pct": rendimento_pct,
            "rendimento_acumulado_rs": rendimento_rs,
            "valor_atual_estimado": valor_atual,
            "valor_no_vencimento": valor_vencimento,
        })

    return resultado


def calcular_alocacao_atual() -> dict[str, float]:
    """Retorna percentual do valor total por classe de ativo."""
    carteira = calcular_carteira()
    if not carteira:
        return {}

    totais: dict[str, float] = {}
    for ativo in carteira:
        totais[ativo["classe"]] = totais.get(ativo["classe"], 0.0) + ativo["valor_atual"]

    total_geral = sum(totais.values())
    return {classe: round(valor / total_geral * 100, 2) for classe, valor in totais.items()}


def salvar_snapshot_patrimonio() -> None:
    """Salva ou atualiza o valor total da carteira no histórico de hoje."""
    try:
        carteira = calcular_carteira()
        if not carteira:
            return
        valor_total = sum(a["valor_atual"] for a in carteira)
        hoje = date.today().strftime("%d/%m/%Y")
        data = _load()
        historico = data.setdefault("historico_patrimonio", [])
        for entrada in historico:
            if entrada["data"] == hoje:
                entrada["valor"] = round(valor_total, 2)
                _dump(data)
                return
        historico.append({"data": hoje, "valor": round(valor_total, 2)})
        _dump(data)
    except Exception:
        pass


def get_historico_patrimonio() -> list:
    return _load().get("historico_patrimonio", [])


def calcular_rentabilidade_historico(historico: list) -> dict | None:
    """Calcula rentabilidade total e anualizada do histórico."""
    if len(historico) < 2:
        return None
    try:
        from datetime import datetime as _dt
        primeiro = historico[0]
        ultimo   = historico[-1]
        v0 = primeiro["valor"]
        v1 = ultimo["valor"]
        if v0 == 0:
            return None
        d0 = _dt.strptime(primeiro["data"], "%d/%m/%Y")
        d1 = _dt.strptime(ultimo["data"],   "%d/%m/%Y")
        dias = max((d1 - d0).days, 1)
        rent_total = (v1 - v0) / v0 * 100
        rent_anual = ((v1 / v0) ** (365 / dias) - 1) * 100
        return {
            "rentabilidade_total":       round(rent_total, 2),
            "rentabilidade_anualizada":  round(rent_anual, 2),
            "dias":                      dias,
        }
    except Exception:
        return None
