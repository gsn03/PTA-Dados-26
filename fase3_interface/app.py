"""
app.py — Cavalcante & Melo | Interface Principal
Integra todas as views: chatbot, prazos_urgentes, status_vertente, view_inadimplencia, notificador_prazos
"""

import streamlit as st
from pathlib import Path
import os
import requests
from datetime import datetime, time

# ── Configuração da página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Cavalcante & Melo",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Carregar CSS global ─────────────────────────────────────────────────────
def load_css():
    css_path = Path(__file__).parent / "style.css"
    if css_path.exists():
        with open(css_path, encoding="utf-8") as f: 
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ── Inicializar session_state ───────────────────────────────────────────────
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "chatbot"

if "mostrar_historico" not in st.session_state:
    st.session_state.mostrar_historico = False

if "ultima_data_interacao" not in st.session_state:
    st.session_state.ultima_data_interacao = None

# ── Controle de Horário e Interação (8:30h da manhã) ────────────────────────
agora = datetime.now()
hoje = agora.date()
horario_gatilho = time(8, 30)

deve_exibir_notificacao = agora.time() >= horario_gatilho and st.session_state.ultima_data_interacao != hoje

if deve_exibir_notificacao and "qtd_criticos" not in st.session_state:
    API_URL = os.getenv("API_KEY", "http://127.0.0.1:8000")
    try:
        resposta = requests.get(f"{API_URL}/ia/alertas_email", params={"dias_exatos": 5}, timeout=5)
        processos_criticos = resposta.json().get("processos", []) if resposta.status_code == 200 else []
        st.session_state.qtd_criticos = len(processos_criticos)
    except Exception:
        st.session_state.qtd_criticos = 0
elif not deve_exibir_notificacao:
    st.session_state.qtd_criticos = 0

<<<<<<< HEAD
=======

>>>>>>> ajustes_chatbot
# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    # ── Logo da Empresa ──────────────────────────────────────────────────────
    logo_cm_path = Path(__file__).parent / "assets" / "logo_empresabranco.png"
    if logo_cm_path.exists():
        st.image(str(logo_cm_path), use_container_width=True)
    else:
        st.markdown(
            "<h3 style='text-align:center; color:#44464a;'>Cavalcante & Melo</h3>", 
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom:1.2rem;'></div>", unsafe_allow_html=True)

    # ── Botão ChatBot ────────────────────────────────────────────────────────
    chatbot_ativo = st.session_state.pagina_atual == "chatbot"
    if st.button(
        "Chatbot",
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
        "Gráficos",
        use_container_width=True,
        key="btn_graficos",
        type="primary" if graficos_ativo else "secondary",
    ):
        if not graficos_ativo:
            st.session_state.pagina_atual = "prazos_urgentes"
            st.rerun()

    if graficos_ativo:
        with st.container():
            prazos_ativo = st.session_state.pagina_atual == "prazos_urgentes"
            if st.button(
                "Prazos urgentes",
                use_container_width=True,
                key="btn_prazos",
                type="primary" if prazos_ativo else "secondary",
            ):
                st.session_state.pagina_atual = "prazos_urgentes"
                st.rerun()

            status_ativo = st.session_state.pagina_atual == "status_vertente"
            if st.button(
                "Status dos processos",
                use_container_width=True,
                key="btn_status",
                type="primary" if status_ativo else "secondary",
            ):
                st.session_state.pagina_atual = "status_vertente"
                st.rerun()

            inadimplencia_ativo = st.session_state.pagina_atual == "inadimplencia"
            if st.button(
                "Inadimplência",
                use_container_width=True,
                key="btn_inadimplencia",
                type="primary" if inadimplencia_ativo else "secondary",
            ):
                st.session_state.pagina_atual = "inadimplencia"
                st.rerun()

            carteira_ativo = st.session_state.pagina_atual == "carteira_advogados"
            if st.button(
                "Carteira dos advogados",
                use_container_width=True,
                key="btn_carteira",
                type="primary" if carteira_ativo else "secondary",
            ):
                st.session_state.pagina_atual = "carteira_advogados"
                st.rerun()

    st.markdown("<div style='margin-bottom:0.6rem;'></div>", unsafe_allow_html=True)

    # ── Botão Notificador de Prazos ──────────────────────────────────────────
    notificador_ativo = st.session_state.pagina_atual == "notificador_prazos"
    if st.button(
        "Notificador dos prazos",
        use_container_width=True,
        key="btn_notificador",
        type="primary" if notificador_ativo else "secondary",
    ):
        st.session_state.pagina_atual = "notificador_prazos"
        st.rerun()

    # ── Logo CITi — injetada via base64 no CSS para garantir position:fixed ───
    import base64
    logo_path = Path(__file__).parent / "assets" / "logo_citi.png"
    if logo_path.exists():
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()
        st.markdown(
            f"""<style>
            body::after {{
                content: '' !important;
                display: block !important;
                position: fixed !important;
                bottom: 1.1rem !important;
                left: 0.7rem !important;
                width: 36px !important;
                height: 36px !important;
                background-image: url('data:image/png;base64,{logo_b64}') !important;
                background-size: contain !important;
                background-repeat: no-repeat !important;
                background-position: center !important;
                z-index: 999999 !important;
                pointer-events: none !important;
            }}
            </style>""",
            unsafe_allow_html=True,
        )

# ── 🚨 RETÂNGULO DE NOTIFICAÇÃO DEITADO (TOPO) ──────────────────────────────
if deve_exibir_notificacao and st.session_state.qtd_criticos > 0:
    with st.container(border=True): # Cria o retângulo em volta
        # Dividimos o retângulo: 60% para o texto, 20% para cada botão
        col_texto, col_btn_ver, col_btn_fechar = st.columns([3, 1, 1])
        
        with col_texto:
            # 2 linhas de mensagem formatadas com HTML nativo para ficarem juntas
            st.markdown(
                f"<h4 style='margin-bottom:0; padding-bottom:5px; color:#c0392b;'>🚨 Aviso de Prazos Críticos</h4>"
                f"<p style='margin-top:0; padding-top:0; color:#555;'>Você tem <b>{st.session_state.qtd_criticos} novos processos</b> entrando em vencimento. Recomendamos a verificação imediata.</p>",
                unsafe_allow_html=True
            )
            
        with col_btn_ver:
            st.write("") # Espaço para o botão descer um pouco e alinhar com o texto
            if st.button("Ver mais", use_container_width=True, key="btn_notif_ver_mais", type="primary"):
                st.session_state.pagina_atual = "notificador_prazos"
                st.session_state.ultima_data_interacao = hoje
                st.rerun()
                
        with col_btn_fechar:
            st.write("") # Espaço para o botão descer um pouco e alinhar com o texto
            if st.button("Fechar", use_container_width=True, key="btn_notif_fechar"):
                st.session_state.ultima_data_interacao = hoje
                st.rerun()


# ── 🚨 RETÂNGULO DE NOTIFICAÇÃO DEITADO (TOPO) ──────────────────────────────
if deve_exibir_notificacao and st.session_state.qtd_criticos > 0:
    with st.container(border=True): # Cria o retângulo em volta
        # Dividimos o retângulo: 60% para o texto, 20% para cada botão
        col_texto, col_btn_ver, col_btn_fechar = st.columns([3, 1, 1])
        
        with col_texto:
            # 2 linhas de mensagem formatadas com HTML nativo para ficarem juntas
            st.markdown(
                f"<h4 style='margin-bottom:0; padding-bottom:5px; color:#c0392b;'>🚨 Aviso de Prazos Críticos</h4>"
                f"<p style='margin-top:0; padding-top:0; color:#555;'>Você tem <b>{st.session_state.qtd_criticos} novos processos</b> entrando em vencimento. Recomendamos a verificação imediata.</p>",
                unsafe_allow_html=True
            )
            
        with col_btn_ver:
            st.write("") # Espaço para o botão descer um pouco e alinhar com o texto
            if st.button("Ver mais", use_container_width=True, key="btn_notif_ver_mais", type="primary"):
                st.session_state.pagina_atual = "notificador_prazos"
                st.session_state.ultima_data_interacao = hoje
                st.rerun()
                
        with col_btn_fechar:
            st.write("") # Espaço para o botão descer um pouco e alinhar com o texto
            if st.button("Fechar", use_container_width=True, key="btn_notif_fechar"):
                st.session_state.ultima_data_interacao = hoje
                st.rerun()

# ── Roteamento de páginas ───────────────────────────────────────────────────
pagina = st.session_state.pagina_atual

if pagina == "chatbot":
    from views.chatbot import renderizar_tela
    renderizar_tela()

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