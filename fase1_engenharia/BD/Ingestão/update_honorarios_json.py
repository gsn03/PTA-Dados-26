import sys
from pathlib import Path
import json

# 1. Ajuste de caminhos no topo
pasta_bd = Path(__file__).resolve().parent.parent
sys.path.append(str(pasta_bd))

from database_model import SessionLocal
from model_honorarios import contrato_honorario
from model_Cliente import Cliente

def limpar_valor_monetario(valor):
    if valor is None or valor == "": return None
    if isinstance(valor, (int, float)): return str(valor)
    valor_limpo = str(valor).replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return str(float(valor_limpo))
    except ValueError:
        return None

def enriquecer_honorarios_json(pasta_jsons: Path):
    db = SessionLocal()
    
    try:
        print("A iniciar a varredura de JSONs para enriquecer Honorários...")
        honorarios_atualizados = 0
        honorarios_inseridos = 0
        
        for arquivo in pasta_jsons.rglob("*.json"): 
            if "Relatorio" in arquivo.name:
                continue
                
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
            
            # Chaves de identificação
            cpf_extraido = dados.get("cpf_cnpj") or dados.get("cpf_cnpj_contratante")
            nome_extraido = dados.get("nome_cliente") or dados.get("contratante") or dados.get("autor") or dados.get("reclamante")
            num_proc = dados.get("numero_processo") or dados.get("processo") or dados.get("n_processo")
            
            if not cpf_extraido and not nome_extraido and not num_proc:
                continue
            
            # Valores a enriquecer (o ouro extraído dos PDFs)
            arq_origem = dados.get("arquivo_origem") or arquivo.name
            val_causa = limpar_valor_monetario(dados.get("valor_causa"))
            val_acordo = limpar_valor_monetario(dados.get("valor_acordo") or dados.get("valor_total_acordo"))
            val_condenacao = limpar_valor_monetario(dados.get("valor_condenacao") or dados.get("valor_total_condenacao"))
            oab = dados.get("oab_advogado") or dados.get("oab")
            
            # 1. Tentar encontrar o Cliente
            cliente_db = None
            if cpf_extraido:
                cliente_db = db.query(Cliente).filter(Cliente.cpf_cnpj == cpf_extraido).first()
            if not cliente_db and nome_extraido:
                cliente_db = db.query(Cliente).filter(Cliente.nome.ilike(f"%{nome_extraido}%")).first()

            # 2. Tentar encontrar o Contrato no banco de dados
            contrato_existente = None
            if num_proc:
                contrato_existente = db.query(contrato_honorario).filter(contrato_honorario.numero_processo == num_proc).first()
            
            # Se não encontrou pelo processo, mas encontrou o cliente, verifica se o cliente só tem 1 contrato ativo
            if not contrato_existente and cliente_db:
                contratos_do_cliente = db.query(contrato_honorario).filter(contrato_honorario.cliente_id == cliente_db.id).all()
                if len(contratos_do_cliente) == 1:
                    contrato_existente = contratos_do_cliente[0]
            
            if contrato_existente:
                # SMART UPDATE: Preenche apenas os espaços em branco
                atualizou = False
                if not contrato_existente.arquivo_origem and arq_origem:
                    contrato_existente.arquivo_origem = arq_origem
                    atualizou = True
                if not contrato_existente.valor_causa and val_causa:
                    contrato_existente.valor_causa = val_causa
                    atualizou = True
                if not contrato_existente.valor_acordo and val_acordo:
                    contrato_existente.valor_acordo = val_acordo
                    atualizou = True
                if not contrato_existente.valor_condenacao and val_condenacao:
                    contrato_existente.valor_condenacao = val_condenacao
                    atualizou = True
                if not contrato_existente.oab_advogado and oab:
                    contrato_existente.oab_advogado = oab
                    atualizou = True
                    
                if atualizou:
                    honorarios_atualizados += 1
            else:
                # INSERT: Se encontrou um acordo/condenação num JSON que não estava na planilha
                if cliente_db:
                    novo_honorario = contrato_honorario(
                        arquivo_origem=arq_origem,
                        cliente_id=cliente_db.id,
                        numero_processo=num_proc,
                        tipo_processo=dados.get("tipo_processo"),
                        nome_advogado=dados.get("nome_advogado") or dados.get("advogado"),
                        oab_advogado=oab,
                        valor_causa=val_causa,
                        valor_acordo=val_acordo,
                        valor_condenacao=val_condenacao
                    )
                    db.add(novo_honorario)
                    db.commit()
                    honorarios_inseridos += 1

        db.commit()
        print("\n--- RESUMO DO ENRIQUECIMENTO DE HONORÁRIOS ---")
        print(f"Contratos atualizados (valores de PDFs injetados): {honorarios_atualizados}")
        print(f"Novos contratos descobertos e inseridos: {honorarios_inseridos}")
        
    except Exception as e:
        db.rollback()
        print(f"Erro crítico no enriquecimento de honorários: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    raiz_projeto = Path(__file__).resolve().parent.parent.parent.parent
    pasta_jsons_principal = raiz_projeto / "data" / "Texto_json"
    
    if not pasta_jsons_principal.exists():
        print(f"A pasta {pasta_jsons_principal} não existe")
    else:
        enriquecer_honorarios_json(pasta_jsons_principal)