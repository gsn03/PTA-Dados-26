import os
import requests
import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

pasta_raiz = Path(__file__).resolve().parent.parent.parent
load_dotenv(pasta_raiz / ".env", override=True)

API_URL = os.getenv("API_KEY", "http://127.0.0.1:8000")

def buscar_dados_inadimplencia():
    """Busca a lista bruta de contratos inadimplentes da API com print de diagnóstico."""
    # Garanta que a API_URL termine sem barra para não duplicar (ex: http://127.0.0.1:8000)
    url_limpa = API_URL.rstrip("/")
    
    # Vamos testar o caminho direto
    link_final = f"{url_limpa}/ia/inadimplencia"
    
    # ESSE PRINT VAI APARECER NO TERMINAL DO SEU VS CODE:
    print(f"\n[DIAGNÓSTICO] O Streamlit está chamando: {link_final}\n")
    
    try:
        resposta = requests.get(link_final, timeout=10) 
        if resposta.status_code == 200:
            return resposta.json().get("detalhamento", [])
        else:
            # Mostra na tela do Streamlit qual link exato deu erro
            st.error(f"Erro na API: Código {resposta.status_code} ao acessar {link_final}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(f"Falha de conexão ao tentar acessar: {link_final}")
        return None

def renderizar_tela():
    st.header("📉 Risco de Carteira e Inadimplência")
    st.markdown("Visualize o valor total de honorários em atraso, segmentado pela idade da dívida.")

    with st.spinner("Processando dados financeiros..."):
        dados_brutos = buscar_dados_inadimplencia()

    if dados_brutos is None:
        return 
        
    if len(dados_brutos) == 0:
        st.success("Excelente notícia! Não há honorários em atraso neste momento.")
        return

    # 1. Transformamos a lista bruta em DataFrame
    df_bruto = pd.DataFrame(dados_brutos)
    df_bruto['valor_em_aberto'] = pd.to_numeric(df_bruto['valor_em_aberto'], errors='coerce').fillna(0.0)
    df_bruto = df_bruto[df_bruto['valor_em_aberto'] > 0]
    
    # 2. Convertemos a data de vencimento e calculamos os dias de atraso
    df_bruto['data_vencimento'] = pd.to_datetime(df_bruto['data_vencimento'])
    hoje = pd.to_datetime(datetime.now().date())
    
    
    # Diferença em dias entre hoje e o vencimento
    df_bruto['dias_atraso'] = (hoje - df_bruto['data_vencimento']).dt.days
    

    # 3. Filtramos: Apenas o que de fato está atrasado (dias_atraso > 0)
    df_atrasados = df_bruto[df_bruto['dias_atraso'] > 0].copy()

    if df_atrasados.empty:
        st.success("Todos os contratos pendentes estão dentro do prazo de vencimento!")
        return

    # 4. Criamos as faixas de atraso dinamicamente usando condições no Pandas
    def definir_faixa(dias):
        if dias <= 30: return "1 a 30 dias"
        elif dias <= 60: return "31 a 60 dias"
        elif dias <= 90: return "61 a 90 dias"
        else: return "> 90 dias"

    df_atrasados['faixa'] = df_atrasados['dias_atraso'].apply(definir_faixa)

    # 5. Agrupamos e somamos o 'valor_em_aberto' por faixa para o gráficoPlotly
    df_agrupado = df_atrasados.groupby('faixa')['valor_em_aberto'].sum().reset_index(name='valor_total')

    # Configurações visuais do Gráfico de Aging
    ordem_faixas = ["1 a 30 dias", "31 a 60 dias", "61 a 90 dias", "> 90 dias"]
    mapa_cores = {
        "1 a 30 dias": "#8C92AC", "31 a 60 dias": "#c5a059", 
        "61 a 90 dias": "#D2691E", "> 90 dias": "#A52A2A"
    }

    total_devido = df_agrupado['valor_total'].sum()
    st.subheader(f"Total Travado em Atraso: R$ {total_devido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    # Desenha o Gráfico
    fig = px.bar(
        df_agrupado, x='faixa', y='valor_total',
        title="Volume de Dívida por Idade do Atraso",
        category_orders={"faixa": ordem_faixas},
        color='faixa', color_discrete_map=mapa_cores, text='valor_total'
    )
    fig.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside', showlegend=False)
    fig.update_layout(
        yaxis_title=None, xaxis_title=None,
        yaxis=dict(showgrid=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Exibe a tabela detalhada com os nomes dos clientes devedores que vieram da API
    st.markdown("### Detalhamento por Cliente")
    
    # Formata a data para exibição na tabela
    df_atrasados['data_vencimento'] = df_atrasados['data_vencimento'].dt.strftime('%d/%m/%Y')
    
    st.dataframe(
        df_atrasados[['nome_cliente', 'numero_processo', 'valor_em_aberto', 'data_vencimento', 'dias_atraso']],
        column_config={
            "nome_cliente": "Cliente",
            "numero_processo": "Processo",
            "valor_em_aberto": st.column_config.NumberColumn("Valor Aberto", format="R$ %.2f"),
            "data_vencimento": "Vencimento",
            "dias_atraso": "Dias em Atraso"
        },
        hide_index=True, use_container_width=True
    )