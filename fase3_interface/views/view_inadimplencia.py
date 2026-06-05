"""
views/view_inadimplencia.py — Risco de Carteira e Inadimplência
Paleta da interface: cinza #44464a | azul petróleo #084d6e
"""

import os
import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

pasta_raiz = Path(__file__).resolve().parent.parent.parent
load_dotenv(pasta_raiz / ".env", override=True)

API_URL = os.getenv("API_KEY", "http://127.0.0.1:8000")

# ── Paleta ────────────────────────────────────────────────────────────────────
COR_PRIMARIA   = "#44464a"
COR_AMARELO    = "#084d6e"
COR_FUNDO_PLOT = "#ffffff"
COR_GRADE      = "#ebebeb"

# Faixas de atraso em tons de cinza escalonados (mais escuro = mais grave)
MAPA_CORES = {
    "1 a 30 dias":  "#9a9b9f",   # cinza claro — menor risco
    "31 a 60 dias": "#6b6d72",   # cinza médio
    "61 a 90 dias": "#44464a",   # cinza escuro
    "> 90 dias":    "#6f0d0d",   # vermelho — alerta máximo
}


def buscar_dados_inadimplencia():
    url_limpa  = API_URL.rstrip("/")
    link_final = f"{url_limpa}/ia/inadimplencia"

    print(f"\n[DIAGNÓSTICO] O Streamlit está chamando: {link_final}\n")

    try:
        resposta = requests.get(link_final, timeout=60)
        if resposta.status_code == 200:
            return resposta.json().get("detalhamento", [])
        else:
            st.error(f"Erro na API: Código {resposta.status_code} ao acessar {link_final}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(f"Falha de conexão ao tentar acessar: {link_final}")
        return None


def renderizar_tela():
    # ── Busca e Tratamento de Dados ───────────────────────────────────────────
    with st.spinner("Processando dados financeiros..."):
        dados_brutos = buscar_dados_inadimplencia()

    if dados_brutos is None:
        return

    if len(dados_brutos) == 0:
        st.success("Excelente notícia! Não há honorários em atraso neste momento.")
        return

    df_bruto = pd.DataFrame(dados_brutos)

    # Filtrar apenas status "atrasado"
    if "status_pagamento" in df_bruto.columns:
        df_bruto = df_bruto[df_bruto["status_pagamento"].str.lower() == "atrasado"]

    df_bruto["valor_em_aberto"] = (
        pd.to_numeric(df_bruto["valor_em_aberto"], errors="coerce").fillna(0.0)
    )
    df_bruto = df_bruto[df_bruto["valor_em_aberto"] > 0]

    if df_bruto.empty:
        st.success("Todos os contratos estão em dia ou quitados!")
        return

    # Calcular dias de atraso
    df_bruto["data_vencimento"] = pd.to_datetime(df_bruto["data_vencimento"])
    hoje = pd.to_datetime(datetime.now().date())
    df_bruto["dias_atraso"] = (hoje - df_bruto["data_vencimento"]).dt.days
    df_bruto.loc[df_bruto["dias_atraso"] <= 0, "dias_atraso"] = 1

    df_atrasados = df_bruto.copy()

    def definir_faixa(dias):
        if dias <= 30:  return "1 a 30 dias"
        elif dias <= 60: return "31 a 60 dias"
        elif dias <= 90: return "61 a 90 dias"
        else:            return "> 90 dias"

    df_atrasados["faixa"] = df_atrasados["dias_atraso"].apply(definir_faixa)

    df_agrupado = (
        df_atrasados.groupby("faixa")["valor_em_aberto"]
        .sum()
        .reset_index(name="valor_total")
    )

    ordem_faixas = ["1 a 30 dias", "31 a 60 dias", "61 a 90 dias", "> 90 dias"]

    total_devido = df_agrupado["valor_total"].sum()
    total_fmt = f"R$ {total_devido:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # ── TOPO: Contexto e Métrica (Lado a Lado - Ajustado sem quebras) ─────────
    col_texto, col_metrica = st.columns([2, 1])

    with col_texto:
        st.markdown(
            f"<p style='color:{COR_PRIMARIA}; font-weight:600; margin-top:0.5rem; margin-bottom:0.5rem;'>"
            "Risco de Carteira e Inadimplência:</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='color:#777; margin-bottom:0;'>"
            "Valor total de honorários em atraso, segmentado pela idade da dívida.</p>",
            unsafe_allow_html=True,
        )

    with col_metrica:
        st.metric(label="Total em Atraso", value=total_fmt)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── CORPO: Gráfico Principal ─────────────────────────────────────────────
    df_plot = (
        pd.DataFrame({"faixa": ordem_faixas})
        .merge(df_agrupado, on="faixa", how="left")
        .fillna(0)
    )

    cores_barras = [MAPA_CORES.get(f, COR_PRIMARIA) for f in df_plot["faixa"]]

    fig = go.Figure(
        go.Bar(
            x=df_plot["faixa"],
            y=df_plot["valor_total"],
            marker_color=cores_barras,
            text=df_plot["valor_total"].apply(
                lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            ),
            textposition="outside",
            textfont=dict(color=COR_PRIMARIA, size=12),
        )
    )

    fig.update_layout(
        title=dict(
            text="<b>Volume de Dívida por Idade do Atraso</b>",
            font=dict(color=COR_AMARELO, size=15),
            x=0,
        ),
        plot_bgcolor=COR_FUNDO_PLOT,
        paper_bgcolor=COR_FUNDO_PLOT,
        xaxis=dict(
            tickfont=dict(color=COR_PRIMARIA),
            gridcolor=COR_GRADE,
        ),
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
        ),
        margin=dict(l=10, r=10, t=55, b=30),
        height=360,
        showlegend=False,
    )

    st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Tabela detalhada ──────────────────────────────────────────────────────
    st.markdown(
        f"<p style='font-weight:700; color:{COR_AMARELO}; font-size:1rem; margin-top:1.5rem;'>"
        "Detalhamento por Cliente</p>",
        unsafe_allow_html=True,
    )

    df_atrasados["data_vencimento"] = df_atrasados["data_vencimento"].dt.strftime("%d/%m/%Y")

    st.dataframe(
        df_atrasados[[
            "nome_cliente", "numero_processo",
            "valor_em_aberto", "data_vencimento",
            "dias_atraso", "status_pagamento",
        ]],
        column_config={
            "nome_cliente":      "Cliente",
            "numero_processo":   "Processo",
            "valor_em_aberto":   st.column_config.NumberColumn("Valor Aberto", format="R$ %.2f"),
            "data_vencimento":   "Vencimento",
            "dias_atraso":       "Dias em Atraso",
            "status_pagamento":  "Status",
        },
        hide_index=True,
        use_container_width=True,
    )


if __name__ == "__main__":
    renderizar_tela()