import json
from pathlib import Path

from datetime import date

from utils.market_data import (
    get_dados_fundamentus,
    get_dados_yfinance_fii,
    get_indices_renda_fixa,
    get_preco_atual,
    get_recomendacoes_analistas,
)

_DATA_PATH = Path(__file__).parent.parent / "data" / "carteira.json"


def _load() -> dict:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _dump(data: dict) -> None:
    with open(_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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
) -> None:
    """Adiciona ativo à carteira. vencimento em formato DD/MM/AAAA, apenas para Renda Fixa."""
    ativo = {
        "ticker": ticker.upper(),
        "quantidade": quantidade,
        "preco_medio": preco_medio,
        "classe": classe,
    }
    if vencimento:
        ativo["vencimento"] = vencimento
    data = _load()
    data.setdefault("ativos", []).append(ativo)
    _dump(data)


def remove_ativo(ticker: str) -> None:
    data = _load()
    data["ativos"] = [a for a in data.get("ativos", []) if a["ticker"] != ticker.upper()]
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
) -> dict:
    """Calcula score de decisão para um FII com base em DY mensal, range 52s e posição."""
    DY_MENSAL_BOM = 0.8
    DY_MENSAL_MINIMO = 0.5

    fatores = []
    total = 0

    fund = get_dados_yfinance_fii(ticker)

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
        range_txt = f"R\$ {p_min:.2f} a R\$ {p_max:.2f}"
        if posicao_range <= 30:
            pts_52s = 1
            explicacao_52s = (
                f"Cota próxima da mínima do range de 52 semanas ({range_txt}): "
                f"oportunidade de entrada."
            )
        elif posicao_range <= 70:
            pts_52s = 0
            explicacao_52s = (
                f"Cota na metade do range de 52 semanas ({range_txt})."
            )
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

    # Fator 3 — Posição do usuário (peso 1)
    fpos = _fator_posicao(preco_atual, preco_medio_usuario)
    total += fpos["pontos"]
    fatores.append(fpos)

    # Fator 4 — Modificador por perfil
    fperfil = _fator_perfil(perfil)
    if fperfil:
        total += fperfil["pontos"]
        fatores.append(fperfil)

    if total >= 3:
        label, cor = "Comprar", "success"
    elif total >= 1:
        label, cor = "Manter", "info"
    else:
        label, cor = "Vender", "warning"

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
) -> dict:
    """Calcula score de decisão para uma ação com base em múltiplos fatores."""
    SELIC = 10.5
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
    fund = get_dados_fundamentus(ticker)
    pl = fund["pl"]
    if pl is not None and pl > 0:
        if pl < 10:
            pts_pl, nivel_pl = 1, "Barato"
        elif pl <= 25:
            pts_pl, nivel_pl = 0, "Neutro"
        else:
            pts_pl, nivel_pl = -1, "Caro"
        explicacao_pl = (
            f"P/L de {pl:.1f}: o mercado paga R\$ {pl:.2f} para cada R\$ 1,00 de lucro. "
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
        if dy >= SELIC:
            pts_dy = 1
            nivel_dy = "supera"
        elif dy >= SELIC * 0.7:
            pts_dy = 0
            nivel_dy = "está próximo da"
        else:
            pts_dy = -1
            nivel_dy = "está abaixo da"
        explicacao_dy = (
            f"Dividend yield de {dy:.2f}% {nivel_dy} Selic atual de {SELIC}%."
        )
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


def calcular_renda_fixa() -> list[dict]:
    """Retorna ativos de renda fixa enriquecidos com status de vencimento."""
    indices = get_indices_renda_fixa()
    rentabilidade_estimada = indices["selic"]
    hoje = date.today()
    resultado = []

    for ativo in get_ativos_por_classe("Renda Fixa"):
        vencimento_str = ativo.get("vencimento")
        dias = None
        status = "Sem vencimento"

        if vencimento_str:
            try:
                dia, mes, ano = vencimento_str.split("/")
                venc = date(int(ano), int(mes), int(dia))
                dias = (venc - hoje).days
                if dias <= 0:
                    status = "Vencido"
                elif dias <= 90:
                    status = "Vence em breve"
                elif dias <= 365:
                    status = "Vence em 1 ano"
                else:
                    status = "Longo prazo"
            except Exception:
                pass

        resultado.append({
            **ativo,
            "dias_para_vencer": dias,
            "status_vencimento": status,
            "rentabilidade_estimada_anual": rentabilidade_estimada,
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
