import sys
from pathlib import Path

# usa o endereço da pasta atual para encontrar a pasta que ela está contida, assim encontra o modulo database_model
pasta_bd = Path(__file__).parent.parent
sys.path.append(str(pasta_bd))

import json
from database_model import SessionLocal
from model_Cliente import Cliente

def carregar_clientes_do_json(pasta_jsons: Path):
    #abre o Banco
    db = SessionLocal()

    try:
        # rastreia os arquivos json na pasta
        for arquivo in pasta_jsons.glob("*.json"):
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)

            # A tabela Clientes exige CPF. Se o JSON não tiver, pula para o prox pdf
            cpf = dados.get("cpf_citado")
            if not cpf:
                continue

            #Verifica se o cliente já existe no banco
            cliente_existente = db.query(Cliente).filter(Cliente.cpf_cnpj == cpf).first()

            if not cliente_existente:
                novo_cliente = Cliente(
                nome=dados.get("nome_citado"),
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
        # Se der qualquer erro crítico, desfaz tudo que estava na base
        db.rollback()
    finally:
    #sempre finaliza a conexão com o banco após cada inserção
        db.close()

if __name__ == "__main__":
    pasta_base = Path(__file__).parent.parent.parent.parent
    pasta_jsons_citacao = pasta_base / "data" / "Texto_json" / "citacao"
    carregar_clientes_do_json(pasta_jsons_citacao)