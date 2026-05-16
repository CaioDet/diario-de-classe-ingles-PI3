"""
app.py — Arquivo principal da aplicação "Diário de Classe".

Ponto de entrada do Streamlit. Responsável por:
  1. Inicializar o banco de dados na primeira execução.
  2. Configurar o layout da página.
  3. Renderizar o menu de abas e delegar para os módulos específicos.

Execução:
    streamlit run app.py
"""

import streamlit as st
from database import inicializar_banco, DATABASE_URL

# ─── Módulos das abas ─────────────────────────────────────────────────────────
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

# ─── Estilos globais ──────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Tipografia e paleta global */
    :root {
        --cor-primaria: #2563EB;
        --cor-acento:   #16A34A;
        --cor-aviso:    #DC2626;
    }

    /* Cabeçalho principal */
    .header-app {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1.5rem 0 1rem 0;
        border-bottom: 2px solid var(--cor-primaria);
        margin-bottom: 1rem;
    }

    /* Remove padding excessivo do container principal */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Estilo das abas */
    [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    [data-baseweb="tab"] {
        font-size: 1rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════════════════
# INICIALIZAÇÃO DO BANCO DE DADOS
# Usa st.cache_resource para rodar APENAS uma vez por sessão do servidor.
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def _inicializar() -> None:
    """Cria as tabelas no banco de dados se ainda não existirem."""
    inicializar_banco()
    return True


_inicializar()


# ═══════════════════════════════════════════════════════════════════════════════
# CABEÇALHO DA APLICAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════

col_logo, col_titulo, col_info = st.columns([1, 8, 3])

with col_logo:
    st.markdown("# 📚")

with col_titulo:
    st.markdown("# Diário de Classe")
    st.caption("Sistema de gestão escolar — Notas, Frequência e Relatórios")

with col_info:
    # Mostra o ambiente ativo (SQLite ou PostgreSQL)
    modo_banco = "🟡 SQLite (Dev)" if "sqlite" in DATABASE_URL.lower() else "🟢 PostgreSQL (Prod)"
    st.markdown(f"**Banco:** {modo_banco}")

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════════
# MENU DE ABAS
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
