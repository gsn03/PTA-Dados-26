import sys
from pathlib import Path
import json
import re # Nova importação para manipular textos

# 1. Ajuste de caminhos 
pasta_bd = Path(__file__).parent.parent
sys.path.append(str(pasta_bd))

# 2. Importações do Banco de Dados
from database_model import SessionLocal
from model_Cliente import Cliente
from model_processos import Processo

def limpar_valor_monetario(valor):
    if valor is None or valor == "": return None
    if isinstance(valor, (int, float)): return float(valor)
    valor_limpo = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(valor_limpo)
    except ValueError:
        return None

# NOVA FUNÇÃO: Tradutor de datas para o padrão do PostgreSQL
def formatar_data(texto_data):
    if not texto_data:
        return None
    
    texto_lower = str(texto_data).lower().strip()
    meses = {
        "janeiro": "01", "fevereiro": "02", "março": "03", "marco": "03",
        "abril": "04", "maio": "05", "junho": "06",
        "julho": "07", "agosto": "08", "setembro": "09",
        "outubro": "10", "novembro": "11", "dezembro": "12"
    }
    
    # Tenta encontrar o padrão "05 de fevereiro de 2026"
    match_extenso = re.search(r"(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})", texto_lower)
    if match_extenso:
        dia = match_extenso.group(1).zfill(2)
        mes = meses.get(match_extenso.group(2))
        ano = match_extenso.group(3)
        if mes:
            return f"{ano}-{mes}-{dia}" # Retorna no formato YYYY-MM-DD
            
    # Tenta encontrar o padrão numérico "15/01/2025"
    match_barras = re.search(r"(\d{2})/(\d{2})/(\d{4})", texto_lower)
    if match_barras:
        return f"{match_barras.group(3)}-{match_barras.group(2)}-{match_barras.group(1)}"
        
    # Se for um texto ilegível para o banco, devolve nulo para não causar erro
    return None

def carregar_processos_do_json(pasta_jsons: Path):
    db = SessionLocal()
    
    try:
        for arquivo in pasta_jsons.rglob("*.json"):
            if "Relatorio" in arquivo.name:
                continue

            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)

            num_proc = dados.get("numero_processo") or dados.get("n_processo")
            if not num_proc:
                continue

            existe = db.query(Processo).filter(Processo.numero_processo == num_proc).first()
            if existe:
                continue

            cliente_encontrado = None
            cpf_extraido = dados.get("cpf_cnpj")
            nome_extraido = dados.get("nome_cliente") or dados.get("acusando_autor") or dados.get("reclamante")

            if cpf_extraido:
                cliente_encontrado = db.query(Cliente).filter(Cliente.cpf_cnpj == cpf_extraido).first()
            
            if not cliente_encontrado and nome_extraido:
                cliente_encontrado = db.query(Cliente).filter(Cliente.nome.ilike(f"%{nome_extraido}%")).first()

            if not cliente_encontrado:
                print(f"Aviso: Cliente não encontrado para o processo {num_proc}. Ficheiro ignorado.")
                continue

            novo_processo = Processo(
                arquivo_origem=dados.get("arquivo_origem"), 
                numero_processo=num_proc,
                cliente_id=cliente_encontrado.id, 
                tipo_processo=dados.get("tipo_processo"),
                fase=dados.get("fase"),
                status=dados.get("status"),
                nome_advogado=dados.get("nome_advogado") or dados.get("advogado"),
                # ATUALIZAÇÃO AQUI: Passando os dados pela função formatadora
                data_abertura=formatar_data(dados.get("data_abertura") or dados.get("data_expedicao")), 
                prazo_proximo=formatar_data(dados.get("prazo_proximo") or dados.get("prazo_contestacao")),
                valor_causa=limpar_valor_monetario(dados.get("valor_causa") or dados.get("valor_total_acordo")),
                vara=dados.get("vara") or dados.get("tribunal_vara"),
                observacoes=dados.get("observacoes") or dados.get("resultado_julgamento")
            )

            db.add(novo_processo)

        db.commit()
        print("Ingestão de processos concluída com sucesso!")

    except Exception as e:
        db.rollback()
        print(f"Erro crítico na ingestão: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    pasta_raiz = Path(__file__).parent.parent.parent.parent
    pasta_processos = pasta_raiz / "data" / "Texto_json"
    
    carregar_processos_do_json(pasta_processos)