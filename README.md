socratic-tutor — MVP
Tutor socrático passo a passo para Álgebra/Funções. Cada passo é validado com SymPy.
Regra de ouro: não dá a resposta; só faz perguntas-guia.

INSTALAÇÃO
1) Atualize o pip:
   python -m pip install -U pip
2) Instale em modo desenvolvimento:
   pip install -e ".[dev]"

TESTES E LINT
1) Ruff:
   ruff check src tests
2) Black (checar formatação):
   black --check src tests
3) Pytest:
   pytest -q

EXECUÇÃO (CLI)
Execute o tutor com um arquivo de problemas:
   socratic-tutor --problems examples/equations.yaml --student "SeuNome"