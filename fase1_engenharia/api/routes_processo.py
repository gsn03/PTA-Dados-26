import sys
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Ajuste de caminhos para encontrar os módulos do banco
pasta_bd = Path(__file__).parent.parent
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from model_processos import Processo

router = APIRouter(prefix="/processos", tags=["Processos"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def listar_processos(db: Session = Depends(get_db)):
    processos = db.query(Processo).all()
    return processos

@router.get("/{numero_cnj}")
def buscar_processo_por_cnj(numero_cnj: str, db: Session = Depends(get_db)):
    processo_encontrado = db.query(Processo).filter(Processo.numero_cnj == numero_cnj).first()
    
    if not processo_encontrado:
        raise HTTPException(status_code=404, detail="Processo não encontrado no banco de dados")
        
    return processo_encontrado