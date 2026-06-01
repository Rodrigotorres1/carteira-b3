import json
from pathlib import Path

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
