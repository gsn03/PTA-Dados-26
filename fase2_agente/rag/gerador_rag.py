from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

ia_escolhida = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)

prompt_rag = ChatPromptTemplate.from_messages([ #Ajustar com a equipe
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