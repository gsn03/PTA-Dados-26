import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Caminho absoluto para a raiz do projeto
pasta_raiz = Path(__file__).resolve().parent.parent.parent
load_dotenv(pasta_raiz / ".env", override=True)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

ia_escolhida = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1, api_key=os.getenv("GOOGLE_API_KEY"))

prompt_rag = ChatPromptTemplate.from_messages([ 
    ("system", """Você é um assistente jurídico de elite.
    Responda à pergunta do usuário baseando-se ÚNICA E EXCLUSIVAMENTE no contexto fornecido abaixo.
    Se a resposta não estiver no contexto, diga: 'Não possuo essa informação na base de dados.'
    Sempre cite o nome do [Arquivo] de onde você tirou a informação.
    
    CONTEXTO RECUPERADO:
    {contexto}
    """),
    ("human", "{pergunta}")
])

motor_geracao = prompt_rag | ia_escolhida 

def gerar_resposta(pergunta: str, contexto: str) -> str:
    resposta = motor_geracao.invoke({
        "contexto": contexto,
        "pergunta": pergunta
    })
    return resposta.content