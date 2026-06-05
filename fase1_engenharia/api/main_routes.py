from fastapi import FastAPI, Depends
from .routes_cliente import router as router_cliente
from .routes_honorarios import router as router_honorarios
from .routes_movimentacoes import router as router_movimentacoes
from .routes_processo import router as router_processo
from .routes_ia import router as router_ia


#recebe a class do fastAPI
app = FastAPI(title="API PTA Dados | Equipe Gustavo")

#Assim que terminatem de fazer a rota, no arquivo routes____.py façam o mesmo que a mesma coisa do router_cliente
app.include_router(router_cliente) #    <------------
app.include_router(router_honorarios)
app.include_router(router_processo)
app.include_router(router_movimentacoes)
app.include_router(router_ia)

