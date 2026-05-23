"""
app.py — Ponto de entrada principal do Diário de Classe.

CORREÇÃO WINDOWS: as primeiras linhas garantem que a pasta do projeto
esteja no sys.path antes de qualquer import local, resolvendo o erro
"ModuleNotFoundError: No module found 'aba_cadastros'" no Windows.
"""

# ── Correção de path (deve ser ANTES de qualquer import local) ────────────────
import sys
import os

# Adiciona a pasta onde este arquivo está ao sys.path
# Isso resolve o ModuleNotFoundError no Windows e em qualquer ambiente
_PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
if _PASTA_PROJETO not in sys.path:
    sys.path.insert(0, _PASTA_PROJETO)
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
from database import inicializar_banco, info_banco
from autenticacao import (
    esta_autenticado,
    obter_usuario_atual,
    fazer_logout,
    renderizar_tela_login,
)
import aba_cadastros
import aba_diario
import aba_dashboard


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DA PÁGINA
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Diário de Classe",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
:root {
    --cor-primaria: #2563EB;
    --cor-acento:   #16A34A;
    --cor-aviso:    #DC2626;
}
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
[data-baseweb="tab-list"] { gap: 1rem; }
[data-baseweb="tab"]      { font-size: 1rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# INICIALIZAÇÃO DO BANCO (executado uma única vez por sessão do servidor)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def _inicializar():
    inicializar_banco()
    return True

_inicializar()


# ═══════════════════════════════════════════════════════════════════════════════
# AUTENTICAÇÃO — bloqueia tudo enquanto não houver login
# ═══════════════════════════════════════════════════════════════════════════════

if not esta_autenticado():
    renderizar_tela_login()
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# CABEÇALHO — exibido somente após login válido
# ═══════════════════════════════════════════════════════════════════════════════

usuario = obter_usuario_atual()

# Proteção: session_state pode ser perdido em reload/reinicialização do Cloud
if usuario is None:
    fazer_logout()
    st.rerun()

perfil  = usuario.get("perfil", "professor")

col_logo, col_titulo, col_info, col_logout = st.columns([1, 6, 3, 1])

with col_logo:
    st.markdown("# 📚")

with col_titulo:
    st.markdown("# Diário de Classe")
    st.caption("Sistema de Gestão Escolar — Notas, Frequência e Relatórios")

with col_info:
    _info_db   = info_banco()
    modo_banco = f"🟡 {_info_db['modo']}" if _info_db['usando_sqlite'] else f"🟢 {_info_db['modo']}"
    badge      = "🛡️ Admin" if perfil == "admin" else "👤 Professor"
    st.markdown(f"**{usuario['nome']}**")
    st.caption(f"{badge} &nbsp;|&nbsp; {modo_banco}")

with col_logout:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Sair", use_container_width=True, help="Encerrar sessão"):
        fazer_logout()
        st.rerun()

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════════
# ABAS PRINCIPAIS
# ═══════════════════════════════════════════════════════════════════════════════

aba1, aba2, aba3 = st.tabs([
    "📋 Cadastros",
    "📖 Diário de Classe",
    "📊 Dashboard & Relatórios",
])

with aba1:
    aba_cadastros.renderizar()

with aba2:
    aba_diario.renderizar()

with aba3:
    aba_dashboard.renderizar()
