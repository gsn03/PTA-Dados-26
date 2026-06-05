from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, case, asc
from datetime import date, timedelta
import sys
import os
import re
from pydantic import BaseModel
from typing import List, Dict, Any
from pathlib import Path
from pydantic import BaseModel

# Ajuste de caminho idêntico ao das suas outras rotas
pasta_bd = Path(__file__).parent.parent / "BD"
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from model_processos import Processo
from model_Cliente import Cliente
from model_honorarios import contrato_honorario

# Criação do Router específico para a Inteligência Artificial
router = APIRouter(prefix="/ia", tags=["IA - Agente LangGraph"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

    
# =====================================================================
# MOTOR RAG E LLM
# =====================================================================
import sys
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage

# Adiciona a pasta do grafo ao sistema para o Python conseguir importar
pasta_grafo = Path(__file__).resolve().parent.parent.parent / "fase2_agente" / "grafo"
sys.path.append(str(pasta_grafo))

# Importa o cérebro LangGraph que construímos
from fluxo_inicial import grafo_completo

from pydantic import BaseModel
from typing import List, Dict, Any

class RequisicaoChat(BaseModel):
    pergunta: str
    historico: List[Dict[str, Any]] = []
    
@router.post("/chat")
def responder_chat(requisicao: RequisicaoChat):
    pergunta_usuario = requisicao.pergunta
    historico_dicts = requisicao.historico
    
    print("\n=======================================================")
    print(f"NOVA REQUISIÇÃO VIA INTERFACE: {pergunta_usuario}")
    print("=======================================================\n")
    
    # 1. Converter o histórico que vem do Streamlit para o formato do LangChain
    mensagens_langgraph = []
    for msg in historico_dicts:
        if msg["role"] == "user":
            mensagens_langgraph.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            mensagens_langgraph.append(AIMessage(content=msg["content"]))
            
    # 2. Adicionar a pergunta atual ao final da lista
    mensagens_langgraph.append(HumanMessage(content=pergunta_usuario))
    
    # 3. Montar o estado inicial exigido pelo seu fluxo_inicial.py
    estado_inicial = {
        "messages": mensagens_langgraph,
        "pergunta_reformulada": "",
        "contexto_recuperado": "",
        "resposta_gerada": ""
    }
    
    # 4. Invocar o Grafo (O verdadeiro Agente Jurídico com Roteador, Buscador, Redator e Validador)
    try:
        estado_final = grafo_completo.invoke(estado_inicial)
        # Extrai a resposta aprovada pelo Auditor
        texto_final = estado_final.get("resposta_gerada", "SISTEMA_VALIDACAO: Não foi possível gerar uma resposta.")
    except Exception as e:
        texto_final = f"SISTEMA_VALIDACAO: Ocorreu um erro no processamento do Agente: {str(e)}"

    return {"resposta": texto_final}

#Prazos Urgentes (Para a Ferramenta de Alerta e Automação)
@router.get("/prazos_urgentes")
def buscar_prazos_urgentes_ia(dias: int = 7, db: Session = Depends(get_db)):
    
    data_hoje = date.today()
    data_limite = data_hoje + timedelta(days=dias)
    
    # Busca processos cujo prazo está entre hoje e o limite escolhido
    processos_urgentes = db.query(Processo).filter(
        Processo.prazo_proximo >= data_hoje,
        Processo.prazo_proximo <= data_limite
    ).order_by(Processo.prazo_proximo).all()
    
    # O LLM precisa do nome do cliente, então montamos uma lista enriquecida
    resultado = []
    for proc in processos_urgentes:
        cliente = db.query(Cliente).filter(Cliente.id == proc.cliente_id).first()
        resultado.append({
            "numero_processo": proc.numero_processo,
            "nome_cliente": cliente.nome if cliente else "Desconhecido",
            "fase_atual": proc.fase,
            "prazo": proc.prazo_proximo,
            "advogado": proc.nome_advogado
        })
        
    return {"total_prazos": len(resultado), "processos_urgentes": resultado}

# Inadimplência Financeira (Atrasos até a data atual e correção do Erro 500)
@router.get("/inadimplencia")
def relatorio_inadimplencia_ia(db: Session = Depends(get_db)):
    from datetime import date # Garante a importação da data
    
    # Captura a data de hoje no formato YYYY-MM-DD
    data_hoje_str = str(date.today())
    
    # 1. Puxamos do banco apenas os contratos não pagos (sem matemática no SQL)
    contratos_pendentes = db.query(contrato_honorario).filter(
        contrato_honorario.status_pagamento != "Pago"
    ).all()
    
    resultado = []
    for contrato in contratos_pendentes:
        # 2. Conversão segura no Python: transforma o texto VARCHAR em Número (Float)
        try:
            # Substitui possível vírgula por ponto para o Python entender
            valor_texto = str(contrato.valor_em_aberto).replace(',', '.')
            valor_num = float(valor_texto)
        except ValueError:
            valor_num = 0.0
            
        # 3. Filtra apenas os que têm dívida real E que já venceram (data <= hoje)
        if valor_num > 0 and contrato.data_vencimento and str(contrato.data_vencimento) <= data_hoje_str:
            cliente = db.query(Cliente).filter(Cliente.id == contrato.cliente_id).first()
            resultado.append({
                "nome_cliente": cliente.nome if cliente else "Desconhecido",
                "contato_cliente": cliente.contato if cliente else "Sem contato",
                "numero_processo": contrato.numero_processo,
                "valor_em_aberto": contrato.valor_em_aberto, # Mantém o texto original para exibição
                "status_pagamento": contrato.status_pagamento,
                "data_vencimento": contrato.data_vencimento
            })
            
    return {"total_inadimplentes": len(resultado), "detalhamento": resultado}

# Histórico de Processo (Busca ancorada no ID do Cliente para suportar processos com múltiplos autores)
@router.get("/processo_historico")
def buscar_historico_processo_ia(numero_processo: str, nome_cliente: str, db: Session = Depends(get_db)):
    import re
    
    # 1. Encontrar o cliente pelo nome (Trazemos todos os IDs que derem 'match' para evitar falhas com homônimos)
    nome_cliente_limpo = nome_cliente.strip()
    clientes = db.query(Cliente).filter(Cliente.nome.ilike(f"%{nome_cliente_limpo}%")).all()
    
    if not clientes:
        raise HTTPException(status_code=404, detail="Cliente não encontrado no banco de dados.")

    # Extrair a lista de IDs auto-incrementáveis desses clientes
    ids_clientes = [c.id for c in clientes]

    # 2. Buscar TODOS os processos atrelados EXCLUSIVAMENTE aos IDs desse cliente
    processos_do_cliente = db.query(Processo).filter(
        Processo.cliente_id.in_(ids_clientes)
    ).order_by(desc(Processo.data_abertura)).all()
    
    # 3. Limpar a pontuação do número que a IA enviou
    num_buscado_limpo = re.sub(r'[^0-9]', '', numero_processo)
    
    historico = []
    
    # 4. O Python procura o número exato apenas dentro da "pasta" deste cliente
    for proc in processos_do_cliente:
        if not proc.numero_processo:
            continue
            
        num_banco_limpo = re.sub(r'[^0-9]', '', proc.numero_processo)
        
        # Exige igualdade estrita dos números limpos e bloqueia strings vazias
        if num_buscado_limpo and num_banco_limpo and (num_buscado_limpo == num_banco_limpo):
            historico.append(proc)
            
    if not historico:
        raise HTTPException(status_code=404, detail=f"O processo {numero_processo} não foi encontrado para o cliente {nome_cliente}.")

    # 5. Construção da Resposta
    status_atual = historico[0]
    dict_atual = {
        "numero_processo": status_atual.numero_processo,
        "fase": status_atual.fase,
        "status": status_atual.status,
        "data_abertura": status_atual.data_abertura.isoformat() if status_atual.data_abertura else "Sem data"
    }
    
    fases_anteriores = []
    if len(historico) > 1:
        for andamento in historico[1:]:
            fases_anteriores.append({
                "numero_processo": andamento.numero_processo,
                "fase": andamento.fase,
                "status": andamento.status,
                "data_abertura": andamento.data_abertura.isoformat() if andamento.data_abertura else "Sem data"
            })

    return {
        "status_mais_recente": dict_atual,
        "historico_anterior": fases_anteriores,
        "total_movimentacoes_registradas": len(historico)
    }
    

@router.get("/alertas_email")
def buscar_prazos_para_email_exato(dias_exatos: int, db: Session = Depends(get_db)):
    """
    Rota exclusiva para automação de e-mails internos (Relatório Matinal).
    Busca processos que vencem em um dia matemático EXATO.
    """
    data_alvo = date.today() + timedelta(days=dias_exatos)
    
    processos_alvo = db.query(Processo).filter(
        Processo.prazo_proximo == data_alvo
    ).all()
    
    resultado = []
    for proc in processos_alvo:
        cliente = db.query(Cliente).filter(Cliente.id == proc.cliente_id).first()
        resultado.append({
            "numero_processo": proc.numero_processo,
            "nome_cliente": cliente.nome if cliente else "Desconhecido",
            "advogado": proc.nome_advogado, # INJEÇÃO DO ADVOGADO AQUI
            "prazo": proc.prazo_proximo,
            "fase_atual": proc.fase
        })
        
    return {"data_alvo": data_alvo, "total_envios": len(resultado), "processos": resultado}

@router.get("/status_vertente")
def obter_status_por_vertente(db: Session = Depends(get_db)):
    # tratar nulos e maiusculo/minusculo para evitar duplicidade
    tipo_tratado = func.coalesce(func.upper(Processo.tipo_processo), "NÃO INFORMADO")
    status_tratado = func.coalesce(func.upper(Processo.status), 'NÃO INFORMADO')

    # query
    resultados = db.query(
        tipo_tratado.label('vertente'),
        status_tratado.label('status'),
        func.count(Processo.id).label('quantidade')
    ).group_by(
        tipo_tratado,
        status_tratado
    ).all()

    # formatando a saída em JSON
    dados_formatados = [
        {"vertente": r.vertente, "status": r.status, "quantidade": r.quantidade} 
        for r in resultados
    ]

    return {"dados_status_vertente": dados_formatados}

@router.get("/carteira_advogados")
def obter_carteira_advogados(db: Session = Depends(get_db)):
    
    # 1. Tratar status e nome do advogado (Evitar nulos e duplicidades por maiúsculas)
    status_ativos = ['ATIVO', 'EM RECURSO'] 
    status_tratado = func.upper(Processo.status)
    advogado_tratado = func.coalesce(Processo.nome_advogado, "Não Atribuído")

    # 2. Query de Agregação: Total a trabalhar, Ativos e Em Recurso
    agrupamento = db.query(
        advogado_tratado.label('nome_advogado'),
        func.count(Processo.id).label('total_trabalhar'),
        func.sum(case((status_tratado == 'ATIVO', 1), else_=0)).label('ativos'),
        func.sum(case((status_tratado == 'EM RECURSO', 1), else_=0)).label('em_recurso')
    ).filter(
        status_tratado.in_(status_ativos)
    ).group_by(
        advogado_tratado
    ).all()

    carteira_final = []

    # 3. Busca detalhada: Os top 5 prazos para cada carteira
    for row in agrupamento:
        nome_adv = row.nome_advogado
        
        # Encontra os processos desse advogado específico que não venceram
        processos_adv = db.query(Processo).filter(
            func.coalesce(Processo.nome_advogado, "Não Atribuído") == nome_adv,
            func.upper(Processo.status).in_(status_ativos),
            Processo.prazo_proximo != None,
            Processo.prazo_proximo >= date.today()
        ).order_by(asc(Processo.prazo_proximo)).limit(5).all()

        lista_prazos = []
        # Loop clássico para buscar o nome do cliente (Mantendo o seu padrão de arquitetura)
        for proc in processos_adv:
            cliente = db.query(Cliente).filter(Cliente.id == proc.cliente_id).first()
            lista_prazos.append({
                "numero_processo": proc.numero_processo,
                "nome_cliente": cliente.nome if cliente else "Desconhecido",
                "tipo_processo": proc.tipo_processo,
                "status": proc.status,
                "data_prazo": proc.prazo_proximo.isoformat() if proc.prazo_proximo else None
            })

        carteira_final.append({
            "nome_advogado": nome_adv,
            "total_trabalhar": int(row.total_trabalhar or 0),
            "ativos": int(row.ativos or 0),
            "em_recurso": int(row.em_recurso or 0),
            "proximos_prazos": lista_prazos
        })

    # Ordena para que o advogado com mais processos apareça no topo da lista
    carteira_final = sorted(carteira_final, key=lambda x: x['total_trabalhar'], reverse=True)

    return {"carteira": carteira_final}