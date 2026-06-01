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


def get_recomendacoes_analistas(ticker: str) -> dict:
    """Retorna consenso de analistas e preço alvo para uma ação da B3."""
    vazio = {"consenso": None, "preco_alvo_medio": None, "num_analistas": 0}
    try:
        ativo = yf.Ticker(ticker + ".SA")

        rec = ativo.recommendations
        consenso = None
        num_analistas = 0
        if rec is not None and not rec.empty:
            ultima = rec.iloc[-1]
            colunas = {"strongBuy", "buy", "hold", "sell", "strongSell"}
            presentes = colunas & set(rec.columns)
            num_analistas = int(sum(ultima.get(c, 0) for c in presentes))
            for col in ("strongBuy", "buy", "hold", "sell", "strongSell"):
                if col in rec.columns and ultima.get(col, 0) == max(
                    ultima.get(c, 0) for c in presentes
                ):
                    consenso = col
                    break

        targets = ativo.analyst_price_targets
        preco_alvo = targets.get("mean", None) if isinstance(targets, dict) else None

        return {
            "consenso": consenso,
            "preco_alvo_medio": float(preco_alvo) if preco_alvo else None,
            "num_analistas": num_analistas,
        }
    except Exception:
        return vazio


def _converter_valor_fundamentus(valor) -> float | None:
    """Converte string do fundamentus para float.

    Regras:
    - Com "%": remove "%" e converte (já está em percentual)
    - Sem "%" e sem vírgula/ponto: converte e divide por 100 (ex: "809" → 8.09)
    - Sem "%" mas com vírgula ou ponto: substitui "," por "." e converte
    """
    try:
        s = str(valor).strip()
        if not s:
            return None
        if "%" in s:
            return float(s.replace("%", "").strip())
        if "," not in s and "." not in s:
            return float(s) / 100
        return float(s.replace(",", "."))
    except Exception:
        return None


def get_dados_fii(ticker: str) -> dict | None:
    """Retorna preço, variação e histórico de um FII da B3."""
    try:
        symbol = ticker + ".SA"
        ativo = yf.Ticker(symbol)
        fi = ativo.fast_info
        info = ativo.info

        preco_atual = float(fi.last_price)
        preco_anterior = float(fi.previous_close)
        variacao_pct = ((preco_atual - preco_anterior) / preco_anterior) * 100

        return {
            "preco_atual": preco_atual,
            "preco_anterior": preco_anterior,
            "variacao_pct": variacao_pct,
            "nome": info.get("shortName", ticker),
            "historico": ativo.history(period="1y"),
        }
    except Exception:
        return None


def get_dados_yfinance_fii(ticker: str) -> dict:
    """Retorna indicadores de mercado de um FII via yfinance."""
    vazio = {
        "dy_anual": None, "dy_mensal": None, "dividend_rate": None,
        "pvp": None, "liquidez": None,
        "preco_52s_min": None, "preco_52s_max": None,
    }
    try:
        info = yf.Ticker(ticker + ".SA").info

        dy_raw = info.get("dividendYield")
        if dy_raw is not None:
            dy_anual = dy_raw if dy_raw > 1 else dy_raw * 100
        else:
            dy_anual = None
        dy_mensal = round(dy_anual / 12, 4) if dy_anual is not None else None

        return {
            "dy_anual": dy_anual,
            "dy_mensal": dy_mensal,
            "dividend_rate": info.get("dividendRate"),
            "pvp": None,
            "liquidez": info.get("averageVolume"),
            "preco_52s_min": info.get("fiftyTwoWeekLow"),
            "preco_52s_max": info.get("fiftyTwoWeekHigh"),
        }
    except Exception:
        return vazio


def get_dados_fundamentus(ticker: str) -> dict:
    """Retorna indicadores fundamentalistas via fundamentus."""
    vazio = {"pl": None, "dy": None, "pvp": None, "roe": None}
    try:
        import fundamentus as fd
        df = fd.get_papel(ticker)
        if df is None or df.empty:
            return vazio
        row = df.iloc[0]
        return {
            "pl":  _converter_valor_fundamentus(row["PL"]),
            "dy":  _converter_valor_fundamentus(row["Div_Yield"]),
            "pvp": _converter_valor_fundamentus(row["PVP"]),
            "roe": _converter_valor_fundamentus(row["ROE"]),
        }
    except Exception:
        return vazio
