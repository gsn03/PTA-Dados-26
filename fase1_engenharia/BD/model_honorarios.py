from sqlalchemy import Column, Integer, String
from database_model import Base as base_honorario

class contrato_honorario(base_honorario):
    __tablename__ = "contratos_honorarios"
    id = Column(Integer, primary_key=True, autoincrement=True)
    arquivo_origem = Column(String, nullable=False, unique=True) #O unique=True faz com que a biblioteca não pegue registros do mesmo PDF
    tipo_processo = Column(String, nullable=True)
    contratante = Column(String, nullable=True)
    cpf_cnpj_contratante = Column(String, nullable=True)
    nome_advogado = Column(String, nullable=True)
    oab_advogado = Column(String, nullable=True)
    endereco_encontrado = Column(String, nullable=True)
    #Valores do contrato base
    valor_total = Column(String, nullable=True) #Mantém string para devolver o R$ retirado no PDF
    honorarios_exito = Column(String, nullable=True)
    #Valores dos outros PDFs
    valor_causa = Column(String, nullable=True)
    valor_acordo = Column(String, nullable=True)
    valor_condenacao = Column(String, nullable=True)