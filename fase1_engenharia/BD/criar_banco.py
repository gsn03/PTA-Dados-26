from database_model import engine, Base
import model_Cliente 
#coloquem os modelos aqui. Sigam o exemplo do import model_Cliente


#Executa a criação das tabelas
Base.metadata.create_all(bind=engine)
