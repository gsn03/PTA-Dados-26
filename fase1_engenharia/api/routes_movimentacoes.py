from fastapi import APIRouter
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import sys
from pathlib import Path


# Vai até o banco
pasta_bd = Path(__file__).parent.parent / "BD"
sys.path.append(str(pasta_bd))


from database_model import SessionLocal
from model_movimentacoes import Movimentacao


#roteador
router = APIRouter(prefix="/movimentacoes", tags=["Movimentações Processuais"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def listar_movimentacoes(db: Session = Depends(get_db)):
    # Listaos registros da tabela
    movimentacoes = db.query(Movimentacao).all()
    return movimentacoes


@router.get("/{numero_processo}")
def buscar_movimentacoes_por_processo(numero_processo: str, db: Session = Depends(get_db)):
    # Buscaas movimentações de um número de processo específico
    # O .all() pega todas as movimetações atreladas
    movimentacoes_encontradas = db.query(Movimentacao).filter(Movimentacao.numero_processo == numero_processo).all()
    if not movimentacoes_encontradas:
        raise HTTPException(status_code=404, detail="Nenhuma movimentação encontrada para este processo")
       
    return movimentacoes_encontradas

