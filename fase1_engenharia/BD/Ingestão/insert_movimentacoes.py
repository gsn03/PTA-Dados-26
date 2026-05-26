
import sys
from pathlib import Path
import json


# Aponta para a pasta BD
pasta_bd = Path(__file__).parent.parent
sys.path.append(str(pasta_bd))


from database_model import SessionLocal
from model_movimentacoes import Movimentacao


def carregar_movimentacoes_do_json(pasta_base_jsons: Path):
    db = SessionLocal()


    try:
        for arquivo in pasta_base_jsons.rglob("*.json"):
            if arquivo.name == "Relatorio_Geral_Contratos.json":
                continue


            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)


            tipos_validos = ["peticao", "acordo", "sentenca", "citacao", "recurso", "notificacao", "intimacao"]
            tipo_doc = dados.get("tipo_documento", "").lower()
           
            if tipo_doc not in tipos_validos:
                continue


            nome_arquivo = dados.get("arquivo_origem")
            if not nome_arquivo:
                continue


            movimentacao_existente = db.query(Movimentacao).filter(
                Movimentacao.arquivo_origem == nome_arquivo
            ).first()


            if not movimentacao_existente:
                nova_movimentacao = Movimentacao(
                    arquivo_origem=nome_arquivo,
                   
                    numero_processo=dados.get("numero_processo") or dados.get("processo") or dados.get("n_processo"),
                    tipo_movimentacao=dados.get("tipo_documento") or dados.get("tipo"),
                    data_movimentacao=dados.get("data_movimentacao") or dados.get("data_expedicao") or dados.get("data"),
                    orgao_julgador=dados.get("tribunal_vara") or dados.get("tipo_vara"),
                    resumo_descricao=dados.get("resumo_descricao") or dados.get("resumo") or dados.get("decisao") or dados.get("objeto"),
                    cliente=dados.get("cliente") or dados.get("nome_cliente") or dados.get("contratante") or dados.get("reclamante") or dados.get("acusando_autor"),
                    advogado=dados.get("advogado") or dados.get("nome_advogado"),
                )
                db.add(nova_movimentacao)


        db.commit()


    except Exception as e:
        db.rollback()
        print(f"{e}")
    finally:
        db.close()


if __name__ == "__main__":
    pasta_raiz = Path(__file__).resolve().parent.parent.parent.parent
    pasta_todos_jsons = pasta_raiz / "data" / "Texto_json"
   
    if not pasta_todos_jsons.exists():
        print(f"A pasta não foi encontrada.")
    else:
        carregar_movimentacoes_do_json(pasta_todos_jsons)