import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

# Navegação de pastas exatamente conforme a imagem enviada
pasta_automacoes = Path(__file__).resolve().parent     
pasta_fase2 = pasta_automacoes.parent                  
pasta_raiz = pasta_fase2.parent

# Carregar o arquivo .env que está na raiz
load_dotenv(pasta_raiz / ".env", override=True)

#Resgatar a variável API_KEY do seu .env
# Sugestão: Se a variável guardar apenas a URL do FastAPI, considere renomeá-la para API_URL no .env no futuro
API_URL = os.getenv("API_KEY") 

if not API_URL:
    print("AVISO: Variável API_KEY não encontrada no arquivo .env!")

# Adicionar a pasta BD ao sistema para o Python conseguir achar o banco_vetorial.py
pasta_bd = pasta_raiz / "fase1_engenharia" / "BD"
sys.path.append(str(pasta_bd))

from banco_vetorial import buscar_contexto_semantico

# FERRAMENTA 1: Busca Semântica em PDFs (pgvector)

@tool
def buscar_jurisprudencia_documentos(pergunta: str) -> str:
    """
    Busca no banco de dados vetorial por trechos de documentos jurídicos, PDFs, 
    petições, sentenças e jurisprudências do escritório.
    USE ESTA FERRAMENTA SEMPRE que o utilizador perguntar sobre o "teor", "argumento", 
    "resumo", ou detalhes narrativos de um arquivo ou processo.
    """
    try:
        resultado = buscar_contexto_semantico(pergunta)
        if not resultado.strip():
            return "RESULTADO_SISTEMA: Nenhum trecho de documento relevante foi encontrado para esta pergunta."
        return resultado
    except Exception as e:
        return f"RESULTADO_SISTEMA: Erro ao buscar documentos vetoriais: {e}"

# FERRAMENTA 2: Consulta de Histórico de Processo via API

@tool
def buscar_historico_processo(numero_processo: str, nome_cliente: str) -> str:
    """
    Busca o status atual e o histórico completo de um processo específico.
    EXIGE DOIS PARÂMETROS OBRIGATÓRIOS: O número do processo e o nome do cliente.
    USE ESTA FERRAMENTA para responder "Qual o status do processo X do cliente Y?".
    """
    try:
        resposta = requests.get(f"{API_URL}/ia/processo_historico", params={"numero_processo": numero_processo, "nome_cliente": nome_cliente})
        
        if resposta.status_code == 200:
            dados = resposta.json()
            recente = dados["status_mais_recente"]
            texto = f"STATUS ATUAL (Processo {recente['numero_processo']} - Cliente {nome_cliente}):\nFase: {recente['fase']} | Status: {recente['status']} | Aberto em: {recente['data_abertura']}\n"
            
            if dados["historico_anterior"]:
                texto += f"\nHISTÓRICO ANTERIOR ({len(dados['historico_anterior'])} andamentos passados encontrados):\n"
                for h in dados["historico_anterior"]:
                    texto += f"- {h['data_abertura']}: Fase {h['fase']} ({h['status']})\n"
            return texto
            
        elif resposta.status_code == 404:
            return f"RESULTADO_SISTEMA: O processo '{numero_processo}' para o cliente '{nome_cliente}' não foi encontrado. Peça ao utilizador para verificar os dados."
        else:
            return f"RESULTADO_SISTEMA: Erro desconhecido da API. Status Code: {resposta.status_code}"
            
    except requests.exceptions.ConnectionError:
        return "RESULTADO_SISTEMA: Erro crítico. A API do escritório está desligada ou inacessível no momento."

# FERRAMENTA 3: Alerta de Prazos Urgentes via API

@tool
def verificar_prazos_processuais(dias: int = 10) -> str:
    """
    Busca processos com prazos ou audiências urgentes nos próximos 'X' dias.
    USE ESTA FERRAMENTA para responder a perguntas sobre calendário, prazos vencendo, urgências ou o que fazer nesta semana.
    """
    try:
        resposta = requests.get(f"{API_URL}/ia/prazos_urgentes", params={"dias": dias})
        
        if resposta.status_code == 200:
            dados = resposta.json()
            if dados["total_prazos"] == 0:
                return f"Nenhum prazo urgente encontrado no sistema para os próximos {dias} dias."
                
            texto = f"FORAM ENCONTRADOS {dados['total_prazos']} PRAZOS URGENTES:\n"
            for p in dados["processos_urgentes"]:
                texto += f"- Cliente: {p['nome_cliente']} | Processo: {p['numero_processo']} | Vence em: {p['prazo']} | Advogado: {p['advogado']}\n"
            return texto
            
        return f"RESULTADO_SISTEMA: Erro da API ao buscar prazos. Status Code: {resposta.status_code}"
        
    except requests.exceptions.ConnectionError:
        return "RESULTADO_SISTEMA: Erro crítico. A API do escritório está desligada ou inacessível no momento."

# FERRAMENTA 4: Relatório de Inadimplência via API
@tool
def checar_inadimplencia_honorarios() -> str:
    """
    Gera um relatório de clientes inadimplentes ou com contratos de honorários em aberto.
    USE ESTA FERRAMENTA para responder quem está a dever dinheiro, valores em aberto ou status de pagamentos.
    """
    try:
        resposta = requests.get(f"{API_URL}/ia/inadimplencia")
        
        if resposta.status_code == 200:
            dados = resposta.json()
            if dados["total_inadimplentes"] == 0:
                return "Excelente notícia. Não há nenhum cliente com honorários atrasados no banco de dados."
                
            texto = f"FORAM ENCONTRADOS {dados['total_inadimplentes']} CONTRATOS COM PENDÊNCIA FINANCEIRA:\n"
            for d in dados["detalhamento"]:
                texto += f"- Cliente: {d['nome_cliente']} (Tel: {d['contato_cliente']}) | Dívida: R$ {d['valor_em_aberto']} | Venceu em: {d['data_vencimento']} | Status: {d['status_pagamento']}\n"
            return texto
            
        return f"RESULTADO_SISTEMA: Erro da API ao buscar inadimplência. Status Code: {resposta.status_code}"
        
    except requests.exceptions.ConnectionError:
        return "RESULTADO_SISTEMA: Erro crítico. A API do escritório está desligada ou inacessível no momento."

# Agrupando as ferramentas numa lista para injetar no Agente mais tarde
lista_de_ferramentas = [
    buscar_jurisprudencia_documentos, 
    buscar_historico_processo, 
    verificar_prazos_processuais, 
    checar_inadimplencia_honorarios
]