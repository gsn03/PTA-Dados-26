from sqlalchemy import Column, Integer, String
from database_model import Base as Base_cliente

class Cliente(Base_cliente):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    cpf_cnpj = Column(String, nullable=True, unique=True)
    
    # Campos Antigos (Vindos da Extração JSON) -
    nacionalidade = Column(String, nullable=True)
    estado_civil = Column(String, nullable=True)
    ocupacao = Column(String, nullable=True)
    endereco_completo = Column(String, nullable=True)
    
    # Campos (Vindos da Planilha CSV)
    contato = Column(String, nullable=True)
    email = Column(String, nullable=True)
    data_inicio = Column(String, nullable=True)
    cidade = Column(String, nullable=True)
    
    
# --- COMANDOS DO ALEMBIC (Para o futuro, quando precisarmos alterar tabelas prontas) ---
# 1. Inicializar o Alembic no projeto (Roda só uma vez na vida):
# alembic init alembic
#
# 2. Gerar o script de atualização após mudar o model_Cliente.py:
# alembic revision --autogenerate -m "Adiciona coluna telefone na tabela clientes"
#
# 3. Aplicar a mudança no banco de dados físico:
# alembic upgrade head

#deixando guarado essas infos