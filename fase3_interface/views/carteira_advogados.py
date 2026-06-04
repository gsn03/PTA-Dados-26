"""
views/carteira_advogados.py — Carteira por Advogado
Página única que exibe a carga de trabalho de um advogado selecionado,
apresentando totais e a tabela dos 5 processos mais urgentes.
Cores: cinza #44464a | amarelo #ffcc00
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
COR_AMARELO    = "#ffcc00"   # amarelo
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
    # Ícone de balança do título (Mesmo padrão do prazos_urgentes)
    balanca_path = Path(__file__).resolve().parent.parent / "assets" / "balanca.png"

    col_t1, col_t2, col_t3 = st.columns([3, 1, 3])
    with col_t2:
        if balanca_path.exists():
            st.image(str(balanca_path), width=40)

    st.markdown(
        f"<h2 style='text-align:center; color:{COR_PRIMARIA}; margin-top:-2rem;'>"
        "Carteira por Advogado</h2>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

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
    
    st.markdown(
        f"<p style='color:{COR_PRIMARIA}; font-weight:600;'>"
        "Selecione o Advogado Responsável:</p>",
        unsafe_allow_html=True,
    )
    
    nome_selecionado = st.selectbox(
        label="selecionar_advogado", 
        options=lista_nomes, 
        label_visibility="collapsed"
    )

    advogado_filtrado = next((adv for adv in dados_carteira if adv["nome_advogado"] == nome_selecionado), None)

    # ── Resumo da Carteira (Card Dinâmico) ───────────────────────────────────
    if advogado_filtrado:
        st.markdown("<br>", unsafe_allow_html=True)
        
        tot_trabalhar = advogado_filtrado.get('total_trabalhar', 0)
        ativos = advogado_filtrado.get('ativos', 0)
        recurso = advogado_filtrado.get('em_recurso', 0)
        
        # Formatando os números com o estilo visual do projeto
        st.markdown(
            f"<h3 style='color:{COR_PRIMARIA}; margin-bottom: 0.5rem;'>"
            f"Total a Trabalhar: <span style='color:{COR_AMARELO};'>{tot_trabalhar} processos</span></h3>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='font-size:1.05rem; color:{COR_PRIMARIA}; margin-left: 1rem; margin-bottom: 0;'>"
            f"↳ <b>{ativos}</b> Ativos</p>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='font-size:1.05rem; color:{COR_PRIMARIA}; margin-left: 1rem; margin-bottom: 1.5rem;'>"
            f"↳ <b>{recurso}</b> Em Recurso</p>",
            unsafe_allow_html=True
        )

        # ── Tabela detalhada ──────────────────────────────────────────────────────
        _tabela_prazos(advogado_filtrado.get("proximos_prazos", []))
        
        st.markdown("---")

if __name__ == "__main__":
    renderizar_tela()