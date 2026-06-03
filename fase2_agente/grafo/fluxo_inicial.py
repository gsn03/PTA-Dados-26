import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

pasta_grafo = Path(__file__).resolve().parent          # fase2_agente/grafo
pasta_fase2 = pasta_grafo.parent                       # fase2_agente
pasta_raiz = pasta_fase2.parent                        # Raiz do projeto

load_dotenv(pasta_raiz / ".env", override=True)
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

sys.path.append(str(pasta_grafo))
sys.path.append(str(pasta_fase2 / "automacoes"))

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage

# Importação de todos os 4 nós construídos
from estado import EstadoAgente
from no_reformulacao import reformular_pergunta
from no_busca import executar_no_de_busca
from no_resposta import executar_no_de_resposta
from no_validacao import no_validacao

# -----------------------------------------------------------------------------
# WRAPPERS DE INTEGRAÇÃO (LANGGRAPH)
# -----------------------------------------------------------------------------

def node_reformulacao_wrapper(state: EstadoAgente) -> Dict[str, Any]:
    # 1. Pega todas as mensagens humanas do estado global
    mensagens_humanas = [m for m in state["messages"] if isinstance(m, HumanMessage)]
    
    # 2. A pergunta atual é a última mensagem da lista
    ultima_msg = mensagens_humanas[-1].content if mensagens_humanas else state["messages"][-1].content
    
    # 3. O histórico são as mensagens humanas anteriores (limitado às últimas 3 para economizar tokens)
    historico_str = ""
    if len(mensagens_humanas) > 1:
        mensagens_anteriores = mensagens_humanas[-4:-1] # Pega até 3 mensagens antes da atual
        for i, m in enumerate(mensagens_anteriores):
            historico_str += f"Pergunta Anterior {i+1}: {m.content}\n"
    
    # 4. Envia o histórico e a pergunta para o novo reformulador
    pergunta_reformulada = reformular_pergunta(ultima_msg, historico=historico_str)
    
    tentativas = state.get("tentativas", 0) or 0
    return {
        "messages": [AIMessage(content=pergunta_reformulada, name="Reformulador")],
        "tentativas": tentativas + 1
    }
    
def node_busca_wrapper(state: EstadoAgente) -> Dict[str, Any]:
    pergunta_reformulada = state["messages"][-1].content
    resultado_json_str = executar_no_de_busca(pergunta_reformulada)
    
    return {
        "messages": [AIMessage(content=resultado_json_str, name="Buscador")],
        "contexto_recuperado": resultado_json_str
    }

def node_resposta_wrapper(state: EstadoAgente) -> Dict[str, Any]:
    pergunta_original = state["messages"][-1].content
    json_busca_str = state["contexto_recuperado"]
    
    resposta_texto = executar_no_de_resposta(pergunta_original, json_busca_str)
    
    return {
        "messages": [AIMessage(content=resposta_texto, name="Redator")],
        "resposta_gerada": resposta_texto
    }

# -----------------------------------------------------------------------------
# ROTEADOR DA VALIDAÇÃO (Conditional Edge)
# -----------------------------------------------------------------------------
def rotear_apos_validacao(state: EstadoAgente) -> str:
    """
    Chama o nó de validação passando o payload correto e decide o rumo do fluxo.
    """
    print("\n--- INICIANDO NÓ DE VALIDAÇÃO (AUDITORIA) ---")
    
    # Se houver um aviso de validação do sistema, encerra direto sem precisar julgar
    if "SISTEMA_VALIDACAO:" in state["resposta_gerada"]:
        print("[ROTEADOR VALIDAÇÃO] Alerta de sistema ou bloqueio detectado. Encerrando.")
        return "finalizar"
        
    if state.get("tentativas", 1) > 3:
        print("[ROTEADOR VALIDAÇÃO] Limite máximo de 3 tentativas atingido. Encerrando para evitar loop.")
        return "finalizar"

    # Constrói o payload exatamente como o no_validacao.py espera
    payload = {
        "contexto_recuperado": state["contexto_recuperado"],
        "resposta_gerada": state["resposta_gerada"],
        "tentativas": state["tentativas"]
    }
    
    # Executa a função do no_validacao.py
    decisao_auditor = no_validacao(payload)
    
    if decisao_auditor.get("status") == "APROVADO" or decisao_auditor.get("proximo_passo") == "fim":
        print("[ROTEADOR VALIDAÇÃO] Resposta aprovada com sucesso pelo auditor.")
        return "finalizar"
    else:
        print(f"[ROTEADOR VALIDAÇÃO] Resposta REPROVADA. Motivo: {decisao_auditor.get('motivo')}")
        print("Retornando ao Nó de Resposta para reescrever o texto...")
        return "corrigir"

# -----------------------------------------------------------------------------
# CONSTRUÇÃO DO FLUXO COMPLETO
# -----------------------------------------------------------------------------
workflow = StateGraph(EstadoAgente)

# Adicionando os nós adaptados
workflow.add_node("reformulacao", node_reformulacao_wrapper)
workflow.add_node("busca", node_busca_wrapper)
workflow.add_node("resposta", node_resposta_wrapper)

# Desenho das conexões fixas do encanamento
workflow.add_edge(START, "reformulacao")
workflow.add_edge("reformulacao", "busca")
workflow.add_edge("busca", "resposta")

# Aresta condicional saindo da Resposta, executando o validador e decidindo o destino
# Aresta condicional saindo da Resposta, executando o validador e decidindo o destino
workflow.add_conditional_edges(
    "resposta",
    rotear_apos_validacao,
    {
        "finalizar": END,
        "corrigir": "resposta"  
    }
)

grafo_completo = workflow.compile()

# -----------------------------------------------------------------------------
# INTERFACE DE CHAT INTERATIVO DO AGENTE JURÍDICO
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n====================================================")
    print("   SISTEMA DE TESTES - GRAFO COMPLETO (4 NÓS COM LOOP)")
    print("====================================================\n")
    
    session_state = {"messages": [], "tentativas": 0}
    
    while True:
        entrada = input("\nUtilizador: ")
        if entrada.lower() == 'sair':
            break
            
        if not entrada.strip():
            continue
            
        session_state["messages"].append(HumanMessage(content=entrada))
        session_state["tentativas"] = 0 # Reseta o contador para a nova pergunta
        
        print("\n[Executando Linha de Produção do Agente...]")
        session_state = grafo_completo.invoke(session_state)
        
        resposta_final = session_state["messages"][-1].content
        print(f"\n[AGENTE JURÍDICO FINAL]:\n{resposta_final}")
        print("=" * 60)