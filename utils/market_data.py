import yfinance as yf


def get_preco_atual(ticker: str, classe: str) -> float | None:
    """Busca o preço atual do ativo via yfinance. Retorna None se indisponível."""
    try:
        if classe in ("Ações", "FIIs"):
            symbol = ticker + ".SA"
        elif classe == "Alternativo" and ticker == "BTC-USD":
            symbol = ticker
        else:
            return None

        preco = yf.Ticker(symbol).fast_info.last_price
        return float(preco) if preco else None
    except Exception:
        return None
