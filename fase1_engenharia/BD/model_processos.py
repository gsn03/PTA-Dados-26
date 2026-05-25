from sqlalchemy import Column, Integer, String, ForeignKey, Date, Numeric, Text
from sqlalchemy.orm import relationship
from database_model import Base as Base_processo

class Processo(Base_processo):
    __tablename__ = "processos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    arquivo_origem = Column(String, nullable=False, unique=True)
    numero_processo = Column(String, nullable=False, unique=True)
    # Chave Estrangeira: liga o processo a um cliente existente
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    # Metadados para filtros do RAG
    tipo_processo = Column(String, nullable=True) # Ex: Cível, Trabalhista
    fase = Column(String, nullable=True) # Ex: Inicial, Recurso, Execução
    status = Column(String, nullable=True) # Ex: Ativo, Suspenso
    nome_advogado = Column(String, nullable=True)
    # Datas: Essenciais para as automações do LangGraph proativo
    data_abertura = Column(Date, nullable=True)
    prazo_proximo = Column(Date, nullable=True)
    # Numeric em vez de String para permitir somas e filtros de valor
    valor_causa = Column(Numeric(12, 2), nullable=True)
    vara = Column(String, nullable=True)
    observacoes = Column(Text, nullable=True) # Text permite textos longos sem limite fixo
    cliente = relationship("Cliente", backref="processos") # Opcional: Cria uma relação facilitada para acessar os dados do cliente direto pelo objeto processo