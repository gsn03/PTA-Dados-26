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
        "texto_bruto": texto_bruto # Fundamental para a Fase 2 (LangChain)
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