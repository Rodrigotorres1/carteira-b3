import json
from pathlib import Path

from utils.market_data import get_preco_atual

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


def add_ativo(ticker: str, quantidade: int, preco_medio: float, classe: str) -> None:
    data = _load()
    data.setdefault("ativos", []).append({
        "ticker": ticker.upper(),
        "quantidade": quantidade,
        "preco_medio": preco_medio,
        "classe": classe,
    })
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
