# carteira-b3

## Contexto do projeto
Aplicação Streamlit para investidores iniciantes brasileiros gerenciarem
sua carteira na B3. Desenvolvido por estudante de Ciência da Computação
visando estágio em Data Science.

## Stack
- Python 3.11+
- Streamlit 1.35
- yfinance, pandas, plotly

## Estrutura
- app.py: entry point e navegação
- pages/: uma página por funcionalidade
- utils/: lógica de negócio separada da UI
- components/: elementos visuais reutilizáveis
- data/carteira.json: persistência local

## Padrões de código
- Funções com docstring em português
- Variáveis e funções em snake_case
- Constantes em MAIÚSCULO no topo do arquivo
- Separar lógica de negócio (utils/) da interface (pages/)
- Nunca repetir lógica de leitura/escrita do JSON fora de utils/

## Idioma dos outputs
- Todos os textos exibidos na interface em português
- Primeira letra maiúscula em títulos, labels, mensagens e botões
- Mensagens de erro, sucesso e aviso também em português
- Nomes de colunas em dataframes em português com primeira letra maiúscula
  Exemplos: "Ticker", "Classe", "Quantidade", "Preço médio", "Valor atual"

## Commits
- Padrão: feat:, fix:, refactor:, docs:
- Mensagem em português
- Um commit por etapa concluída

## O que evitar
- Não usar st.experimental_ (APIs depreciadas)
- Não instalar bibliotecas fora do requirements.txt sem avisar
- Não hardcodar caminhos de arquivo, usar PATH constante em utils/
- Não misturar lógica de cálculo dentro dos arquivos de pages/
