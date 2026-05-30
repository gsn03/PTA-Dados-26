from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

# Esta classe é o "caderno de anotações" do nosso Agente.
# Tudo o que for gerado (perguntas, respostas, resultados de buscas) ficará salvo aqui.
class EstadoAgente(TypedDict):
    # A anotação 'add_messages' garante que as novas mensagens (como o resultado do banco de dados)
    # sejam adicionadas ao histórico da conversa, em vez de apagarem a pergunta original.
    messages: Annotated[list, add_messages]