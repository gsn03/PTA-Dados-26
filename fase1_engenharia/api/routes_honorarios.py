from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import sys
from pathlib import Path

#Vai até a pasta do banco
pasta_bd = Path(__file__).parent.parent / "BD"
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from model_honorarios import contrato_honorario

router = APIRouter(prefix="/honorarios", tags=["Contratos de Honorários"])

def get_db(): 
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def listar_honorarios(db: Session = Depends(get_db)):
    # Lista todos os registros da tabela
    honorarios = db.query(contrato_honorario).all()
    return honorarios

@router.get("/{cpf}")
def buscar_honorario_por_cpf(cpf: str, db: Session = Depends(get_db)):
    # Busca contrato específico usando CPF/CNPJ do contratante
    honorario_encontrado = db.query(contrato_honorario).filter(contrato_honorario.cpf_cnpj_contratante == cpf).first()
    
    if not honorario_encontrado:
        raise HTTPException(status_code=404, detail="Contrato/Honorário não encontrado no banco de dados")
        
    return honorario_encontrado
