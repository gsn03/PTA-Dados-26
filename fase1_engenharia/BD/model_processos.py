from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from database_model import Base as Base_processo

class Processo(Base_processo):
    __tablename__ = "processos"
    
    # SOLUÇÃO DO CONFLITO: Diz ao SQLAlchemy para reaproveitar o registro se ele já existir na memória
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    arquivo_origem = Column(String, nullable=True) 
    numero_processo = Column(String, nullable=False, unique=False)
    
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    
    tipo_processo = Column(String, nullable=True) 
    fase = Column(String, nullable=True) 
    status = Column(String, nullable=True) 
    nome_advogado = Column(String, nullable=True)
    data_abertura = Column(Date, nullable=True)
    prazo_proximo = Column(Date, nullable=True)
    valor_causa = Column(String, nullable=True)
    vara = Column(String, nullable=True)
    observacoes = Column(Text, nullable=True) 
    
    cliente = relationship("Cliente", backref="processos")