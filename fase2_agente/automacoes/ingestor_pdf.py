from sqlalchemy import text
import sys
from pathlib import Path
#Usando o LangChain
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

pasta_raiz = Path(__file__).parent.parent.parent
sys.path.append(str(pasta_raiz / "fase1_engenharia"))
sys.path.append(str(pasta_raiz / "fase2_agente"))

from BD.database_model import SessionLocal, engine
from rag.banco_vetorial import DocumentoVetorial, embeddings_model, Base

def ingerir_pdfs_para_vetores():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.execute(text("DROP TABLE IF EXISTS documentos_vetoriais CASCADE;"))
    Base.metadata.create_all(bind=engine)
    
    pasta_pdfs = pasta_raiz / "data" / "pdfs_brutos"
    db = SessionLocal()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=150
    )
    
    try:
        for arquivo_pdf in pasta_pdfs.rglob("*.pdf"):
            print(f"Processando: {arquivo_pdf.name}")
            
            loader = PyPDFLoader(str(arquivo_pdf))
            paginas = loader.load()
            
            chunks = text_splitter.split_documents(paginas)
            
            for chunk in chunks:
                texto = chunk.page_content
                # Gera o vetor matemático
                vetor = embeddings_model.embed_query(texto)
                
                # Salva no banco PostgreSQL
                novo_doc = DocumentoVetorial(
                    nome_arquivo=arquivo_pdf.name,
                    conteudo=texto,
                    embedding=vetor
                )
                db.add(novo_doc)
                
        db.commit()
        print("\n✅ Ingestão vetorial concluída com sucesso!")
        
    except Exception as e:
        db.rollback()
        print(f"Erro na ingestão: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    ingerir_pdfs_para_vetores()