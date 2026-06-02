import requests
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
    """Retorna indicadores de mercado de um FII via yfinance.

    Se pvp não disponível no yfinance, usa o valor cadastrado pelo usuário.
    """
    vazio = {
        "dy_anual": None, "dy_mensal": None, "dividend_rate": None,
        "pvp": None, "liquidez": None,
        "preco_52s_min": None, "preco_52s_max": None,
    }
    try:
        from utils.portfolio import get_ativos
        info = yf.Ticker(ticker + ".SA").info

        dy_raw = info.get("dividendYield")
        if dy_raw is not None:
            dy_anual = dy_raw if dy_raw > 1 else dy_raw * 100
        else:
            dy_anual = None
        dy_mensal = round(dy_anual / 12, 4) if dy_anual is not None else None

        pvp_cadastro = next(
            (a.get("pvp") for a in get_ativos() if a["ticker"] == ticker.upper()),
            None,
        )

        return {
            "dy_anual": dy_anual,
            "dy_mensal": dy_mensal,
            "dividend_rate": info.get("dividendRate"),
            "pvp": pvp_cadastro,
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


def get_indices_renda_fixa() -> dict:
    """Busca Selic, CDI e IPCA atuais na API do Banco Central.

    Selic e CDI vêm como taxa diária e são anualizados por 252 dias úteis.
    IPCA vem como taxa mensal e é retornado diretamente.
    """
    fallback = {"selic": 13.75, "cdi": 13.65, "ipca": 0.67, "data_atualizacao": "N/A"}
    _urls = {
        "selic": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados/ultimos/1?formato=json",
        "cdi":   "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados/ultimos/1?formato=json",
        "ipca":  "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados/ultimos/1?formato=json",
    }

    def _anualizar(taxa_diaria: float) -> float:
        return ((1 + taxa_diaria / 100) ** 252 - 1) * 100

    try:
        resultados = {}
        data_atualizacao = "N/A"
        for chave, url in _urls.items():
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            item = resp.json()[0]
            valor = float(item["valor"])
            resultados[chave] = _anualizar(valor) if chave in ("selic", "cdi") else valor
            if chave == "selic":
                data_atualizacao = item["data"]
        return {**resultados, "data_atualizacao": data_atualizacao}
    except Exception:
        return fallback


def detectar_moeda(ticker: str) -> str:
    """Retorna 'USD' para tickers sem sufixo .SA, 'BRL' para os demais."""
    t = ticker.upper()
    if t.endswith("-USD") or t.endswith("=F"):
        return "USD"
    return "BRL"


def detectar_casas_decimais(ticker: str) -> int:
    """Retorna 8 casas para criptos, 2 para demais alternativos."""
    t = ticker.upper()
    if "BTC" in t or "ETH" in t:
        return 8
    return 2


def get_dados_ativo_alternativo(ticker: str) -> dict | None:
    """Retorna preço atual, variações e histórico de um ativo alternativo."""
    try:
        ativo = yf.Ticker(ticker)
        fi = ativo.fast_info
        hist = ativo.history(period="1y")

        preco_atual = float(fi.last_price)
        preco_anterior = float(fi.previous_close)
        variacao_diaria = ((preco_atual - preco_anterior) / preco_anterior) * 100

        closes = hist["Close"]
        preco_7d = float(closes.iloc[-7]) if len(closes) >= 7 else None
        preco_30d = float(closes.iloc[-30]) if len(closes) >= 30 else None

        return {
            "preco_atual": preco_atual,
            "preco_anterior": preco_anterior,
            "variacao_diaria_pct": variacao_diaria,
            "historico": hist,
            "variacao_7d_pct": ((preco_atual - preco_7d) / preco_7d * 100) if preco_7d else None,
            "variacao_30d_pct": ((preco_atual - preco_30d) / preco_30d * 100) if preco_30d else None,
        }
    except Exception:
        return None


def get_dados_alternativos() -> dict | None:
    """Retorna preço e variações de Bitcoin, Ouro e Prata em USD."""
    _tickers = {"Bitcoin": "BTC-USD", "Ouro": "GC=F", "Prata": "SI=F"}
    try:
        dados = yf.download(
            list(_tickers.values()), period="1y",
            auto_adjust=True, progress=False,
        )
        closes = dados["Close"].dropna()
        resultado = {}
        for nome, ticker in _tickers.items():
            serie = closes[ticker].dropna()
            if len(serie) < 2:
                continue
            preco = float(serie.iloc[-1])
            resultado[nome] = {
                "preco_atual": preco,
                "variacao_1d":  ((preco / float(serie.iloc[-2])) - 1) * 100 if len(serie) >= 2 else None,
                "variacao_7d":  ((preco / float(serie.iloc[-7])) - 1) * 100 if len(serie) >= 7 else None,
                "variacao_30d": ((preco / float(serie.iloc[-30])) - 1) * 100 if len(serie) >= 30 else None,
                "variacao_12m": ((preco / float(serie.iloc[0])) - 1) * 100,
                "historico_normalizado": serie / float(serie.iloc[0]) * 100,
            }
        return resultado if resultado else None
    except Exception:
        return None


def get_cotacao_dolar() -> float:
    """Retorna a cotação atual do dólar em reais."""
    try:
        preco = yf.Ticker("USDBRL=X").fast_info.last_price
        return float(preco)
    except Exception:
        return 5.70


def get_correlacao_com_ibov(ticker: str) -> dict | None:
    """Calcula correlação e performance comparada de um ativo vs Ibovespa em 12 meses."""
    try:
        dados = yf.download([ticker, "^BVSP"], period="1y", auto_adjust=True, progress=False)
        closes = dados["Close"].dropna()

        retornos = closes.pct_change().dropna()
        correlacao = float(retornos[ticker].corr(retornos["^BVSP"]))

        perf_ativo = ((closes[ticker].iloc[-1] / closes[ticker].iloc[0]) - 1) * 100
        perf_ibov = ((closes["^BVSP"].iloc[-1] / closes["^BVSP"].iloc[0]) - 1) * 100

        normalizado = closes.copy()
        normalizado["Ativo"] = normalizado[ticker] / normalizado[ticker].iloc[0] * 100
        normalizado["IBOV"] = normalizado["^BVSP"] / normalizado["^BVSP"].iloc[0] * 100

        return {
            "correlacao": correlacao,
            "perf_ativo_12m": float(perf_ativo),
            "perf_ibov_12m": float(perf_ibov),
            "historico_normalizado": normalizado[["Ativo", "IBOV"]],
        }
    except Exception:
        return None


def get_contexto_macro() -> dict:
    """Retorna indicadores macroeconômicos atuais com classificações qualitativas."""
    try:
        selic = get_indices_renda_fixa()["selic"]
        vix = float(yf.Ticker("^VIX").fast_info.last_price)
        dolar = get_cotacao_dolar()

        hist_ibov = yf.Ticker("^BVSP").history(period="ytd")
        ibov_no_ano = ((hist_ibov["Close"].iloc[-1] / hist_ibov["Close"].iloc[0]) - 1) * 100

        nivel_risco = "Alto" if vix > 30 else ("Moderado" if vix > 20 else "Baixo")
        atratividade_rf = "Alta" if selic > 13 else ("Moderada" if selic > 10 else "Baixa")
        momento_bolsa = "Favorável" if ibov_no_ano > 10 else ("Neutro" if ibov_no_ano > 0 else "Desfavorável")

        resumo_macro = (
            f"Selic em {selic:.1f}% a.a. torna a renda fixa {atratividade_rf.lower()}. "
            f"Ibovespa acumula {ibov_no_ano:+.1f}% no ano, "
            f"momento {momento_bolsa.lower()} para a bolsa. "
            f"VIX em {vix:.1f} indica risco global {nivel_risco.lower()}. "
            f"Dólar a R\$ {dolar:.2f}."
        )

        return {
            "selic": selic,
            "vix": vix,
            "ibov_no_ano": float(ibov_no_ano),
            "dolar": dolar,
            "nivel_risco": nivel_risco,
            "atratividade_renda_fixa": atratividade_rf,
            "momento_bolsa": momento_bolsa,
            "resumo_macro": resumo_macro,
        }
    except Exception:
        return {
            "selic": 13.75, "vix": 18.0, "ibov_no_ano": 0.0, "dolar": 5.70,
            "nivel_risco": "Moderado", "atratividade_renda_fixa": "Alta",
            "momento_bolsa": "Neutro",
            "resumo_macro": "Dados macroeconômicos temporariamente indisponíveis.",
        }


def get_preco_entrada_saida(ticker: str, classe: str) -> dict:
    """Calcula preços de entrada e saída sugeridos para um ativo."""
    fallback = {
        "preco_atual": None, "preco_alvo": None, "upside": None,
        "num_analistas": 0,
        "entrada_texto": "Consulte sua corretora",
        "saida_texto": "Consulte sua corretora",
    }
    try:
        symbol = ticker if classe == "Alternativos" else ticker + ".SA"
        ativo_yf = yf.Ticker(symbol)
        preco_atual = float(ativo_yf.fast_info.last_price)

        targets = ativo_yf.analyst_price_targets
        preco_alvo = float(targets.get("mean")) if isinstance(targets, dict) and targets.get("mean") else None
        num_analistas = int(targets.get("numberOfAnalysts", 0)) if isinstance(targets, dict) else 0

        fund = get_dados_fundamentus(ticker) if classe == "Ações" else {"pl": None, "dy": None}

        # Entrada
        if preco_alvo:
            upside = ((preco_alvo - preco_atual) / preco_atual) * 100
            if upside > 5:
                entrada_texto = f"Até R\$ {preco_atual * 1.03:.2f} (3% acima do atual)"
            else:
                entrada_texto = "Aguardar correção"
        elif fund.get("pl") and fund["pl"] > 0:
            entrada_texto = (
                f"Até R\$ {preco_atual * 1.05:.2f} (P/L atrativo)"
                if fund["pl"] < 15
                else "Aguardar melhor ponto de entrada"
            )
            upside = None
        else:
            upside = None
            entrada_texto = "Consulte sua corretora"

        # Saída
        if preco_alvo:
            saida_texto = f"R\$ {preco_alvo:.2f} (preço alvo médio de {num_analistas} analistas)"
        elif fund.get("pl") and fund["pl"] > 0:
            pl_alvo = 20
            lpa = preco_atual / fund["pl"]
            preco_justo = lpa * pl_alvo
            saida_texto = f"R\$ {preco_justo:.2f} (baseado em P/L alvo de {pl_alvo}x)"
        else:
            saida_texto = "Consulte sua corretora"

        # Branch FIIs: complementa ou substitui cálculo via P/VP
        if classe == "FIIs" and saida_texto == "Consulte sua corretora":
            fii_fund = get_dados_yfinance_fii(ticker)
            pvp = fii_fund.get("pvp")
            if pvp is not None:
                if pvp < 1.0:
                    preco_patrimonial = preco_atual / pvp
                    entrada_texto = (
                        f"Até R\$ {preco_atual * 1.02:.2f} "
                        f"(P/VP de {pvp:.2f}, abaixo do patrimônio)"
                    )
                    saida_texto = (
                        f"R\$ {preco_patrimonial:.2f} "
                        f"(cota patrimonial, P/VP = 1.0)"
                    )
                elif pvp < 1.1:
                    entrada_texto = "Preço próximo do justo, aguardar correção"
                    saida_texto = (
                        f"R\$ {preco_atual * 1.08:.2f} "
                        f"(estimativa +8% sobre preço atual)"
                    )
                else:
                    entrada_texto = "P/VP elevado, aguardar correção"
                    saida_texto = "Realizar lucro no preço atual"

        if preco_alvo:
            upside = ((preco_alvo - preco_atual) / preco_atual) * 100

        return {
            "preco_atual": preco_atual,
            "preco_alvo": preco_alvo,
            "upside": upside,
            "num_analistas": num_analistas,
            "entrada_texto": entrada_texto,
            "saida_texto": saida_texto,
        }
    except Exception:
        return fallback
