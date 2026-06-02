# Carteira B3

> Aplicação web para investidores iniciantes brasileiros gerenciarem sua carteira na B3 com inteligência.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Sobre o Projeto

Carteira B3 é uma aplicação Streamlit que centraliza a gestão de investimentos para investidores iniciantes brasileiros. O usuário cadastra sua carteira, define seu perfil de risco e recebe análises automáticas baseadas em dados reais de mercado.

O projeto consome dados de múltiplas fontes gratuitas:
- yfinance para cotações em tempo real de ações, FIIs, Bitcoin, Ouro e Prata
- API do Banco Central do Brasil para Selic, CDI e IPCA
- Fundamentus para dados fundamentalistas de ações brasileiras
- VIX (^VIX) como termômetro de risco global

---

## Funcionalidades

### Gestão de Carteira
- Cadastro de ativos por classe: Ações, FIIs, Renda Fixa e Alternativos
- Campos específicos por classe: P/VP para FIIs, taxa e vencimento para Renda Fixa, precisão de 8 casas decimais para criptomoedas
- Persistência local em JSON

### Perfil do Investidor
- Onboarding com três perfis: Conservador, Moderado e Arrojado
- Alocação alvo definida automaticamente por perfil
- Recomendações e scores ajustados conforme o perfil

### Painel de Alocação
- Comparativo visual entre alocação atual e alvo
- Alertas de rebalanceamento com três níveis de urgência
- Gráficos de pizza lado a lado com Plotly

### Painel de Ações
- Score de decisão por ativo: Comprar, Manter ou Vender
- Fontes do score: consenso de analistas via yfinance, preço alvo médio, P/L e DY via Fundamentus, posição do usuário e perfil de risco
- Explicação detalhada de cada fator do score
- Histórico de preços 12 meses

### Painel de FIIs
- DY mensal, range de 52 semanas e posição do usuário
- P/VP cadastrado pelo usuário integrado ao score
- Score adaptado para a lógica específica de fundos imobiliários

### Renda Fixa
- Suporte a Prefixado, % do CDI, CDI+ e IPCA+
- Cálculo de rentabilidade acumulada e projetada até o vencimento
- Comparativo com Selic, CDI e IPCA em tempo real via API BCB
- Barra de progresso do prazo e alertas de vencimento

### Alternativos
- Suporte genérico a qualquer ativo cotado em USD (BTC-USD, GC=F) ou BRL (GOLD11)
- Correlação com Ibovespa nos últimos 12 meses
- Comparativo de performance entre Bitcoin, Ouro e Prata

### Sugestões de Ativos
- Sugestões por perfil e objetivo: Renda, Crescimento ou Combinado
- Contexto macroeconômico automático: Selic, VIX, IBOV no ano, dólar
- Alertas de impacto macro por ativo e por perfil
- Preço de entrada sugerido e alvo de saída baseados em analistas e indicadores fundamentalistas
- Indicação de ativos já presentes na carteira do usuário

---

## Stack

| Tecnologia | Uso |
|---|---|
| Python 3.11+ | Linguagem principal |
| Streamlit 1.35 | Interface web |
| yfinance | Cotações e dados de mercado |
| pandas | Manipulação de dados |
| Plotly | Visualizações interativas |
| Fundamentus | Dados fundamentalistas BR |
| requests | API do Banco Central |

---

## Como Rodar

### Pré-requisitos
- Python 3.11+
- Git

### Instalação

```bash
# Clone o repositório
git clone https://github.com/Rodrigotorres1/carteira-b3.git
cd carteira-b3

# Crie o ambiente virtual
python -m venv .venv

# Ative o ambiente (Windows)
.venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Rode a aplicação
streamlit run App.py
```

A aplicação abre automaticamente em `http://localhost:8501`

---

## Estrutura do Projeto

```
carteira-b3/
├── App.py                  # Entry point e navegação
├── pages/
│   ├── 01_Carteira.py      # Cadastro de ativos
│   ├── 02_Alocação.py      # Alocação atual vs alvo
│   ├── 03_Ações.py         # Painel de ações com score
│   ├── 04_FIIs.py          # Painel de FIIs
│   ├── 05_Renda_Fixa.py    # Renda fixa e benchmarks
│   ├── 06_Alternativo.py   # Bitcoin e outros alternativos
│   └── 07_Sugestões.py     # Sugestões por perfil e macro
├── utils/
│   ├── portfolio.py        # Lógica de carteira e scores
│   ├── market_data.py      # Integração com APIs e yfinance
│   ├── profile.py          # Perfil do investidor
│   └── sugestoes.py        # Base de sugestões por perfil
├── components/             # Componentes visuais reutilizáveis
├── data/
│   └── carteira.json       # Dados locais do usuário
├── CLAUDE.md               # Guia para desenvolvimento com IA
├── requirements.txt
└── README.md
```

---

## Decisões Técnicas

**Persistência em JSON local**
Escolha intencional para um projeto local sem dependência de banco de dados externo. Simples, legível e portável.

**Score de decisão multicritério**
O score combina fontes distintas com pesos diferentes, tornando a recomendação mais robusta do que usar um único indicador. Cada fator é explicado ao usuário em linguagem simples.

**P/VP de FIIs via cadastro do usuário**
APIs gratuitas não fornecem P/VP para FIIs brasileiros. A solução adotada foi permitir que o usuário informe o valor uma vez, que é propagado automaticamente para o score e as sugestões. Mais preciso que scraping frágil.

**Contexto macro automático**
Selic via API BCB, VIX via yfinance e IBOV YTD calculado sobre o histórico. Quatro indicadores combinados geram alertas contextualizados por perfil de investidor, sem dependência de APIs pagas de análise.

**Detecção automática de moeda para alternativos**
Tickers terminando em `-USD` ou `=F` são tratados como cotados em USD. Demais tickers como BRL. Isso permite suportar tanto Bitcoin quanto ETFs brasileiros como GOLD11 sem configuração manual.

---

## Aviso Legal

Este projeto é de uso educacional e pessoal. As sugestões e scores gerados não constituem recomendação de investimento. Consulte um assessor de investimentos certificado (AAI) antes de tomar decisões financeiras.

---

## Autor

**Rodrigo Torres**  
Estudante de Ciência da Computação — Recife, PE  
[GitHub](https://github.com/Rodrigotorres1)

---

*Desenvolvido com Python, Streamlit e dados públicos de mercado brasileiro.*
