import os
import sys
from pathlib import Path
from dotenv import load_dotenv

pasta_grafo = Path(__file__).resolve().parent          # fase2_agente/grafo
pasta_fase2 = pasta_grafo.parent                       # fase2_agente
pasta_raiz = pasta_fase2.parent                        # Raiz
pasta_rag = pasta_fase2 / "rag"                        # fase2_agente/rag

# Carrega a chave do Google
load_dotenv(pasta_raiz / ".env", override=True)
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# Adiciona a pasta rag ao sys.path para conseguirmos importar a lista_de_ferramentas
sys.path.append(str(pasta_rag))

from tools import lista_de_ferramentas
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

llm_roteador = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# "Ensinando" as ferramentas ao LLM
# O método bind_tools conecta as nossas 4 ferramentas Python ao cérebro do Gemini
llm_com_ferramentas = llm_roteador.bind_tools(lista_de_ferramentas)

# um dicionário para poder executar a ferramenta pelo nome que o LLM escolher
mapa_ferramentas = {ferramenta.name: ferramenta for ferramenta in lista_de_ferramentas}

# A FUNÇÃO PRINCIPAL DO SEU NÓ (Esta é a função que a equipa do LangGraph vai chamar)
def executar_no_de_busca(entrada_texto: str) -> str:
    """
    Recebe a pergunta limpa da equipa de Tradução, decide qual ferramenta usar,
    valida regras de negócio rigorosas e devolve o contexto do Banco de Dados.
    """
    
    # A INSTRUÇÃO RIGOROSA DE SEGURANÇA (O System Prompt do nosso nó)
    prompt_sistema = SystemMessage(content="""
    Você é o Roteador de Ferramentas de um sistema jurídico de elite.
    A sua ÚNICA função é ler a frase do usuário e acionar a ferramenta correta.
    
    REGRAS CRÍTICAS DE VALIDAÇÃO:
    1. Se a intenção for buscar o histórico/status de um processo, você DEVE acionar a ferramenta 'buscar_historico_processo'.
    2. PROIBIÇÃO: A ferramenta 'buscar_historico_processo' exige o número do processo E o nome do cliente. 
       Se o usuário NÃO fornecer o nome do cliente na frase, NÃO acione a ferramenta. 
       Responda EXATAMENTE: 'SISTEMA_VALIDACAO: Para consultar este processo, por favor, informe também o nome do cliente associado.'
    3. Se não precisar de ferramentas, apenas responda normalmente.
    
    A Proibição: "Se a pergunta do utilizador NÃO tiver nenhuma relação com processos, prazos, clientes, finanças do escritório ou documentos jurídicos, NÃO acione nenhuma ferramenta.
    Responda: 'SISTEMA_VALIDACAO: Sou um agente restrito ao contexto do escritório. Não posso responder a perguntas fora deste escopo.'
    
    A Proibição: "A ferramenta 'checar_inadimplencia_honorarios' não aceita parâmetros.
    Se o utilizador perguntar sobre a dívida de um cliente específico, acione a ferramenta SEM parâmetros, e a equipa de Geração filtrará a resposta final."
    
    A Proibição: "Para acionar a ferramenta 'buscar_jurisprudencia_documentos', a pergunta deve conter um tema ou assunto claro. 
    Se o utilizador disser apenas 'busque um documento', NÃO acione a ferramenta. 
    Responda: 'SISTEMA_VALIDACAO: Sobre qual tema, cliente ou processo deseja que eu busque nos documentos?'"
    """)
    
    mensagem_usuario = HumanMessage(content=entrada_texto)
    
    try:
        print(f"[NÓ DE BUSCA] Analisando a entrada: '{entrada_texto}'...")
        
        # O LLM pensa e decide
        resposta_ia = llm_com_ferramentas.invoke([prompt_sistema, mensagem_usuario])
        
        # CENÁRIO A: A IA decidiu chamar uma ferramenta
        if resposta_ia.tool_calls:
            chamada = resposta_ia.tool_calls[0]
            nome_ferramenta = chamada["name"]
            argumentos = chamada["args"]
            
            print(f"[NÓ DE BUSCA] Ferramenta escolhida: {nome_ferramenta}")
            print(f"[NÓ DE BUSCA] Parâmetros extraídos: {argumentos}")
            
            # Executa a ferramenta Python real com os argumentos que a IA extraiu
            ferramenta_real = mapa_ferramentas[nome_ferramenta]
            resultado_api = ferramenta_real.invoke(argumentos)
            
            print(f"[NÓ DE BUSCA] Sucesso! Dados recuperados da API.")
            return resultado_api
            
        # CENÁRIO B: A IA foi bloqueada pela nossa regra (Ex: Faltou o nome do cliente)
        else:
            print("[NÓ DE BUSCA] Nenhuma ferramenta foi acionada (Regra de Validação ou Pergunta Genérica).")
            return resposta_ia.content

    except Exception as e:
        erro_msg = f"RESULTADO_SISTEMA: Erro interno no Nó de Busca: {e}"
        print(erro_msg)
        return erro_msg

# -----------------------------------------------------------------------------
# ÁREA DE TESTES LOCAIS (Para você testar antes de entregar para o LangGraph)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n--- TESTE 1: Bloqueio por falta de nome do cliente ---")
    teste1 = executar_no_de_busca("Qual o status do processo 3679963-72.2020.9.29.7859?")
    print(f"RETORNO: {teste1}\n")
    
    print("--- TESTE 2: Busca completa (Sucesso esperado) ---")
    teste2 = executar_no_de_busca("Qual o status do processo 3679963-72.2020.9.29.7859 do cliente Leandro Pinto?")
    print(f"RETORNO: {teste2}\n")
    
    print("--- TESTE 3: Ferramenta de Prazos ---")
    teste3 = executar_no_de_busca("Quais são os nossos prazos urgentes para os próximos 5 dias?")
    print(f"RETORNO: {teste3}\n")
    
    print("--- TESTE 4: Busca Vetorial em PDFs (pgvector) ---")
    teste4 = executar_no_de_busca("Qual o valor do acordo da Fernanda Costa nos documentos?")
    print(f"RETORNO: {teste4}\n")
    
    print("--- TESTE 5: Busca Vetorial (Teses/Argumentos) ---")
    teste5 = executar_no_de_busca("Temos algum documento sobre danos morais ou acordo trabalhista?")
    print(f"RETORNO: {teste5}\n")