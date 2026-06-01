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


def get_dados_acao(ticker: str) -> dict | None:
    """Retorna dados fundamentalistas e histórico de uma ação da B3."""
    try:
        symbol = ticker + ".SA"
        ativo = yf.Ticker(symbol)
        fi = ativo.fast_info
        info = ativo.info

        preco_atual = float(fi.last_price)
        preco_anterior = float(fi.previous_close)
        variacao_pct = ((preco_atual - preco_anterior) / preco_anterior) * 100

        dy_raw = info.get("dividendYield", 0) or 0
        return {
            "preco_atual": preco_atual,
            "preco_anterior": preco_anterior,
            "variacao_pct": variacao_pct,
            "dividend_yield": dy_raw * 100,
            "pl": info.get("trailingPE", None),
            "nome": info.get("shortName", ticker),
            "historico": ativo.history(period="1y"),
        }
    except Exception:
        return None
