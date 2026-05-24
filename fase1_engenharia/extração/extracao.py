import pdfplumber as plu
from regras_extracao import extrair_intimacao, extrair_citacao, extrair_peticao
import json
from pathlib import Path
from typing import Callable #callable ele mostra que não é um string ou um inteiro,
#faz com que a função entenda qeue o parâmetro é uma função

def extrair_texto(caminho_pdf : Path) ->str:
    texto_extraido= ""
    
    with plu.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                texto_extraido += texto + "\n"
    return texto_extraido



def processar_lote_pdfs(diretorio_pdfs: Path, diretorio_saida_json: Path, funcao_extracao: Callable):
    
    diretorio_saida_json.mkdir(parents=True, exist_ok=True)
    
    for arquivo_pdf in diretorio_pdfs.glob("*.pdf"):
        
        texto = extrair_texto(arquivo_pdf)
        if texto:
            dados = funcao_extracao(texto, arquivo_pdf.name)
            
            #Pega o nome do PDF sem a extensão (ex: 'acordo_trabalhista' em vez de 'acordo_trabalhista.pdf')
            nome_base = arquivo_pdf.stem 
            caminho_arquivo_json = diretorio_saida_json / f"{nome_base}.json"
        
            with open(caminho_arquivo_json, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)


if __name__ == "__main__": 
    pasta_base = Path(__file__).parent.parent.parent
    
    #intimações
    pasta_pdfs_intimacoes = pasta_base / "data" / "pdfs_brutos" / "intimacao" 
    pasta_saida_jsons = pasta_base / "data" / "Texto_json" / "intimacao"
    processar_lote_pdfs(pasta_pdfs_intimacoes, pasta_saida_jsons, extrair_intimacao)
    
    #Citações
    pasta_pdfs_citacoes = pasta_base / "data" / "pdfs_brutos" / "citacao"
    pasta_saida_citacoes = pasta_base / "data" / "Texto_json" / "citacao"    
    processar_lote_pdfs(pasta_pdfs_citacoes, pasta_saida_citacoes, extrair_citacao)

    #Petições
    pasta_pdfs_peticoes = pasta_base / "data" / "pdfs_brutos" / "peticao" 
    pasta_saida_peticoes = pasta_base / "data" / "Texto_json" / "peticao"
    processar_lote_pdfs(pasta_pdfs_peticoes, pasta_saida_peticoes, extrair_peticao)