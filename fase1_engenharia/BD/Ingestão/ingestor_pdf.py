import sys
from pathlib import Path
from sqlalchemy import text
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Ajuste de caminhos no topo
pasta_ingestao = Path(__file__).resolve().parent
pasta_bd = pasta_ingestao.parent # Aponta para fase1_engenharia/BD
pasta_raiz = pasta_bd.parent.parent # Aponta para a raiz do projeto

sys.path.append(str(pasta_bd))

# Agora consegue achar os arquivos da Fase 1 perfeitamente
from database_model import SessionLocal, engine, Base
from banco_vetorial import DocumentoVetorial, embeddings_model

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
        if not pasta_pdfs.exists():
            print(f"ERRO: A pasta {pasta_pdfs} não foi encontrada.")
            return

        for arquivo_pdf in pasta_pdfs.rglob("*.pdf"):
            print(f"Processando: {arquivo_pdf.name}")
            
            loader = PyPDFLoader(str(arquivo_pdf))
            paginas = loader.load()
            
            chunks = text_splitter.split_documents(paginas)
            
            for chunk in chunks:
                texto = chunk.page_content
                vetor = embeddings_model.embed_query(texto)
                
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