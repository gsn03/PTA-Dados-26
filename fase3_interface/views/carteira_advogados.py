import os
import requests
import pandas as pd
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# 1. Ajuste de Arquitetura (Padrão da equipe)
pasta_raiz = Path(__file__).resolve().parent.parent.parent
load_dotenv(pasta_raiz / ".env", override=True)

API_URL = os.getenv("API_KEY", "http://127.0.0.1:8000")

def buscar_dados_carteira():
    """Busca a carteira de todos os advogados na API (Mantido igual)"""
    url_limpa = API_URL.rstrip("/")
    link_final = f"{url_limpa}/ia/carteira_advogados"
    
    try:
        resposta = requests.get(link_final, timeout=10)
        if resposta.status_code == 200:
            return resposta.json().get("carteira", [])
        else:
            st.error(f"Erro na API: Código {resposta.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Falha de conexão: O servidor FastAPI está ligado?")
        return None

def _renderizar_card_detalhado(advogado):
    """
    Renderiza o corpo do card com os dados do advogado selecionado.
    """
    # Exibe os totais com a mesma identidade do seu rascunho
    st.markdown(f"### **{advogado.get('total_trabalhar', 0)} PROCESSOS A TRABALHAR**")
    st.markdown(f"↳ **{advogado.get('ativos', 0)}** Ativos")
    st.markdown(f"↳ **{advogado.get('em_recurso', 0)}** Em Recurso")
    
    prazos = advogado.get("proximos_prazos", [])
    
    # Tabela com as 5 colunas obrigatórias
    if prazos:
        df_prazos = pd.DataFrame(prazos)
        
        if 'data_prazo' in df_prazos.columns:
            df_prazos['data_prazo'] = pd.to_datetime(df_prazos['data_prazo'], errors='coerce').dt.strftime('%d/%m/%Y')
            
        st.dataframe(
            df_prazos,
            column_config={
                "numero_processo": "Processo",
                "nome_cliente": "Cliente",
                "tipo_processo": "Tipo",
                "status": "Status",
                "data_prazo": "Vencimento"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("Não há prazos urgentes definidos para esta carteira.")

def renderizar_tela():
    """
    Função principal adaptada para Card Único com seletor de Advogado.
    """
    st.header("💼 Carteira por Advogado")
    st.markdown("Selecione o profissional para visualizar o volume de atuação e os próximos 5 prazos urgentes.")

    # Indicador de carregamento
    with st.spinner("Mapeando a carteira da equipe..."):
        dados_carteira = buscar_dados_carteira()

    if dados_carteira is None:
        return 
        
    if len(dados_carteira) == 0:
        st.warning("Nenhum dado de carteira encontrado na base.")
        return

    # --- O PULO DO GATO: SELETOR NO LUGAR DO NOME ---
    # 1. Extraímos apenas os nomes dos advogados para colocar no "botão/seletor"
    lista_nomes = [adv.get("nome_advogado") for adv in dados_carteira]
    
    st.write("---") # Linha divisória para abrir o Card
    
    # Criamos uma linha estilizada para o topo do card
    col_titulo, col_seletor = st.columns([1, 2])
    
    with col_titulo:
        st.markdown("#### 👤 Advogado Responsável:")
    
    with col_seletor:
        # O selectbox substitui o texto estático do nome. 
        # label_visibility="collapsed" esconde o texto "Selecione" e deixa o layout limpo.
        nome_selecionado = st.selectbox(
            "Selecionar Advogado", 
            options=lista_nomes, 
            label_visibility="collapsed"
        )
    
    # 2. Filtramos os dados do advogado que o usuário clicou
    advogado_filtrado = next((adv for adv in dados_carteira if adv["nome_advogado"] == nome_selecionado), None)
    
    # 3. Desenha o card apenas do advogado escolhido
    if advogado_filtrado:
        _renderizar_card_detalhado(advogado_filtrado)
        
    st.write("---") # Linha divisória para fechar o Card

if __name__ == "__main__":
    renderizar_tela()