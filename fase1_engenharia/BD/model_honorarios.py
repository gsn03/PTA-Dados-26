from sqlalchemy import Column, Integer, String, ForeignKey
from database_model import Base as base_honorario

class contrato_honorario(base_honorario):
    __tablename__ = "contratos_honorarios"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # nullable=True e unique=False
    arquivo_origem = Column(String, nullable=True) 
    
    # Ligando os honorários ao cliente no banco de dados
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    numero_processo = Column(String, nullable=True)
    
    # Campos Antigos (Vindos da Extração JSON) 
    tipo_processo = Column(String, nullable=True)
    contratante = Column(String, nullable=True)
    cpf_cnpj_contratante = Column(String, nullable=True)
    nome_advogado = Column(String, nullable=True)
    oab_advogado = Column(String, nullable=True)
    endereco_encontrado = Column(String, nullable=True)
    valor_total = Column(String, nullable=True) 
    honorarios_exito = Column(String, nullable=True)
    valor_causa = Column(String, nullable=True)
    valor_acordo = Column(String, nullable=True)
    valor_condenacao = Column(String, nullable=True)
    
    #Campos Financeiros (Vindos da Planilha CSV) 
    valor_total_contratado = Column(String, nullable=True)
    n_parcelas = Column(String, nullable=True)
    parcelas_pagas = Column(String, nullable=True)
    valor_pago = Column(String, nullable=True)
    valor_em_aberto = Column(String, nullable=True)
    data_contrato = Column(String, nullable=True)
    data_vencimento = Column(String, nullable=True)
    forma_pagamento = Column(String, nullable=True)
    percentual_exito = Column(String, nullable=True)
    status_pagamento = Column(String, nullable=True)