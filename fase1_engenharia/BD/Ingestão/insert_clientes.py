import sys
from pathlib import Path
import json

# usa o endereço da pasta atual para encontrar a pasta que ela está contida
pasta_bd = Path(__file__).parent.parent
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from model_Cliente import Cliente

def carregar_clientes_do_json(pasta_base_jsons: Path):
    db = SessionLocal()

    try:
        for arquivo in pasta_base_jsons.rglob("*.json"):
            if arquivo.name == "Relatorio_Geral_Contratos.json":
                continue

            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)

            cpf = dados.get("cpf_cnpj")
            if not cpf:
                continue
            
            nome_extraido = dados.get("nome_cliente") or dados.get("acusando_autor") or dados.get("reclamante")
            
            if not nome_extraido:
                continue

            endereco_extraido = dados.get("endereco_completo") or dados.get("endereco_encontrado")

            cliente_existente = db.query(Cliente).filter(Cliente.cpf_cnpj == cpf).first()

            if not cliente_existente:
                novo_cliente = Cliente(
                    nome=nome_extraido, 
                    cpf_cnpj=cpf,
                    nacionalidade=dados.get("nacionalidade"),
                    estado_civil=dados.get("estado_civil"),
                    ocupacao=dados.get("ocupacao"),
                    endereco_completo=endereco_extraido
                )
                db.add(novo_cliente)
            else:
                if not cliente_existente.nacionalidade and dados.get("nacionalidade"):
                    cliente_existente.nacionalidade = dados.get("nacionalidade")
                    
                if not cliente_existente.estado_civil and dados.get("estado_civil"):
                    cliente_existente.estado_civil = dados.get("estado_civil")
                    
                if not cliente_existente.ocupacao and dados.get("ocupacao"):
                    cliente_existente.ocupacao = dados.get("ocupacao")
                    
                if not cliente_existente.endereco_completo and endereco_extraido:
                    cliente_existente.endereco_completo = endereco_extraido

        # Confirma todas as inserções e atualizações
        db.commit()
        print("Ingestão de CLIENTES concluída com sucesso!")

    except Exception as e:
        db.rollback()
        print(f"Erro crítico na ingestão de clientes: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    pasta_raiz = Path(__file__).parent.parent.parent.parent
    pasta_todos_jsons = pasta_raiz / "data" / "Texto_json"
    
    carregar_clientes_do_json(pasta_todos_jsons)