import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Configuração de caminhos estável
pasta_raiz = Path(__file__).resolve().parent.parent.parent
load_dotenv(pasta_raiz / ".env", override=True)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm_geracao = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1, api_key=os.getenv("GOOGLE_API_KEY"))

prompt_resposta = ChatPromptTemplate.from_messages([
    ("system", """Você é o Redator Jurídico Final do escritório.
    Sua única missão é ler os DADOS BRUTOS fornecidos pelo sistema e redigir uma resposta elegante, clara e direta para a pergunta do usuário.

    MANUAL DE FORMATAÇÃO OBRIGATÓRIO (Siga estritamente com base na ferramenta utilizada):

    1. Se os dados vierem de 'buscar_jurisprudencia_documentos' (Busca Semântica em PDFs):
       - Analise todos os trechos recebidos, filtre e descarte os que não respondem diretamente à pergunta.
       - Crie um resumo estruturado em tópicos (bullet points) destacando apenas as informações cruciais (Valores, Partes envolvidas, Objeto do documento).
       - OBRIGATÓRIO: No final do texto ou parágrafo, cite a fonte utilizando rigorosamente o padrão '[Doc: Nome_do_Arquivo.pdf]'. Nunca use outro formato, pois o validador exige exatamente esse padrão com colchetes.

    2. Se os dados vierem de 'verificar_prazos_processuais':
       - Pegue a lista de prazos recebida e organize-a em ordem CRONOLÓGICA CRESCENTE (do prazo mais urgente/próximo para o mais distante).
       - Apresente o resultado em tópicos limpos.

    3. Se os dados vierem de 'buscar_historico_processo':
       - Divida a resposta em dois blocos visuais bem definidos: 
         * '📌 STATUS ATUAL' (Com as principais informações da fase e status atual)
         * '⏳ HISTÓRICO DE ANDAMENTOS' (Um resumo cronológico simplificado dos andamentos passados).

    4. Se os dados vierem de 'checar_inadimplencia_honorarios':
       - Liste os devedores em tópicos (bullet points) bem definidos.
       - Para cada registro, informe explicitamente: o nome do cliente, o valor da dívida atual, a data de vencimento e, se disponível nos dados brutos, detalhe quantas parcelas já foram pagas pelo cliente.

    REGRAS GERAIS DE CONGRUÊNCIA:
    - Baseie-se APENAS nos dados fornecidos no contexto. NUNCA invente prazos, valores, nomes ou status.
    - 3. RESPEITO AOS DADOS: Se a ferramenta informar que 'Nenhum prazo foi encontrado' ou 'Não há dívidas', repasse essa exata informação ao usuário de forma natural. Não altere os resultados negativos originais. Não tente reordenar listas numéricas, apenas exiba os dados na ordem exata em que foram recebidos no contexto.
    - Seja direto. Não explique o funcionamento técnico do sistema para o cliente.
    """),
    ("human", "PERGUNTA DO USUÁRIO: '{pergunta_usuario}'\n\nDADOS BRUTOS DO SISTEMA:\n{dados_contexto}")
])

motor_geracao = prompt_resposta | llm_geracao | StrOutputParser()

def executar_no_de_resposta(pergunta_usuario: str, json_busca_str: str) -> str:
    """
    Recebe a pergunta e o JSON vindo do Nó de Busca.
    Gera a resposta final em linguagem natural ou repassa os alertas de segurança.
    """
    print("\n--- INICIANDO NÓ DE RESPOSTA ---")
    
    try:
        resultado_busca = json.loads(json_busca_str)
        status = resultado_busca.get("status")
        
        # Se houver bloqueio do roteador jurídico, repassamos o alerta de forma limpa
        if status == "bloqueio_seguranca" or status == "erro_critico":
            mensagem = resultado_busca.get("mensagem_orientacao", "Erro desconhecido.")
            print("[NÓ DE RESPOSTA] Repassando alerta de validação do roteador.")
            return f"SISTEMA_VALIDACAO: {mensagem}"
            
        elif status == "sucesso":
            dados_brutos = resultado_busca.get("dados_recuperados")
            ferramenta = resultado_busca.get("ferramenta_utilizada", "Banco de Dados")
            
            print(f"[NÓ DE RESPOSTA] Formatando saída baseada na ferramenta: {ferramenta}...")
            
            if isinstance(dados_brutos, str):
                dados_para_prompt = dados_brutos
            else:
                dados_para_prompt = json.dumps(dados_brutos, ensure_ascii=False, indent=2)
            
            texto_gerado = motor_geracao.invoke({
                "dados_contexto": f"Ferramenta: {ferramenta}\nContexto:\n{dados_para_prompt}",
                "pergunta_usuario": pergunta_usuario
            })
            
            return texto_gerado
            
        else:
            return "SISTEMA_VALIDACAO: Erro. Status desconhecido retornado pelo nó de busca."
            
    except json.JSONDecodeError:
        return "SISTEMA_VALIDACAO: Erro fatal. O nó de busca não retornou um JSON válido."
    except Exception as e:
        return f"SISTEMA_VALIDACAO: Erro interno no nó de resposta: {e}"