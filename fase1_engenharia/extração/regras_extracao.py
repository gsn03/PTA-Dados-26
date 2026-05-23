def extrair_intimacao(texto_bruto: str, nome_arquivo: str) -> dict:
    """Regras para extrair dados de intimações"""
    import re
    padrao_cnj = r"\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2}\.\d{4}"
    match_processo = re.search(padrao_cnj, texto_bruto)
    numero_encontrado = match_processo.group(0) if match_processo else None
    return {
        "arquivo_origem": nome_arquivo,
        "tipo_documento": "intimacao_citacao",
        "numero_processo": numero_encontrado,
        "tribunal_origem": None, 
        "partes": None,
        "prazos_identificados": None,
        "texto_bruto": texto_bruto
    }
    
    

def extrair_contrato(texto_bruto: str, nome_arquivo: str) -> dict:
    """Regras para extrair dados de contratos"""

    return {"tipo": "contrato", "arquivo": nome_arquivo, "texto_bruto": texto_bruto}


def extrair_citacao(texto_bruto: str, nome_arquivo: str) -> dict:
    """Regras para extrair dados de citações"""

    import re
    
    # Pegar o número do processo (padrão CNJ)
    padrao_cnj = r"\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2}\.\d{4}"
    match_processo = re.search(padrao_cnj, texto_bruto)
    numero_encontrado = match_processo.group(0) if match_processo else None
    
    #Pegar o CPF do Réu/Citado (muito comum em citações)
    padrao_cpf = r"\d{3}\.\d{3}\.\d{3}-\d{2}"
    match_cpf = re.search(padrao_cpf, texto_bruto)
    cpf_encontrado = match_cpf.group(0) if match_cpf else None

    return {
        "arquivo_origem": nome_arquivo,
        "tipo_documento": "citacao",
        "numero_processo": numero_encontrado,
        "cpf_citado": cpf_encontrado,
        "autor_acao": None,          
        "prazo_contestacao": None,   
        "texto_bruto": texto_bruto    
    }

def extrair_peticao(texto_bruto: str, nome_arquivo: str) -> dict:
    #Bibliotecas
    import re
    #Regras para a extração
        #Pega o núm do processo
    padrao_cnj = r"\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2}\.\d{4}"
    match_processo = re.search(padrao_cnj, texto_bruto)
    numero_encontrado = match_processo.group(0) if match_processo else None
        #Reclamante
    padrao_reclamante = r"Reclamante:\s*([^\n\r]+)" 
    match_reclamante = re.search(padrao_reclamante, texto_bruto)
    reclamante_encontrado = match_reclamante.group(1).strip() if match_reclamante else None
        #Reclamada
    padrao_reclamada = r"Reclamada:\s*([^\n\r]+)" 
    match_reclamada = re.search(padrao_reclamada, texto_bruto)
    reclamada_encontrado = match_reclamada.group(1).strip() if match_reclamada else None
        #Ação da causa
    padrao_acao = r"Tipo de ação:\s*([^\n\r]+)"
    match_acao = re.search(padrao_acao, texto_bruto)
    acao_encontrada = match_acao.group(1).strip() if match_acao else None
        #Valor da causa
    padrao_valorcausa = r"valor de\s*(R\$\s*[\d\.,]+)"#Pega o valor final, garante que seja o valor da cusa especificamente
    match_valor = re.findall(padrao_valorcausa, texto_bruto, re.IGNORECASE)
    valor_encontrado = match_valor[-1].strip() if match_valor else None

    return {
        "arquivo_origem": nome_arquivo,
        "tipo_documento": "peticao",
        "numero_processo": numero_encontrado,
        "reclamante": reclamante_encontrado,
        "reclamada": reclamada_encontrado,
        "tipo_acao": acao_encontrada,
        "valor_causa": valor_encontrado,
        "texto_bruto": texto_bruto
    }