"""
app.py — Cavalcanti & Melo | Interface Principal
Passo 1: Layout, sidebar, navegação entre views
"""

import streamlit as st
from pathlib import Path

# ── Configuração da página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Cavalcanti & Melo",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Carregar CSS global ─────────────────────────────────────────────────────
def load_css():
    css_path = Path(__file__).parent / "style.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ── Inicializar session_state ───────────────────────────────────────────────
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "chatbot"

if "mostrar_historico" not in st.session_state:
    st.session_state.mostrar_historico = True

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo CITi no topo
    logo_path = Path(__file__).parent / "assets" / "logo_citi.png"
    if logo_path.exists():
        st.image(str(logo_path), width=80)

    st.markdown("---")

    # Título "Serviços" com ícone de engrenagem
    engrenagem_path = Path(__file__).parent / "assets" / "engrenagem.png"
    col_icon, col_title = st.columns([1, 3])
    with col_icon:
        if engrenagem_path.exists():
            st.image(str(engrenagem_path), width=32)
    with col_title:
        st.markdown("### Serviços")

    st.markdown("<br>", unsafe_allow_html=True)

    # Botão ChatBot
    if st.button("💬  ChatBot", use_container_width=True, key="btn_chatbot"):
        st.session_state.pagina_atual = "chatbot"

    st.markdown("<br>", unsafe_allow_html=True)

    # Botão Gráficos
    if st.button("📊  Gráficos", use_container_width=True, key="btn_graficos"):
        st.session_state.pagina_atual = "graficos"

    st.markdown("<br>", unsafe_allow_html=True)

    # Botão Notificações Prazos (desabilitado por enquanto — em desenvolvimento)
    st.button(
        "🔔  Notificações prazos",
        use_container_width=True,
        key="btn_notif",
        disabled=True,
    )
    st.caption("*(em desenvolvimento)*")

    # Logo CITi no rodapé da sidebar
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    if logo_path.exists():
        st.image(str(logo_path), width=60)

# ── Roteamento de páginas ───────────────────────────────────────────────────
pagina = st.session_state.pagina_atual

if pagina == "chatbot":
    from views.chatbot import render
    render()

elif pagina == "graficos":
    from views.prazos_urgentes import render
    render()