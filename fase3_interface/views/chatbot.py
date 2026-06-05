"""
views/chatbot.py — Interface de Chat com o Assistente Jurídico
"""

import os
import time
import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

pasta_raiz = Path(__file__).resolve().parent.parent.parent
load_dotenv(pasta_raiz / ".env", override=True)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# ── Paleta ────────────────────────────────────────────────────────────────────
COR_PRIMARIA   = "#44464a"
COR_AMARELO    = "#ffcc00"
COR_FUNDO_PLOT = "#ffffff"
COR_GRADE      = "#ebebeb"
COR_USUARIO    = "#1565c0"
COR_BOT        = "#ffffff"

# ── Gerenciamento de conversas ────────────────────────────────────────────────
def _novo_id() -> str:
    return f"conv_{int(time.time() * 1000)}"

def _gerar_titulo(mensagens: list) -> str:
    for msg in mensagens:
        if msg["role"] == "user":
            t = msg["content"]
            return (t[:44] + "…") if len(t) > 44 else t
    return "Nova conversa"

def _salvar_ativa():
    hist = st.session_state.historico_chat
    if not hist:
        return
    cid      = st.session_state.conversa_ativa_id
    anterior = st.session_state.conversas.get(cid, {})
    st.session_state.conversas[cid] = {
        "id":        cid,
        "titulo":    _gerar_titulo(hist),
        "mensagens": list(hist),
        "criada_em": anterior.get("criada_em", datetime.now().strftime("%d/%m/%Y %H:%M")),
    }

def _nova_conversa():
    _salvar_ativa()
    st.session_state.conversa_ativa_id = _novo_id()
    st.session_state.historico_chat    = []
    st.session_state.aguardando        = False

def _carregar_conversa(conv_id: str):
    _salvar_ativa()
    conv = st.session_state.conversas.get(conv_id)
    if conv:
        st.session_state.conversa_ativa_id = conv_id
        st.session_state.historico_chat    = list(conv["mensagens"])
        st.session_state.aguardando        = False

def _deletar_conversa(conv_id: str):
    st.session_state.conversas.pop(conv_id, None)
    if st.session_state.conversa_ativa_id == conv_id:
        _nova_conversa()

# ── Comunicação com a API ─────────────────────────────────────────────────────
def enviar_mensagem_api(mensagem: str, historico: list) -> str:
    """Envia a pergunta ao endpoint RAG/Langchain e retorna a resposta."""
    link_final = f"{API_URL}/ia/chat"
    payload    = {"pergunta": mensagem, "historico": historico}

    try:
        resposta = requests.post(link_final, json=payload, timeout=90)
        
        # ADICIONE ESTAS DUAS LINHAS:
        if resposta.status_code == 422:
            print(f"🕵️ DETALHE DO ERRO 422: {resposta.text}")
        if resposta.status_code == 200:
            return resposta.json().get("resposta", "Sem resposta do servidor.")
        return f"⚠️ Erro na API: Código {resposta.status_code}"
    except requests.exceptions.ConnectionError:
        return "⚠️ Falha de conexão com a API. Verifique se o servidor está ativo."
    except requests.exceptions.Timeout:
        return "⚠️ A requisição excedeu o tempo limite. Tente novamente."

# ── Componentes de balão (COM DEGRADÊS) ───────────────────────────────────────
def _bubble_usuario(texto: str) -> str:
    return f"""
    <div style="display:flex;justify-content:flex-end;margin:4px 0 4px 80px;">
        <div style="background:linear-gradient(135deg, #084d6e 0%, #1565c0 100%);color:#ffffff;padding:10px 15px;border-radius:18px 18px 4px 18px;max-width:72%;word-wrap:break-word;font-size:.9rem;line-height:1.55;box-shadow:0 2px 8px rgba(21,101,192,.28);">
            {texto}
        </div>
    </div>"""

def _bubble_bot(texto: str) -> str:
    return f"""
    <div style="display:flex;justify-content:flex-start;align-items:flex-end;gap:8px;margin:4px 80px 4px 0;">
        <div style="width:30px;height:30px;border-radius:50%;background:{COR_AMARELO};display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0;">⚖️</div>
        <div style="background:linear-gradient(135deg, #ffffff 0%, #f0f4f8 100%);color:{COR_PRIMARIA};padding:10px 15px;border-radius:18px 18px 18px 4px;max-width:72%;border:1px solid {COR_GRADE};word-wrap:break-word;font-size:.9rem;line-height:1.55;box-shadow:0 1px 4px rgba(0,0,0,.07);">
            {texto}
        </div>
    </div>"""

def _bubble_digitando() -> str:
    return f"""
    <div style="display:flex;justify-content:flex-start;align-items:flex-end;gap:8px;margin:4px 80px 8px 0;">
        <div style="width:30px;height:30px;border-radius:50%;background:{COR_AMARELO};display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0;">⚖️</div>
        <div style="background:linear-gradient(135deg, #ffffff 0%, #f0f4f8 100%);color:{COR_PRIMARIA};padding:10px 16px;border-radius:18px 18px 18px 4px;border:1px solid {COR_GRADE};font-size:.88rem;box-shadow:0 1px 4px rgba(0,0,0,.07);">
            <span style="letter-spacing:3px;">• • •</span>
        </div>
    </div>"""

# ── Histórico Lateral (Direita — Estilo Claude) ──────────────────────────────
def renderizar_historico_direito():
    st.markdown("""
    <style>
    /* Força todas as linhas do histórico a serem flex row */
    div[data-testid="stVerticalBlock"]:has(.right-sidebar-marker) [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 4px !important;
        flex-wrap: nowrap !important;
    }
    div[data-testid="stVerticalBlock"]:has(.right-sidebar-marker) [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
        flex: 1 1 auto !important;
        min-width: 0 !important;
        width: auto !important;
    }
    div[data-testid="stVerticalBlock"]:has(.right-sidebar-marker) [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {
        flex: 0 0 28px !important;
        min-width: 28px !important;
        max-width: 28px !important;
        width: 28px !important;
        padding: 0 !important;
    }
    /* Botões gerais do histórico */
    div[data-testid="stVerticalBlock"]:has(.right-sidebar-marker) .stButton > button {
        background: transparent !important; border: none !important; color: #1a1a1a !important;
        text-align: left !important; justify-content: flex-start !important;
        font-family: 'Barlow', sans-serif !important; font-size: 0.86rem !important;
        font-weight: 400 !important; padding: 0.42rem 0.65rem !important;
        border-radius: 6px !important; box-shadow: none !important; margin-bottom: 1px !important;
        white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important;
        width: 100% !important;
    }
    div[data-testid="stVerticalBlock"]:has(.right-sidebar-marker) .stButton > button:hover {
        background: #efefef !important; color: #1a1a1a !important;
    }
    /* Botão fechar */
    div[data-testid="stVerticalBlock"]:has(.right-sidebar-marker) button[title="Fechar"] {
        width: 32px !important; height: 32px !important; min-width: 32px !important;
        border-radius: 6px !important; padding: 0 !important; color: #666 !important;
        font-size: 0.8rem !important; background: transparent !important; border: 1px solid #e0e0e0 !important;
        justify-content: center !important;
    }
    div[data-testid="stVerticalBlock"]:has(.right-sidebar-marker) button[title="Fechar"]:hover {
        background: #f0f0f0 !important; color: #1a1a1a !important;
    }
    /* Botão nova conversa */
    div[data-testid="stVerticalBlock"]:has(.right-sidebar-marker) button[title="Nova Conversa"] {
        background: #ffffff !important; border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important; color: #1a1a1a !important; font-weight: 500 !important;
        font-size: 0.88rem !important; padding: 0.5rem 0.9rem !important;
        margin-bottom: 0.6rem !important; box-shadow: 0 1px 3px rgba(0,0,0,0.07) !important;
        justify-content: center !important;
    }
    div[data-testid="stVerticalBlock"]:has(.right-sidebar-marker) button[title="Nova Conversa"]:hover {
        background: #f5f5f5 !important; border-color: #d0d0d0 !important;
    }
    /* Botão excluir — na última coluna, sempre centralizado e pequeno */
    div[data-testid="stVerticalBlock"]:has(.right-sidebar-marker) [data-testid="stColumn"]:last-child .stButton > button {
        width: 28px !important; min-width: 28px !important; max-width: 28px !important;
        height: 28px !important; padding: 0 !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
        text-align: center !important; font-size: 0.82rem !important;
        opacity: 0.45 !important; color: #888 !important;
        background: transparent !important; border: none !important; box-shadow: none !important;
        margin: 0 !important;
    }
    div[data-testid="stVerticalBlock"]:has(.right-sidebar-marker) [data-testid="stColumn"]:last-child .stButton > button:hover {
        opacity: 1 !important; color: #c0392b !important;
        background: #fdf0ee !important; border-radius: 5px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col_titulo, col_fechar = st.columns([7, 1])
    with col_titulo:
        st.markdown(
            "<p style='font-family:Barlow,sans-serif; font-size:0.82rem; font-weight:600;"
            " color:#888; text-transform:uppercase; letter-spacing:0.08em;"
            " margin: 0.3rem 0 0.8rem 0.2rem;'>Histórico</p>",
            unsafe_allow_html=True,
        )
    with col_fechar:
        if st.button("✕", help="Fechar", use_container_width=True):
            st.session_state.mostrar_historico = False
            st.rerun()

    if st.button("＋  Nova conversa", help="Nova Conversa", use_container_width=True):
        _nova_conversa()
        st.rerun()

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    conversas = st.session_state.get("conversas", {})
    if not conversas:
        st.markdown(
            "<p style='color:#bbb; font-size:0.83rem; padding:0.4rem 0.2rem;'>Nenhuma conversa ainda.</p>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        "<div style='height:1px; background:#e8e8e8; margin-bottom:0.5rem;'></div>",
        unsafe_allow_html=True,
    )

    ordenadas = sorted(conversas.values(), key=lambda c: c["id"], reverse=True)
    for conv in ordenadas:
        col_btn, col_del = st.columns([10, 1])
        with col_btn:
            titulo_curto = conv["titulo"][:36] + "…" if len(conv["titulo"]) > 36 else conv["titulo"]
            if st.button(titulo_curto, key=f"conv_{conv['id']}", use_container_width=True):
                _carregar_conversa(conv["id"])
                st.rerun()
        with col_del:
            if st.button("🗑", key=f"del_{conv['id']}", use_container_width=True, help="Excluir"):
                _deletar_conversa(conv["id"])
                st.rerun()

# ── Tela principal ────────────────────────────────────────────────────────────
def renderizar_tela():
    if "conversas" not in st.session_state: st.session_state.conversas = {}
    if "conversa_ativa_id" not in st.session_state: st.session_state.conversa_ativa_id = _novo_id()
    if "historico_chat" not in st.session_state: st.session_state.historico_chat = []
    if "aguardando" not in st.session_state: st.session_state.aguardando = False
    if "mostrar_historico" not in st.session_state: st.session_state.mostrar_historico = False

    # ── BOTÃO HISTÓRICO — FIXO NO CANTO SUPERIOR DIREITO ─────────────────────
    if not st.session_state.mostrar_historico:
        st.markdown("""
        <style>
        button[title="Ver Histórico"] {
            position: fixed !important; top: 0.7rem !important; right: 1.1rem !important;
            z-index: 999999 !important; border-radius: 50% !important;
            width: 38px !important; height: 38px !important; min-width: 38px !important;
            padding: 0 !important; background: rgba(255,255,255,0.92) !important;
            backdrop-filter: blur(6px) !important; border: 1px solid #dce3e8 !important;
            color: #44464a !important; font-size: 1rem !important;
            box-shadow: 0 1px 5px rgba(0,0,0,0.12) !important;
        }
        button[title="Ver Histórico"]:hover {
            background: #eef4f7 !important; border-color: #9dbdcc !important;
        }
        </style>
        """, unsafe_allow_html=True)
        _c1, _c2 = st.columns([20, 1])
        with _c2:
            if st.button("🕒", help="Ver Histórico", use_container_width=False):
                _salvar_ativa()
                st.session_state.mostrar_historico = True
                st.rerun()

    # ── VERDADEIRA SIDEBAR DIREITA ────────────────────────────────────────────
    if st.session_state.mostrar_historico:
        sidebar_direita = st.container()
        with sidebar_direita:
            st.markdown('<div class="right-sidebar-marker"></div>', unsafe_allow_html=True)
            renderizar_historico_direito()

    # ── ÁREA PRINCIPAL DO CHAT ────────────────────────────────────────────────
    vazio = len(st.session_state.historico_chat) == 0 and not st.session_state.aguardando

    st.markdown("""
        <style>
        /* Vincula o degradê à raiz absoluta do documento */
        html, body, .stApp {
            background: linear-gradient(to right, #ebebeb 0%, #f4f4f4 35%, #ffffff 100%) !important;
            background-attachment: fixed !important;
            min-height: 100vh !important;
        }
        
        /* Limpa fundos do wrapper principal e força transparência no bloco fixo inferior */
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stHeader"],
        [data-testid="stBottomBlockContainer"],
        div[class*="stBottomBlockContainer"],
        div:has(> [data-testid="stBottomBlockContainer"]),
        section[data-testid="stSidebar"] ~ div {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
        }

        /* Suprime a máscara nativa superior do contêiner do chat input */
        [data-testid="stBottomBlockContainer"]::before,
        div[class*="stBottomBlockContainer"]::before {
            display: none !important;
            background: transparent !important;
        }

        /* Preserva o fundo branco da caixa de texto do Chat */
        [data-testid="stChatInput"], [data-testid="stChatInput"] * {
            background-color: #ffffff !important;
        }

        .gemini-title {
            text-align: center; font-size: 3.2rem; font-weight: 600; letter-spacing: -0.02em;
            background: -webkit-linear-gradient(45deg, #084d6e, #44464a, #0a5f87);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            animation: fadeIn 1.2s ease-in;
            margin: 0; padding: 0;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-15px); } to { opacity: 1; transform: translateY(0); } }

        /* Wrapper fixo ancorado entre o topo (descontando header ~3.5rem)
           e a base (descontando a altura do stBottomBlockContainer ~100px).
           O flexbox centraliza o titulo verticalmente no espaco livre,
           tornando-o imune a qualquer conteudo acima (banner de avisos, etc.). */
        .gemini-title-wrapper {
            position: fixed;
            top: 3.5rem;
            left: 200px;
            right: 0;
            bottom: 100px;
            display: flex;
            align-items: center;
            justify-content: center;
            pointer-events: none;
            z-index: 1;
        }
        </style>
    """, unsafe_allow_html=True)

    if vazio:
        # Confia no session_state calculado pelo app.py.
        # qtd_criticos > 0 significa: ha processos criticos E o usuario nao fechou hoje.
        banner_ativo = st.session_state.get("qtd_criticos", 0) > 0

        if banner_ativo:
            # COM banner: input fica na posicao nativa (base da tela).
            # Titulo centralizado no espaco livre entre header e input (bottom=100px do wrapper).
            input_css = ""
            wrapper_bottom = "100px"
        else:
            # SEM banner: eleva o container do input para o centro da tela
            # e ajusta o wrapper do titulo para acompanhar.
            input_css = """
            [data-testid="stBottomBlockContainer"] {
                transform: translateY(-30vh) !important;
                background: transparent !important;
            }
            [data-testid="stBottomBlockContainer"]::before {
                display: none !important;
            }
            """
            # bottom do wrapper = 100px (input) + 30vh deslocamento
            wrapper_bottom = "calc(100px + 30vh)"

        st.markdown(f"""
            <style>
            {input_css}
            .gemini-title-wrapper {{
                bottom: {wrapper_bottom} !important;
            }}
            </style>
            <div class="gemini-title-wrapper">
                <h1 class="gemini-title">Como posso otimizar seu trabalho hoje?</h1>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div style="padding-top: 1rem;"></div>', unsafe_allow_html=True)
        for msg in st.session_state.historico_chat:
            fn = _bubble_usuario if msg["role"] == "user" else _bubble_bot
            st.markdown(fn(msg["content"]), unsafe_allow_html=True)

        if st.session_state.aguardando:
            st.markdown(_bubble_digitando(), unsafe_allow_html=True)

        st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)

    # ── CAIXA DE INPUT NATIVA DO STREAMLIT ────────────────────────────────────
    mensagem = st.chat_input(
        placeholder="Digite sua pergunta jurídica aqui...",
        disabled=st.session_state.aguardando,
    )

    if mensagem and not st.session_state.aguardando:
        st.session_state.historico_chat.append({"role": "user", "content": mensagem.strip()})
        st.session_state.aguardando = True
        _salvar_ativa()
        st.rerun()

    if st.session_state.aguardando:
        with st.spinner("Consultando o assistente jurídico..."):
            contexto = [{"role": m["role"], "content": m["content"]} for m in st.session_state.historico_chat[:-1]]
            ultima = st.session_state.historico_chat[-1]["content"]
            resposta = enviar_mensagem_api(ultima, contexto)

        st.session_state.historico_chat.append({"role": "assistant", "content": resposta})
        st.session_state.aguardando = False
        _salvar_ativa()
        st.rerun()

if __name__ == "__main__":
    renderizar_tela()
