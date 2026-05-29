import sys
from pathlib import Path
from sqlalchemy import Column, Integer, String, Text, select
from pgvector.sqlalchemy import Vector
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Ajuste de caminho para a mesma pasta (BD)
pasta_bd = Path(__file__).resolve().parent
sys.path.append(str(pasta_bd))

from database_model import Base, SessionLocal

class DocumentoVetorial(Base):
    __tablename__ = "documentos_vetoriais"
    
    # SOLUÇÃO DO CONFLITO: Permite recriação ou extensão sem erro
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    nome_arquivo = Column(String, index=True)
    conteudo = Column(Text, nullable=False)
    embedding = Column(Vector(3072))

# Configuração dos embeddings
embeddings_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

def buscar_contexto_semantico(pergunta: str, limite: int = 5) -> str:
    print(f"Buscando PDFs para a pergunta: '{pergunta}'...")
    vetor_pergunta = embeddings_model.embed_query(pergunta)  
    db = SessionLocal()
    try:
        resultados = db.scalars(
            select(DocumentoVetorial)
            .order_by(DocumentoVetorial.embedding.cosine_distance(vetor_pergunta))
            .limit(limite)
        ).all()
        
        textos = []
        for doc in resultados:
            textos.append(f"[Arquivo: {doc.nome_arquivo}]\n{doc.conteudo}")
            
        return "\n\n".join(textos)
    finally:
        db.close()