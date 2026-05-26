import pandas as pd
import numpy as np
from pathlib import Path

basedir = Path(__file__).resolve().parent 
caminho_entrada = basedir.parent.parent / "data" / "Planilhas_sem_tratamento" / "Processos.xlsx"
caminho_saida = basedir.parent.parent / "data" / "Bases_Tratadas" / "Processos_Tratados.csv"



def pipeline_Tratamento_Processos (caminho_entrada, caminho_saida):
  df_processos = pd.read_excel(caminho_entrada)
  #formatando os nomes das colunas para tirar espaços em branco:
  df_processos.columns = df_processos.columns.str.strip()
  #removendo linhas nulas e duplicadas:
  df_processos = df_processos.dropna(how = 'all')
  df_processos = df_processos.drop_duplicates()


  #--PADRONIZANDO--

  #TIPO
  mapa_tipo = {
      'TRABALHISTA' : 'Trabalhista',
      'trabalhista' : 'Trabalhista',
      'Trabalhista' : 'Trabalhista',
      'civil' : 'Civil',
      'Civil' : 'Civil',
      'cível' : 'Civil'
  }

  df_processos['tipo'] = df_processos['tipo'].map(mapa_tipo)


  #STATUS
  mapa_status = {
      'ATIVO' : 'Ativo',
      'ativo' : 'Ativo',
      'Ativo' : 'Ativo',
      'active': 'Ativo',
      'Encerrado' : 'Encerrado',
      'closed' : 'Encerrado',
      'encerrado' : 'Encerrado',
      'acordo' : 'Acordo',
      'suspenso' : 'Suspenso',
      'suspended' : 'Suspenso',
      'em recurso' : 'Em recurso',
      'settlement' : 'Acordo',
      'appeal' : 'Ativo'
  }

  df_processos['status'] = df_processos['status'].map(mapa_status)


  #ADVOGADOS
  mapa_advogados = {
      'Dra. Cavalcante' : 'Dra. Cavalcante',
      'DRA. CAVALCANTE' : 'Dra. Cavalcante',
      'Dra. Fontes' : 'Dra. Fontes',
      'Dra Fontes' : 'Dra. Fontes',
      'dr. melo' : 'Dr. Melo',
      'Dr. Melo' : 'Dr. Melo',
      'Dr. Barros' : 'Dr. Barros'
  }

  df_processos['advogado_responsavel'] = df_processos['advogado_responsavel'].map(mapa_advogados)


  #OBSERVAÇÕES
  df_processos['observacoes'] = df_processos['observacoes'].str.title()
  
  mapa_observacoes = {
      'Cliente Não Responde' : 'Aguardando documentos'   
  }

  df_processos['observacoes'] = df_processos['observacoes'].map(mapa_observacoes)
  df_processos['observacoes'] = df_processos['observacoes'].fillna('Sem observações')


  #Formatando a FASE
  df_processos['fase'] = df_processos['fase'].str.title()

  #PADRONIZANDO O VALOR DA CAUSA:


  #fazendo a interação das linhas das colunas
  for indicie in df_processos.index:
    linha_atual = str(df_processos.loc[indicie, 'valor_causa'])

    if pd.isna(linha_atual) or (isinstance(linha_atual, str) and linha_atual.strip() == '') or str(linha_atual).lower() in ('nan', 'none') or (linha_atual == 'Sem valor'):
      df_processos.loc[indicie, 'valor_causa'] = np.nan 
      continue  #as proximas alterações desconsideram os valores nulos

    if 'R$' in linha_atual:
      linha_atual = linha_atual.replace('R$', '') #tirando o R$
      df_processos.loc[indicie, 'valor_causa'] = linha_atual
      if '.' in linha_atual:
        df_processos.loc[indicie, 'valor_causa'] = linha_atual.replace('.', '') #tirando os pontos de milhar

    if ',' in linha_atual:
      df_processos.loc[indicie, 'valor_causa'] = linha_atual.replace(',', '.')  #trocando a virgula dos centavos para ponto

    df_processos.loc[indicie, 'valor_causa'] = float(df_processos.loc[indicie, 'valor_causa'])  #trandformando o valor em float

  #preenchendo os nulos com 'sem valor'
  df_processos['valor_causa'] = df_processos['valor_causa'].fillna('Sem valor')


  #FORMANTANDO AS DATAS de ABERTURA PARA YYYY-MM-DD 
  mapa_mes ={
    'janeiro': '01',
    'fevereiro': '02',
    'março': '03',
    'abril': '04',
    'maio': '05',
    'junho': '06',
    'julho': '07',
    'agosto': '08',
    'setembro': '09',
    'outubro': '10',
    'novembro': '11',
    'dezembro': '12'
  }
  #Limpeza do texto da coluna
  df_processos['data_abertura'] = df_processos['data_abertura'].astype(str).str.lower().str.strip()
  #Transforma o "de" em /
  df_processos['data_abertura'] = df_processos['data_abertura'].str.replace(' de ', '/', regex=False)
  #substituindo o mes por extenso para numeros
  for antigo, novo in mapa_mes.items():
      df_processos['data_abertura'] = df_processos['data_abertura'].str.replace(antigo, novo, regex=False)


  df_processos['data_abertura'] = pd.to_datetime(df_processos['data_abertura'], dayfirst=True, format='mixed')
  df_processos['data_abertura'] = df_processos['data_abertura'].dt.strftime('%Y-%m-%d')



  #FORMANTANDO AS DATAS DO PROXIMO PRAZO PARA YYYY-MM-DD 

  #Limpeza do texto da coluna
  df_processos['prazo_proximo'] = df_processos['prazo_proximo'].astype(str).str.lower().str.strip()
  #Transforma o "de" em /
  df_processos['prazo_proximo'] = df_processos['prazo_proximo'].str.replace(' de ', '/', regex=False)
  #substituindo o mes por extenso para numeros
  for antigo, novo in mapa_mes.items(): #reutiliza o mapa_mes
      df_processos['prazo_proximo'] = df_processos['prazo_proximo'].str.replace(antigo, novo, regex=False)
      

  df_processos['prazo_proximo'] = pd.to_datetime(df_processos['prazo_proximo'], dayfirst=True, format='mixed')
  df_processos['prazo_proximo'] = df_processos['prazo_proximo'].dt.strftime('%Y-%m-%d')

  df_processos['prazo_proximo'] = df_processos['prazo_proximo'].fillna('Sem prazo delimitado') #preenche os nulos com 'Sem prazo delimitado'
# FORÇANDO TIPAGEM DE DADOS (Type Casting)

  # 1. Transforma tudo que não for número no valor_causa em NaN
  df_processos['valor_causa'] = pd.to_numeric(df_processos['valor_causa'], errors='coerce')
  
  # 2. Transforma tudo que não for data válida no prazo_proximo em NaT
  df_processos['prazo_proximo'] = pd.to_datetime(df_processos['prazo_proximo'], errors='coerce')
  df_processos['prazo_proximo'] = df_processos['prazo_proximo'].dt.strftime('%Y-%m-%d')

  # EXPORTAÇÃO
  df_processos.to_csv(caminho_saida, index=False, sep=',', encoding='utf-8')
#BAIXANDO A BASE DE DADOS TRATADA
  df_processos.to_csv(caminho_saida, index = False)



pipeline_Tratamento_Processos(caminho_entrada, caminho_saida)