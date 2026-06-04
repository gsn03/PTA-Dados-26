"""
views/notificador_prazos.py — Notificador de Prazos
Exibe os processos em estado crítico (5 dias) e de atenção (15 dias),
espelhando exatamente os dados enviados pelo relatório matinal via e-mail.
Paleta: cinza #44464a | amarelo #ffcc00 | fundo #f5f5f5
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
COR_PRIMARIA = "#44464a"
COR_AMARELO  = "#ffcc00"
COR_FUNDO    = "#f5f5f5"
COR_GRADE    = "#ebebeb"


# ── Função de Ligação com o Banco de Dados (API) ─────────────────────────────
def _buscar_alertas(dias_exatos: int):
    """Faz a requisição HTTP para a rota /ia/alertas_email e trata os erros."""
    try:
        resposta = requests.get(
            f"{API_URL}/ia/alertas_email",
            params={"dias_exatos": dias_exatos},
            timeout=10,
        )
        if resposta.status_code == 200:
            return resposta.json().get("processos", [])
        else:
            st.error(f"Erro na API: Código {resposta.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Falha de conexão: O servidor da API (FastAPI) não está ligado.")
        return None
    except Exception as e:
        st.error(f"Erro inesperado: {e}")
        return None


# ── Componente: Tabela de Processos ──────────────────────────────────────────
def _tabela_processos(processos: list):
    """Renderiza a tabela de processos com o padrão visual do projeto."""
    if not processos:
        st.info("Nenhum processo encontrado para esta categoria.")
        return

    df = pd.DataFrame(processos)

    if "prazo" in df.columns:
        df["prazo"] = pd.to_datetime(df["prazo"]).dt.strftime("%d/%m/%Y")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "numero_processo": st.column_config.TextColumn("Processo",   width="medium"),
            "nome_cliente":    st.column_config.TextColumn("Cliente",    width="medium"),
            "prazo":           st.column_config.TextColumn("Vencimento", width="small"),
            "fase_atual":      st.column_config.TextColumn("Fase Atual", width="medium"),
        },
    )


# ── View principal ────────────────────────────────────────────────────────────
def renderizar_tela():
    # ── Buscar dados das duas zonas ───────────────────────────────────────────
    with st.spinner("Verificando prazos críticos e de atenção..."):
        processos_perigo  = _buscar_alertas(dias_exatos=5)
        processos_atencao = _buscar_alertas(dias_exatos=15)

    if processos_perigo is None or processos_atencao is None:
        return

    total_perigo = len(processos_perigo)
    total_atencao = len(processos_atencao)

    # ── TOPO: Contexto e Métricas (Lado a Lado) ──────────────────────────────
    col_texto, col_m1, col_m2 = st.columns([2, 1, 1])

    with col_texto:
        st.markdown(
            f"<p style='color:{COR_PRIMARIA}; font-weight:600; margin-top:0.5rem; margin-bottom:0.5rem;'>"
            "Notificador de Prazos 🔔</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='color:#777; margin-bottom:0;'>"
            "Processos em estado crítico e de atenção, conforme o relatório matinal enviado à equipe.</p>",
            unsafe_allow_html=True,
        )

    with col_m1:
        st.metric(label="Zona de Perigo (5 dias)", value=str(total_perigo))

    with col_m2:
        st.metric(label="Zona de Atenção (15 dias)", value=str(total_atencao))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Zona de Perigo (5 dias) ───────────────────────────────────────────────
    st.markdown(
        f"<p style='font-weight:700; color:{COR_PRIMARIA}; font-size:1rem;'>"
        "🔴 Zona de Perigo — Vencimento em 5 dias</p>",
        unsafe_allow_html=True,
    )
    _tabela_processos(processos_perigo)

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # ── Zona de Atenção (15 dias) ─────────────────────────────────────────────
    st.markdown(
        f"<p style='font-weight:700; color:{COR_PRIMARIA}; font-size:1rem;'>"
        "🟡 Zona de Atenção — Vencimento em 15 dias</p>",
        unsafe_allow_html=True,
    )
    _tabela_processos(processos_atencao)

    st.markdown("---")
    st.markdown(
        "<p style='text-align:center; color:#aaa; font-size:0.8rem;'>"
        "Os dados acima espelham exatamente o conteúdo do relatório matinal "
        "enviado por e-mail à equipe.</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    renderizar_tela()