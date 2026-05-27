from sqlalchemy import Column, Integer, String
from database_model import Base as Base_movimentacoes

class Movimentacao(Base_movimentacoes):
    __tablename__ = "movimentacoes"
   
    id = Column(Integer, primary_key=True, autoincrement=True)
    
  
    arquivo_origem = Column(String, nullable=True)
    numero_processo = Column(String, nullable=True)
    
    # Campos Vindos da Extração JSOns
    cliente = Column(String, nullable=True)
    advogado = Column(String, nullable=True)
    tipo_movimentacao = Column(String, nullable=True)
    data_movimentacao = Column(String, nullable=True)
    orgao_julgador = Column(String, nullable=True)
    resumo_descricao = Column(String, nullable=True)
    
    #  Campos Vindos da Planilha CSV
    tipo_ato = Column(String, nullable=True)
    advogado_responsavel = Column(String, nullable=True)
    descricao = Column(String, nullable=True)
    prazo_gerado = Column(String, nullable=True)
    concluido = Column(String, nullable=True)
    prazo_final = Column(String, nullable=True)
    dias_prazo = Column(String, nullable=True)