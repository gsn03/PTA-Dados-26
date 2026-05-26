import sys
from pathlib import Path
import json

# 1. Ajuste de caminhos no topo
pasta_bd = Path(__file__).parent.parent
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from model_honorarios import contrato_honorario

def carregar_honorarios_json(pasta_jsons: Path):
    db = SessionLocal()
    
    try:
        # Usa rglob para varrer Contratos, Petições, Acordos e Intimações
        for arquivo in pasta_jsons.rglob("*.json"): 
            if "Relatorio" in arquivo.name:
                continue
                
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
            
            # 2. Mapeamento Inteligente: Chaves antigas vs padronizadas
            cpf_extraido = dados.get("cpf_cnpj") or dados.get("cpf_cnpj_contratante")
            nome_extraido = dados.get("nome_cliente") or dados.get("contratante") or dados.get("acusando_autor") or dados.get("reclamante")
            
            # Se o documento não tiver CPF nem Nome, não conseguimos vincular
            if not cpf_extraido and not nome_extraido:
                continue

            # Unifica outras informações
            endereco_extraido = dados.get("endereco_completo") or dados.get("endereco_encontrado")
            oab_extraida = dados.get("oab_advogado") or dados.get("oab_advogado_reu")
            adv_extraido = dados.get("nome_advogado") or dados.get("advogado")

            # Mapeia os valores dependendo do tipo de documento
            valor_causa = dados.get("valor_causa")
            valor_acordo = dados.get("valor_total_acordo") or dados.get("valor_acordo")
            
            valores_cond_bruto = dados.get("valores_condenacao") or dados.get("valor_condenacao")
            valor_cond_tratado = " | ".join(valores_cond_bruto) if isinstance(valores_cond_bruto, list) else valores_cond_bruto

            # 3. Procura se o contrato já existe na base (por CPF ou Nome)
            contrato_existente = None
            if cpf_extraido:
                contrato_existente = db.query(contrato_honorario).filter(contrato_honorario.cpf_cnpj_contratante == cpf_extraido).first()
            if not contrato_existente and nome_extraido:
                contrato_existente = db.query(contrato_honorario).filter(contrato_honorario.contratante.ilike(f"%{nome_extraido}%")).first()

            if not contrato_existente:
                # SÓ cria uma nova linha na tabela se o ficheiro lido for efetivamente um contrato.
                # (Isso impede que uma petição crie um contrato fantasma vazio)
                if dados.get("tipo_documento") == "contrato_honorarios":
                    novo_contrato = contrato_honorario(
                        arquivo_origem=dados.get("arquivo_origem"),
                        tipo_processo=dados.get("tipo_processo"),
                        contratante=nome_extraido,
                        cpf_cnpj_contratante=cpf_extraido,
                        nome_advogado=adv_extraido,
                        oab_advogado=oab_extraida,
                        endereco_encontrado=endereco_extraido,
                        valor_total=dados.get("valor_total_honorarios") or dados.get("valor_total"),
                        honorarios_exito=dados.get("honorarios_exito"),
                        valor_causa=valor_causa,
                        valor_acordo=valor_acordo,
                        valor_condenacao=valor_cond_tratado
                    )
                    db.add(novo_contrato)
            else:
                # 4. SMART UPDATE: Se o contrato já existe, atualizamos a linha com os valores dos outros processos!
                if not contrato_existente.valor_causa and valor_causa:
                    contrato_existente.valor_causa = valor_causa
                if not contrato_existente.valor_acordo and valor_acordo:
                    contrato_existente.valor_acordo = valor_acordo
                if not contrato_existente.valor_condenacao and valor_cond_tratado:
                    contrato_existente.valor_condenacao = valor_cond_tratado
                
                # Conserta dados de qualificação caso o contrato inicial estivesse incompleto
                if not contrato_existente.cpf_cnpj_contratante and cpf_extraido:
                    contrato_existente.cpf_cnpj_contratante = cpf_extraido
                if not contrato_existente.endereco_encontrado and endereco_extraido:
                    contrato_existente.endereco_encontrado = endereco_extraido

        db.commit()
        print("Ingestão de HONORÁRIOS concluída com sucesso!")
        
    except Exception as e:
        db.rollback()
        print(f"Erro crítico na ingestão de honorários: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    raiz_projeto = Path(__file__).resolve().parent.parent.parent.parent
    pasta_jsons_principal = raiz_projeto / "data" / "Texto_json"
    
    if not pasta_jsons_principal.exists():
        print(f"A pasta {pasta_jsons_principal} não existe")
    else:
        carregar_honorarios_json(pasta_jsons_principal)