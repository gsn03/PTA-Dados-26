import sys
from pathlib import Path
from sqlalchemy import Column, Integer, String, Text, select
from pgvector.sqlalchemy import Vector
from langchain_google_genai import GoogleGenerativeAIEmbeddings
#Conecta com o banco de dados
pasta_raiz = Path(__file__).parent.parent.parent
sys.path.append(str(pasta_raiz / "fase1_engenharia"))
from BD.database_model import Base, SessionLocal

class DocumentoVetorial(Base):
    __tablename__ = "documentos_vetoriais"

    id = Column(Integer, primary_key=True, index=True)
    nome_arquivo = Column(String, index=True)
    conteudo = Column(Text, nullable=False)
    embedding = Column(Vector(3072))

#Ver com a equipe --> configuração dos embeddings
embeddings_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

#Função de busca vetorial
def buscar_contexto_semantico(pergunta: str, limite: int = 1) -> str:
    print(f"Buscando PDFs para a pergunta: '{pergunta}'...")
    #Transforma em vetor
    vetor_pergunta = embeddings_model.embed_query(pergunta)  
    db = SessionLocal()
    try:
        resultados = db.scalars(
            select(DocumentoVetorial)
            .order_by(DocumentoVetorial.embedding.cosine_distance(vetor_pergunta))
            .limit(limite)
        ).all()
        #Formata o texto
        textos = []
        for doc in resultados:
            textos.append(f"[Arquivo: {doc.nome_arquivo}]\n{doc.conteudo}")
            
        return "\n\n".join(textos)
    finally:
        db.close()