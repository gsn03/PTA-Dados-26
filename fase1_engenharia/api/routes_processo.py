from fastapi import APIRouter
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import sys
from pathlib import Path

# Ajuste de path
pasta_bd = Path(__file__).parent.parent / "BD"
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

# Rota para listar TUDO 
@router.get("/")
def listar_todos_processos(db: Session = Depends(get_db)):
    return db.query(Processo).all()

# Rota para buscar um processo específico pelo número 
@router.get("/{numero_processo}")
def buscar_por_numero(numero_processo: str, db: Session = Depends(get_db)):
    processo = db.query(Processo).filter(Processo.numero_processo == numero_processo).first()
    
    if not processo:
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    
    return processo

# Buscar processos de um cliente específico
@router.get("/cliente/{id_cliente}")
def listar_por_cliente(id_cliente: int, db: Session = Depends(get_db)):
    return db.query(Processo).filter(Processo.cliente_id == id_cliente).all()
