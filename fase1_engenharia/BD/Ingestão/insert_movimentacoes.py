import sys
from pathlib import Path
import pandas as pd
import numpy as np

# 1. Ajuste de caminhos no topo
pasta_bd = Path(__file__).resolve().parent.parent
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from model_movimentacoes import Movimentacao

# FUNÇÃO HIGIENIZADORA: Transforma 'nan' do Pandas em None puro do Python
def limpar_dado(valor):
    if pd.isna(valor): 
        return None
    if str(valor).strip().lower() in ["nan", "nat", "none", ""]: 
        return None
    return valor

def carregar_movimentacoes_csv(caminho_csv: Path):
    db = SessionLocal()
    
    try:
        print("A ler a base de dados de movimentações...")
        df_mov = pd.read_csv(caminho_csv, sep=",", encoding="utf-8")
        
        # 1. REMOÇÃO DE DUPLICATAS NA PLANILHA (Ignorando o ID)
        qtd_antes = len(df_mov)
        colunas_verificacao = [col for col in df_mov.columns if col != "movimentacao_id"]
        df_mov = df_mov.drop_duplicates(subset=colunas_verificacao, keep="first")
        qtd_depois = len(df_mov)
        if qtd_antes > qtd_depois:
            print(f"Duplicatas removidas da planilha: {qtd_antes - qtd_depois} linhas ignoradas.")
        
        mov_inseridas = 0
        mov_ignoradas = 0
        
        print("A iniciar inserção no banco de dados...")
        for index, row in df_mov.iterrows():
            
            num_proc = limpar_dado(row.get("numero_processo"))
            if not num_proc:
                continue

            # Variáveis-chave para verificar se a movimentação já existe no histórico
            data_mov = limpar_dado(row.get("data_movimentacao"))
            desc = limpar_dado(row.get("descricao"))
            tipo = limpar_dado(row.get("tipo_ato"))

            # Validação: Evita que o mesmo andamento seja inserido duas vezes no mesmo processo
            mov_existente = db.query(Movimentacao).filter(
                Movimentacao.numero_processo == num_proc,
                Movimentacao.data_movimentacao == data_mov,
                Movimentacao.descricao == desc
            ).first()
            
            if mov_existente:
                mov_ignoradas += 1
                continue

            # 3. CRIAÇÃO COM HIGIENIZAÇÃO LINHA A LINHA
            nova_movimentacao = Movimentacao(
                numero_processo=num_proc,
                data_movimentacao=data_mov,
                tipo_ato=tipo,
                advogado_responsavel=limpar_dado(row.get("advogado_responsavel")),
                descricao=desc,
                prazo_gerado=limpar_dado(row.get("prazo_gerado")),
                concluido=limpar_dado(row.get("concluido")),
                prazo_final=limpar_dado(row.get("prazo_final")),
                # Dias de prazo pode vir como número, então convertemos para string de forma segura
                dias_prazo=str(limpar_dado(row.get("dias_prazo"))) if limpar_dado(row.get("dias_prazo")) is not None else None
            )
            
            db.add(nova_movimentacao)
            mov_inseridas += 1

        db.commit()
        print(f"\n--- RESUMO DA INGESTÃO DE MOVIMENTAÇÕES ---")
        print(f"Movimentações inseridas no histórico: {mov_inseridas}")
        print(f"Movimentações ignoradas (já existiam no banco): {mov_ignoradas}")
        
    except Exception as e:
        db.rollback()
        print(f"Erro crítico na ingestão de movimentações: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    raiz_projeto = Path(__file__).resolve().parent.parent.parent.parent
    caminho_csv_mov = raiz_projeto / "data" / "Bases_Tratadas" / "Movimentacoes_tratado.csv"
    
    if not caminho_csv_mov.exists():
        print(f"ERRO: Verifique se o ficheiro Movimentacoes_tratado.csv existe na pasta.")
    else:
        carregar_movimentacoes_csv(caminho_csv_mov)