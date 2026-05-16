"""
autenticacao.py — Módulo de autenticação e controle de acesso.

Estratégia:
  - Senhas armazenadas com hash SHA-256 (nunca em texto puro).
  - Sessão controlada via st.session_state (nativa do Streamlit).
  - Usuários definidos em st.secrets (produção) ou em lista local (dev).
  - Perfis: 'admin' (acesso total) e 'professor' (acesso às abas).

Configuração no secrets.toml:
  [usuarios]
  admin     = "hash_da_senha_admin"
  professor = "hash_da_senha_professor"

  [perfis]
  admin     = "admin"
  professor = "professor"
"""

import hashlib
import streamlit as st


# ─── Usuários padrão para desenvolvimento (quando não há secrets) ─────────────
# ATENÇÃO: em produção, SEMPRE use st.secrets. Estes são apenas para dev local.
# Senhas padrão: admin=admin123 | professor=prof123
_USUARIOS_DEV = {
    "admin":     {"hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9", "perfil": "admin",     "nome": "Administrador"},
    "professor": {"hash": "00624b02e1f9b996a3278f559d5d55313552ad2c0bafc82adfd975c12df61eaf", "perfil": "professor", "nome": "Professor(a)"},
}

# Senha admin123 em SHA-256 real para referência
# hashlib.sha256("admin123".encode()).hexdigest()


def _hash_senha(senha: str) -> str:
    """Gera o hash SHA-256 de uma senha."""
    return hashlib.sha256(senha.encode()).hexdigest()


def _carregar_usuarios() -> dict:
    """
    Carrega os usuários do st.secrets (produção) ou do dicionário local (dev).
    Em produção, o secrets.toml deve ter a seção [usuarios] e [perfis].
    """
    try:
        if "usuarios" in st.secrets:
            usuarios = {}
            for login, hash_senha in st.secrets["usuarios"].items():
                perfil = st.secrets.get("perfis", {}).get(login, "professor")
                nomes  = st.secrets.get("nomes",  {})
                nome   = nomes.get(login, login.capitalize())
                usuarios[login] = {"hash": hash_senha, "perfil": perfil, "nome": nome}
            return usuarios
    except Exception:
        pass

    return _USUARIOS_DEV


def verificar_login(usuario: str, senha: str) -> dict | None:
    """
    Verifica as credenciais.
    Retorna o dicionário do usuário se válido, ou None se inválido.
    """
    usuarios = _carregar_usuarios()
    dados = usuarios.get(usuario.strip().lower())
    if dados and dados["hash"] == _hash_senha(senha):
        return dados
    return None


def esta_autenticado() -> bool:
    """Retorna True se há um usuário autenticado na sessão atual."""
    return st.session_state.get("autenticado", False)


def obter_usuario_atual() -> dict | None:
    """Retorna os dados do usuário logado ou None."""
    return st.session_state.get("usuario_atual", None)


def fazer_login(usuario: str, dados: dict) -> None:
    """Registra o usuário na sessão do Streamlit."""
    st.session_state["autenticado"]  = True
    st.session_state["usuario_atual"] = {
        "login":  usuario,
        "nome":   dados["nome"],
        "perfil": dados["perfil"],
    }


def fazer_logout() -> None:
    """Remove o usuário da sessão."""
    st.session_state["autenticado"]   = False
    st.session_state["usuario_atual"] = None


def gerar_hash(senha: str) -> str:
    """Utilitário para gerar o hash de uma nova senha (use no terminal)."""
    return _hash_senha(senha)


# ─── Tela de Login ────────────────────────────────────────────────────────────

def renderizar_tela_login() -> None:
    """
    Renderiza a tela de login centralizada.
    Bloqueia o acesso ao restante da aplicação até autenticação válida.
    """
    # CSS da tela de login
    st.markdown("""
    <style>
    /* Esconde a barra lateral e o menu no login */
    [data-testid="stSidebar"]        { display: none; }
    [data-testid="stToolbar"]        { display: none; }

    /* Centraliza o card de login */
    .login-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 80vh;
    }
    .login-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #0f2341 100%);
        border: 1px solid #2563EB44;
        border-radius: 1rem;
        padding: 2.5rem 2rem;
        max-width: 420px;
        width: 100%;
        box-shadow: 0 8px 32px rgba(37, 99, 235, 0.15);
        text-align: center;
    }
    .login-titulo {
        font-size: 2rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0.25rem;
    }
    .login-subtitulo {
        font-size: 0.95rem;
        color: #94A3B8;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Layout centralizado com colunas
    _, col_centro, _ = st.columns([1, 2, 1])

    with col_centro:
        st.markdown("<br><br>", unsafe_allow_html=True)

        # Cabeçalho do card
        st.markdown("""
        <div style='text-align:center; margin-bottom: 1rem;'>
            <div style='font-size:3.5rem;'>📚</div>
            <div style='font-size:1.8rem; font-weight:700; color:#FFFFFF;'>Diário de Classe</div>
            <div style='font-size:0.9rem; color:#94A3B8; margin-top:0.25rem;'>
                Sistema de Gestão Escolar
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Formulário de login
        with st.form("form_login", clear_on_submit=False):
            usuario = st.text_input(
                "👤 Usuário",
                placeholder="Digite seu usuário",
                autocomplete="username",
            )
            senha = st.text_input(
                "🔒 Senha",
                type="password",
                placeholder="Digite sua senha",
                autocomplete="current-password",
            )

            st.markdown("<br>", unsafe_allow_html=True)
            entrar = st.form_submit_button(
                "➡️ Entrar",
                use_container_width=True,
                type="primary",
            )

        if entrar:
            if not usuario or not senha:
                st.error("⚠️ Preencha usuário e senha.")
            else:
                dados = verificar_login(usuario, senha)
                if dados:
                    fazer_login(usuario.strip().lower(), dados)
                    st.success(f"✅ Bem-vindo(a), **{dados['nome']}**!")
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("🔐 Acesso restrito. Em caso de dúvidas, contate o administrador.")
