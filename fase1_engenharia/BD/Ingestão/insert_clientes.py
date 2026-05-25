import sys
from pathlib import Path
import json

# usa o endereço da pasta atual para encontrar a pasta que ela está contida
pasta_bd = Path(__file__).parent.parent
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from model_Cliente import Cliente

def carregar_clientes_do_json(pasta_base_jsons: Path):
    #abre o Banco
    db = SessionLocal()

    try:
        
        for arquivo in pasta_base_jsons.rglob("*.json"):
            # Ignora o arquivo de relatório unificado para não dar erro
            if arquivo.name == "Relatorio_Geral_Contratos.json":
                continue

            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)

            
            cpf = dados.get("cpf_cnpj")
            
            #A tabela Clientes exige CPF. Se o JSON não tiver, pula para o prox pdf
            if not cpf:
                continue

            #Verifica se o cliente já existe no banco
            cliente_existente = db.query(Cliente).filter(Cliente.cpf_cnpj == cpf).first()

            if not cliente_existente:
                novo_cliente = Cliente(
                    nome=dados.get("nome_cliente"), 
                    cpf_cnpj=cpf,
                    nacionalidade=dados.get("nacionalidade"),
                    estado_civil=dados.get("estado_civil"),
                    ocupacao=dados.get("ocupacao"),
                    endereco_completo=dados.get("endereco_completo")
                )
                # Adiciona ao banco
                db.add(novo_cliente)

        # Confirma todas as inserções no banco físico
        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Erro ao inserir dados: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # ALTERAÇÃO 4: Apontamos para a pasta raiz dos JSONs, e não apenas para "citacao"
    pasta_raiz = Path(__file__).parent.parent.parent.parent
    pasta_todos_jsons = pasta_raiz / "data" / "Texto_json"
    
    carregar_clientes_do_json(pasta_todos_jsons)
   