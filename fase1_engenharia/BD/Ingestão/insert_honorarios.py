import sys
from pathlib import Path

#Usa a pasta pra encrontrar os modelos
pasta_bd = Path(__file__).parent.parent
sys.path.append(str(pasta_bd))

#Import do modelo
import json
from database_model import SessionLocal
from model_honorarios import contrato_honorario

def carregamento_honorarios_json(pasta_jsons: Path): #Essa função faz com que os dados do JSON sejam inseridos no SQL
    #Abre a conexão com o banco
    db = SessionLocal()
    try:
        for arquivo in pasta_jsons.glob("*.json"): #Identifica os arquivos .json
            if arquivo.name == "Relatorio_Geral_Contratos.json":
                continue
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if dados.get("tipo_documento") != "contrato_honorarios": #Apenas documentos marcados como honorários
                print(f"Pulei o arquivo {arquivo.name} porque o tipo não bate.")
                continue
            nome_arquivo = dados.get("arquivo_origem")
            if not nome_arquivo:
                continue
            contrato_existente = db.query(contrato_honorario).filter( #O .filter verifica se o arquivo já foi inserido no banco
                contrato_honorario.arquivo_origem == nome_arquivo
            ).first()
            if not contrato_existente: #Se não tiver sido inserido, prossegue:
                novo_contrato = contrato_honorario(
                    arquivo_origem=nome_arquivo,
                    tipo_processo=dados.get("tipo_processo"),
                    contratante=dados.get("contratante"),
                    cpf_cnpj_contratante=dados.get("cpf_cnpj_contratante"),
                    nome_advogado=dados.get("nome_advogado"),
                    oab_advogado=dados.get("oab_advogado"),
                    endereco_encontrado=dados.get("endereco_encontrado"),
                    valor_total=dados.get("valor_total"),
                    honorarios_exito=dados.get("honorarios_exito")
                )
                db.add(novo_contrato)
        #Confirma as inserções
        db.commit()
    except Exception as e:
        #Se tiver falha, as alterações são desfeitas 
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
# Garante o caminho absoluto correto subindo até a raiz do projeto
    raiz_projeto = Path(__file__).resolve().parent.parent.parent.parent
    pasta_jsons_honorarios = raiz_projeto / "data" / "Texto_json" / "honorarios"
# Verifica se a pasta realmente existe no disco
    if not pasta_jsons_honorarios.exists():
        print(f"❌ ERRO: A pasta {pasta_jsons_honorarios} NÃO EXISTE no seu computador!")
    else:
        # Conta quantos arquivos .json existem lá dentro
        arquivos = list(pasta_jsons_honorarios.glob("*.json"))
# Executa a inserção
        carregamento_honorarios_json(pasta_jsons_honorarios)