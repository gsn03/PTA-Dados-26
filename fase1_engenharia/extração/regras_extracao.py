import re

def extrair_intimacao(texto_bruto: str, nome_arquivo: str) -> dict:
    """Regras para extrair dados de intimações"""
    padrao_processo = r"\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2}\.\d{4}"
    match_processo = re.search(padrao_processo, texto_bruto)
    n_processo = match_processo.group(0) if match_processo else None
    
    match_cnpj = re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", texto_bruto)
    cnpj = match_cnpj.group(0) if match_cnpj else None
    
    tipo_processo = "Trabalhista" if "TRT" in texto_bruto or "Trabalho" in texto_bruto else "Cível"
    
    tipo_acao = None
    match_acao = re.search(r"ação de\s+([^\(]+?)\s*\(?processo", texto_bruto, re.IGNORECASE)
    if match_acao:
        tipo_acao = match_acao.group(1).strip()

    autor, reu = None, None
    match_partes = re.search(r"movida por\s+(.+?)\s+em face de\s+(.+?),", texto_bruto, re.IGNORECASE)
    if match_partes:
        autor = match_partes.group(1).strip()
        reu = match_partes.group(2).strip()
        
    advogado, oab = None, None
    match_adv = re.search(r"Dra?\.\s+([^,]+),\s+inscrita.*?OAB.*?nº\s+([\d\.]+)", texto_bruto, re.IGNORECASE)
    if match_adv:
        advogado = match_adv.group(1).strip()
        oab = match_adv.group(2).strip()
        
    resultado_julgamento = None
    match_resultado = re.search(r"julgando\s+(PROCEDENTES|IMPROCEDENTES|PARCIALMENTE PROCEDENTES)", texto_bruto, re.IGNORECASE)
    if match_resultado:
        resultado_julgamento = match_resultado.group(1).upper()
        
    valores = re.findall(r"R\$\s*[\d\.]+,[\d]{2}", texto_bruto)

    data_expedicao = None
    match_data = re.search(r"Recife,\s+([\d]{1,2}\s+de\s+[a-zA-Z]+\s+de\s+[\d]{4})", texto_bruto, re.IGNORECASE)
    if match_data:
        data_expedicao = match_data.group(1).strip()
    
    tribunal_vara = None
    match_tribunal = re.search(r"(?:COMARCA DE.+?|PODER JUDICIÁRIO.+?)\s+([^\n]+Vara[^\n]+|[^\n]+Turma[^\n]+)", texto_bruto, re.IGNORECASE)
    if match_tribunal:
        tribunal_vara = match_tribunal.group(1).strip()

    return {
        "arquivo_origem": nome_arquivo,
        "tribunal_vara": tribunal_vara,
        "tipo_documento": "intimacao",
        "tipo_processo": tipo_processo,
        "tipo_acao": tipo_acao,
        "n_processo": n_processo,
        "acusando_autor": autor,
        "acusado_reu": reu,
        "nome_advogado": advogado,
        "oab_advogado": oab,
        "resultado_julgamento": resultado_julgamento,
        "valores_condenacao": valores if valores else None,
        "cpf_cnpj": cnpj, # PADRONIZADO
        "data_expedicao": data_expedicao,
        "texto_bruto": texto_bruto
    }
    

def extrair_citacao(texto_bruto: str, nome_arquivo: str) -> dict:
    """Regras para extrair dados de citações"""
    padrao_cnj = r"\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2}\.\d{4}"
    match_processo = re.search(padrao_cnj, texto_bruto)
    n_processo = match_processo.group(0) if match_processo else None
    
    match_cpf = re.search(r"\d{3}\.\d{3}\.\d{3}-\d{2}", texto_bruto)
    cpf = match_cpf.group(0) if match_cpf else None

    tipo_processo = "Trabalhista" if "TRT" in texto_bruto or "Trabalho" in texto_bruto else "Cível"

    nome, nacionalidade, estado_civil, ocupacao = None, None, None, None
    match_qualificacao = re.search(r"Cite-se\s+([^,]+),\s+([^,]+),\s+([^,]+),\s+([^,]+),\s+CPF", texto_bruto, re.IGNORECASE)
    if match_qualificacao:
        nome = match_qualificacao.group(1).strip()
        nacionalidade = match_qualificacao.group(2).strip()
        estado_civil = match_qualificacao.group(3).strip()
        ocupacao = match_qualificacao.group(4).strip()
    
    tipo_acao = None
    match_acao = re.search(r"ação de\s+([^\(]+?)\s*\(?processo", texto_bruto, re.IGNORECASE)
    if match_acao:
        tipo_acao = match_acao.group(1).strip()

    endereco = None
    match_endereco = re.search(r"residente e domiciliado na\s+(.+?), ou onde for", texto_bruto, re.IGNORECASE)
    if match_endereco:
        endereco = match_endereco.group(1).strip()
        
    promovente = None
    match_promovente = re.search(r"move\s+(.+?), processo", texto_bruto, re.IGNORECASE)
    if match_promovente:
        promovente = match_promovente.group(1).strip()
        
    prazo = None
    match_prazo = re.search(r"prazo(?: improrrogável)? de\s+(.+?)\s*,", texto_bruto, re.IGNORECASE)
    if match_prazo:
        prazo = match_prazo.group(1).strip()
        
    data_expedicao = None
    match_data = re.search(r"Expedido em.+?(no mês.+?\.)", texto_bruto, re.IGNORECASE)
    if match_data:
        data_expedicao = match_data.group(1).strip()
    
    tribunal_vara = None
    match_tribunal = re.search(r"(?:COMARCA DE.+?|PODER JUDICIÁRIO.+?)\s+([^\n]+Vara[^\n]+|[^\n]+Turma[^\n]+)", texto_bruto, re.IGNORECASE)
    if match_tribunal:
        tribunal_vara = match_tribunal.group(1).strip()
        
    return {
        "arquivo_origem": nome_arquivo,
        "tribunal_vara": tribunal_vara,
        "tipo_documento": "citacao",
        "tipo_ação": tipo_acao,
        "tipo_processo": tipo_processo,
        "n_processo": n_processo,
        "nome_cliente": nome, 
        "cpf_cnpj": cpf,      
        "nacionalidade": nacionalidade,
        "estado_civil": estado_civil,
        "ocupacao": ocupacao,
        "endereco_completo": endereco,
        "quem_promove": promovente,
        "prazo_contestacao": prazo,
        "data_expedicao": data_expedicao,
        "texto_bruto": texto_bruto
    }

def extrair_peticao(texto_bruto: str, nome_arquivo: str) -> dict:
    # (Mantido exatamente igual, pois não foca no cliente direto no momento)
    padrao_cnj = r"\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2}\.\d{4}"
    match_processo = re.search(padrao_cnj, texto_bruto)
    numero_encontrado = match_processo.group(0) if match_processo else None

    padrao_reclamante = r"Reclamante:\s*([^\n\r]+)" 
    match_reclamante = re.search(padrao_reclamante, texto_bruto)
    reclamante_encontrado = match_reclamante.group(1).strip() if match_reclamante else None

    padrao_reclamada = r"Reclamada:\s*([^\n\r]+)" 
    match_reclamada = re.search(padrao_reclamada, texto_bruto)
    reclamada_encontrado = match_reclamada.group(1).strip() if match_reclamada else None

    padrao_acao = r"Tipo de ação:\s*([^\n\r]+)"
    match_acao = re.search(padrao_acao, texto_bruto)
    acao_encontrada = match_acao.group(1).strip() if match_acao else None

    padrao_valorcausa = r"valor de\s*(R\$\s*[\d\.,]+)"
    match_valor = re.findall(padrao_valorcausa, texto_bruto, re.IGNORECASE)
    valor_encontrado = match_valor[-1].strip() if match_valor else None

    padrao_advogado = r"([^\n\|]+?)\s*\|\s*(OAB/[A-Z]{2}\s*[\d\.]+)"
    match_advogado = re.search(padrao_advogado, texto_bruto, re.IGNORECASE)
    advogado_encontrado = match_advogado.group(1).strip() if match_advogado else None
    oab_encontrada = match_advogado.group(2).strip() if match_advogado else None

    return {
        "arquivo_origem": nome_arquivo,
        "tipo_documento": "peticao",
        "numero_processo": numero_encontrado,
        "reclamante": reclamante_encontrado,
        "reclamada": reclamada_encontrado,
        "tipo_acao": acao_encontrada,
        "valor_causa": valor_encontrado,
        "advogado": advogado_encontrado,
        "oab_advogado": oab_encontrada,
        "texto_bruto": texto_bruto
    }

def extrair_contrato_honorarios(texto_bruto: str, nome_arquivo: str) -> dict:
    """Regras para extrair dados de Contratos de Honorários (Trazido para o script principal)"""
    texto_upper = texto_bruto.upper()
    
    if any(x in texto_upper for x in ["TRABALHISTA", "TRABALHO", "RESCISÃO", "TRT"]):
        tipo_processo = "Trabalhista"
    elif any(x in texto_upper for x in ["EMPRESARIAL", "SOCIEDADE", "FALÊNCIA", "RECUPERAÇÃO JUDICIAL"]):
        tipo_processo = "Empresarial"
    else:
        tipo_processo = "Cível"

    match_oab = re.search(r"OAB/([A-Z]{2})\s*(?:Nº\s*|SOB O Nº\s*)?([\d\.]+)", texto_bruto, re.IGNORECASE)
    oab_encontrada = f"{match_oab.group(1)} {match_oab.group(2)}" if match_oab else "Não encontrada"

    endereco = "Não encontrado"
    match_end = re.search(r"(?:residente|situado|domiciliado)\s+(?:na|no)\s+([^.\n]+)", texto_bruto, re.IGNORECASE)
    if match_end:
        endereco = match_end.group(1).strip()
        endereco = re.split(r",\s*inscrito|,\s*CPF|,\s*portador", endereco, flags=re.IGNORECASE)[0]
    else:
        match_fallback = re.search(r"(?:CPF|CNPJ)\s*[\d\.\-/]+,\s*([^.\n]+)", texto_bruto, re.IGNORECASE)
        if match_fallback:
            endereco = match_fallback.group(1).strip()

    match_partes = re.search(r"(?:Contratante|CLIENTE):\s*([^,]+),\s*(?:CPF|CNPJ)\s*([\d\.\-/]+)", texto_bruto, re.IGNORECASE)

    match_advogado = re.search(r"Dra\.\s*([^\n,]+)", texto_bruto, re.IGNORECASE)
    advogado_encontrado = match_advogado.group(1).strip() if match_advogado else "Não encontrado"
    
    match_valor = re.search(r"(?:total de|Valor fixo:)\s*(R\$\s*[\d\.,]+)", texto_bruto, re.IGNORECASE)
    match_exito = re.search(r"(\d+%\s*(?:\(.+?\))?\s*sobre)", texto_bruto, re.IGNORECASE)

    return {
        "arquivo_origem": nome_arquivo,
        "tipo_documento": "contrato_honorarios",
        "tipo_processo": tipo_processo,
        "nome_cliente": match_partes.group(1).strip() if match_partes else None, 
        "cpf_cnpj": match_partes.group(2).strip() if match_partes else None,    
        "nacionalidade": None,
        "estado_civil": None,
        "ocupacao": None,
        "endereco_completo": endereco,                                         
        "nome_advogado": advogado_encontrado,
        "oab_advogado": oab_encontrada,
        "valor_total_honorarios": match_valor.group(1).strip() if match_valor else None,
        "honorarios_exito": match_exito.group(1).strip() if match_exito else None
    }

def extrair_acordos(texto_bruto: str, nome_arquivo: str) -> dict:
    """Regras para extrair dados de acordos"""
    import re # usada para encontrar sequência de caracteres específicas 
    
        # 1) Número do processo
    padrao_n_processo = r"\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2}\.\d{4}"
    match_n_processo = re.search(padrao_n_processo, texto_bruto)
    numero_processo =  match_n_processo.group(0) if match_n_processo else None

        # 2) Nome do cliente (Reclamante ou Autor/Autora)
    padrao_nome_cliente = r"(?:Reclamante|Autor(?:a)?)\s+([A-Za-z][A-Za-z\s\-]+?)(?:,|e|\.|\n|$)"   #inclui tanto os nomes todo maiúsculo quanto com letras minúsculas tbm
    match_nome_cliente = re.search(padrao_nome_cliente , texto_bruto, re.IGNORECASE)
    nome_cliente = match_nome_cliente.group(1).strip() if match_nome_cliente else ''   #caso nn ache nome, retorna uma string vazia
        
        # 3) Nome de quem está sendo processado (Reclamada ou Réu)
    padrao_nome_processado = r"(?:Reclamada|Réu)\s+([A-Za-z][A-Za-z\s\-\.]{1,}(?:LTDA\.|S/A)?)(?:,|e|\.|\n|$)"
    match_nome_processado = re.search(padrao_nome_processado , texto_bruto, re.IGNORECASE)
    nome_processado = match_nome_processado.group(1).strip() if match_nome_processado else ''   
    
        # 4) Nome dos Advogados 
    padrao_advogados = r"((?:Dr\.|Dra\.)\s+(?!OAB|—|-)[^,\(\s\n]+(?:\s+(?!Dr\.|Dra\.|OAB|—|-)[^,\(\s\n]+)*)(?:[^,]*?((?:Dr\.|Dra\.)\s+(?!OAB|—|-)[^,\(\s\n]+(?:\s+(?!Dr\.|Dra\.|OAB|—|-)[^,\(\s\n]+)*))?"
    match_advogado = re.search(padrao_advogados, texto_bruto, re.IGNORECASE)
    nome_adv_cliente = match_advogado.group(1).strip() if match_advogado and match_advogado.group(1) else None  #pega o primeiro nome encontrado
    nome_adv_processado = match_advogado.group(2).strip() if match_advogado and match_advogado.group(2) else None   #pega o segundo nome encontrado


        # 6) OAB dos  advogados
    padrao_oab_advogados = r"(OAB/[A-Z]{2}\s+[\d\.]+)(?:[^,]*?(OAB/[A-Z]{2}\s+[\d\.]+))?"
    match_oab_advogado = re.search(padrao_oab_advogados, texto_bruto, re.IGNORECASE)

    oab_adv_cliente = None
    oab_adv_processado = None

    if match_oab_advogado:
        if match_oab_advogado.group(1):
            oab_adv_cliente = match_oab_advogado.group(1)   #pega a primeira oab encontrada
        if match_oab_advogado.group(2):
            oab_adv_processado = match_oab_advogado.group(2)  #pega a segunda oab encontrada

    # se o nome de um advogado não for encontrado, a OAB será None
    if not nome_adv_cliente:
        oab_adv_cliente = None
    if not nome_adv_processado:
        oab_adv_processado = None

        # 8) Valor total a ser pago
    padrao_valor_total = r"valor de\s*(R\$\s*[\d\.,]+)"
    match_valor = re.search(padrao_valor_total, texto_bruto)
    valor_total_acordo = match_valor.group(1) if match_valor else ''

        # 9) Tipo do processo
    if "TRT" in texto_bruto or "reclamant" in texto_bruto.lower() or "Trabalho" in texto_bruto:
        tipo_processo = "Trabalhista"
    else:
        tipo_processo = "Cível"

        # 10) Vara do processo
    tipo_vara = None
    padrao_vara = r"(\d+ª\s+Vara\s+(Cível | Trabalhista)\s+de\s+Recife)"
    match_vara = re.search(padrao_vara, texto_bruto, re.IGNORECASE)
    if match_vara:
        tipo_vara = match_vara.group(1).strip()


    return {
        "arquivo_origem": nome_arquivo,
        "tipo_documento": "acordo",
        "texto_bruto": texto_bruto,
        "n_processo" : numero_processo,
        "acusando_autor" : nome_cliente,
        "acusado_reu" : nome_processado,
        "nome_advogado" : nome_adv_cliente,
        "nome_advogado_reu" : nome_adv_processado,
        "oab_advogado" : oab_adv_cliente,
        "oab_advogado_reu" : oab_adv_processado,
        "valor_total_acordo" : valor_total_acordo,
        "tipo_processo" :tipo_processo,
        "tribunal_vara" : tipo_vara

    }
    

