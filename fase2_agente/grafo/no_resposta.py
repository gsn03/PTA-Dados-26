import os
import sys
import json
from datetime import date
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
    Sua missão é responder à PERGUNTA DO USUÁRIO de forma exata e direta, baseando-se EXCLUSIVAMENTE nos DADOS BRUTOS.
    
    INFORMAÇÃO DE CONTEXTO TEMPORAL:
    - Hoje é {data_atual}.

    MANUAL DE FORMATAÇÃO OBRIGATÓRIO (Siga estritamente com base na ferramenta utilizada):

    1. Se os dados vierem de 'buscar_jurisprudencia_documentos' (Busca Semântica em PDFs):
       - FOCO ABSOLUTO NA PERGUNTA: Leia a pergunta do usuário e extraia APENAS a resposta exata.
       - PROIBIÇÃO DE RESUMO: Não crie resumos genéricos do documento, não cite o objeto do contrato ou outras cláusulas se não forem expressamente solicitadas. Se o usuário pedir um valor, responda APENAS o valor.
       - IGNORE O RUÍDO: Ignore completamente os dados de terceiros que vierem misturados no contexto.
       - CITAÇÃO OBRIGATÓRIA (CRÍTICO): Independentemente do tamanho da sua resposta, você É OBRIGADO a incluir no final da frase a citação no padrão exato: [Doc: Nome_do_Arquivo.pdf]. Se você responder "R$ 2.750,00", você DEVE escrever: "O valor é R$ 2.750,00. [Doc: contrato_honorarios_ana_lima.pdf]".

    2. Se os dados vierem de 'verificar_prazos_processuais':
       - CONFIANÇA CEGA NA API: A ferramenta já filtrou as datas e fez a matemática corretamente em relação ao dia de hoje. NUNCA diga que faltam dados para calcular ou que não conseguiu identificar. APENAS LISTE os prazos recuperados.
       - Organize a lista de prazos em ordem CRONOLÓGICA CRESCENTE.
       - Apresente o resultado em tópicos limpos.

    3. Se os dados vierem de 'buscar_historico_processo':
       - Divida a resposta em dois blocos: '📌 STATUS ATUAL' e '⏳ HISTÓRICO DE ANDAMENTOS'.

    4. Se os dados vierem de 'checar_inadimplencia_honorarios':
       - Liste os devedores em tópicos informando: nome, valor, vencimento e status.

    REGRAS GERAIS DE CONGRUÊNCIA:
    - Baseie-se APENAS nos dados fornecidos no contexto. NUNCA invente prazos, valores ou nomes.
    - Seja direto, objetivo e profissional. Não explique o funcionamento técnico do sistema.
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
            return f"{mensagem}"
            
        elif status == "sucesso":
            dados_brutos = resultado_busca.get("dados_recuperados")
            ferramenta = resultado_busca.get("ferramenta_utilizada", "Banco de Dados")
            
            print(f"[NÓ DE RESPOSTA] Formatando saída baseada na ferramenta: {ferramenta}...")
            
            if isinstance(dados_brutos, str):
                dados_para_prompt = dados_brutos
            else:
                dados_para_prompt = json.dumps(dados_brutos, ensure_ascii=False, indent=2)
            
            texto_gerado = motor_geracao.invoke({
                "data_atual": str(date.today()), # Injetando a data atual dinamicamente
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

if __name__ == "__main__":
    pass