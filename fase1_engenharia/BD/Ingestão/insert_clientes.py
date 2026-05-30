import sys
from pathlib import Path
import pandas as pd

# 1. Ajuste de caminhos no topo
pasta_bd = Path(__file__).resolve().parent.parent
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from model_Cliente import Cliente

def carregar_clientes_csv(caminho_csv: Path):
    db = SessionLocal()
    
    try:
        # Lê o CSV usando Pandas
        print(f"Lendo arquivo: {caminho_csv}")
        df_clientes = pd.read_csv(caminho_csv, sep=",", encoding="utf-8")
        
        # TRATAMENTO DE NULOS: Converte 'NaN' do Pandas para 'None' do Python/SQLAlchemy
        df_clientes = df_clientes.where(pd.notnull(df_clientes), None)
        
        clientes_inseridos = 0
        clientes_ignorados = 0
        
        # Itera linha por linha na tabela
        for index, row in df_clientes.iterrows():
            cpf_extraido = row.get("cpf")
            nome_extraido = row.get("nome")
            
            # Se não tiver CPF nem Nome, pula a linha por segurança
            if not cpf_extraido and not nome_extraido:
                continue

            # Verifica se o cliente já existe no banco pelo CPF
            cliente_existente = None
            if cpf_extraido:
                cliente_existente = db.query(Cliente).filter(Cliente.cpf_cnpj == cpf_extraido).first()
            
            if not cliente_existente:
                # Cria o novo cliente mapeando as colunas do CSV para o Model
                novo_cliente = Cliente(
                    nome=nome_extraido,
                    cpf_cnpj=cpf_extraido,
                    contato=row.get("contato"),
                    email=row.get("email"),
                    data_inicio=row.get("data_inicio"),
                    cidade=row.get("cidade")
                    # Nota: as colunas antigas da extração (nacionalidade, etc.) 
                    # ficarão como NULL, o que é perfeitamente seguro agora.
                )
                db.add(novo_cliente)
                clientes_inseridos += 1
            else:
                # Se o cliente já existe, ignoramos para não dar erro de duplicidade
                clientes_ignorados += 1

        db.commit()
        print(f"Ingestão concluída com SUCESSO!")
        print(f" - Clientes novos inseridos: {clientes_inseridos}")
        print(f" - Clientes ignorados (já existiam): {clientes_ignorados}")
        
    except Exception as e:
        db.rollback()
        print(f"Erro crítico na ingestão de clientes: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Navega até a pasta raiz do projeto e depois para a pasta de tabelas tratadas
    raiz_projeto = Path(__file__).resolve().parent.parent.parent.parent
    caminho_csv_clientes = raiz_projeto / "data" / "Bases_Tratadas" / "Clientes_Tratados.csv"
    
    if not caminho_csv_clientes.exists():
        print(f"ERRO: O arquivo {caminho_csv_clientes} não foi encontrado.")
    else:
        carregar_clientes_csv(caminho_csv_clientes)