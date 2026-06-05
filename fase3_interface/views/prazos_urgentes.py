"""
views/prazos_urgentes.py — Sobrecarga de Prazos por Responsável
Página única (sem abas) com gráfico de barras horizontais e timeline.
Pizza (gráfico_fases) removida conforme solicitação.
Cores: cinza #44464a | azul petróleo #084d6e
"""

import os
import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from dotenv import load_dotenv

# ── Configuração de Variáveis de Ambiente e API ──────────────────────────────
pasta_raiz = Path(__file__).resolve().parent.parent.parent
load_dotenv(pasta_raiz / ".env", override=True)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# ── Paleta ───────────────────────────────────────────────────────────────────
COR_PRIMARIA   = "#44464a"   # cinza escuro
COR_AMARELO    = "#084d6e"   # azul petróleo (mantido o nome da variável original)
COR_FUNDO      = "#f5f5f5"
COR_FUNDO_PLOT = "#ffffff"
COR_GRADE      = "#ebebeb"

# ── Função de Ligação com o Banco de Dados (API) ─────────────────────────────
def buscar_dados_prazos(dias: int):
    """Faz a requisição HTTP para a API real e trata os erros."""
    try:
        resposta = requests.get(
            f"{API_URL}/ia/prazos_urgentes",
            params={"dias": dias},
            timeout=60,
        )
        if resposta.status_code == 200:
            return resposta.json().get("processos_urgentes", [])
        else:
            st.error(f"Erro na API: Código {resposta.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Falha de conexão: O servidor da API (FastAPI) não está ligado.")
        return None
    except Exception as e:
        st.error(f"Erro inesperado: {e}")
        return None


# ── Gráfico de barras horizontais: volume por advogado ───────────────────────
def _grafico_volume_advogado(df: pd.DataFrame):
    contagem = (
        df.groupby("Responsável")
        .size()
        .reset_index(name="Quantidade")
        .sort_values("Quantidade", ascending=True)
    )

    fig = go.Figure(
        go.Bar(
            y=contagem["Responsável"],
            x=contagem["Quantidade"],
            orientation="h",
            marker=dict(
                color=COR_PRIMARIA,
                line=dict(color=COR_PRIMARIA, width=0),
            ),
            text=contagem["Quantidade"],
            textposition="outside",
            textfont=dict(color=COR_PRIMARIA, size=13),
        )
    )

    fig.update_layout(
        title=dict(
            text="<b>Volumes de prazos urgentes por Advogado</b>",
            font=dict(color=COR_AMARELO, size=15),
            x=0,
        ),
        plot_bgcolor=COR_FUNDO_PLOT,
        paper_bgcolor=COR_FUNDO_PLOT,
        xaxis=dict(
            gridcolor=COR_GRADE,
            zerolinecolor=COR_GRADE,
            tickfont=dict(color=COR_PRIMARIA),
        ),
        yaxis=dict(
            tickfont=dict(color=COR_PRIMARIA),
            automargin=True,
        ),
        margin=dict(l=10, r=40, t=50, b=20),
        height=320,
    )

    return fig


# ── Gráfico de linha: prazos por dia de vencimento ───────────────────────────
def _grafico_timeline(df: pd.DataFrame):
    df_copia = df.copy()
    df_copia["Data"] = pd.to_datetime(df_copia["Vencimento"], format="%d/%m/%Y")
    por_dia = (
        df_copia.groupby("Data")
        .size()
        .reset_index(name="Quantidade")
        .sort_values("Data")
    )

    fig = go.Figure(
        go.Scatter(
            x=por_dia["Data"],
            y=por_dia["Quantidade"],
            mode="lines+markers",
            line=dict(color=COR_PRIMARIA, width=2.5),
            marker=dict(
                color=COR_AMARELO,
                size=8,
                line=dict(color=COR_PRIMARIA, width=1.5),
            ),
            fill="tozeroy",
            fillcolor="rgba(68,70,74,0.08)",
        )
    )

    fig.update_layout(
        title=dict(
            text="<b>Prazos por Data de Vencimento</b>",
            font=dict(color=COR_AMARELO, size=15),
            x=0,
        ),
        plot_bgcolor=COR_FUNDO_PLOT,
        paper_bgcolor=COR_FUNDO_PLOT,
        xaxis=dict(
            gridcolor=COR_GRADE,
            tickfont=dict(color=COR_PRIMARIA),
            tickformat="%d/%m",
        ),
        yaxis=dict(
            gridcolor=COR_GRADE,
            tickfont=dict(color=COR_PRIMARIA),
        ),
        margin=dict(l=10, r=10, t=50, b=20),
        height=320, # Ajustado para alinhar visualmente com o gráfico de barras
    )

    return fig


# ── Tabela detalhada ──────────────────────────────────────────────────────────
def _tabela_detalhada(df: pd.DataFrame):
    st.markdown(
        f"<p style='font-weight:700; color:{COR_AMARELO}; font-size:1rem; margin-top: 1rem;'>"
        "Detalhamento individual dos processos urgentes:</p>",
        unsafe_allow_html=True,
    )

    colunas_exibir = ["Responsável", "Vencimento", "Processo", "Cliente", "Fase Atual"]
    df_exib = df[colunas_exibir].reset_index(drop=True)

    st.dataframe(
        df_exib,
        use_container_width=True,
        height=280,
        hide_index=True,
        column_config={
            "Responsável": st.column_config.TextColumn("Responsável", width="medium"),
            "Vencimento":  st.column_config.TextColumn("Vencimento",  width="small"),
            "Processo":    st.column_config.TextColumn("Processo",    width="large"),
            "Cliente":     st.column_config.TextColumn("Cliente",     width="medium"),
            "Fase Atual":  st.column_config.TextColumn("Fase Atual",  width="medium"),
        },
    )


# ── View principal ────────────────────────────────────────────────────────────
def render():
    # Carregar dados com uma janela inicial para evitar que a interface quebre antes do slider
    janela = 7

    # ── TOPO: Filtro e Métrica (Lado a Lado) ─────────────────────────────────
    col_filtro, col_metrica = st.columns([2, 1])

    with col_filtro:
        st.markdown(
            f"<p style='color:{COR_PRIMARIA}; font-weight:600; margin-top:0.5rem;'>"
            "Analisar prazos para os próximos (dias):</p>",
            unsafe_allow_html=True,
        )
        janela = st.slider(
            label="janela_dias",
            min_value=1,
            max_value=90,
            value=7,
            step=1,
            label_visibility="collapsed",
        )

    # Carregar dados
    with st.spinner("A consultar os prazos processuais no banco de dados..."):
        dados_prazos = buscar_dados_prazos(dias=janela)

    if dados_prazos is None:
        return

    if len(dados_prazos) == 0:
        st.success(f"Excelente notícia! Não há prazos urgentes para os próximos {janela} dias.")
        return

    # Tratamento de dados
    df = pd.DataFrame(dados_prazos)
    df.rename(columns={
        "advogado":        "Responsável",
        "prazo":           "Vencimento",
        "numero_processo": "Processo",
        "nome_cliente":    "Cliente",
        "fase_atual":      "Fase Atual",
    }, inplace=True)

    df["Responsável"] = df["Responsável"].fillna("Não Atribuído")
    df["Vencimento"]  = pd.to_datetime(df["Vencimento"]).dt.strftime("%d/%m/%Y")
    total = len(df)

    with col_metrica:
        st.metric(label="Total de Prazos na Janela Selecionada", value=str(total))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── CORPO: Gráficos (Lado a Lado) ────────────────────────────────────────
    col_grafico1, col_grafico2 = st.columns(2)

    with col_grafico1:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.plotly_chart(
            _grafico_volume_advogado(df),
            use_container_width=True,
            config={"displaylogo": False},
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_grafico2:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.plotly_chart(
            _grafico_timeline(df),
            use_container_width=True,
            config={"displaylogo": False},
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Tabela detalhada no fundo ─────────────────────────────────────────────
    _tabela_detalhada(df)
