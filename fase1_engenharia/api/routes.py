from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import sys
from pathlib import Path

pasta_bd = Path(__file__).parent.parent / "BD"
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from model_Cliente import Cliente

#recebe a class do fastAPI
app = FastAPI()

def get_db(): 
    
    db = SessionLocal()
    
    try:
        yield db
        
    finally:
        db.close()
        
@app.get("/clientes")

def listar_clientes(db: Session = Depends(get_db)):
    Clientes = db.query(Cliente).all()
    return Clientes
