import pandas as pd
import os

caminho = "data/sujo/processos.csv"

destino = "data/limpo"

df = pd.read_csv(caminho)

print("=====================")
print("tratamento do Tipo")
print("=====================")

#uso do unique antes do tratamento
print(df["tipo"].unique())
#['cível' 'civil' 'trabalhista' 'TRABALHISTA' 'Trabalhista' 'Civil']

mapa_tipo = {
    "cível" : "Civil",
    "civil" : "Civil",
    "trabalhista" : "Trabalhista",
    "TRABALHISTA" : "Trabalhista",
    "Trabalhista" : "Trabalhista",
    "Civil" : "Civil"
}

df["tipo"] = (df["tipo"].map(mapa_tipo))

#uso do unique apos o tratamento
print(df["tipo"].unique())
#['Civil' 'Trabalhista']

print("=====================")
print("tratamento da fase")
print("=====================")

print(df["fase"].unique())

df["fase"] = df["fase"].str.capitalize()

print(df["fase"].unique())

