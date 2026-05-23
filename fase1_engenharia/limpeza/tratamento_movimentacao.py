import pandas as pd
import numpy as np
import dateparser
from pathlib import Path

# LEITURA
basedir = Path(__file__).resolve().parent.parent.parent
caminho_bruto = basedir / "data" / "Planilhas_sem_tratamento" / "movimentacoes.csv"
caminho_tratado = basedir / "data" / "Bases_Tratadas" / "Movimentacoes_tratado.csv"

df = pd.read_csv(caminho_bruto, sep=',', encoding='utf-8')

# função para parsing de datas
def parse_data(valor):
    if pd.notnull(valor):
        return dateparser.parse(str(valor), languages=["pt"])
    return pd.NaT

# PADRONIZAÇÃO DE NOMES
df['advogado_responsavel'] = df['advogado_responsavel'].str.upper().str.strip() # nomes dos advogados em maiúsculo
df['tipo_ato'] = df['tipo_ato'].str.lower().str.strip() # tipos de ato em minúsculo

# PADRONIZAÇÃO DE DATAS
df['data_movimentacao'] = pd.to_datetime(df['data_movimentacao'], errors='coerce', dayfirst=True, format='mixed')
df["prazo_gerado"] = df["prazo_gerado"].apply(parse_data)

mapeamento_concluido = { 
    'sim': 'Sim', 
    's': 'Sim',
    '1': 'Sim',
    'n': 'Não', 
    'não': 'Não', 
    '0': 'Não', 
    'nao': 'Não'
}
df['concluido'] = df['concluido'].astype(str).str.lower().str.strip().replace(mapeamento_concluido)

# TRATAMENTO DE NULOS
df["descricao"] = (df["descricao"].replace(r'^\s*$', np.nan, regex=True).fillna("Não informado"))
df["concluido"] = df["concluido"].fillna("Não informado")

# TRATAMENTO DE PRAZOS
# pegando possíveis datas informadas na descrição
df["data_descricao"] = df["descricao"].str.extract(r'(\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}\s+de\s+\w+\s+de\s+\d{4})')
# aplicando parsing
df["data_descricao"] = df["data_descricao"].apply(parse_data)
# nova coluna de prazo final
# usa a data na descrição se houver valor, caso não, usa a do prazo gerado
df["prazo_final"] = (df["data_descricao"].combine_first(df["prazo_gerado"]))
# nova coluna dias de prazo (citado na descrição)
df["dias_prazo"] = df["descricao"].str.extract(
    r'(\d+)\s*dias?'
)

# TRATAMENTO DUPLICATAS
# remover linhas 100% iguais
df_duplicatas = df.drop_duplicates()
print(f"Duplicatas 100% iguais: {df_duplicatas}")
# remover linhas que possuem o mesmo id
df = df.drop_duplicates(subset=['movimentacao_id'], keep='first')

# EXPORTAÇÃO
df_export = df.copy()

#formatando as datas
colunas_data = ["data_movimentacao", "prazo_gerado", "data_descricao", "prazo_final"]
for col in colunas_data:
    df_export[col] = df_export[col].dt.strftime('%Y-%m-%d')

caminho_tratado.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(caminho_tratado, sep=';', index=False, encoding='utf-8-sig')

# visualização
pd.set_option('display.max_columns', None, 'display.width', None)
print(df.dtypes) # verificar tipos
print(df.isnull().sum()) # verificar nulos

print(f"Linhas iniciais: {df.head()}")
print(f"Duplicatas removidas: {df_duplicatas}")
