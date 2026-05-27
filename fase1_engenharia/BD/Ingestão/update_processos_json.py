import sys
from pathlib import Path
import json
import re

# 1. Ajuste de caminhos no topo
pasta_bd = Path(__file__).resolve().parent.parent
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from model_processos import Processo
from model_Cliente import Cliente

# Funções de limpeza adaptadas do seu script original
def limpar_valor_monetario(valor):
    if valor is None or valor == "": return None
    if isinstance(valor, (int, float)): return str(valor)
    valor_limpo = str(valor).replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return str(float(valor_limpo))
    except ValueError:
        return None

def formatar_data(texto_data):
    if not texto_data: return None
    # Simples extrator de data AAAA-MM-DD
    match = re.search(r"(\d{4}-\d{2}-\d{2})", str(texto_data))
    if match: return match.group(1)
    # Tenta converter DD/MM/AAAA para AAAA-MM-DD
    match_br = re.search(r"(\d{2})/(\d{2})/(\d{4})", str(texto_data))
    if match_br: return f"{match_br.group(3)}-{match_br.group(2)}-{match_br.group(1)}"
    return None

def enriquecer_processos_json(pasta_jsons: Path):
    db = SessionLocal()
    
    try:
        print(f"Iniciando varredura de JSONs para enriquecer Processos...")
        processos_atualizados = 0
        processos_inseridos = 0
        
        for arquivo in pasta_jsons.rglob("*.json"): 
            if "Relatorio" in arquivo.name:
                continue
                
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
            
            num_proc = dados.get("numero_processo") or dados.get("processo") or dados.get("n_processo")
            if not num_proc:
                continue
            
            # Dados do JSON que precisamos resgatar
            arq_origem = dados.get("arquivo_origem") or arquivo.name
            val_causa = limpar_valor_monetario(dados.get("valor_causa") or dados.get("valor_total_acordo"))
            vara = dados.get("vara") or dados.get("tribunal_vara")
            dt_abertura = formatar_data(dados.get("data_abertura") or dados.get("data_expedicao"))
            dt_prazo = formatar_data(dados.get("prazo_proximo") or dados.get("prazo_contestacao"))
            
            # Busca TODAS as fases desse processo no banco
            processos_existentes = db.query(Processo).filter(Processo.numero_processo == num_proc).all()
            
            if processos_existentes:
                atualizou_algo = False
                for proc in processos_existentes:
                    # SMART UPDATE: Só preenche o que for nulo (None)
                    if not proc.arquivo_origem and arq_origem:
                        proc.arquivo_origem = arq_origem
                        atualizou_algo = True
                    if not proc.valor_causa and val_causa:
                        proc.valor_causa = val_causa
                        atualizou_algo = True
                    if not proc.vara and vara:
                        proc.vara = vara
                        atualizou_algo = True
                    if not proc.data_abertura and dt_abertura:
                        proc.data_abertura = dt_abertura
                        atualizou_algo = True
                    if not proc.prazo_proximo and dt_prazo:
                        proc.prazo_proximo = dt_prazo
                        atualizou_algo = True
                        
                if atualizou_algo:
                    processos_atualizados += 1
            else:
                # INSERT DE PROCESSO NOVO (Requer encontrar o cliente)
                cpf_cliente = dados.get("cpf_cnpj") or dados.get("cpf_cnpj_contratante")
                nome_cliente = dados.get("nome_cliente") or dados.get("autor") or dados.get("reclamante")
                
                cliente_db = None
                if cpf_cliente:
                    cliente_db = db.query(Cliente).filter(Cliente.cpf_cnpj == cpf_cliente).first()
                if not cliente_db and nome_cliente:
                    cliente_db = db.query(Cliente).filter(Cliente.nome.ilike(f"%{nome_cliente}%")).first()
                    
                if cliente_db:
                    novo_processo = Processo(
                        arquivo_origem=arq_origem,
                        numero_processo=num_proc,
                        cliente_id=cliente_db.id,
                        tipo_processo=dados.get("tipo_processo"),
                        fase=dados.get("fase"),
                        status=dados.get("status"),
                        nome_advogado=dados.get("nome_advogado") or dados.get("advogado"),
                        data_abertura=dt_abertura,
                        prazo_proximo=dt_prazo,
                        valor_causa=val_causa,
                        vara=vara,
                        observacoes=dados.get("observacoes") or dados.get("resultado_julgamento")
                    )
                    db.add(novo_processo)
                    db.commit() # Commit imediato para o loop
                    processos_inseridos += 1

        db.commit()
        print("\n--- RESUMO DO ENRIQUECIMENTO DE PROCESSOS ---")
        print(f"Processos atualizados (lacunas e arquivos preenchidos): {processos_atualizados}")
        print(f"Novos processos descobertos e inseridos: {processos_inseridos}")
        
    except Exception as e:
        db.rollback()
        print(f"Erro crítico no enriquecimento de processos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    raiz_projeto = Path(__file__).resolve().parent.parent.parent.parent
    pasta_jsons_principal = raiz_projeto / "data" / "Texto_json"
    
    if not pasta_jsons_principal.exists():
        print(f"A pasta {pasta_jsons_principal} não existe")
    else:
        enriquecer_processos_json(pasta_jsons_principal)