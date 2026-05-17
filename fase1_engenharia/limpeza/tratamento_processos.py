import pandas as pd
import os

caminho = "data/sujo/processos.csv"

destino = "data/limpo"

df = pd.read_csv(caminho)

print("===============================================================")
print("tratamento de linahs duplicadas + espaços vazios")
print("===============================================================")

df.columns = df.columns.str.strip()

#linhas antes da remoção de duplicados
print("Shape: ", df.shape)

df = df.drop_duplicates()
#linhas depois da remoção dos duplicados 
print("Shape: ", df.shape)

print("===============================================================")
print("tratamento do Tipo")
print("===============================================================")

#uso do unique antes do tratamento
print(df["tipo"].unique())
#['cível' 'civil' 'trabalhista' 'TRABALHISTA' 'Trabalhista' 'Civil']

mapa_tipo = {
    "cível" : "Civil",
    "civil" : "Civil",
    "Civil" : "Civil",

    "trabalhista" : "Trabalhista",
    "TRABALHISTA" : "Trabalhista",
    "Trabalhista" : "Trabalhista"
}

df["tipo"] = (df["tipo"].map(mapa_tipo))

#uso do unique apos o tratamento
print(df["tipo"].unique())
#['Civil' 'Trabalhista']

print("===============================================================")
print("tratamento da fase")
print("===============================================================")

#tipo antes do tratamento
print(df["fase"].unique())
#['inicial' 'recurso' 'instrução' 'execução' 'sentença','acordo extrajudicial' 'arquivado' 'audiência']

df["fase"] = df["fase"].str.capitalize()

#tipo depois do tratamento
print(df["fase"].unique())
#['Inicial' 'Recurso' 'Instrução' 'Execução' 'Sentença','Acordo extrajudicial' 'Arquivado' 'Audiência']

print("===============================================================")
print("tratamento do status")
print("===============================================================")

#antes do tratamento de status
print(df["status"].unique())
#['appeal' 'active' 'encerrado' 'settlement' 'suspenso' 'suspended' 'ativo','acordo' 'closed' 'ATIVO' 'Ativo' 'Encerrado' 'em recurso']

mapa_status = {
    'ATIVO' : "Ativo",
    'Ativo' : "Ativo",
    'active' : "Ativo",
    'ativo' : "Ativo",

    'encerrado' : "Encerrado",
    'closed' : "Encerrado",
    'Encerrado' : "Encerrado",
    'settlement' : "Encerrado",
    'acordo' : "Encerrado",

    'suspenso' : "Suspenso",
    'suspended' : "Suspenso",


    'appeal' : "Em recurso",
    'em recurso' : "Em recurso",
}

df["status"] = (df["status"].map(mapa_status))

#após o tratamento de status
print(df["status"].unique())

print("===============================================================")
print("tratamento de advogado_responsavel")
print("===============================================================")

#antes do tratamento
print(df["advogado_responsavel"].unique())
#['Dra. Cavalcante' 'Dra. Fontes' 'dr. melo' 'Dr. Melo' 'DRA. CAVALCANTE''Dra Fontes' 'Dr. Barros']

df["advogado_responsavel"] = df["advogado_responsavel"].str.lower()
df["advogado_responsavel"] = df["advogado_responsavel"].str.title()

#depois do tratamento
print(df["advogado_responsavel"].unique())
#['Dra. Cavalcante' 'Dra. Fontes' 'Dr. Melo' 'Dra Fontes' 'Dr. Barros']

print("===============================================================")
print("tratamento da data_abertura")
print("===============================================================")


mapa_meses = {
    "janeiro": "01",
    "fevereiro": "02",
    "março": "03",
    "abril": "04",
    "maio": "05",
    "junho": "06",
    "julho": "07",
    "agosto": "08",
    "setembro": "09",
    "outubro": "10",
    "novembro": "11",
    "dezembro": "12"
}
df["data_abertura"] = df["data_abertura"].str.lower().replace(mapa_meses, regex=True)
df["data_abertura"] = df["data_abertura"].str.replace(r'[de]', ' ', regex=True)

df["data_abertura"] = pd.to_datetime(df["data_abertura"],format="mixed")
df["data_abertura"] = df["data_abertura"].dt.strftime("%d-%m-%Y")

print(df["data_abertura"])

print("===============================================================")
print("tratamento prazo proximo")
print("===============================================================")

df["prazo_proximo"] = df["prazo_proximo"].str.lower().replace(mapa_meses, regex=True)
df["prazo_proximo"] = df["prazo_proximo"].str.replace(r'[de]', ' ', regex=True)

df["prazo_proximo"] = pd.to_datetime(df["prazo_proximo"],format="mixed")
df["prazo_proximo"] = df["prazo_proximo"].dt.strftime("%d-%m-%Y")
df["prazo_proximo"] = df["prazo_proximo"].fillna("Não informado")

print(df["prazo_proximo"].head(10))

print("===============================================================")
print("tratamento valor_causa")
print("===============================================================")

df["valor_causa"] = df["valor_causa"].astype(str).str.strip()
df["valor_causa"] = df["valor_causa"].replace(r'R\$','',regex=True)
df["valor_causa"] = pd.to_numeric(df["valor_causa"], errors='coerce')

media = df["valor_causa"].mean().round(2) 

df["valor_causa"] = df["valor_causa"].fillna(media)

pd.set_option("display.float_format", lambda x: f"R$ {x:.2f}")

print(df["valor_causa"])

print("===============================================================")
print("tratamento de observacoes")
print("===============================================================")

df["observacoes"] = df["observacoes"].str.capitalize()
df["observacoes"] = df["observacoes"].fillna("Não informado")

print(df["observacoes"].unique())