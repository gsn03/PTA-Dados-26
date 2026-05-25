def extrair_intimacao(texto_bruto: str, nome_arquivo: str) -> dict:
    """Regras para extrair dados de intimações"""
    import re # usada para encontrar sequência de caracteres específicas 
    
    padrao_processo = r"\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2}\.\d{4}"
    match_processo = re.search(padrao_processo, texto_bruto)
    n_processo = match_processo.group(0) if match_processo else None
    
    match_cnpj = re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", texto_bruto)
    cnpj = match_cnpj.group(0) if match_cnpj else None
    
    # 2. Tipo de Processo
    tipo_processo = "Trabalhista" if "TRT" in texto_bruto or "Trabalho" in texto_bruto else "Cível"
    
    # 3. Tipo de Ação
    tipo_acao = None
    match_acao = re.search(r"ação de\s+([^\(]+?)\s*\(?processo", texto_bruto, re.IGNORECASE)
    if match_acao:
        tipo_acao = match_acao.group(1).strip()

    # 4. Partes (Acusador/Acusado - Autor/Réu)
    autor, reu = None, None
    match_partes = re.search(r"movida por\s+(.+?)\s+em face de\s+(.+?),", texto_bruto, re.IGNORECASE)
    if match_partes:
        autor = match_partes.group(1).strip()
        reu = match_partes.group(2).strip()
        
    # 5. Advogado e OAB
    advogado, oab = None, None
    match_adv = re.search(r"Dra?\.\s+([^,]+),\s+inscrita.*?OAB.*?nº\s+([\d\.]+)", texto_bruto, re.IGNORECASE)
    if match_adv:
        advogado = match_adv.group(1).strip()
        oab = match_adv.group(2).strip()
        
    # 6. Decisão e Valores (Deferido/Indeferido/Parcial)
    resultado_julgamento = None
    match_resultado = re.search(r"julgando\s+(PROCEDENTES|IMPROCEDENTES|PARCIALMENTE PROCEDENTES)", texto_bruto, re.IGNORECASE)
    if match_resultado:
        resultado_julgamento = match_resultado.group(1).upper()
        
    # Captura todos os valores em Reais (R$) encontrados no documento
    valores = re.findall(r"R\$\s*[\d\.]+,[\d]{2}", texto_bruto)

    # 7. Data de Expedição
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
        "cnpj_encontrado": cnpj,
        "data_expedicao": data_expedicao,
        "texto_bruto": texto_bruto
    }
    

def extrair_citacao(texto_bruto: str, nome_arquivo: str) -> dict:
    """Regras para extrair dados de citações"""
    import re
    
    padrao_cnj = r"\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2}\.\d{4}"
    match_processo = re.search(padrao_cnj, texto_bruto)
    n_processo = match_processo.group(0) if match_processo else None
    
    match_cpf = re.search(r"\d{3}\.\d{3}\.\d{3}-\d{2}", texto_bruto)
    cpf = match_cpf.group(0) if match_cpf else None

    # 2. Tipo de Processo (Inferido pelas palavras-chave)
    tipo_processo = "Trabalhista" if "TRT" in texto_bruto or "Trabalho" in texto_bruto else "Cível"

    # 3. Qualificação do Citado (Nome, Nacionalidade, Estado Civil, Ocupação)
    # Baseado na estrutura: "Cite-se [NOME], [Nacionalidade], [Estado Civil], [Ocupação], CPF..."
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
    # 4. Endereço Completo
    endereco = None
    match_endereco = re.search(r"residente e domiciliado na\s+(.+?), ou onde for", texto_bruto, re.IGNORECASE)
    if match_endereco:
        endereco = match_endereco.group(1).strip()
        
    # 5. Quem está promovendo a ação
    promovente = None
    match_promovente = re.search(r"move\s+(.+?), processo", texto_bruto, re.IGNORECASE)
    if match_promovente:
        promovente = match_promovente.group(1).strip()
        
    # 6. Prazo de Contestação
    prazo = None
    match_prazo = re.search(r"prazo(?: improrrogável)? de\s+(.+?)\s*,", texto_bruto, re.IGNORECASE)
    if match_prazo:
        prazo = match_prazo.group(1).strip()
        
    # 7. Data de Expedição
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
        "nome_citado": nome,
        "cpf_citado": cpf,
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

def extrair_acordos(texto_bruto: str, nome_arquivo: str) -> dict:
    """Regras para extrair dados de acordos"""
    import re # usada para encontrar sequência de caracteres específicas 
    
    #numero do processo
    padrao_processo = r"\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2}\.\d{4}"
    match_processo = re.search(padrao_processo, texto_bruto)
    n_processo = match_processo.group(0) if match_processo else None
    
    
    # 2. Tipo de Processo
    tipo_processo = "Trabalhista" if "TRT" in texto_bruto or "Trabalho" in texto_bruto else "Cível"
    
    # 3. Tipo de Ação
    tipo_acao = None
    match_acao = re.search(r"ação de\s+([^\(]+?)\s*\(?processo", texto_bruto, re.IGNORECASE)
    if match_acao:
        tipo_acao = match_acao.group(1).strip()

    # 4. Partes (Acusador/Acusado - Autor/Réu)
    autor, reu = None, None
    match_partes = re.search(r"movida por\s+(.+?)\s+em face de\s+(.+?),", texto_bruto, re.IGNORECASE)
    if match_partes:
        autor = match_partes.group(1).strip()
        reu = match_partes.group(2).strip()
        
    # 5. Advogado e OAB
    advogado, oab = None, None
    match_adv = re.search(r"Dra?\.\s+([^,]+),\s+inscrita.*?OAB.*?nº\s+([\d\.]+)", texto_bruto, re.IGNORECASE)
    if match_adv:
        advogado = match_adv.group(1).strip()
        oab = match_adv.group(2).strip()
        
    # 6. Decisão e Valores (Deferido/Indeferido/Parcial)
    resultado_julgamento = None
    match_resultado = re.search(r"julgando\s+(PROCEDENTES|IMPROCEDENTES|PARCIALMENTE PROCEDENTES)", texto_bruto, re.IGNORECASE)
    if match_resultado:
        resultado_julgamento = match_resultado.group(1).upper()
        
    # Captura todos os valores em Reais (R$) encontrados no documento
    valores = re.findall(r"R\$\s*[\d\.]+,[\d]{2}", texto_bruto)

    # 7. Data de Expedição
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
        "n_processo": n_processo,
        "acusando_autor": autor,
        "acusado_reu": reu,
        "nome_advogado": advogado,
        "oab_advogado": oab,
        "valores_condenacao": valores if valores else None,
        "data_expedicao": data_expedicao,
        "texto_bruto": texto_bruto
    }
    


    ''''
    Número do processo      OK
Unidade (qual vara ou  juizado)
Partes (e consequentemente os patronos, ou seja, os advogados)
Valor da causa (se tiver no acordo, mas é parte importante do processo, então já deixa anotado caso tenha outra atividade dessa)
Objeto do processo 
Valores que serão pagos e condições de pagamento
    '''