import sys
from pathlib import Path

# Adiciona o caminho para importar a pasta RAG
sys.path.append(str(Path(__file__).parent.parent))

from rag.banco_vetorial import buscar_contexto_semantico
from rag.gerador_rag import gerar_resposta

def executar_rag(pergunta_usuario: str):
    print("="*40)
    print("INICIANDO FLUXO RAG")
    print("="*40)
    # Recuperação
    contexto = buscar_contexto_semantico(pergunta_usuario)
    
    if not contexto.strip():
        return "Nenhum documento relevante encontrado na base."
    
    # Geração
    resposta_final = gerar_resposta(pergunta_usuario, contexto)
    
    print("\n--- RESPOSTA FINAL ---")
    return resposta_final

if __name__ == "__main__":
    # Teste 
    pergunta = "Quais são as condições da cláusula de rescisão no contrato de honorários?"
    resposta = executar_rag(pergunta)
    print(resposta)