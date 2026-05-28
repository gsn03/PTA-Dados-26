import os
import sys
from pathlib import Path
from dotenv import load_dotenv

pasta_raiz = Path(__file__).resolve().parent.parent.parent
load_dotenv(pasta_raiz / ".env", override=True)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

ia_reformulacao = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1, api_key=os.getenv("GEMINI_API_KEY"))

prompt_reformulacao = ChatPromptTemplate.from_messages([ 
    ("system", """Você é um assistente jurídico de elite.
    Sua tarefa é reformular a pergunta original do cliente para torná-la clara, concisa e, acima de tudo, otimizada para busca semântica em uma base de documentos jurídicos (PDFs de contratos, leis e pareceres).
 
    DIRETRIZES DE REFORMULAÇÃO:
    1. **Mantenha o significado original:** Não invente novas perguntas. Apenas reescreva.
    2. **Clarifique ambiguidades:** Se o cliente usar termos como "negócio", tente interpretar pelo contexto se ele se refere a um "contrato", "cláusula" ou "processo".
    3. **Melhore o vocabulário:** Use termos jurídicos adequados quando apropriado, sem exagerar. Substitua gírias ou termos imprecisos.
    4. **Simplifique:** Se a pergunta for muito longa ou confusa, quebre-a em uma pergunta direta.
    5. **Otimize para Busca:** Pense em como o conceito estaria escrito dentro de um contrato PDF.
 
    **Responda APENAS com a pergunta reformulada.**
    """),
    ("human", "PERGUNTA ORIGINAL DO CLIENTE: '{pergunta_original}'")
])

motor_reformulacao = prompt_reformulacao | ia_reformulacao

def reformular_pergunta(pergunta_original: str) -> str:
    print(f"\n--- REFORMULANDO PERGUNTA ---")
    print(f"Original: '{pergunta_original}'")
    #Chama a LLM
    resposta = motor_reformulacao.invoke({
    "pergunta_original": pergunta_original
    })

    pergunta_reformulada = resposta.content.strip()
 
    print(f"Reformulada: '{pergunta_reformulada}'")
    print("-----------------------------")
    return pergunta_reformulada

if __name__ == "__main__":
    #Teste 
    pergunta_teste = "Onde que eu vejo negócio de quanto eu tenho que pagar de honorários baseado nos PDFs?"
    pergunta_reformulada = reformular_pergunta(pergunta_teste)