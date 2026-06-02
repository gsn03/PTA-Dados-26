from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date, timedelta
import sys
from pathlib import Path

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

#Histórico de Processo (Resolve o problema dos números duplicados)

@router.get("/processo_historico")
def buscar_historico_processo_ia(numero_processo: str, nome_cliente: str, db: Session = Depends(get_db)):
    
    #Encontrar o ID verdadeiro do cliente usando um filtro "parecido" (ilike)
    cliente = db.query(Cliente).filter(Cliente.nome.ilike(f"%{nome_cliente}%")).first()
    
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado. Verifique o nome.")

    #  Buscar APENAS os processos que têm aquele número E pertencem àquele cliente
    # O 'order_by(desc())' garante que a data mais recente venha primeiro
    historico = db.query(Processo).filter(
        Processo.numero_processo == numero_processo,
        Processo.cliente_id == cliente.id
    ).order_by(desc(Processo.data_abertura)).all()
    
    if not historico:
        raise HTTPException(status_code=404, detail="Nenhum processo encontrado para este cliente com este número.")

    #  Estruturar a resposta para o LLM entender o que é o "agora" e o que é o "passado"
    status_atual = historico[0]
    fases_anteriores = historico[1:] if len(historico) > 1 else []

    return {
        "status_mais_recente": status_atual,
        "historico_anterior": fases_anteriores,
        "total_movimentacoes_registradas": len(historico)
    }
    
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

#Inadimplência Financeira (Para a Ferramenta de Honorários)
@router.get("/inadimplencia")
def relatorio_inadimplencia_ia(db: Session = Depends(get_db)):
    
    # Busca todos os contratos cujo status NÃO É 'Pago'
    contratos_pendentes = db.query(contrato_honorario).filter(
        contrato_honorario.status_pagamento != "Pago"
    ).all()
    
    resultado = []
    for contrato in contratos_pendentes:
        cliente = db.query(Cliente).filter(Cliente.id == contrato.cliente_id).first()
        resultado.append({
            "nome_cliente": cliente.nome if cliente else "Desconhecido",
            "contato_cliente": cliente.contato if cliente else "Sem contato",
            "numero_processo": contrato.numero_processo,
            "valor_em_aberto": contrato.valor_em_aberto,
            "status_pagamento": contrato.status_pagamento,
            "data_vencimento": contrato.data_vencimento
        })
        
    return {"total_inadimplentes": len(resultado), "detalhamento": resultado}

@router.get("/alertas_email")
def buscar_prazos_para_email_exato(dias_exatos: int, db: Session = Depends(get_db)):
    """
    Rota exclusiva para automação de e-mails internos (Relatório Matinal).
    Busca processos que vencem em um dia matemático EXATO.
    """
    data_alvo = date.today() + timedelta(days=dias_exatos)
    
    # Busca APENAS os processos que vencem NAQUELA data exata
    processos_alvo = db.query(Processo).filter(
        Processo.prazo_proximo == data_alvo
    ).all()
    
    resultado = []
    for proc in processos_alvo:
        cliente = db.query(Cliente).filter(Cliente.id == proc.cliente_id).first()
        resultado.append({
            "numero_processo": proc.numero_processo,
            "nome_cliente": cliente.nome if cliente else "Desconhecido",
            "prazo": proc.prazo_proximo,
            "fase_atual": proc.fase
        })
        
    return {"data_alvo": data_alvo, "total_envios": len(resultado), "processos": resultado}