import sys
from pathlib import Path
import json

# 1. Ajuste de caminhos no topo
pasta_bd = Path(__file__).resolve().parent.parent
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from model_Cliente import Cliente

def enriquecer_clientes_json(pasta_jsons: Path):
    db = SessionLocal()
    
    try:
        print(f"Iniciando varredura de JSONs na pasta: {pasta_jsons}")
        clientes_atualizados = 0
        clientes_novos_inseridos = 0
        
        # Usa rglob para varrer todos os arquivos JSON (Contratos, Petições, etc.)
        for arquivo in pasta_jsons.rglob("*.json"): 
            if "Relatorio" in arquivo.name:
                continue
                
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
            
            # Mapeamento Inteligente: Chaves antigas vs padronizadas
            cpf_extraido = dados.get("cpf_cnpj") or dados.get("cpf_cnpj_contratante")
            nome_extraido = dados.get("nome_cliente") or dados.get("contratante") or dados.get("autor") or dados.get("reclamante")
            
            if not cpf_extraido and not nome_extraido:
                continue

            # Busca no banco de dados
            cliente_existente = None
            if cpf_extraido:
                cliente_existente = db.query(Cliente).filter(Cliente.cpf_cnpj == cpf_extraido).first()
            if not cliente_existente and nome_extraido:
                cliente_existente = db.query(Cliente).filter(Cliente.nome.ilike(f"%{nome_extraido}%")).first()

            # Variáveis a serem injetadas
            nacionalidade = dados.get("nacionalidade")
            estado_civil = dados.get("estado_civil")
            ocupacao = dados.get("ocupacao")
            endereco = dados.get("endereco_completo") or dados.get("endereco_encontrado")

            if cliente_existente:
                # SMART UPDATE: Só injeta o dado se o banco estiver vazio (None)
                atualizou_algo = False
                
                if not cliente_existente.nacionalidade and nacionalidade:
                    cliente_existente.nacionalidade = nacionalidade
                    atualizou_algo = True
                if not cliente_existente.estado_civil and estado_civil:
                    cliente_existente.estado_civil = estado_civil
                    atualizou_algo = True
                if not cliente_existente.ocupacao and ocupacao:
                    cliente_existente.ocupacao = ocupacao
                    atualizou_algo = True
                if not cliente_existente.endereco_completo and endereco:
                    cliente_existente.endereco_completo = endereco
                    atualizou_algo = True
                if not cliente_existente.cpf_cnpj and cpf_extraido:
                    cliente_existente.cpf_cnpj = cpf_extraido
                    atualizou_algo = True

                if atualizou_algo:
                    clientes_atualizados += 1
            else:
                # -------------------------------------------------------------
                # INSERT: Cliente novo encontrado no JSON
                # -------------------------------------------------------------
                novo_cliente = Cliente(
                    nome=nome_extraido,
                    cpf_cnpj=cpf_extraido,
                    nacionalidade=nacionalidade,
                    estado_civil=estado_civil,
                    ocupacao=ocupacao,
                    endereco_completo=endereco
                )
                db.add(novo_cliente)
                db.commit() # Commit imediato para ele existir nas próximas iterações do loop
                clientes_novos_inseridos += 1

        db.commit()
        print("\n--- RESUMO DO ENRIQUECIMENTO ---")
        print(f"Clientes atualizados (lacunas preenchidas): {clientes_atualizados}")
        print(f"Novos clientes descobertos e inseridos: {clientes_novos_inseridos}")
        
    except Exception as e:
        db.rollback()
        print(f"Erro crítico no enriquecimento de clientes: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    raiz_projeto = Path(__file__).resolve().parent.parent.parent.parent
    pasta_jsons_principal = raiz_projeto / "data" / "Texto_json"
    
    if not pasta_jsons_principal.exists():
        print(f"A pasta {pasta_jsons_principal} não existe")
    else:
        enriquecer_clientes_json(pasta_jsons_principal)