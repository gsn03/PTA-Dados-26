import sys
from pathlib import Path
from dotenv import load_dotenv

# 1. Ajuste de caminhos no topo
pasta_rag = Path(__file__).resolve().parent # pasta: fase2_agente/rag
pasta_agente = pasta_rag.parent             # pasta: fase2_agente
pasta_raiz = pasta_agente.parent            # pasta: raiz do projeto

# Carrega as variáveis de ambiente (API Key) a partir da raiz
load_dotenv(pasta_raiz / ".env", override=True)

# Adiciona o caminho da Fase 1 (BD) ao sistema para resgatar o banco_vetorial.py
pasta_bd = pasta_raiz / "fase1_engenharia" / "BD"
sys.path.append(str(pasta_bd))

# Como fluxo.py e gerador_rag.py estão lado a lado, adicionamos a própria pasta rag ao path
sys.path.append(str(pasta_rag)) 

pasta_grafo = pasta_agente / "grafo"
sys.path.append(str(pasta_grafo))

from banco_vetorial import buscar_contexto_semantico
from gerador_rag import gerar_resposta
from no_reformulacao import reformular_pergunta

def executar_rag(pergunta_usuario: str):
    # Recuperação
    pergunta_reformulada = reformular_pergunta(pergunta_usuario)
    contexto = buscar_contexto_semantico(pergunta_reformulada)
    
    if not contexto.strip():
        return "Nenhum documento relevante encontrado na base."
    
    # Geração
    resposta_final = gerar_resposta(pergunta_reformulada, contexto)
    
    print("\n--- RESPOSTA FINAL ---")
    return resposta_final

if __name__ == "__main__":
    # Teste 
    pergunta = "Qual o valor do acordo da Fernanda Costa?"
    resposta = executar_rag(pergunta)
    print(resposta)