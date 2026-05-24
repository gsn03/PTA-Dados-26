import pandas as pd
import numpy as np
import dateparser
from pathlib import Path

# LEITURA
basedir = Path(__file__).resolve().parent.parent.parent
caminho_bruto = basedir / "data" / "Planilhas_sem_tratamento" / "movimentacoes.csv"
caminho_tratado = basedir / "data" / "Bases_Tratadas" / "Movimentacoes_tratado.csv"


def pipeline_movimentacao(df):
    df = pd.read_csv(caminho_bruto, sep=',', encoding='utf-8')

    # função para parsing de datas
    def parse_data(valor):
        if pd.notnull(valor):
            return dateparser.parse(str(valor), languages=["pt"])
        return pd.NaT

    # PADRONIZAÇÃO DE NOMES
    df['advogado_responsavel'] = df['advogado_responsavel'].str.upper().str.strip()
    df['tipo_ato'] = df['tipo_ato'].str.lower().str.strip()

    # PADRONIZAÇÃO DE DATAS
    df['data_movimentacao'] = pd.to_datetime(
        df['data_movimentacao'],
        errors='coerce',
        dayfirst=True,
        format='mixed'
    )

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

    df['concluido'] = (
        df['concluido']
        .astype(str)
        .str.lower()
        .str.strip()
        .replace(mapeamento_concluido)
    )

    # TRATAMENTO DE NULOS
    df["descricao"] = (
        df["descricao"]
        .replace(r'^\s*$', np.nan, regex=True)
        .fillna("Não informado")
    )

    df["concluido"] = df["concluido"].fillna("Não informado")

    # TRATAMENTO DE PRAZOS
    df["data_descricao"] = df["descricao"].str.extract(
        r'(\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}\s+de\s+\w+\s+de\s+\d{4})'
    )

    df["data_descricao"] = df["data_descricao"].apply(parse_data)

    df["prazo_final"] = (
        df["data_descricao"].combine_first(df["prazo_gerado"])
    )

    df["dias_prazo"] = df["descricao"].str.extract(
        r'(\d+)\s*dias?'
    )

    df["dias_prazo"] = (
        df["dias_prazo"]
        .fillna(0)
        .astype(int)
    )

    df["prazo_final"] = df["prazo_final"].fillna(pd.NaT)

    # TRATAMENTO DUPLICATAS
    df = df.drop_duplicates()
    df = df.drop_duplicates(
        subset=['movimentacao_id'],
        keep='first'
    )

    # EXPORTAÇÃO
    df_export = df.copy()

    # formatando as datas
    colunas_data = [
        "data_movimentacao",
        "prazo_gerado",
        "data_descricao",
        "prazo_final"
    ]

    for col in colunas_data:
        df[col] = df[col].dt.strftime('%Y-%m-%d')

    df["prazo_gerado"] = df["prazo_gerado"].fillna("Sem prazo")
    df["data_movimentacao"] = df["data_movimentacao"].fillna("Sem data")
    df["data_descricao"] = df["data_descricao"].fillna("Sem data")
    df["prazo_final"] = df["prazo_final"].fillna("Sem prazo final")

    caminho_tratado.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        caminho_tratado,
        sep=';',
        index=False,
        encoding='utf-8-sig'
    )


tabela_movimentacao = pd.read_csv(
    caminho_bruto,
    sep=',',
    encoding='utf-8'
)

pipeline_movimentacao(tabela_movimentacao)