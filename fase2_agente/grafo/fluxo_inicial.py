import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

# Ajuste rigoroso de caminhos para comunicação entre módulos
pasta_grafo = Path(__file__).resolve().parent          # fase2_agente/grafo
pasta_fase2 = pasta_grafo.parent                       # fase2_agente
pasta_raiz = pasta_fase2.parent                        # Raiz do projeto

# Carrega as variáveis de ambiente e a chave da API do Google
load_dotenv(pasta_raiz / ".env", override=True)
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# Adiciona os caminhos ao sistema para que as importações funcionem sem quebras
sys.path.append(str(pasta_grafo))
sys.path.append(str(pasta_fase2 / "rag"))

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage

# Importando os ficheiros e funções desenvolvidos pela sua equipa
from estado import EstadoAgente
from no_reformulacao import reformular_pergunta
from no_busca import executar_no_de_busca

# ADAPTADORES (WRAPPERS) PARA O LANGGRAPH

# Como as suas funções atuais recebem e devolvem strings puras, criamos estes
# "embrulhos" para adaptá-las ao padrão de dicionários exigido pelo LangGraph.

def no_langgraph_reformulacao(state: EstadoAgente) -> Dict[str, Any]:
    """
    Nó que extrai a última mensagem do utilizador, executa a função 
    de reformulação e anota o resultado no Estado do Grafo.
    """
    # Pega na última mensagem de texto enviada pelo utilizador humano
    ultima_mensagem = state["messages"][-1].content
    
    # Executa a função contida no seu no_reformulacao.py
    pergunta_reformulada = reformular_pergunta(ultima_mensagem)
    
    # Retorna uma AIMessage para ser adicionada à lista de mensagens do estado
    return {"messages": [AIMessage(content=pergunta_reformulada, name="Reformulador")]}


def no_langgraph_busca(state: EstadoAgente) -> Dict[str, Any]:
    """
    Nó que lê a pergunta reformulada, passa para o vosso Roteador Inteligente
    e guarda o resultado/contexto final obtido no Banco de Dados ou API.
    """
    # Pega na pergunta que acabou de ser processada e limpa pelo nó anterior
    pergunta_para_busca = state["messages"][-1].content
    
    # Executa a função contida no vosso no_busca.py
    resultado_da_busca = executar_no_de_busca(pergunta_para_busca)
    
    # Retorna o resultado para atualizar a lista de mensagens do estado
    return {"messages": [AIMessage(content=resultado_da_busca, name="Buscador")]}



# MONTAGEM E COMPILAÇÃO DO GRAFO (ORQUESTRAÇÃO)
# Iniciamos o fluxo definindo qual é a estrutura do nosso Estado (caderno)
workflow = StateGraph(EstadoAgente)

# Registamos os nós modulares dentro do tabuleiro do grafo
workflow.add_node("reformulacao_node", no_langgraph_reformulacao)
workflow.add_node("busca_node", no_langgraph_busca)

# Definimos as regras de caminhos e setas (Edges)
workflow.add_edge(START, "reformulacao_node")              # O fluxo começa na reformulação
workflow.add_edge("reformulacao_node", "busca_node")       # Da reformulação vai direto para a busca
workflow.add_edge("busca_node", END)                       # A busca encerra o fluxo atual (Entrega o dado)

# Compilamos o Grafo para transformá-lo num programa executável
grafo_inicial = workflow.compile()



if __name__ == "__main__":
    print("\n====================================================")
    print("   SISTEMA DE TESTES - FLUXO MODULAR REFORMULAÇÃO -> BUSCA")
    print("====================================================\n")
    print("Instruções: Digite a sua pergunta jurídica abaixo.")
    print("Para encerrar o teste, digite 'sair'.\n")
    
    # Mantém a memória da conversa ativa nesta sessão do terminal
    historico_da_conversao = {"messages": []}
    
    while True:
        entrada_usuario = input("\nUtilizador: ")
        if entrada_usuario.lower() == 'sair':
            print("Encerrando o ambiente de testes do grafo.")
            break
            
        if not entrada_usuario.strip():
            continue
            
        #Injeta a nova frase do utilizador como uma HumanMessage no histórico
        historico_da_conversao["messages"].append(HumanMessage(content=entrada_usuario))
        
        print("\n[Executando Grafo LangGraph...]")
        
        #O Grafo executa todos os nós sequencialmente recebendo o histórico acumulado
        estado_final = grafo_inicial.invoke(historico_da_conversao)
        
        #Atualiza a memória da sessão com o estado final devolvido pelo grafo
        historico_da_conversao = estado_final
        
        #Extrai e exibe apenas o último movimento do grafo (o retorno do Nó de Busca)
        resposta_final_do_no = estado_final["messages"][-1].content
        print(f"\n[RETORNO DO SEU NÓ DE BUSCA]:\n{resposta_final_do_no}")
        print("=" * 60)