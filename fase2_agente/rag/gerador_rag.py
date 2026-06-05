import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ── 1. CONFIGURAÇÃO DE CAMINHOS ───────────────────────────────────────────────
pasta_raiz = Path(__file__).resolve().parent.parent.parent
load_dotenv(pasta_raiz / ".env", override=True)

# Adiciona a pasta BD ao sistema para importar os modelos do banco
pasta_bd = pasta_raiz / "fase1_engenharia" / "BD"
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from banco_vetorial import DocumentoVetorial, embeddings_model

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ── 2. FUNÇÃO DE EXTRAÇÃO E INGESTÃO (O TRATOR) ─────────────────────────────
def ingerir_pdfs_no_banco():
    # Caminho onde os seus PDFs estão salvos
    pasta_pdfs = pasta_raiz / "data" / "pdfs_brutos"
    
    print(f"\n📁 Procurando PDFs na pasta: {pasta_pdfs}")
    
    if not pasta_pdfs.exists():
        print("❌ A pasta de PDFs não existe! Verifique o caminho.")
        return

    # A. Carregar PDFs
    loader = PyPDFDirectoryLoader(str(pasta_pdfs))
    documentos = loader.load()
    
    if not documentos:
        print("⚠️ Nenhum PDF encontrado. Coloque seus arquivos na pasta 'pdfs_brutos'.")
        return
        
    print(f"📄 Encontradas {len(documentos)} páginas de PDF. Iniciando fatiamento...")

    # B. Fatiar o texto (O LLM não consegue ler o PDF todo de uma vez)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,   # Pega blocos de 1000 letras
        chunk_overlap=200  # Repete 200 letras para não cortar uma frase no meio
    )
    pedacos = text_splitter.split_documents(documentos)
    print(f"🔪 Textos fatiados em {len(pedacos)} pedaços. Convertendo para vetores (isso pode levar um minuto)...")

    # C. Salvar no Banco PostgreSQL
    db = SessionLocal()
    try:
        for i, pedaco in enumerate(pedacos):
            # Extrai o nome do arquivo 
            nome_arquivo = Path(pedaco.metadata.get("source", "desconhecido.pdf")).name
            texto_puro = pedaco.page_content
            
            print(f"⏳ Inserindo {i+1}/{len(pedacos)} no banco: {nome_arquivo}...")
            
            # Converte as palavras em números (Embeddings do Google)
            vetor = embeddings_model.embed_query(texto_puro)
            
            # Prepara a linha da tabela
            novo_doc = DocumentoVetorial(
                nome_arquivo=nome_arquivo,
                conteudo=texto_puro,
                embedding=vetor
            )
            # Salva na memória
            db.add(novo_doc)
        
        # Consolida tudo no banco de dados de uma vez
        db.commit()
        print("\n✅ SUCESSO ABSOLUTO! Todos os PDFs foram injetados no PostgreSQL!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Ocorreu um erro crítico ao salvar no banco: {e}")
    finally:
        db.close()

# ── 3. GATILHO DE EXECUÇÃO ──────────────────────────────────────────────────
# É isso aqui que faz o Python rodar o código quando você der "Enter" no terminal
if __name__ == "__main__":
    ingerir_pdfs_no_banco()