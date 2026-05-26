import pandas as pd
import numpy as np
import dateparser
import re
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

    # padronizar cnj (n° processo)
    def formatar_cnj(numero):
        # remove qualquer caractere que não seja número 
        apenas_numeros = re.sub(r'\D', '', str(numero))
        
        if not apenas_numeros:
            return "Número Inválido"
        
        # o padrão CNJ tem 20 dígitos. Se tiver menos, preenchemos com zeros à esquerda
        apenas_numeros = apenas_numeros.zfill(20)
        
        # Aplica a máscara: NNNNNNN-DD.AAAA.J.TR.OOOO
        return (f"{apenas_numeros[:7]}-{apenas_numeros[7:9]}.{apenas_numeros[9:13]}."
                f"{apenas_numeros[13:14]}.{apenas_numeros[14:16]}.{apenas_numeros[16:]}")

    # 2. APLICAR PADRONIZAÇÃO (Coloque logo após a leitura do CSV)
    df['numero_processo'] = df['numero_processo'].apply(formatar_cnj)
    
    # PADRONIZAÇÃO DE NOMES
    df['advogado_responsavel'] = df['advogado_responsavel'].str.upper().str.strip()
    df['tipo_ato'] = df['tipo_ato'].str.lower().str.strip()

    # PADRONIZAÇÃO DE DATAS
    df['data_movimentacao'] = df['data_movimentacao'].apply(parse_data)
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
    """extração do prazo fatal na descrição"""
    df["prazo_fatal"] = df["descricao"].str.extract(
        r'(\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}\s+de\s+\w+\s+de\s+\d{4})'
    )
    df["prazo_fatal"] = df["prazo_fatal"].apply(parse_data)

    """extração do prazo pra recurso"""
    df["dias_recurso"] = df["descricao"].str.lower().str.extract(r'prazo para recurso:\s*(\d+)')[0]
    # soma os dias de recurso à data de movimentação
    df["prazo_recurso_calc"] = df.apply(
        lambda x: x['data_movimentacao'] + pd.Timedelta(days=int(x['dias_recurso']))
        if pd.notnull(x['dias_recurso']) and pd.notnull(x['data_movimentacao'])
        else pd.NaT, axis=1
    )
    # fechando prazo final : fatal > recurso > prazo gerado
    df["prazo_final"] = (
        df["prazo_fatal"]
        .combine_first(df["prazo_recurso_calc"])
        .combine_first(df["prazo_gerado"])
    )

    # TRATAMENTO DUPLICATAS
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset=['movimentacao_id'],keep='first')

    # formatando as datas
    colunas_data = ["data_movimentacao","prazo_gerado"]
    for col in colunas_data:
        df[col] = df[col].dt.strftime('%Y-%m-%d')
    # prazo final em datatime
    df["prazo_final"] = pd.to_datetime(df["prazo_final"], errors='coerce')
    df["prazo_final"] = df["prazo_final"].fillna(pd.NaT)
    
    df = df.drop(columns=["dias_recurso", "prazo_fatal", "prazo_recurso_calc"])

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