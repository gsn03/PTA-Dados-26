from fastapi import APIRouter,HTTPException, Depends
from sqlalchemy.orm import Session
import sys
from pathlib import Path

pasta_bd = Path(__file__).parent.parent / "BD"
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from model_Cliente import Cliente

router = APIRouter(prefix="/clientes", tags=["Clientes"])

def get_db(): 
    
    db = SessionLocal()
    
    try:
        yield db
        
    finally:
        db.close()
        
@router.get("/")

def listar_clientes(db: Session = Depends(get_db)):
    Clientes = db.query(Cliente).all()
    return Clientes

@router.get("/{cpf}")
def buscar_cliente_por_cpf(cpf: str, db: Session = Depends(get_db)):
    
    
    cliente_encontrado = db.query(Cliente).filter(Cliente.cpf_cnpj == cpf).first()
    
    
    if not cliente_encontrado:
        raise HTTPException(status_code=404, detail="Cliente não encontrado no banco de dados")
        
    return cliente_encontrado