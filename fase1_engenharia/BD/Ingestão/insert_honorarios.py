import sys
from pathlib import Path
import pandas as pd
import numpy as np

# 1. Ajuste de caminhos no topo
pasta_bd = Path(__file__).resolve().parent.parent
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from model_honorarios import contrato_honorario
from model_Cliente import Cliente

# FUNÇÃO HIGIENIZADORA: Destrói qualquer variação de NaN/Vazio e transforma em None
def limpar_dado(valor):
    if pd.isna(valor): 
        return None
    if str(valor).strip().lower() in ["nan", "nat", "none", ""]: 
        return None
    return valor

def carregar_honorarios_csv(caminho_honorarios: Path, caminho_clientes: Path):
    db = SessionLocal()
    
    try:
        print("Lendo bases de dados financeiras...")
        df_honorarios = pd.read_csv(caminho_honorarios, sep=",", encoding="utf-8")
        df_clientes = pd.read_csv(caminho_clientes, sep=",", encoding="utf-8")
        
        # 1. DESARMANDO DUPLICATAS DA PLANILHA (Remove linhas idênticas ignorando honorario_id)
        qtd_antes = len(df_honorarios)
        colunas_verificacao = [col for col in df_honorarios.columns if col != "honorario_id"]
        df_honorarios = df_honorarios.drop_duplicates(subset=colunas_verificacao, keep="first")
        qtd_depois = len(df_honorarios)
        if qtd_antes > qtd_depois:
            print(f"Duplicatas removidas: {qtd_antes - qtd_depois} linhas ignoradas.")
        
        # 2. MAPEAMENTO DE CHAVES ESTRANGEIRAS
        mapa_clientes_csv = df_clientes.set_index("cliente_id")["cpf"].to_dict()
        
        honorarios_inseridos = 0
        honorarios_ignorados = 0
        
        print("Iniciando inserção no banco de dados...")
        for index, row in df_honorarios.iterrows():
            
            numero = limpar_dado(row.get("numero_processo"))
            id_csv = row.get("cliente_id")
            cpf_cliente = mapa_clientes_csv.get(id_csv)
            
            if not cpf_cliente:
                continue

            # Busca o cliente real no banco
            cliente_db = db.query(Cliente).filter(Cliente.cpf_cnpj == cpf_cliente).first()
            if not cliente_db:
                continue

            # Validação de Duplicata no Banco (mesmo cliente e mesmo processo)
            contrato_existente = db.query(contrato_honorario).filter(
                contrato_honorario.cliente_id == cliente_db.id,
                contrato_honorario.numero_processo == numero
            ).first()
            
            if contrato_existente:
                honorarios_ignorados += 1
                continue

            # 3. CRIAÇÃO COM HIGIENIZAÇÃO LINHA A LINHA
            novo_honorario = contrato_honorario(
                cliente_id=cliente_db.id,
                numero_processo=numero,
                valor_total_contratado=str(limpar_dado(row.get("valor_total_contratado"))),
                n_parcelas=str(limpar_dado(row.get("n_parcelas"))),
                parcelas_pagas=str(limpar_dado(row.get("parcelas_pagas"))),
                valor_pago=str(limpar_dado(row.get("valor_pago"))),
                valor_em_aberto=str(limpar_dado(row.get("valor_em_aberto"))),
                data_contrato=limpar_dado(row.get("data_contrato")),
                data_vencimento=limpar_dado(row.get("data_vencimento")),
                forma_pagamento=limpar_dado(row.get("forma_pagamento")),
                honorarios_exito=limpar_dado(row.get("honorario_exito")), # Repare na diferença do 's' final
                percentual_exito=str(limpar_dado(row.get("percentual_exito"))),
                status_pagamento=limpar_dado(row.get("status_pagamento"))
            )
            
            db.add(novo_honorario)
            honorarios_inseridos += 1

        db.commit()
        print(f"\n--- RESUMO DA INGESTÃO DE HONORÁRIOS ---")
        print(f"Contratos inseridos: {honorarios_inseridos}")
        print(f"Contratos ignorados (já existiam no banco): {honorarios_ignorados}")
        
    except Exception as e:
        db.rollback()
        print(f"Erro crítico na ingestão de honorários: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    raiz_projeto = Path(__file__).resolve().parent.parent.parent.parent
    caminho_csv_honorarios = raiz_projeto / "data" / "Bases_Tratadas" / "Honorarios_Tratados.csv"
    caminho_csv_clientes = raiz_projeto / "data" / "Bases_Tratadas" / "Clientes_Tratados.csv"
    
    if not caminho_csv_honorarios.exists() or not caminho_csv_clientes.exists():
        print(f"ERRO: Verifique se os ficheiros CSV existem na pasta.")
    else:
        carregar_honorarios_csv(caminho_csv_honorarios, caminho_csv_clientes)