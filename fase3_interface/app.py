"""
app.py — Cavalcanti & Melo | Interface Principal
Integra todas as views: chatbot, prazos_urgentes, status_vertente, view_inadimplencia, notificador_prazos
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
    st.session_state.mostrar_historico = False

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo + nome da empresa "Cavalcanti & Melo"
    balanca_path = Path(__file__).parent / "assets" / "balanca.png"
    col_icon, col_title = st.columns([1, 3])
    with col_icon:
        if balanca_path.exists():
            st.image(str(balanca_path), width=28)
        else:
            st.markdown("⚖️")
    with col_title:
        st.markdown(
            "<h3 style='margin:0; padding:0; line-height:1.3; font-size:0.95rem;'>Cavalcanti<br>&amp; Melo</h3>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom:1.2rem;'></div>", unsafe_allow_html=True)

    # ── Botão ChatBot ────────────────────────────────────────────────────────
    chatbot_ativo = st.session_state.pagina_atual == "chatbot"
    if st.button(
        "💬  ChatBot",
        use_container_width=True,
        key="btn_chatbot",
        type="primary" if chatbot_ativo else "secondary",
    ):
        st.session_state.pagina_atual = "chatbot"
        st.rerun()

    st.markdown("<div style='margin-bottom:0.6rem;'></div>", unsafe_allow_html=True)

    # ── Botão Gráficos (submenu) ─────────────────────────────────────────────
    graficos_ativo = st.session_state.pagina_atual in (
        "prazos_urgentes", "status_vertente", "inadimplencia", "carteira_advogados"
    )
    if st.button(
        "📊  Gráficos",
        use_container_width=True,
        key="btn_graficos",
        type="primary" if graficos_ativo else "secondary",
    ):
        # Abre submenu ou navega para a primeira sub-view
        if not graficos_ativo:
            st.session_state.pagina_atual = "prazos_urgentes"
            st.rerun()

    # Sub-botões de Gráficos — visíveis apenas quando a seção está ativa
    if graficos_ativo:
        with st.container():
            prazos_ativo = st.session_state.pagina_atual == "prazos_urgentes"
            if st.button(
                "⏰  Prazos Urgentes",
                use_container_width=True,
                key="btn_prazos",
                type="primary" if prazos_ativo else "secondary",
            ):
                st.session_state.pagina_atual = "prazos_urgentes"
                st.rerun()

            status_ativo = st.session_state.pagina_atual == "status_vertente"
            if st.button(
                "📋  Status Vertente",
                use_container_width=True,
                key="btn_status",
                type="primary" if status_ativo else "secondary",
            ):
                st.session_state.pagina_atual = "status_vertente"
                st.rerun()

            inadimplencia_ativo = st.session_state.pagina_atual == "inadimplencia"
            if st.button(
                "📉  Inadimplência",
                use_container_width=True,
                key="btn_inadimplencia",
                type="primary" if inadimplencia_ativo else "secondary",
            ):
                st.session_state.pagina_atual = "inadimplencia"
                st.rerun()

            carteira_ativo = st.session_state.pagina_atual == "carteira_advogados"
            if st.button(
                "💼  Carteira Advogados",
                use_container_width=True,
                key="btn_carteira",
                type="primary" if carteira_ativo else "secondary",
            ):
                st.session_state.pagina_atual = "carteira_advogados"
                st.rerun()

    st.markdown("<div style='margin-bottom:0.6rem;'></div>", unsafe_allow_html=True)

    # ── Botão Notificador de Prazos (Nova Hierarquia Principal) ──────────────
    notificador_ativo = st.session_state.pagina_atual == "notificador_prazos"
    if st.button(
        "🔔  Notificador de Prazos",
        use_container_width=True,
        key="btn_notificador",
        type="primary" if notificador_ativo else "secondary",
    ):
        st.session_state.pagina_atual = "notificador_prazos"
        st.rerun()


    # ── Logo CITi no rodapé ──────────────────────────────────────────────────
    st.markdown(
        "<div style='position:fixed; bottom:1.2rem; left:0.8rem;'>",
        unsafe_allow_html=True,
    )
    logo_path = Path(__file__).parent / "assets" / "logo_citi.png"
    if logo_path.exists():
        st.image(str(logo_path), width=48)
    st.markdown("</div>", unsafe_allow_html=True)

# ── Roteamento de páginas ───────────────────────────────────────────────────
pagina = st.session_state.pagina_atual

if pagina == "chatbot":
    from views.chatbot import render
    render()

elif pagina == "prazos_urgentes":
    from views.prazos_urgentes import render
    render()

elif pagina == "status_vertente":
    from views.status_vertente import renderizar_tela
    renderizar_tela()

elif pagina == "inadimplencia":
    from views.view_inadimplencia import renderizar_tela
    renderizar_tela()

elif pagina == "carteira_advogados":
    from views.carteira_advogados import renderizar_tela
    renderizar_tela()

elif pagina == "notificador_prazos":
    from views.notificador_prazos import renderizar_tela
    renderizar_tela()