import pandas as pd
from pathlib import Path

basedir = Path(__file__).resolve().parent 

caminho_entrada = basedir.parent.parent / "data" / "Planilhas_sem_tratamento" / "Clientes.csv"  
caminho_saida = basedir.parent.parent / "data" / "Bases_Tratadas" / "Clientes_Tratados.csv"


df = pd.read_csv(caminho_entrada)
#Remoção de duplicatas:         #Garante que não sejam retirados da planilha usuários não duplicados
df = df.drop_duplicates(subset=["cliente_id", "cpf", "contato"], keep="first")
#Primeiramente, vou ordenar a ordem do ID do cliente de 1 até o último, de forma crescente
df = df.sort_values(by="cliente_id", ascending=True)
#Usei a função reset_index para resetar o índice visual (ver na documentação)
df = df.reset_index(drop=True)
#O índice agora começa em 1
df.index = df.index + 1
#Formatação dos nomes para letra maiúscula no primeiro caractere 
df["nome"] = df["nome"].str.title()
#Agora, os números de telefone nulos ou com formatação incorreta serão "Não informado"
df["contato"] = df["contato"].fillna("Não informado") #Nulos
df["contato"] = df["contato"].replace("não informado", "Não informado") #Fora do padrão
#Mesma coisa para os e-mails. As células nulas serão "Não informado"
df["email"] = df["email"].fillna("Não informado")
#Criação de um mapa para transformar os valores em extenso para número
mapa_mes = {
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
df['data_inicio'] = df['data_inicio'].astype(str).str.lower().str.strip()
#Transforma o "de" em /
df['data_inicio'] = df['data_inicio'].str.replace(' de ', '/', regex=False)
for mes_nome, mes_num in mapa_mes.items(): #For que varre a coluna de dados para cada mês
    df['data_inicio'] = df['data_inicio'].str.replace(mes_nome, mes_num, regex=False)
#Formatação das datas para YYYY-MM-DD --> pode ser mudado 
df['data_inicio'] = pd.to_datetime(df['data_inicio'], dayfirst=True, format='mixed')
df['data_inicio'] = df['data_inicio'].dt.strftime('%Y-%m-%d')
#Por último, a formatação do nome das cidades 
df["cidade"] = df["cidade"].str.title()
#Printa as primeiras linhas da planilha
print(df.head())
#Gera a planilha tratada
df.to_csv(caminho_saida, index=False, encoding='utf-8-sig')


