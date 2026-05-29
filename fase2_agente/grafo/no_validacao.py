import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# 1. PADRONIZAÇÃO DE CAMINHOS
pasta_grafo = Path(__file__).resolve().parent 
pasta_fase2 = pasta_grafo.parent 
pasta_raiz = pasta_fase2.parent

# carrega a chave do google
load_dotenv(pasta_raiz / ".env", override=True)
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# 2. CONFIGURAÇÃO DA IA DE VALIDAÇÃO
# Usamos temperatura 0 pois um juiz precisa ser determinístico e não criativo

llm_validador = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# 3. SCHEMA DE DADOS
class ValidacaoPayload(TypedDict):
    contexto_recuperado: str 
    resposta_gerada: str 
    tentativas: int

def no_validacao(data: ValidacaoPayload) -> dict:
    prompt_validador = ChatPromptTemplate.from_messages([
    ("system", """Você é um Auditor Jurídico de alta precisão. Sua tarefa é validar se a RESPOSTA DA IA é fiel ao CONTEXTO.
    
    CRITÉRIOS DE REPROVAÇÃO:
    1. INCONGRUÊNCIA: A resposta diz que não achou algo que ESTÁ no contexto.
    2. ALUCINAÇÃO: A resposta inventou nomes, valores ou fatos que NÃO estão no contexto.
    3. FONTE VAZIA: O contexto está vazio e a IA afirmou fatos como se fossem verdadeiros.
    4. CITAÇÃO: A resposta não citou a fonte no padrão [Doc: Nome].

    REGRAS DE OURO:
     - Se o nome da pessoa for diferente: REPROVADO.
     - Se o número do processo ou vara for diferente: REPROVADO.
     - Se a IA inventar algo que não está no texto: REPROVADO.
     - A resposta deve ser APENAS o objeto JSON, sem textos adicionais.

    SAÍDA ESPERADA:
    Você deve responder EXATAMENTE no formato JSON abaixo:
    {{
        "status": "APROVADO" ou "REPROVADO",
        "motivo": "Explicação breve caso seja reprovado",
        "proximo_passo": "fim" ou "no_reformulacao"
    }}
    """),
    ("human", "CONTEXTO: {contexto}\n\nRESPOSTA DA IA: {resposta}")
    ])

    motor_validacao = prompt_validador | llm_validador

    # Bypass para erros de sistema
    if "SISTEMA_VALIDACAO:" in data["resposta_gerada"]:
        return {"status": "APROVADO", "motivo": "Erro de sistema já tratado.", "proximo_passo": "fim"}

    # Chamada da IA para julgar a congruência
    resposta_juiz = motor_validacao.invoke({
        "contexto": data["contexto_recuperado"],
        "resposta": data["resposta_gerada"]
    })

    # Aqui a IA nos devolve o JSON de decisão
    import json
    import re
    resposta_juiz.content = re.sub(r"```json|```", "", resposta_juiz.content).strip()
    try:
        decisao = json.loads(resposta_juiz.content)
        print(f"[NÓ VALIDAÇÃO IA] Status: {decisao['status']}")
        if decisao['status'] == "REPROVADO":
            print(f"[NÓ VALIDAÇÃO IA] Motivo: {decisao['motivo']}")
        return decisao
    except:
        # Fallback caso a IA não responda em JSON puro
        return {
            "status": "REPROVADO", 
            "motivo": "Erro técnico na formatação da crítica.", 
            "proximo_passo": "no_reformulacao"
        }

if __name__ == "__main__":
    # Teste de Alucinação
    payload_teste = {
        "contexto_recuperado": "O processo 123 de João Silva está na 5ª vara.",
        "resposta_gerada": "O processo de Maria Santos está na 10ª vara. [Doc: Inicial]",
        "tentativas": 1
    }
    print(resultado := no_validacao(payload_teste))