"""
views/carteira_advogados.py — Carteira por Advogado
Página única que exibe a carga de trabalho de um advogado selecionado,
apresentando totais e a tabela dos 5 processos mais urgentes.
Cores: cinza #44464a | azul petróleo #084d6e
"""

import os
import requests
import streamlit as st
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# ── Configuração de Variáveis de Ambiente e API ──────────────────────────────
pasta_raiz = Path(__file__).resolve().parent.parent.parent
load_dotenv(pasta_raiz / ".env", override=True)

API_URL = os.getenv("API_KEY", "http://127.0.0.1:8000")

# ── Paleta ───────────────────────────────────────────────────────────────────
COR_PRIMARIA   = "#44464a"   # cinza escuro
COR_AMARELO    = "#084d6e"   # amarelo
COR_FUNDO      = "#f5f5f5"
COR_GRADE      = "#ebebeb"

# ── Função de Ligação com o Banco de Dados (API) ─────────────────────────────
def buscar_dados_carteira():
    """Faz a requisição HTTP para a API real e trata os erros."""
    try:
        resposta = requests.get(
            f"{API_URL}/ia/carteira_advogados",
            timeout=10,
        )
        if resposta.status_code == 200:
            return resposta.json().get("carteira", [])
        else:
            st.error(f"Erro na API: Código {resposta.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Falha de conexão: O servidor da API (FastAPI) não está ligado.")
        return None
    except Exception as e:
        st.error(f"Erro inesperado: {e}")
        return None

# ── Componente: Tabela de Prazos ─────────────────────────────────────────────
def _tabela_prazos(prazos: list):
    st.markdown(
        f"<p style='font-weight:700; color:{COR_AMARELO}; font-size:1rem; margin-top: 1rem;'>"
        "Top 5 - Próximos prazos urgentes na carteira:</p>",
        unsafe_allow_html=True,
    )

    if not prazos:
        st.info("Não há prazos urgentes definidos para esta carteira no momento.")
        return

    df = pd.DataFrame(prazos)
    
    if 'data_prazo' in df.columns:
        df['data_prazo'] = pd.to_datetime(df['data_prazo']).dt.strftime('%d/%m/%Y')

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "numero_processo": st.column_config.TextColumn("Processo", width="medium"),
            "nome_cliente":    st.column_config.TextColumn("Cliente", width="medium"),
            "tipo_processo":   st.column_config.TextColumn("Tipo", width="small"),
            "status":          st.column_config.TextColumn("Status", width="small"),
            "data_prazo":      st.column_config.TextColumn("Vencimento", width="small"),
        },
    )

# ── View principal ────────────────────────────────────────────────────────────
def renderizar_tela():
    # ── Carregar dados reais da API ──────────────────────────────────────────
    with st.spinner("A mapear a carteira da equipa no banco de dados..."):
        dados_carteira = buscar_dados_carteira()

    if dados_carteira is None:
        return

    if len(dados_carteira) == 0:
        st.warning("Nenhum dado de carteira encontrado na base.")
        return

    # ── Seletor de Advogado ──────────────────────────────────────────────────
    lista_nomes = [adv.get("nome_advogado") for adv in dados_carteira]
    
    # ── TOPO: Filtro e Métricas (Lado a Lado) ────────────────────────────────
    col_filtro, col_m1, col_m2, col_m3 = st.columns([2, 1, 1, 1])

    with col_filtro:
        st.markdown(
            f"<p style='color:{COR_PRIMARIA}; font-weight:600; margin-top:0.5rem; margin-bottom:0.5rem;'>"
            "Selecione o Advogado Responsável:</p>",
            unsafe_allow_html=True,
        )
        nome_selecionado = st.selectbox(
            label="selecionar_advogado", 
            options=lista_nomes, 
            label_visibility="collapsed"
        )

    advogado_filtrado = next((adv for adv in dados_carteira if adv["nome_advogado"] == nome_selecionado), None)

    # ── Resumo da Carteira (Cards Dinâmicos) ─────────────────────────────────
    if advogado_filtrado:
        tot_trabalhar = advogado_filtrado.get('total_trabalhar', 0)
        ativos = advogado_filtrado.get('ativos', 0)
        recurso = advogado_filtrado.get('em_recurso', 0)
        
        with col_m1:
            st.metric(label="Total a Trabalhar", value=str(tot_trabalhar))
        with col_m2:
            st.metric(label="Ativos", value=str(ativos))
        with col_m3:
            st.metric(label="Em Recurso", value=str(recurso))

        # ── Tabela detalhada ─────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        _tabela_prazos(advogado_filtrado.get("proximos_prazos", []))

if __name__ == "__main__":
    renderizar_tela()