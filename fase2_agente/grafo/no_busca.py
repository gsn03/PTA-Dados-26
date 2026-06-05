import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import json

pasta_grafo = Path(__file__).resolve().parent          # fase2_agente/grafo
pasta_fase2 = pasta_grafo.parent                       # fase2_agente
pasta_raiz = pasta_fase2.parent                        # Raiz
pasta_automacoes = pasta_fase2 / "automacoes"

sys.path.append(str(pasta_automacoes))

# Carrega a chave do Google
load_dotenv(pasta_raiz / ".env", override=True)
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# Adiciona a pasta rag ao sys.path para conseguirmos importar a lista_de_ferramentas

from tools import lista_de_ferramentas
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

llm_roteador = ChatGoogleGenerativeAI(model=os.getenv("LLM_MODEL", "gemini-2.5-flash"), temperature=0)

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
    

    prompt_sistema = SystemMessage(content="""
        Você é o Roteador de Ferramentas de um sistema jurídico de elite.
        A sua ÚNICA função é ler a frase do usuário e acionar a ferramenta correta.
        
        REGRAS CRÍTICAS DE VALIDAÇÃO:
        1. HISTÓRICO E STATUS: Se a frase pedir o histórico, status ou andamento de um processo E contiver o nome do cliente, você DEVE acionar a ferramenta 'buscar_historico_processo' preenchendo os dois parâmetros ('numero_processo' e 'nome_cliente').
        
        2. REGRA DO NOME AUSENTE: Se a frase pedir o histórico/status de um processo, mas NÃO contiver o nome do cliente, NÃO acione a ferramenta. Responda APENAS com este texto exato: 'SISTEMA_VALIDACAO: Para consultar este processo, por favor, informe também o nome do cliente associado.'
        
        3. REGRA DOS PRAZOS: Se a pergunta for sobre prazos ou processos urgentes, acione a ferramenta 'verificar_prazos_processuais'. 
       - Se o usuário informar a quantidade de dias (ex: 7 dias, 15 dias, 30 dias), extraia esse número e passe-o como parâmetro 'dias'.
       - Se o usuário NÃO especificar os dias, acione a ferramenta usando o valor padrão de 10 dias.
       
        4. PROIBIÇÃO DE ESCOPO: Se o assunto não tiver relação com processos, prazos, finanças, documentos ou vir vazio(sem nenhuma palavra), responda APENAS: 'SISTEMA_VALIDACAO: Sou um agente restrito ao contexto do escritório. Não posso responder a perguntas fora deste escopo.'
        
        5. AÇÕES INEXISTENTES: Se pedirem para redigir petição, enviar e-mail ou agendar algo, responda APENAS: 'SISTEMA_VALIDACAO: Não possuo uma ferramenta integrada para realizar esta ação. Minhas funções são exclusivas para busca de dados.'
        
        6. HONORÁRIOS: Para saber de dívidas ou inadimplência, acione 'checar_inadimplencia_honorarios'. Se for de um cliente específico, use o parâmetro 'nome_cliente'.
        
        7. DOCUMENTOS E CONTRATOS: Se perguntarem sobre valores, cláusulas, parcelas, bancos ou detalhes de um CONTRATO específico de um cliente, DEVE acionar a ferramenta 'buscar_jurisprudencia_documentos'.
        """)

        
    mensagem_usuario = HumanMessage(content=entrada_texto)
    try:
        print(f"[NÓ DE BUSCA] Analisando a entrada: '{entrada_texto}'...")
        
        resposta_ia = llm_com_ferramentas.invoke([prompt_sistema, mensagem_usuario])
        
        
        # CENÁRIO A: A IA decidiu chamar uma ferramenta
        # CENÁRIO A: A IA decidiu chamar uma ou mais ferramentas
        if resposta_ia.tool_calls:
            resultados_multiplos = []
            ferramentas_usadas = []
            
            # LOOP: Agora o sistema executa todas as ferramentas solicitadas, e não apenas a primeira [0]
            for chamada in resposta_ia.tool_calls:
                nome_ferramenta = chamada["name"]
                argumentos = chamada["args"]
                
                print(f"[NÓ DE BUSCA] Ferramenta escolhida: {nome_ferramenta}")
                
                # Executa a ferramenta
                ferramenta_real = mapa_ferramentas[nome_ferramenta]
                resultado_api = ferramenta_real.invoke(argumentos)
                
                # Guarda o resultado de cada ferramenta numa lista
                resultados_multiplos.append({
                    "origem_ferramenta": nome_ferramenta,
                    "dados": resultado_api
                })
                ferramentas_usadas.append(nome_ferramenta)
            
            # Formata o SUCESSO com todos os dados empacotados num único JSON
            resposta_padronizada = {
                "status": "sucesso",
                "ferramenta_utilizada": ", ".join(ferramentas_usadas),
                "dados_recuperados": resultados_multiplos
            }
            return json.dumps(resposta_padronizada, ensure_ascii=False, indent=2)
            
        # CENÁRIO B: A IA foi bloqueada pela nossa regra de segurança
        else:
            print("[NÓ DE BUSCA] Regra de Validação ativada.")
            # Garante que, se a IA devolver um texto vazio, nós injetamos um aviso padrão
            texto_alerta = resposta_ia.content.strip()
            if not texto_alerta:
                texto_alerta = "SISTEMA_VALIDACAO: Não consegui processar a solicitação. Por favor, seja mais específico."
                
            resposta_padronizada = {
                "status": "bloqueio_seguranca",
                "mensagem_orientacao": texto_alerta
            }
            return json.dumps(resposta_padronizada, ensure_ascii=False, indent=2)

    except Exception as e:
        erro_msg = f"Erro interno no Nó de Busca: {e}"
        print(f"[NÓ DE BUSCA] {erro_msg}")
        resposta_padronizada = {
            "status": "erro_critico",
            "mensagem_orientacao": erro_msg
        }
        return json.dumps(resposta_padronizada, ensure_ascii=False, indent=2)
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
