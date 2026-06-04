"""
views/status_vertente.py — Status dos Processos por Vertente
Paleta da interface: cinza #44464a | azul petróleo #084d6e
"""

import os
import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

pasta_raiz = Path(__file__).resolve().parent.parent.parent
load_dotenv(pasta_raiz / ".env", override=True)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# ── Paleta ────────────────────────────────────────────────────────────────────
COR_PRIMARIA   = "#44464a"
COR_AMARELO    = "#084d6e"
COR_FUNDO_PLOT = "#ffffff"
COR_GRADE      = "#ebebeb"

# Tons de cinza para barras agrupadas por status
PALETA_CINZAS = [
    "#44464a",   # cinza escuro (principal)
    "#6b6d72",   # cinza médio
    "#9a9b9f",   # cinza claro
    "#c4c5c8",   # cinza muito claro
    "#084d6e",   # azul petróleo (destaque extra)
]


def buscar_dados_status_vertente():
    url_limpa = API_URL.rstrip("/")
    link_final = f"{url_limpa}/ia/status_vertente"

    try:
        resposta = requests.get(link_final, timeout=10)
        if resposta.status_code == 200:
            return resposta.json().get("dados_status_vertente", [])
        else:
            st.error(f"Erro na API: Código {resposta.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Falha de conexão com a API.")
        return None


def renderizar_tela():
    st.markdown(
        f"<h2 style='text-align:center; color:{COR_PRIMARIA};'>"
        "Status dos Processos por Vertente ⚖️</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:#777;'>"
        "Distribuição do volume de processos (Ativos, Encerrados, etc.) "
        "divididos por área de atuação.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    with st.spinner("Buscando dados no banco..."):
        dados = buscar_dados_status_vertente()

    if dados is None:
        return

    if len(dados) == 0:
        st.warning("Não existem processos cadastrados para análise.")
        return

    df = pd.DataFrame(dados)

    df["vertente"] = df["vertente"].astype(str).str.upper()
    df = df[~df["vertente"].isin(["NÃO INFORMADO", "NAO INFORMADO"])]
    df["vertente"] = df["vertente"].replace({"CÍVEL": "CIVIL"})
    df = df.groupby(["vertente", "status"], as_index=False)["quantidade"].sum()

    # ── Filtros ───────────────────────────────────────────────────────────────
    st.markdown(
        f"<p style='color:{COR_PRIMARIA}; font-weight:600; font-size:0.95rem;'>"
        "🔍 Filtros de Análise</p>",
        unsafe_allow_html=True,
    )
    col_f1, col_f2 = st.columns(2)

    opcoes_vertentes = df["vertente"].unique().tolist()
    opcoes_status    = df["status"].unique().tolist()

    with col_f1:
        vertentes_selecionadas = st.multiselect(
            "Área(s) de Atuação:",
            options=opcoes_vertentes,
            default=opcoes_vertentes,
        )
    with col_f2:
        status_selecionados = st.multiselect(
            "Status:",
            options=opcoes_status,
            default=opcoes_status,
        )

    df_filtrado = df[
        (df["vertente"].isin(vertentes_selecionadas)) &
        (df["status"].isin(status_selecionados))
    ]

    if df_filtrado.empty:
        st.info("Nenhum dado encontrado para os filtros selecionados.")
        return

    st.markdown("---")
    st.markdown(
        f"<p style='color:{COR_PRIMARIA}; font-weight:700;'>"
        f"Total de cruzamentos encontrados: "
        f"<span style='color:{COR_AMARELO};'>{len(df_filtrado)}</span></p>",
        unsafe_allow_html=True,
    )

    # ── Gráfico de barras agrupadas na paleta cinza/amarelo ───────────────────
    vertentes = df_filtrado["vertente"].unique().tolist()
    status_list = df_filtrado["status"].unique().tolist()

    fig = go.Figure()

    for i, status in enumerate(status_list):
        df_s = df_filtrado[df_filtrado["status"] == status]
        cor = PALETA_CINZAS[i % len(PALETA_CINZAS)]

        fig.add_trace(
            go.Bar(
                name=status,
                x=df_s["vertente"],
                y=df_s["quantidade"],
                marker_color=cor,
                text=df_s["quantidade"],
                textposition="outside",
                textfont=dict(color=COR_PRIMARIA, size=12),
            )
        )

    fig.update_layout(
        barmode="group",
        title=dict(
            text="<b>Volume de Processos por Área e Status</b>",
            font=dict(color=COR_AMARELO, size=15),
            x=0,
        ),
        plot_bgcolor=COR_FUNDO_PLOT,
        paper_bgcolor=COR_FUNDO_PLOT,
        xaxis=dict(
            title="Área de Atuação",
            tickfont=dict(color=COR_PRIMARIA),
            gridcolor=COR_GRADE,
        ),
        yaxis=dict(
            title="Nº de Processos",
            tickfont=dict(color=COR_PRIMARIA),
            gridcolor=COR_GRADE,
            showgrid=True,
        ),
        legend=dict(
            font=dict(color=COR_PRIMARIA, size=11),
            title_text="Status",
            title_font_color=COR_PRIMARIA,
        ),
        margin=dict(l=10, r=10, t=55, b=30),
        height=380,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

    # ── Tabela de detalhamento ────────────────────────────────────────────────
    st.markdown(
        f"<p style='font-weight:700; color:{COR_AMARELO}; font-size:1rem;'>"
        "Detalhamento</p>",
        unsafe_allow_html=True,
    )
    st.dataframe(
        df_filtrado,
        column_config={
            "vertente":   "Vertente Jurídica",
            "status":     "Situação",
            "quantidade": st.column_config.NumberColumn("Volume", format="%d"),
        },
        hide_index=True,
        use_container_width=True,
    )


if __name__ == "__main__":
    renderizar_tela()
