import os
import requests
import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

pasta_raiz = Path(__file__).resolve().parent.parent.parent
load_dotenv(pasta_raiz / ".env", override=True)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

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
    st.header("📊 Status dos Processos por Vertente")
    st.markdown("Distribuição do volume de processos (Ativos, Encerrados, etc.) divididos por área de atuação (Cível, Trabalhista).")

    with st.spinner("Buscando dados no banco..."):
        dados = buscar_dados_status_vertente()

    if not dados:
        return

    if len(dados) == 0:
        st.warning("Não existem processos cadastrados para análise.")
        return
    
    df = pd.DataFrame(dados)

    # filtros
    st.markdown("### 🔍 Filtros de Análise")
    col_filtro1, col_filtro2 = st.columns(2)
    
    # Pegamos os valores únicos para colocar nas opções do filtro
    opcoes_vertentes = df['vertente'].unique().tolist()
    opcoes_status = df['status'].unique().tolist()

    with col_filtro1:
        vertentes_selecionadas = st.multiselect(
            "Selecione a(s) Área(s) de Atuação:",
            options=opcoes_vertentes,
            default=opcoes_vertentes # Por padrão, todas vêm selecionadas
        )

    with col_filtro2:
        status_selecionados = st.multiselect(
            "Selecione o(s) Status:",
            options=opcoes_status,
            default=opcoes_status
        )

    df_filtrado = df[
        (df['vertente'].isin(vertentes_selecionadas)) & 
        (df['status'].isin(status_selecionados))
    ]

    # Tratamento caso o usuário desmarque todas as opções
    if df_filtrado.empty:
        st.info("Nenhum dado encontrado para os filtros selecionados.")
        return

    st.divider() # Linha visual para separar filtros do gráfico
    st.subheader(f"Total de cruzamentos encontrados: {len(df_filtrado)}")

    # Gráfico de Barras Agrupadas no Plotly
    fig = px.bar(
        df_filtrado,
        x="vertente",
        y="quantidade",
        color="status",
        barmode="group", # Coloca as barras lado a lado
        title="Volume de Processos por Área e Status",
        labels={
            "vertente": "Área de Atuação", 
            "quantidade": "Nº de Processos", 
            "status": "Status do Processo"
            },
        text_auto=True,
        color_discrete_sequence=px.colors.qualitative.Set2 # Paleta de cores suave 
    )
    
    fig.update_layout(yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

    # Tabela de dados brutos
    st.subheader("Detalhamento")

    # Tabela resumida abaixo do gráfico
    st.dataframe(
        df_filtrado,
        column_config={
            "vertente": "Vertente Jurídica",
            "status": "Situação",
            "quantidade": st.column_config.NumberColumn("Volume", format="%d")
        },
        hide_index=True,
        use_container_width=True
    )

if __name__ == "__main__":
    renderizar_tela()