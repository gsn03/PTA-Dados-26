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
    # ── Título ────────────────────────────────────────────────────────────────
    balanca_path = Path(__file__).resolve().parent.parent / "assets" / "balanca.png"

    col_t1, col_t2, col_t3 = st.columns([3, 1, 3])
    with col_t2:
        if balanca_path.exists():
            st.image(str(balanca_path), width=40)

    st.markdown(
        f"<h2 style='text-align:center; color:{COR_PRIMARIA}; margin-top:-2rem;'>"
        "Notificador de Prazos 🔔</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:#777;'>"
        "Processos em estado crítico e de atenção, "
        "conforme o relatório matinal enviado à equipe.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # ── Buscar dados das duas zonas ───────────────────────────────────────────
    with st.spinner("Verificando prazos críticos e de atenção..."):
        processos_perigo  = _buscar_alertas(dias_exatos=5)
        processos_atencao = _buscar_alertas(dias_exatos=15)

    if processos_perigo is None or processos_atencao is None:
        return

    # ── Zona de Perigo (5 dias) ───────────────────────────────────────────────
    total_perigo = len(processos_perigo)
    st.markdown(
        f"<h3 style='color:{COR_PRIMARIA};'>"
        f"🔴 Zona de Perigo — Vencimento em 5 dias "
        f"<span style='color:{COR_AMARELO}; font-size:1rem;'>"
        f"({total_perigo} processo(s))</span></h3>",
        unsafe_allow_html=True,
    )
    _tabela_processos(processos_perigo)

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # ── Zona de Atenção (15 dias) ─────────────────────────────────────────────
    total_atencao = len(processos_atencao)
    st.markdown(
        f"<h3 style='color:{COR_PRIMARIA};'>"
        f"🟡 Zona de Atenção — Vencimento em 15 dias "
        f"<span style='color:{COR_AMARELO}; font-size:1rem;'>"
        f"({total_atencao} processo(s))</span></h3>",
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