import sys
from pathlib import Path
import pandas as pd
import numpy as np

# 1. Ajuste de caminhos no topo
pasta_bd = Path(__file__).resolve().parent.parent
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from model_processos import Processo
from model_Cliente import Cliente

# FUNÇÃO HIGIENIZADORA: Destrói qualquer variação de NaN/Vazio e transforma em None
def limpar_dado(valor):
    if pd.isna(valor): 
        return None
    if str(valor).strip().lower() in ["nan", "nat", "none", ""]: 
        return None
    return valor

def carregar_processos_csv(caminho_processos: Path, caminho_clientes: Path):
    db = SessionLocal()
    
    try:
        print("Lendo bases de dados...")
        df_processos = pd.read_csv(caminho_processos, sep=",", encoding="utf-8")
        df_clientes = pd.read_csv(caminho_clientes, sep=",", encoding="utf-8")
        
        # 1. DESARMANDO A BOMBA DE DUPLICATAS (Nova Regra)
        qtd_antes = len(df_processos)
        colunas_verificacao = [col for col in df_processos.columns if col != "processo_id"]
        df_processos = df_processos.drop_duplicates(subset=colunas_verificacao, keep="first")
        qtd_depois = len(df_processos)
        print(f"Duplicatas removidas: {qtd_antes - qtd_depois} linhas ignoradas.")     
           
        # 2. MAPEAMENTO DE CHAVES ESTRANGEIRAS
        mapa_clientes_csv = df_clientes.set_index("cliente_id")["cpf"].to_dict()
        
        processos_inseridos = 0
        processos_ignorados = 0
        
        print("Iniciando inserção no banco de dados...")
        for index, row in df_processos.iterrows():
            numero = limpar_dado(row.get("numero_processo"))
            
            if not numero:
                continue

            # --- VALIDAÇÃO DE HISTÓRICO CORRIGIDA ---
            fase_limpa = limpar_dado(row.get("fase"))
            status_limpo = limpar_dado(row.get("status"))
            
            proc_existente = db.query(Processo).filter(
                Processo.numero_processo == numero,
                Processo.fase == fase_limpa,
                Processo.status == status_limpo
            ).first()
            
            if proc_existente:
                processos_ignorados += 1
                continue
            # ----------------------------------------

            # --- RECUPERAÇÃO DO CLIENTE CORRIGIDA ---
            id_csv = row.get("cliente_id")
            cpf_cliente = mapa_clientes_csv.get(id_csv)
            
            if not cpf_cliente:
                continue

            cliente_db = db.query(Cliente).filter(Cliente.cpf_cnpj == cpf_cliente).first()
            
            if not cliente_db:
                continue
            # ----------------------------------------

            # 3. CRIAÇÃO COM HIGIENIZAÇÃO LINHA A LINHA
            valor_causa_limpo = limpar_dado(row.get("valor_causa"))
            
            novo_processo = Processo(
                numero_processo=numero,
                cliente_id=cliente_db.id,
                tipo_processo=limpar_dado(row.get("tipo")),
                fase=fase_limpa,
                status=status_limpo,
                nome_advogado=limpar_dado(row.get("advogado_responsavel")),
                data_abertura=limpar_dado(row.get("data_abertura")),
                prazo_proximo=limpar_dado(row.get("prazo_proximo")),
                valor_causa=str(valor_causa_limpo) if valor_causa_limpo else None,
                vara=limpar_dado(row.get("vara")),
                observacoes=limpar_dado(row.get("observacoes"))
            )
            
            db.add(novo_processo)
            processos_inseridos += 1

        db.commit()
        print(f"\n--- RESUMO DA INGESTÃO DE PROCESSOS ---")
        print(f"Processos inseridos: {processos_inseridos}")
        print(f"Processos ignorados (já existiam com a mesma fase/status): {processos_ignorados}")
        
    except Exception as e:
        db.rollback()
        print(f"Erro crítico na ingestão de processos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    raiz_projeto = Path(__file__).resolve().parent.parent.parent.parent
    caminho_csv_processos = raiz_projeto / "data" / "Bases_Tratadas" / "Processos_Tratados.csv"
    caminho_csv_clientes = raiz_projeto / "data" / "Bases_Tratadas" / "Clientes_Tratados.csv"
    
    if not caminho_csv_processos.exists() or not caminho_csv_clientes.exists():
        print(f"ERRO: Verifique se os arquivos CSV existem na pasta.")
    else:
        carregar_processos_csv(caminho_csv_processos, caminho_csv_clientes)