from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

# Esta classe é o "caderno de anotações" do nosso Agente completo.
class EstadoAgente(TypedDict):
    # Histórico de mensagens trocadas no grafo
    messages: Annotated[list, add_messages]
    
    # Campos de controle exigidos para o Nó de Validação
    contexto_recuperado: str
    resposta_gerada: str
    tentativas: int