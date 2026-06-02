import json
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent / "data" / "carteira.json"

_ALOCACOES = {
    "conservador": {"acoes": 15, "fiis": 20, "renda_fixa": 60, "alternativos": 5},
    "moderado":    {"acoes": 35, "fiis": 25, "renda_fixa": 30, "alternativos": 10},
    "arrojado":    {"acoes": 55, "fiis": 15, "renda_fixa": 15, "alternativos": 15},
}


def _load() -> dict:
    if not _DATA_PATH.exists():
        _DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        _dump({})
        return {}
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _dump(data: dict) -> None:
    with open(_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def profile_exists() -> bool:
    return "perfil" in _load()


def get_profile() -> str:
    return _load()["perfil"]


def get_alocacao_alvo() -> dict:
    return _load()["alocacao_alvo"]


def save_profile(perfil: str) -> None:
    data = _load()
    data["perfil"] = perfil
    data["alocacao_alvo"] = _ALOCACOES[perfil]
    _dump(data)
