import pdfplumber
import pandas as pd
import re
import json
from pathlib import Path

def extrair_contrato_honorarios(texto_bruto, nome_arquivo):
    texto_upper = texto_bruto.upper()
    
    # tipo de Processo
    if any(x in texto_upper for x in ["TRABALHISTA", "TRABALHO", "RESCISÃO", "TRT"]):
        tipo_processo = "Trabalhista"
    elif any(x in texto_upper for x in ["EMPRESARIAL", "SOCIEDADE", "FALÊNCIA", "RECUPERAÇÃO JUDICIAL"]):
        tipo_processo = "Empresarial"
    else:
        tipo_processo = "Cível"

    # extração de OAB
    # Busca padrões como OAB/PE 12.345 ou OAB/SP nº 123456
    match_oab = re.search(r"OAB/([A-Z]{2})\s*(?:Nº\s*|SOB O Nº\s*)?([\d\.]+)", texto_bruto, re.IGNORECASE)
    oab_encontrada = f"{match_oab.group(1)} {match_oab.group(2)}" if match_oab else "Não encontrada"

    endereco = "Não encontrado"
    
    # Busca por palavras-chave de endereço
    match_end = re.search(r"(?:residente|situado|domiciliado)\s+(?:na|no)\s+([^.\n]+)", texto_bruto, re.IGNORECASE)
    
    if match_end:
        endereco = match_end.group(1).strip()
        # Remove resíduos comuns se o regex pegar demais (como "inscrito no CPF")
        endereco = re.split(r",\s*inscrito|,\s*CPF|,\s*portador", endereco, flags=re.IGNORECASE)[0]
    else:
        # Busca secundária: o que vem após o CPF/CNPJ até o final da linha ou ponto
        match_fallback = re.search(r"(?:CPF|CNPJ)\s*[\d\.\-/]+,\s*([^.\n]+)", texto_bruto, re.IGNORECASE)
        if match_fallback:
            endereco = match_fallback.group(1).strip()

    # 4. Contratante e CPF/CNPJ
    match_partes = re.search(r"(?:Contratante|CLIENTE):\s*([^,]+),\s*(?:CPF|CNPJ)\s*([\d\.\-/]+)", texto_bruto, re.IGNORECASE)
    
    # 5. Valor do Contrato
    match_valor = re.search(r"(?:total de|Valor fixo:)\s*(R\$\s*[\d\.,]+)", texto_bruto, re.IGNORECASE)
    
    # 6. Honorários de êxito
    match_exito = re.search(r"(\d+%\s*(?:\(.+?\))?\s*sobre)", texto_bruto, re.IGNORECASE)

    return {
        "arquivo_origem": nome_arquivo,
        "tipo_documento": "contrato_honorarios",
        "tipo_processo": tipo_processo,
        "contratante": match_partes.group(1).strip() if match_partes else "Não encontrado",
        "cpf_cnpj_contratante": match_partes.group(2).strip() if match_partes else None,
        "oab_advogado": oab_encontrada,
        "endereco_encontrado": endereco,
        "valor_total": match_valor.group(1).strip() if match_valor else None,
        "honorarios_exito": match_exito.group(1).strip() if match_exito else None
    }

def processar_pdfs():
    # --- MAPEAMENTO DE CAMINHOS BASEADO NA SUA IMAGEM ---
    # Define a raiz do projeto (PTA-Dados-26) baseada na localização deste script
    raiz_projeto = Path(__file__).resolve().parent.parent.parent
    
    pasta_pdfs = raiz_projeto / "data" / "pdfs_brutos" / "contrato"
    pasta_saida_tabelas = raiz_projeto / "data" / "Texto_json" / "honorarios"

    arquivos_pdf = list(pasta_pdfs.glob("*.pdf"))
    
    if not arquivos_pdf:
        print(f"Atenção: Nenhum PDF encontrado em {pasta_pdfs}")
        return

    resultados = []

    for arquivo in arquivos_pdf:
        print(f"Processando: {arquivo.name}")
        
        with pdfplumber.open(arquivo) as pdf:
            texto_completo = ""
            for i, pagina in enumerate(pdf.pages):
                texto_completo += (pagina.extract_text() or "") + "\n"
                
                # Extração de tabelas para a pasta correta
                tabela = pagina.extract_table()
                if tabela:
                    df_tab = pd.DataFrame(tabela[1:], columns=tabela[0])
                    caminho_csv = pasta_saida_tabelas / f"tabela_{arquivo.stem}_pag_{i+1}.csv"
                    df_tab.to_csv(caminho_csv, index=False, encoding='utf-8-sig')

            # Extração de dados via Regex
            if "CONTRATO" in texto_completo.upper():
                dados = extrair_contrato_honorarios(texto_completo, arquivo.name)
            else:
                dados = {"arquivo_origem": arquivo.name, "tipo_documento": "Não identificado"}
            
            # Salvando JSON Individual na pasta Texto_json
            caminho_json = pasta_saida_tabelas / f"extracao_{arquivo.stem}.json"
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)
            
            resultados.append(dados)

    # Relatório Geral consolidado
    caminho_relatorio = pasta_saida_tabelas / "Relatorio_Geral_Contratos.json"
    with open(caminho_relatorio, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=4)
    
    print(f"\n[SUCESSO] Processamento concluído!")
    print(f"Tabelas salvas em: {pasta_saida_tabelas}")

processar_pdfs()