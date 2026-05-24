import pdfplumber
import pandas as pd
import re
import json
from pathlib import Path

def extrair_contrato_honorarios(texto_bruto, nome_arquivo):
    texto_upper = texto_bruto.upper()
    
    # 1. Identificação do Tipo de Processo
    if any(x in texto_upper for x in ["TRABALHISTA", "TRABALHO", "RESCISÃO", "TRT"]):
        tipo_processo = "Trabalhista"
    elif any(x in texto_upper for x in ["EMPRESARIAL", "SOCIEDADE", "FALÊNCIA", "RECUPERAÇÃO JUDICIAL"]):
        tipo_processo = "Empresarial"
    else:
        # Padrão para Cível (Indenização, Cobrança, etc)
        tipo_processo = "Cível"

    # 2. Extração de Endereço
    # Procura por "residente na", "situado na" ou endereço após o CPF/CNPJ
    match_end = re.search(r"(?:residente|situado|domiciliado)\s+(?:na|no)\s+([^,.\n]+(?:,\s*[^,.\n]+){1,3})", texto_bruto, re.IGNORECASE)
    if not match_end:
        # Tenta pegar o que vem logo após o CPF/CNPJ (comum no modelo da Maria Oliveira)
        match_end = re.search(r"(?:CPF|CNPJ)\s*[\d\.\-/]+,\s*([^.\n]+)", texto_bruto, re.IGNORECASE)
    
    endereco = match_end.group(1).strip() if match_end else "Não encontrado"

    # 3. Contratante e CPF/CNPJ
    match_partes = re.search(r"(?:Contratante|CLIENTE):\s*([^,]+),\s*(?:CPF|CNPJ)\s*([\d\.\-/]+)", texto_bruto, re.IGNORECASE)
    
    # 4. Valor do Contrato
    match_valor = re.search(r"(?:total de|Valor fixo:)\s*(R\$\s*[\d\.,]+)", texto_bruto, re.IGNORECASE)
    
    # 5. Honorários de êxito
    match_exito = re.search(r"(\d+%\s*(?:\(.+?\))?\s*sobre)", texto_bruto, re.IGNORECASE)

    return {
        "arquivo_origem": nome_arquivo,
        "tipo_documento": "contrato_honorarios",
        "tipo_processo": tipo_processo,
        "contratante": match_partes.group(1).strip() if match_partes else "Não encontrado",
        "cpf_cnpj_contratante": match_partes.group(2).strip() if match_partes else None,
        "endereco_encontrado": endereco,
        "valor_total": match_valor.group(1).strip() if match_valor else None,
        "honorarios_exito": match_exito.group(1).strip() if match_exito else None
    }

def processar_pdfs(pasta_caminho):
    pasta = Path(pasta_caminho)
    resultados = []
    
    arquivos_pdf = list(pasta.glob("*.pdf"))
    
    if not arquivos_pdf:
        print("Nenhum arquivo PDF encontrado na pasta.")
        return

    for arquivo in arquivos_pdf:
        print(f"Processando: {arquivo.name}")
        
        with pdfplumber.open(arquivo) as pdf:
            texto_completo = ""
            
            for i, pagina in enumerate(pdf.pages):
                texto_pagina = pagina.extract_text() or ""
                texto_completo += texto_pagina + "\n"
                
                # Continua salvando tabelas em CSV se existirem (ex: João Silva)
                tabela = pagina.extract_table()
                if tabela:
                    df_tabela = pd.DataFrame(tabela[1:], columns=tabela[0])
                    nome_tabela = f"tabela_{arquivo.stem}_pag_{i+1}.csv"
                    df_tabela.to_csv(nome_tabela, index=False, encoding='utf-8-sig')

            # Extração de dados
            if "CONTRATO" in texto_completo.upper():
                dados = extrair_contrato_honorarios(texto_completo, arquivo.name)
            else:
                dados = {"arquivo_origem": arquivo.name, "tipo_documento": "Não identificado"}
            
            # Salvando JSON Individual
            nome_json = f"extração_{arquivo.stem}.json"
            with open(nome_json, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)
            
            resultados.append(dados)

    # Salvando Relatório Geral em JSON
    with open("Relatorio_Geral_Contratos.json", 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=4)
    
    print("\n[SUCESSO] Arquivos JSON e Relatório Geral gerados!")

# Execução
caminho_pasta = "pdfs_extracao"
processar_pdfs(caminho_pasta)