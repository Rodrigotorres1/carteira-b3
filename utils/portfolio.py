import json
from pathlib import Path

from utils.market_data import (
    get_dados_fundamentus,
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
            f"P/L de {pl:.1f}: o mercado paga R$ {pl:.2f} para cada R$ 1 de lucro. "
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
    var_pos = ((preco_atual - preco_medio_usuario) / preco_medio_usuario) * 100
    if var_pos < -10:
        pts_pos = 1
        explicacao_pos = (
            f"Seu preço médio é R$ {preco_medio_usuario:.2f}. "
            f"O ativo está {abs(var_pos):.1f}% abaixo do seu custo médio — "
            f"possível oportunidade de aporte."
        )
    elif var_pos <= 20:
        pts_pos = 0
        direcao_pos = "acima" if var_pos >= 0 else "abaixo"
        explicacao_pos = (
            f"Seu preço médio é R$ {preco_medio_usuario:.2f}. "
            f"O ativo está {abs(var_pos):.1f}% {direcao_pos} do seu custo médio."
        )
    else:
        pts_pos = -1
        explicacao_pos = (
            f"Seu preço médio é R$ {preco_medio_usuario:.2f}. "
            f"O ativo está {var_pos:.1f}% acima do seu custo médio — "
            f"considere realizar parte do lucro."
        )
    total += pts_pos
    fatores.append({"nome": "Sua posição na carteira", "pontos": pts_pos, "explicacao": explicacao_pos})

    # Fator 6 — Modificador por perfil
    if perfil == "conservador":
        total -= 1
        fatores.append({
            "nome": "Modificador de perfil",
            "pontos": -1,
            "explicacao": "Perfil conservador: recomendação ajustada para maior cautela.",
        })
    elif perfil == "arrojado":
        total += 1
        fatores.append({
            "nome": "Modificador de perfil",
            "pontos": 1,
            "explicacao": "Perfil arrojado: recomendação ajustada para maior tolerância a risco.",
        })

    # Label e cor final
    if total >= 4:
        label, cor = "Comprar", "success"
    elif total >= 1:
        label, cor = "Manter", "info"
    else:
        label, cor = "Vender", "warning"

    # Resumo textual
    fator_principal = max(fatores, key=lambda f: abs(f["pontos"]))
    resumo = (
        f"Score total: {total:+d} → **{label}**. "
        f"Fator de maior peso: {fator_principal['nome']} ({fator_principal['pontos']:+d} pts). "
        f"{fator_principal['explicacao']}"
    )

    return {
        "score": total,
        "label": label,
        "cor": cor,
        "fatores": fatores,
        "resumo": resumo,
    }


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
