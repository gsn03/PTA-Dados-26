import sys
from pathlib import Path
import json
from datetime import datetime

pasta_bd = Path(__file__).parent.parent / "BD"
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from model_processos import Processo

def limpar_valor_monetario(valor):
    """Converte 'R$ 1.200,50' ou 1200.5 em float puro"""
    if valor is None or valor == "": return None
    if isinstance(valor, (int, float)): return float(valor)
    
    # Se for string, limpa os caracteres não numéricos
    valor_limpo = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(valor_limpo)
    except ValueError:
        return None

def carregar_processos_do_json(pasta_jsons: Path):
    db = SessionLocal()
    
    try:
        for arquivo in pasta_jsons.rglob("*.json"):
            # Ignora arquivos de relatório se houver
            if "Relatorio" in arquivo.name:
                continue

            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)

            num_proc = dados.get("numero_processo")
            if not num_proc:
                continue

            # 1. Verifica se o processo já existe para evitar duplicidade
            existe = db.query(Processo).filter(Processo.numero_processo == num_proc).first()
            if existe:
                continue

            # 2. Cria o novo objeto de Processo com os dados limpos
            novo_processo = Processo(
                numero_processo=num_proc,
                cliente_id=dados.get("cliente_id"), # Deve ser um ID numérico que já existe na tabela clientes
                tipo_processo=dados.get("tipo_processo"),
                fase=dados.get("fase"),
                status=dados.get("status"),
                nome_advogado=dados.get("nome_advogado"),
                data_abertura=dados.get("data_abertura"), # O Postgres aceita strings ISO (AAAA-MM-DD)
                prazo_proximo=dados.get("prazo_proximo"),
                valor_causa=limpar_valor_monetario(dados.get("valor_causa")),
                vara=dados.get("vara"),
                observacoes=dados.get("observacoes")
            )

            db.add(novo_processo)

        # salva todas as alterações 
        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Erro crítico na ingestão: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Define o caminho para a pasta onde os JSONs de processos estão
    pasta_raiz = Path(__file__).parent.parent.parent.parent
    pasta_processos = pasta_raiz / "data" / "Texto_json"
    
    carregar_processos_do_json(pasta_processos)