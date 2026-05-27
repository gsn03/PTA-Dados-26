import sys
from pathlib import Path
import json
import re

# 1. Ajuste de caminhos no topo
pasta_bd = Path(__file__).resolve().parent.parent
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from model_movimentacoes import Movimentacao

def formatar_data(texto_data):
    if not texto_data: return None
    match = re.search(r"(\d{4}-\d{2}-\d{2})", str(texto_data))
    if match: return match.group(1)
    match_br = re.search(r"(\d{2})/(\d{2})/(\d{4})", str(texto_data))
    if match_br: return f"{match_br.group(3)}-{match_br.group(2)}-{match_br.group(1)}"
    return None

def enriquecer_movimentacoes_json(pasta_jsons: Path):
    db = SessionLocal()
    
    try:
        print("A iniciar a varredura de JSONs para enriquecer Movimentações...")
        movimentacoes_atualizadas = 0
        movimentacoes_inseridas = 0
        
        for arquivo in pasta_jsons.rglob("*.json"): 
            if "Relatorio" in arquivo.name:
                continue
                
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
            
            # Filtro original do seu script para aceitar apenas documentos jurídicos válidos
            tipos_validos = ["peticao", "acordo", "sentenca", "citacao", "recurso", "notificacao", "intimacao"]
            tipo_doc = dados.get("tipo_documento", "").lower()
            
            if tipo_doc not in tipos_validos and tipo_doc != "":
                continue

            num_proc = dados.get("numero_processo") or dados.get("processo") or dados.get("n_processo")
            if not num_proc:
                continue
            
            arq_origem = dados.get("arquivo_origem") or arquivo.name
            data_mov = formatar_data(dados.get("data_movimentacao") or dados.get("data_expedicao") or dados.get("data"))
            orgao = dados.get("tribunal_vara") or dados.get("tipo_vara")
            resumo = dados.get("resumo_descricao") or dados.get("resumo") or dados.get("decisao") or dados.get("objeto")
            cliente_str = dados.get("cliente") or dados.get("nome_cliente") or dados.get("contratante") or dados.get("reclamante") or dados.get("acusando_autor")
            advogado_str = dados.get("advogado") or dados.get("nome_advogado")

            # Tenta encontrar uma movimentação existente para aquele processo na MESMA data
            mov_existente = None
            if data_mov:
                mov_existente = db.query(Movimentacao).filter(
                    Movimentacao.numero_processo == num_proc,
                    Movimentacao.data_movimentacao == data_mov
                ).first()

            if mov_existente:
                # SMART UPDATE: Só preenche o que está vazio (None) para não sobrescrever o CSV
                atualizou = False
                if not mov_existente.arquivo_origem and arq_origem:
                    mov_existente.arquivo_origem = arq_origem
                    atualizou = True
                if not mov_existente.orgao_julgador and orgao:
                    mov_existente.orgao_julgador = orgao
                    atualizou = True
                if not mov_existente.resumo_descricao and resumo:
                    mov_existente.resumo_descricao = resumo
                    atualizou = True
                if not mov_existente.cliente and cliente_str:
                    mov_existente.cliente = cliente_str
                    atualizou = True
                if not mov_existente.advogado and advogado_str:
                    mov_existente.advogado = advogado_str
                    atualizou = True
                if not mov_existente.tipo_movimentacao and tipo_doc:
                    mov_existente.tipo_movimentacao = tipo_doc
                    atualizou = True
                    
                if atualizou:
                    movimentacoes_atualizadas += 1
            else:
                # INSERT: Se for um documento novo cuja data não estava no CSV
                nova_movimentacao = Movimentacao(
                    arquivo_origem=arq_origem,
                    numero_processo=num_proc,
                    tipo_movimentacao=tipo_doc,
                    data_movimentacao=data_mov,
                    orgao_julgador=orgao,
                    resumo_descricao=resumo,
                    cliente=cliente_str,
                    advogado=advogado_str
                )
                db.add(nova_movimentacao)
                db.commit()
                movimentacoes_inseridas += 1

        db.commit()
        print("\n--- RESUMO DO ENRIQUECIMENTO DE MOVIMENTAÇÕES ---")
        print(f"Andamentos atualizados (PDFs vinculados): {movimentacoes_atualizadas}")
        print(f"Novos andamentos descobertos em PDFs e inseridos: {movimentacoes_inseridas}")
    except Exception as e:
        db.rollback()
        print(f"Erro crítico no enriquecimento de movimentações: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    raiz_projeto = Path(__file__).resolve().parent.parent.parent.parent
    pasta_jsons_principal = raiz_projeto / "data" / "Texto_json"
    
    if not pasta_jsons_principal.exists():
        print(f"A pasta {pasta_jsons_principal} não existe")
    else:
        enriquecer_movimentacoes_json(pasta_jsons_principal)