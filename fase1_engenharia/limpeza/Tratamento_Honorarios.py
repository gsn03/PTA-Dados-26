import pandas as pd
from pathlib import Path

basedir = Path(__file__).resolve().parent 
caminho_entrada = basedir.parent.parent / "data" / "Planilhas_sem_tratamento" / "Honorarios.csv"
caminho_saida = basedir.parent.parent / "data" / "Bases_Tratadas" / "Honorarios_Tratados.csv"

tabela_honorarios = pd.read_csv(caminho_entrada)

def pipeline_honorarios(df_honorarios):
    #Limpeza inicial
    df_honorarios.columns= df_honorarios.columns.str.strip() #limpo todo e qualquer espaço nos nomes da colunas

    #remoção simples
    df_honorarios= df_honorarios.dropna(how='all') #remove todas linhas totalmente nulas
    df_honorarios = df_honorarios.drop_duplicates()

    #Padronizar metodo de pagamento ✅
    map_forma_pg={
        'boleto' : 'Boleto',
        'Boleto' : 'Boleto',
        'TED': 'Transferência',
        'transferência': 'Transferência',
        'PIX': 'PIX',
        'pix': 'PIX',
    }
    df_honorarios['forma_pagamento']= df_honorarios['forma_pagamento'].str.strip().map(map_forma_pg).fillna('Não informado')

    #Padronizar n_parcelas ✅
    df_honorarios['n_parcelas'] = df_honorarios['n_parcelas'].astype(str)
    df_honorarios['n_parcelas'] = df_honorarios['n_parcelas'].str.strip( )
    df_honorarios['n_parcelas'] = df_honorarios['n_parcelas'].astype(int)

    #status_pagamento ✅
    mapa_status_pg ={
        'quitado' : 'Quitado',
        'ATRASADO': 'Atrasado',
        'em dia': 'Em Dia',
        'Em Dia': 'Em Dia',
        'atrasado': 'Atrasado',
    }
    df_honorarios['status_pagamento'] = df_honorarios['status_pagamento'].str.strip().map(mapa_status_pg).fillna('Não informado')

    #honorario_exito✅
    mapa_honorario_exito={
        'N': 'Não',
        'não': 'Não',
        'Não': 'Não',
        'nao': 'Não',
        'S': 'Sim',
        'Sim': 'Sim',
        'sim': 'Sim',
    }
    df_honorarios['honorario_exito'] =( df_honorarios['honorario_exito']
        .str.strip()
        .map(mapa_honorario_exito)
        .fillna('Não informado')
    )

    # percentual_exito

    df_honorarios['percentual_exito']= df_honorarios['percentual_exito'].replace('%', '')
    df_honorarios['percentual_exito']= (df_honorarios['percentual_exito'] * 100).fillna(0).astype(int)

    #para fazer a conversão tive que transformar os nulos em 0, logo nulos = 0 

    # data_contrato ✅
    mapa_replace_data= {
        'janeiro' : '01',
        'fevereiro': '02',
        'março': '03',
        'abril': '04',
        'maio': '05',
        'junho': '06',
        'julho': '07',
        'agosto': '08',
        'setembro': '09',
        'outubro': '10',
        'dezembro':'12',
        'novembro': '11',
    }
    
    df_honorarios['data_contrato'] = df_honorarios['data_contrato'].astype(str).replace(mapa_replace_data, regex=True)
    df_honorarios['data_contrato'] = df_honorarios['data_contrato'].str.replace(' de ', '-').str.strip()
    df_honorarios['data_contrato']= pd.to_datetime(df_honorarios['data_contrato'], dayfirst= True, format='mixed')

    # data_vencimento✅
    df_honorarios['data_vencimento'] = df_honorarios['data_vencimento'].astype(str).replace(mapa_replace_data, regex=True)
    df_honorarios['data_vencimento'] = df_honorarios['data_vencimento'].str.replace(' de ', '-').str.strip()
    df_honorarios['data_vencimento']= pd.to_datetime(df_honorarios['data_vencimento'], dayfirst= True, format='mixed', errors='coerce') # faz os nan virarem NaT                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         

    #Localiza as colunas nulas e faz a operação de soma com o número de parcelas
    nulos_venc = df_honorarios['data_vencimento'].isna()
    df_honorarios.loc[nulos_venc, 'data_vencimento'] = df_honorarios[nulos_venc].apply(
        lambda row: row['data_contrato'] + pd.DateOffset(months=int(row['n_parcelas'])), 
        axis=1
    )
    
    #Organização datas
    df_honorarios['data_contrato'] = df_honorarios['data_contrato'].dt.strftime('%Y-%m-%d')
    df_honorarios['data_vencimento'] = df_honorarios['data_vencimento'].dt.strftime('%Y-%m-%d')

    # deixo somenrte os número
    mapa_valores= {
        r'R\$ ': '',
        r'\.': '',
        ',' : '',
        '-' : '',
    }

    # valor_pago ✅
    linhas_corrompidas = df_honorarios['valor_pago'].notna() 
    df_honorarios.loc[linhas_corrompidas,'valor_pago'] =(df_honorarios.loc[linhas_corrompidas, 'valor_pago']
        .replace(mapa_valores, regex=True)
        .str.strip()
        )

    df_honorarios['valor_pago'] = df_honorarios['valor_pago'].astype(float)
    df_honorarios['valor_pago'] = df_honorarios['valor_pago'] / 100

    # valor_total_contratado ✅

    linhas_corrompidas = df_honorarios['valor_total_contratado'].notna() 
    df_honorarios.loc[linhas_corrompidas,'valor_total_contratado'] =(df_honorarios.loc[linhas_corrompidas, 'valor_total_contratado']
        .replace(mapa_valores, regex=True)
        .str.strip()
        )

    df_honorarios['valor_total_contratado'] = df_honorarios['valor_total_contratado'].astype(float)
    df_honorarios['valor_total_contratado'] = df_honorarios['valor_total_contratado'] / 100
    
    #valor_em_aberto ✅

    linhas_corrompidas = df_honorarios['valor_em_aberto'].notna() 
    df_honorarios.loc[linhas_corrompidas,'valor_em_aberto'] =(df_honorarios.loc[linhas_corrompidas, 'valor_em_aberto']
        .replace(mapa_valores, regex=True)
        .str.strip()
        )

    df_honorarios['valor_em_aberto'] = df_honorarios['valor_em_aberto'].astype(float)
    df_honorarios['valor_em_aberto'] = df_honorarios['valor_em_aberto'] / 100
    
    valor_a_pagar= df_honorarios['valor_total_contratado'] - df_honorarios['valor_pago']
    #valor_calculado = valor_calculado.clip(lower=0) # garante que não vai existir nem um valor negativo
    
    df_honorarios['valor_em_aberto'] = df_honorarios['valor_em_aberto'].fillna(valor_a_pagar)
    
 
    
    
    df_honorarios.to_csv(caminho_saida, index=False, encoding='utf-8-sig')
    
pipeline_honorarios(tabela_honorarios)
