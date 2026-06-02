import os
import requests
import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# 1. Ajuste de Arquitetura: Forçando a leitura do .env na raiz do projeto
# views(1) -> fase3_interface(2) -> raiz(3)
pasta_raiz = Path(__file__).resolve().parent.parent.parent
load_dotenv(pasta_raiz / ".env", override=True)

# URL da API (Com o Plano B de segurança)
API_URL = os.getenv("API_KEY", "http://127.0.0.1:8000")

def buscar_dados_prazos(dias: int):
    """
    Faz a requisição HTTP e trata erros de conexão.
    """
    try:
        resposta = requests.get(f"{API_URL}/ia/prazos_urgentes", params={"dias": dias}, timeout=10)
        if resposta.status_code == 200:
            return resposta.json().get("processos_urgentes", [])
        else:
            st.error(f"Erro na API: Código {resposta.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Falha de conexão: O servidor da API não está respondendo. Verifique se o FastAPI está ligado.")
        return None
    except Exception as e:
        st.error(f"Erro inesperado: {e}")
        return None

def renderizar_tela():
    """
    Função principal que será chamada pelo app.py.
    """
    st.header("⚖️ Sobrecarga de Prazos por Responsável")
    st.markdown("Acompanhe o volume de urgências atribuídas a cada advogado nos próximos dias.")

    # Filtro de dias interativo
    dias_filtro = st.slider("Analisar prazos para os próximos (dias):", min_value=1, max_value=30, value=7)

    # Indicador de carregamento
    with st.spinner("Analisando a carga de trabalho da equipe..."):
        dados_prazos = buscar_dados_prazos(dias=dias_filtro)

    # Tratar o estado vazio
    if dados_prazos is None:
        return 
        
    if len(dados_prazos) == 0:
        st.success(f"Excelente notícia! Não há nenhum prazo urgente para a equipe nos próximos {dias_filtro} dias.")
        return

    # Parsear o JSON para DataFrame do Pandas
    df = pd.DataFrame(dados_prazos)
    
    # Se algum processo não tiver advogado, evitamos que o gráfico quebre
    df['advogado'] = df['advogado'].fillna("Não Atribuído")
    
    # Formatação de data para a tabela
    df['prazo'] = pd.to_datetime(df['prazo']).dt.strftime('%d/%m/%Y')

    st.subheader(f"Total de {len(dados_prazos)} prazos na janela selecionada")
    
    # Agrupamento: Quantos prazos cada advogado tem
    contagem_por_advogado = df.groupby('advogado').size().reset_index(name='quantidade')
    
    # Ordenar do mais sobrecarregado para o menos
    contagem_por_advogado = contagem_por_advogado.sort_values(by='quantidade', ascending=True)

    # Gráfico Plotly: Sobrecarga por Responsável
    fig = px.bar(
        contagem_por_advogado, 
        x='quantidade', 
        y='advogado',
        orientation='h', # Gráfico horizontal é melhor para ler nomes de pessoas
        title="Volume de Prazos Urgentes por Advogado",
        labels={'advogado': 'Equipe', 'quantidade': 'Quantidade de Prazos'},
        color_discrete_sequence=['#e67e22'], # Cor de atenção (Laranja)
        text_auto=True
    )
    
    # Limpeza visual do gráfico
    fig.update_layout(yaxis_title=None)
    
    st.plotly_chart(fig, use_container_width=True)

    st.caption("Detalhamento individual dos processos urgentes:")
    
    # Exibe a tabela para o advogado saber exatamente quais são os processos dele
    st.dataframe(
        df[['advogado', 'prazo', 'numero_processo', 'nome_cliente', 'fase_atual']],
        column_config={
            "advogado": "Responsável",
            "prazo": "Vencimento",
            "numero_processo": "Processo",
            "nome_cliente": "Cliente",
            "fase_atual": "Fase Atual"
        },
        hide_index=True,
        use_container_width=True
    )