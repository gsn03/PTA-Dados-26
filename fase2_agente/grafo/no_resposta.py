import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Configuração de caminhos (mesmo padrão dos seus nós anteriores)
pasta_raiz = Path(__file__).resolve().parent.parent.parent
load_dotenv(pasta_raiz / ".env", override=True)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Inicializa o LLM para geração da resposta (pode ter uma temperature um pouquinho maior para texto natural, mas mantemos baixa para evitar alucinação)
llm_geracao = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1, api_key=os.getenv("GOOGLE_API_KEY"))

# O Prompt rigoroso de Geração
prompt_resposta = ChatPromptTemplate.from_messages([
    ("system", """Você é o Redator Jurídico Final do escritório.
    Sua única missão é ler os DADOS BRUTOS fornecidos pelo sistema e redigir uma resposta elegante, clara e direta para a pergunta do usuário.

    REGRAS CRÍTICAS:
    1. Baseie-se APENAS nos dados fornecidos no contexto. NUNCA invente prazos, valores, nomes ou status.
    2. Se os dados retornados estiverem vazios (ex: listas vazias, 'não encontrado'), responda claramente: "A informação solicitada não foi localizada nos registros do escritório."
    3. Seja direto. Não precisa explicar como você buscou, apenas entregue a resposta.
    
    DADOS BRUTOS DO SISTEMA (Contexto):
    {dados_contexto}
    """),
    ("human", "PERGUNTA DO USUÁRIO: '{pergunta_usuario}'")
])

motor_geracao = prompt_resposta | llm_geracao | StrOutputParser()

def executar_no_de_resposta(pergunta_usuario: str, json_busca_str: str) -> str:
    """
    Recebe a pergunta (reformulada) e o JSON vindo do Nó de Busca.
    Gera a resposta final em linguagem natural ou repassa os alertas de segurança.
    """
    print("\n--- INICIANDO NÓ DE RESPOSTA ---")
    
    try:
        # 1. Lê o JSON que veio do nó de busca
        resultado_busca = json.loads(json_busca_str)
        status = resultado_busca.get("status")
        
        # 2. Tratamento de Erros e Bloqueios 
        if status == "bloqueio_seguranca" or status == "erro_critico":
            mensagem = resultado_busca.get("mensagem_orientacao", "Erro desconhecido.")
            print("[NÓ DE RESPOSTA] Repassando alerta do roteador/sistema.")
            return f"⚠️ {mensagem}"
            
        # 3. Tratamento de Sucesso (Geração com LLM)
        elif status == "sucesso":
            dados_brutos = resultado_busca.get("dados_recuperados")
            ferramenta = resultado_busca.get("ferramenta_utilizada", "Banco de Dados")
            
            print("[NÓ DE RESPOSTA] Gerando texto com base nos dados recuperados...")
            
            # Formata os dados para o prompt
            dados_para_prompt = json.dumps(dados_brutos, ensure_ascii=False, indent=2)
            
            # Chama a LLM para redigir a resposta
            texto_gerado = motor_geracao.invoke({
                "dados_contexto": dados_para_prompt,
                "pergunta_usuario": pergunta_usuario
            })
            
            # 4. Adiciona a Rastreabilidade (Obrigatório no RAG Jurídico)
            resposta_final = f"{texto_gerado}\n\n---\n*🔍 Fonte: Consultada via ferramenta `{ferramenta}`*"
            return resposta_final
            
        else:
            return "⚠️ Erro: Status desconhecido retornado pelo nó de busca."
            
    except json.JSONDecodeError:
        return "⚠️ Erro fatal: O nó de busca não retornou um JSON válido."
    except Exception as e:
        return f"⚠️ Erro interno no nó de geração de resposta: {e}"


# ÁREA DE TESTES LOCAIS (Simulando os outputs do seu Nó de Busca)
if __name__ == "__main__":
    
    # Simulação 1: O nó de busca bloqueou a requisição (faltou nome do cliente)
    json_bloqueio = json.dumps({
        "status": "bloqueio_seguranca",
        "mensagem_orientacao": "SISTEMA_VALIDACAO: Para consultar este processo, por favor, informe também o nome do cliente associado."
    })
    
    print("\n--- TESTE 1: Tratando Bloqueio de Segurança ---")
    resp_1 = executar_no_de_resposta("Qual o status do processo 12345?", json_bloqueio)
    print(f"RESPOSTA FINAL:\n{resp_1}")


    # Simulação 2: O nó de busca encontrou os dados com sucesso
    json_sucesso = json.dumps({
        "status": "sucesso",
        "ferramenta_utilizada": "buscar_historico_processo",
        "dados_recuperados": [
            {"data": "2024-05-10", "evento": "Petição inicial protocolada", "status": "Ativo"},
            {"data": "2024-05-20", "evento": "Citação expedida", "status": "Aguardando prazo"}
        ]
    })
    
    print("\n--- TESTE 2: Tratando Sucesso (RAG) ---")
    resp_2 = executar_no_de_resposta("Qual o status do processo do Leandro Pinto?", json_sucesso)
    print(f"RESPOSTA FINAL:\n{resp_2}")