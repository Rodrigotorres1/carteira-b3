from utils.database import carregar_dados, salvar_dados

_ALOCACOES = {
    "conservador": {"acoes": 15, "fiis": 20, "renda_fixa": 60, "alternativos": 5},
    "moderado":    {"acoes": 35, "fiis": 25, "renda_fixa": 30, "alternativos": 10},
    "arrojado":    {"acoes": 55, "fiis": 15, "renda_fixa": 15, "alternativos": 15},
}


def _load() -> dict:
    return carregar_dados()


def _dump(data: dict) -> None:
    salvar_dados(data)


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
