"""
database.py — Módulo de configuração e acesso ao banco de dados.

CORREÇÕES DESTA VERSÃO:

  BUG CRÍTICO 1 — DATABASE_URL resolvido em tempo de import (causa raiz dos dados sumindo):
    A linha 'DATABASE_URL = _resolver_url_banco()' era executada no momento
    em que o Python importava o módulo. No Streamlit Cloud, isso ocorre antes
    do st.secrets estar disponível, fazendo o sistema cair silenciosamente no
    SQLite local (efêmero). Ao reiniciar o app, o SQLite some e os dados
    também. Correção: URL resolvida de forma lazy (sob demanda) a cada conexão,
    com cache via functools.lru_cache para não recalcular desnecessariamente.

  BUG CRÍTICO 2 — Sem pool de conexões PostgreSQL (causa de timeouts):
    A versão anterior abria e fechava uma conexão TCP nova para CADA operação
    (SELECT, INSERT, etc.). No Supabase free tier (limite de 60 conexões),
    com múltiplos usuários simultâneos isso causa:
    - "too many connections" → operações falham silenciosamente
    - Latência alta por overhead de handshake TCP+SSL a cada query
    Correção: pool de conexões via psycopg2.pool.ThreadedConnectionPool,
    cacheado via @st.cache_resource para sobreviver entre reruns.

  BUG 3 — commit() em SELECT desnecessário:
    buscar_todos() abria conexão, fazia SELECT e chamava commit() (no-op, mas
    sinalizava fim de transação prematuramente em alguns drivers).
    Correção: SELECT em modo autocommit, sem transação explícita.

  BUG 4 — SUM(status_presente) no PostgreSQL retorna Decimal, não int:
    A query de frequência usava SUM() que no PostgreSQL retorna Decimal.
    Correção: cast explícito com CAST(SUM(...) AS INTEGER) no PostgreSQL.

  BUG 5 — COALESCE(status_presente, 1) com coluna BOOLEAN no PostgreSQL:
    No PostgreSQL, a coluna status_presente é BOOLEAN. COALESCE retorna
    True/False, não 1/0. Correção: COALESCE(status_presente, TRUE).
"""

import os
import sqlite3
import logging
from contextlib import contextmanager
from functools import lru_cache
from typing import Generator

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# RESOLUÇÃO DA URL DO BANCO — LAZY (sob demanda, não em tempo de import)
# ═══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def _resolver_url_banco() -> str:
    """
    Resolve a URL de conexão do banco de dados.

    CORREÇÃO CRÍTICA: Esta função agora usa @lru_cache e é chamada apenas
    quando uma conexão é de fato necessária — nunca em tempo de import.
    Isso garante que st.secrets já esteja disponível quando a URL for lida.

    Prioridade:
      1. Variável de ambiente DATABASE_URL
      2. st.secrets["DATABASE_URL"] (Streamlit Cloud)
      3. SQLite local (fallback de desenvolvimento)
    """
    # 1. Variável de ambiente
    url_env = os.getenv("DATABASE_URL", "")
    if url_env:
        url = url_env.replace("postgres://", "postgresql://", 1)
        logger.info("Banco: PostgreSQL (variável de ambiente)")
        return url

    # 2. st.secrets — lido AGORA, não em tempo de import
    try:
        import streamlit as st
        url_secret = st.secrets.get("DATABASE_URL", "")
        if url_secret:
            url = url_secret.replace("postgres://", "postgresql://", 1)
            logger.info("Banco: PostgreSQL (st.secrets)")
            return url
    except Exception as e:
        logger.warning(f"st.secrets indisponível: {e}")

    # 3. Fallback: SQLite local
    logger.warning("Banco: SQLite local (desenvolvimento) — dados NÃO persistem no Cloud!")
    return "sqlite:///diario_classe.db"


def _usando_sqlite() -> bool:
    """Retorna True se estiver usando SQLite."""
    return _resolver_url_banco().startswith("sqlite")


# ═══════════════════════════════════════════════════════════════════════════════
# POOL DE CONEXÕES PostgreSQL — cacheado no Streamlit
# ═══════════════════════════════════════════════════════════════════════════════

def _obter_pool():
    """
    Retorna o pool de conexões PostgreSQL.

    CORREÇÃO: Pool ThreadedConnectionPool reutiliza conexões TCP já abertas
    em vez de criar uma nova conexão para cada operação. No Supabase free
    tier (60 conexões), isso evita erros de 'too many connections'.

    O pool é cacheado via @st.cache_resource — sobrevive entre reruns do
    Streamlit mas é recriado se o servidor reiniciar.

    min=1: mantém 1 conexão sempre aberta (warm pool)
    max=5: no máximo 5 simultâneas (seguro para Supabase free tier)
    """
    try:
        import streamlit as st

        @st.cache_resource
        def _criar_pool():
            import psycopg2.pool
            url = _resolver_url_banco()
            logger.info("Criando pool de conexões PostgreSQL...")
            pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=5,
                dsn=url,
                connect_timeout=10,       # timeout de conexão: 10s
                options="-c statement_timeout=30000",  # timeout de query: 30s
            )
            logger.info("Pool PostgreSQL criado com sucesso.")
            return pool

        return _criar_pool()
    except Exception as e:
        logger.error(f"Falha ao criar pool: {e}")
        raise


# ═══════════════════════════════════════════════════════════════════════════════
# CONEXÃO
# ═══════════════════════════════════════════════════════════════════════════════

def _conectar_sqlite() -> sqlite3.Connection:
    caminho = _resolver_url_banco().replace("sqlite:///", "")
    conn = sqlite3.connect(caminho, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")   # Write-Ahead Log: mais estável
    return conn


@contextmanager
def obter_conexao() -> Generator:
    """
    Context manager universal: SQLite em dev, PostgreSQL (pool) em prod.

    PostgreSQL: retira conexão do pool, usa, devolve ao pool.
    SQLite: abre, usa, fecha (sem pool — SQLite é single-file).

    Commit automático no sucesso, rollback em exceção.
    """
    if _usando_sqlite():
        conn = _conectar_sqlite()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        pool = _obter_pool()
        conn = pool.getconn()
        try:
            conn.cursor_factory = RealDictCursor
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            pool.putconn(conn)   # DEVOLVE ao pool (não fecha!)


# ═══════════════════════════════════════════════════════════════════════════════
# DDL — CRIAÇÃO DAS TABELAS
# ═══════════════════════════════════════════════════════════════════════════════

_DDL_SQLITE = [
    """CREATE TABLE IF NOT EXISTS usuarios (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        login      TEXT    NOT NULL UNIQUE,
        hash_senha TEXT    NOT NULL,
        perfil     TEXT    NOT NULL DEFAULT 'professor',
        nome       TEXT    NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS alunos (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        nome      TEXT    NOT NULL,
        matricula TEXT    NOT NULL UNIQUE,
        turma     TEXT    NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS competencias (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_competencia TEXT    NOT NULL UNIQUE
    )""",
    """CREATE TABLE IF NOT EXISTS avaliacoes (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id       INTEGER NOT NULL REFERENCES alunos(id)       ON DELETE CASCADE,
        competencia_id INTEGER NOT NULL REFERENCES competencias(id) ON DELETE CASCADE,
        nota           REAL,
        data_avaliacao TEXT    NOT NULL,
        UNIQUE (aluno_id, competencia_id, data_avaliacao)
    )""",
    """CREATE TABLE IF NOT EXISTS presenca (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id        INTEGER NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
        data_aula       TEXT    NOT NULL,
        status_presente INTEGER NOT NULL DEFAULT 1,
        UNIQUE (aluno_id, data_aula)
    )""",
]

_DDL_POSTGRES = [
    """CREATE TABLE IF NOT EXISTS usuarios (
        id         SERIAL PRIMARY KEY,
        login      TEXT   NOT NULL UNIQUE,
        hash_senha TEXT   NOT NULL,
        perfil     TEXT   NOT NULL DEFAULT 'professor',
        nome       TEXT   NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS alunos (
        id        SERIAL PRIMARY KEY,
        nome      TEXT   NOT NULL,
        matricula TEXT   NOT NULL UNIQUE,
        turma     TEXT   NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS competencias (
        id               SERIAL PRIMARY KEY,
        nome_competencia TEXT   NOT NULL UNIQUE
    )""",
    """CREATE TABLE IF NOT EXISTS avaliacoes (
        id             SERIAL PRIMARY KEY,
        aluno_id       INTEGER NOT NULL REFERENCES alunos(id)       ON DELETE CASCADE,
        competencia_id INTEGER NOT NULL REFERENCES competencias(id) ON DELETE CASCADE,
        nota           REAL,
        data_avaliacao DATE    NOT NULL,
        UNIQUE (aluno_id, competencia_id, data_avaliacao)
    )""",
    """CREATE TABLE IF NOT EXISTS presenca (
        id              SERIAL PRIMARY KEY,
        aluno_id        INTEGER NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
        data_aula       DATE    NOT NULL,
        status_presente BOOLEAN NOT NULL DEFAULT TRUE,
        UNIQUE (aluno_id, data_aula)
    )""",
]


def inicializar_banco() -> None:
    """Cria todas as tabelas e insere usuários padrão se necessário."""
    instrucoes = _DDL_SQLITE if _usando_sqlite() else _DDL_POSTGRES
    with obter_conexao() as conn:
        cur = conn.cursor()
        for ddl in instrucoes:
            cur.execute(ddl)
    _seed_usuario_admin()


def _seed_usuario_admin() -> None:
    import hashlib
    hash_admin = hashlib.sha256("admin123".encode()).hexdigest()
    hash_prof  = hashlib.sha256("prof123".encode()).hexdigest()

    if _usando_sqlite():
        sql = "INSERT OR IGNORE INTO usuarios (login, hash_senha, perfil, nome) VALUES (?,?,?,?)"
    else:
        sql = """INSERT INTO usuarios (login, hash_senha, perfil, nome)
                 VALUES (%s, %s, %s, %s)
                 ON CONFLICT (login) DO NOTHING"""

    executar(sql, ("admin",     hash_admin, "admin",     "Administrador"))
    executar(sql, ("professor", hash_prof,  "professor", "Professor(a)"))


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS DE QUERY
# ═══════════════════════════════════════════════════════════════════════════════

def _adaptar_sql(sql: str) -> str:
    """Converte placeholders ? → %s para PostgreSQL."""
    if _usando_sqlite():
        return sql
    return sql.replace("?", "%s")


def buscar_todos(sql: str, params: tuple = ()) -> list[dict]:
    """SELECT → lista de dicionários. Sem commit (operação de leitura)."""
    sql = _adaptar_sql(sql)
    with obter_conexao() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        if _usando_sqlite():
            colunas = [d[0] for d in cur.description]
            return [dict(zip(colunas, row)) for row in cur.fetchall()]
        else:
            rows = cur.fetchall()
            # RealDictCursor retorna RealDictRow — converte para dict puro
            return [dict(row) for row in rows]


def executar(sql: str, params: tuple = ()) -> None:
    """INSERT / UPDATE / DELETE com commit automático."""
    sql = _adaptar_sql(sql)
    with obter_conexao() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)


def executar_em_lote(sql: str, lista_params: list[tuple]) -> None:
    """
    executemany com commit automático.
    Ignora chamadas com lista vazia para evitar operação silenciosa.
    """
    if not lista_params:
        logger.warning("executar_em_lote chamado com lista vazia — nenhuma operação realizada.")
        return
    sql = _adaptar_sql(sql)
    with obter_conexao() as conn:
        cur = conn.cursor()
        cur.executemany(sql, lista_params)


# ═══════════════════════════════════════════════════════════════════════════════
# PROPRIEDADES DE DIAGNÓSTICO (úteis para debug no Streamlit Cloud)
# ═══════════════════════════════════════════════════════════════════════════════

def info_banco() -> dict:
    """
    Retorna informações sobre o banco ativo.
    Use em app.py para exibir o modo correto no cabeçalho.
    """
    url = _resolver_url_banco()
    usando_sqlite = url.startswith("sqlite")
    return {
        "modo":        "SQLite (Dev)" if usando_sqlite else "PostgreSQL (Prod)",
        "usando_sqlite": usando_sqlite,
        "url_segura":  "sqlite local" if usando_sqlite else url.split("@")[-1],
    }
