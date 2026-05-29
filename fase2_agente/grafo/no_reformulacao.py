import os
import sys
from pathlib import Path
from dotenv import load_dotenv

pasta_raiz = Path(__file__).resolve().parent.parent.parent
load_dotenv(pasta_raiz / ".env", override=True)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

ia_reformulacao = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1, api_key=os.getenv("GOOGLE_API_KEY"))

prompt_reformulacao = ChatPromptTemplate.from_messages([ 
    ("system", """Você é um assistente jurídico de elite.
    Sua tarefa é reformular a pergunta original do cliente para torná-la clara e concisa, otimizando-a para o sistema de busca do escritório.
 
    DIRETRIZES DE REFORMULAÇÃO:
    
    RESPEITE A INTENÇÃO: O nosso sistema faz buscas em BANCOS DE DADOS EXATOS (prazos, honorários, andamentos) e em PDFs. Não transforme perguntas sobre prazos ou processos em buscas por cláusulas contratuais.
 
    NÃO INVENTE: Mantenha nomes de clientes, números de processos e quantidades de dias EXATAMENTE como foram digitados.
    Clarifique ambiguidades: Se o cliente usar termos imprecisos, melhore o vocabulário, mas sem mudar o sujeito da frase.
    Simplifique: Quebre perguntas muito longas em uma instrução direta.

     Responda APENAS com a pergunta reformulada.
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