"""
views/chat_juridico.py — Interface de Chat com o Assistente Jurídico
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
COR_USUARIO    = "#1565c0"   # azul — mensagens do usuário (direita)
COR_BOT        = "#ffffff"   # branco — respostas do chatbot (esquerda)

MENSAGEM_INICIAL = (
    "Olá! 👋 Sou o assistente jurídico virtual desta consultoria. "
    "Posso ajudá-lo com dúvidas sobre processos, legislação e áreas de atuação. "
    "Como posso auxiliá-lo hoje?"
)


# ── Gerenciamento de conversas ────────────────────────────────────────────────
def _novo_id() -> str:
    """Gera um ID único por timestamp em milissegundos."""
    return f"conv_{int(time.time() * 1000)}"


def _gerar_titulo(mensagens: list) -> str:
    """Usa a primeira mensagem do usuário como título da conversa."""
    for msg in mensagens:
        if msg["role"] == "user":
            t = msg["content"]
            return (t[:44] + "…") if len(t) > 44 else t
    return "Nova conversa"


def _salvar_ativa():
    """Persiste o histórico atual no dicionário de conversas da sessão."""
    hist = st.session_state.historico_chat
    if not hist:
        return
    cid      = st.session_state.conversa_ativa_id
    anterior = st.session_state.conversas.get(cid, {})
    st.session_state.conversas[cid] = {
        "id":        cid,
        "titulo":    _gerar_titulo(hist),
        "mensagens": list(hist),
        "criada_em": anterior.get(
            "criada_em", datetime.now().strftime("%d/%m/%Y %H:%M")
        ),
    }


def _nova_conversa():
    """Salva a conversa atual e abre uma nova sessão em branco."""
    _salvar_ativa()
    st.session_state.conversa_ativa_id = _novo_id()
    st.session_state.historico_chat    = []
    st.session_state.aguardando        = False


def _carregar_conversa(conv_id: str):
    """Salva a conversa atual e carrega a conversa selecionada."""
    _salvar_ativa()
    conv = st.session_state.conversas.get(conv_id)
    if conv:
        st.session_state.conversa_ativa_id = conv_id
        st.session_state.historico_chat    = list(conv["mensagens"])
        st.session_state.aguardando        = False


def _deletar_conversa(conv_id: str):
    """Remove uma conversa do histórico e abre nova se era a ativa."""
    st.session_state.conversas.pop(conv_id, None)
    if st.session_state.conversa_ativa_id == conv_id:
        _nova_conversa()


# ── Comunicação com a API ─────────────────────────────────────────────────────
def enviar_mensagem_api(mensagem: str, historico: list) -> str:
    """Envia a pergunta ao endpoint RAG/Langchain e retorna a resposta."""
    link_final = "http://127.0.0.1:8000/ia/chat"
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


# ── Componentes de balão ──────────────────────────────────────────────────────
def _bubble_usuario(texto: str) -> str:
    """Balão direito — fundo azul, texto branco."""
    return f"""
    <div style="display:flex;justify-content:flex-end;margin:4px 0 4px 80px;">
        <div style="
            background:{COR_USUARIO};color:#ffffff;
            padding:10px 15px;border-radius:18px 18px 4px 18px;
            max-width:72%;word-wrap:break-word;
            font-size:.9rem;line-height:1.55;
            box-shadow:0 2px 8px rgba(21,101,192,.28);">
            {texto}
        </div>
    </div>"""


def _bubble_bot(texto: str) -> str:
    """Balão esquerdo — fundo branco, borda sutil, ícone amarelo."""
    return f"""
    <div style="
        display:flex;justify-content:flex-start;
        align-items:flex-end;gap:8px;margin:4px 80px 4px 0;">
        <div style="
            width:30px;height:30px;border-radius:50%;
            background:{COR_AMARELO};display:flex;
            align-items:center;justify-content:center;
            font-size:14px;flex-shrink:0;">⚖️</div>
        <div style="
            background:{COR_BOT};color:{COR_PRIMARIA};
            padding:10px 15px;border-radius:18px 18px 18px 4px;
            max-width:72%;border:1px solid {COR_GRADE};
            word-wrap:break-word;font-size:.9rem;line-height:1.55;
            box-shadow:0 1px 4px rgba(0,0,0,.07);">
            {texto}
        </div>
    </div>"""


def _bubble_digitando() -> str:
    """Indicador animado enquanto aguarda a resposta da API."""
    return f"""
    <div style="
        display:flex;justify-content:flex-start;
        align-items:flex-end;gap:8px;margin:4px 80px 8px 0;">
        <div style="
            width:30px;height:30px;border-radius:50%;
            background:{COR_AMARELO};display:flex;
            align-items:center;justify-content:center;
            font-size:14px;flex-shrink:0;">⚖️</div>
        <div style="
            background:{COR_BOT};color:{COR_PRIMARIA};
            padding:10px 16px;border-radius:18px 18px 18px 4px;
            border:1px solid {COR_GRADE};font-size:.88rem;
            box-shadow:0 1px 4px rgba(0,0,0,.07);">
            <span style="letter-spacing:3px;">• • •</span>
        </div>
    </div>"""


# ── Histórico Lateral (Direita) ───────────────────────────────────────────────
def renderizar_historico_direito():
    """Renderiza a coluna direita com o histórico de conversas."""

    # CSS global para os botões da "falsa sidebar" direita (segunda coluna)
    st.markdown(f"""
    <style>
    /* Botões de conversa — estado padrão na coluna da direita */
    div[data-testid="column"]:nth-of-type(2) .stButton > button {{
        text-align: left !important;
        justify-content: flex-start !important;
        background: #f5f5f5;
        border: 1px solid #e0e0e0;
        color: {COR_PRIMARIA};
        font-size: 0.82rem;
        padding: 7px 10px;
        border-radius: 8px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        transition: background .15s, border-color .15s;
    }}
    div[data-testid="column"]:nth-of-type(2) .stButton > button:hover {{
        background: #fff9d6;
        border-color: {COR_AMARELO};
        color: {COR_PRIMARIA};
    }}
    /* Botão da conversa ativa (type="primary") */
    div[data-testid="column"]:nth-of-type(2) .stButton > button[data-testid="baseButton-primary"] {{
        background: {COR_AMARELO} !important;
        border-color: {COR_AMARELO} !important;
        color: {COR_PRIMARIA} !important;
        font-weight: 700;
    }}
    /* Botão "Nova Conversa" */
    div[data-testid="column"]:nth-of-type(2) .stButton > button[data-testid="baseButton-secondary"]:first-of-type {{
        background: {COR_PRIMARIA};
        border-color: {COR_PRIMARIA};
        color: #ffffff;
        font-weight: 600;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── Cabeçalho do Histórico ──────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="
            padding:12px 4px 4px 4px;
            border-bottom:2px solid {COR_AMARELO};
            margin-bottom:12px;">
            <h3 style="color:{COR_PRIMARIA};margin:0;font-size:1.05rem;">
                💬 Histórico de Conversas
            </h3>
            <p style="color:#999;font-size:0.75rem;margin:4px 0 0 0;">
                Conversas desta sessão
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Botão nova conversa ───────────────────────────────────────────────
    if st.button("➕  Nova Conversa", use_container_width=True):
        _nova_conversa()
        st.rerun()

    st.markdown(
        f"<hr style='border:none;border-top:1px solid {COR_GRADE};margin:12px 0;'>",
        unsafe_allow_html=True,
    )

    conversas = st.session_state.get("conversas", {})
    ativa_id  = st.session_state.get("conversa_ativa_id", "")

    # ── Lista vazia ───────────────────────────────────────────────────────
    if not conversas:
        st.markdown(
            f"""
            <div style="
                text-align:center;padding:24px 8px;
                color:#ccc;font-size:0.82rem;line-height:1.6;">
                <div style="font-size:1.8rem;margin-bottom:6px;">🗂️</div>
                Nenhuma conversa salva ainda.<br>
                Envie uma mensagem para começar.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ── Ordenação: mais recente primeiro ──────────────────────────────────
    ordenadas = sorted(
        conversas.values(), key=lambda c: c["id"], reverse=True
    )

    for conv in ordenadas:
        is_ativa = conv["id"] == ativa_id
        n_trocas = len(conv["mensagens"]) // 2

        col_btn, col_del = st.columns([5, 1])

        # Botão principal da conversa
        with col_btn:
            rotulo = f"▶  {conv['titulo']}" if is_ativa else conv["titulo"]
            if st.button(
                rotulo,
                key=f"conv_{conv['id']}",
                use_container_width=True,
                type="primary" if is_ativa else "secondary",
                help=f"Aberta em: {conv['criada_em']}",
            ):
                if not is_ativa:
                    _carregar_conversa(conv["id"])
                    st.rerun()

        # Botão de exclusão
        with col_del:
            if st.button(
                "✕",
                key=f"del_{conv['id']}",
                help="Excluir esta conversa",
                use_container_width=True,
            ):
                _deletar_conversa(conv["id"])
                st.rerun()

        # Metadados abaixo do botão
        st.markdown(
            f"<p style='color:#bbb;font-size:0.7rem;margin:-4px 0 8px 4px;'>"
            f"🕐 {conv['criada_em']} · {n_trocas} troca(s)</p>",
            unsafe_allow_html=True,
        )


# ── Tela principal ────────────────────────────────────────────────────────────
def renderizar_tela():
    # ── Inicialização do estado da sessão ─────────────────────────────────────
    if "conversas" not in st.session_state:
        st.session_state.conversas = {}
    if "conversa_ativa_id" not in st.session_state:
        st.session_state.conversa_ativa_id = _novo_id()
    if "historico_chat" not in st.session_state:
        st.session_state.historico_chat = []
    if "aguardando" not in st.session_state:
        st.session_state.aguardando = False

    # ── DIVISÃO DA TELA: Chat (Esquerda/Centro) e Histórico (Direita) ─────────
    col_chat, col_historico = st.columns([7, 3], gap="large")

    # ── Coluna do Histórico (Direita) ─────────────────────────────────────────
    with col_historico:
        renderizar_historico_direito()

    # ── Coluna do Chat Principal (Esquerda/Centro) ────────────────────────────
    with col_chat:
        # Cabeçalho
        st.markdown(
            f"<h2 style='text-align:center; color:{COR_PRIMARIA};'>"
            "Assistente Jurídico Virtual ⚖️</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; color:#777;'>"
            "Tire suas dúvidas sobre processos, legislação e áreas de atuação "
            "com nosso assistente especializado em RAG.</p>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # Barra de status da conversa ativa
        st.markdown(
            f"<p style='color:{COR_PRIMARIA}; font-weight:600; font-size:0.95rem;'>"
            "💬 Conversa Ativa</p>",
            unsafe_allow_html=True,
        )

        col_status, col_nova = st.columns([9, 1])
        with col_status:
            n = len(st.session_state.historico_chat)
            if n:
                titulo_ativo = _gerar_titulo(st.session_state.historico_chat)
                trocas = n // 2
                st.markdown(
                    f"<p style='color:{COR_PRIMARIA}; font-size:0.82rem; margin:0;'>"
                    f"🗂️ <b>{titulo_ativo}</b> &nbsp;·&nbsp; {trocas} troca(s)</p>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<p style='color:#aaa; font-size:0.82rem; margin:0;'>"
                    "Nenhuma mensagem ainda. Faça sua pergunta abaixo.</p>",
                    unsafe_allow_html=True,
                )
        with col_nova:
            if st.button("➕", use_container_width=True, help="Nova conversa", key="btn_nova_conversa_main"):
                _nova_conversa()
                st.rerun()

        # Container com o histórico de mensagens da conversa atual
        with st.container(height=460, border=True):
            if not st.session_state.historico_chat and not st.session_state.aguardando:
                st.markdown(_bubble_bot(MENSAGEM_INICIAL), unsafe_allow_html=True)
            else:
                for msg in st.session_state.historico_chat:
                    fn = _bubble_usuario if msg["role"] == "user" else _bubble_bot
                    st.markdown(fn(msg["content"]), unsafe_allow_html=True)

                if st.session_state.aguardando:
                    st.markdown(_bubble_digitando(), unsafe_allow_html=True)

        # Caixa de entrada ancorada na coluna do chat
        mensagem = st.chat_input(
            placeholder="Digite sua pergunta jurídica aqui...",
            disabled=st.session_state.aguardando,
        )

        # Fluxo: envio → spinner → resposta
        if mensagem and not st.session_state.aguardando:
            st.session_state.historico_chat.append(
                {"role": "user", "content": mensagem.strip()}
            )
            st.session_state.aguardando = True
            _salvar_ativa()  # persiste imediatamente para aparecer na sidebar
            st.rerun()

        if st.session_state.aguardando:
            with st.spinner("Consultando o assistente jurídico..."):
                contexto = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.historico_chat[:-1]
                ]
                ultima   = st.session_state.historico_chat[-1]["content"]
                resposta = enviar_mensagem_api(ultima, contexto)

            st.session_state.historico_chat.append(
                {"role": "assistant", "content": resposta}
            )
            st.session_state.aguardando = False
            _salvar_ativa()  # persiste com a resposta incluída
            st.rerun()

if __name__ == "__main__":
    renderizar_tela()