import streamlit as st

# 1. Importação dos Módulos da Equipa
from views import prazos_urgentes
from views import view_inadimplencia
# from views import honorarios  # Remover o comentário quando o seu colega terminar
# from views import movimentacoes # Remover o comentário quando o colega terminar

# 2. Configuração Global da Página (DEVE ser a primeira instrução Streamlit)
st.set_page_config(
    page_title="Dashboard | PTA Dados",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # 3. Construção do Menu Lateral (Sidebar)
    st.sidebar.title("Navegação Central")
    st.sidebar.markdown("Selecione o módulo que deseja visualizar:")

    # Lista de opções disponíveis no menu
    opcoes_menu = [
        "Início", 
        "Prazos Urgentes", 
        "Honorários Financeiros", 
        "Movimentações Processuais"
    ]
    
    escolha = st.sidebar.radio("Módulos:", opcoes_menu)

    st.sidebar.markdown("---")
    st.sidebar.caption("Agente Jurídico Automático - Equipa Gustavo")

    # 4. Roteador de Ecrãs (A Arquitetura Modular)
    if escolha == "Início":
        st.title("🏛️ Bem-vindo ao Sistema de Gestão Jurídica")
        st.markdown("""
        Este painel consolida os dados do escritório em tempo real.
        Utilize o menu lateral para navegar entre os módulos analíticos desenvolvidos pela equipa.
        """)
        
    elif escolha == "Prazos Urgentes":
        # Aqui o Roteador chama o seu módulo isolado
        prazos_urgentes.renderizar_tela()
        
    elif escolha == "Honorários Financeiros":
        # Placeholder (Espaço reservado) para o código do seu colega
        view_inadimplencia.renderizar_tela()
        
    elif escolha == "Movimentações Processuais":
        # Placeholder (Espaço reservado) para o código do seu colega
        st.warning("🚧 Módulo de Movimentações atualmente em desenvolvimento pela equipa.")

if __name__ == "__main__":
    main()