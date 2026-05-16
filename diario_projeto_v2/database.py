"""
database.py — Módulo de configuração e acesso ao banco de dados.

Suporte a dois bancos:
  - SQLite  (desenvolvimento local — sem configuração)
  - PostgreSQL / Supabase (produção — via st.secrets ou variável de ambiente)

MIGRAÇÃO PARA PRODUÇÃO:
  Adicione no Streamlit Cloud → App Settings → Secrets:

    DATABASE_URL = "postgresql://postgres:SENHA@db.XXXX.supabase.co:5432/postgres"

  Ou localmente em .streamlit/secrets.toml (nunca suba esse arquivo pro GitHub).

DIFERENÇAS SQLite × PostgreSQL tratadas aqui:
  - AUTOINCREMENT  → SERIAL
  - ? (placeholder) → %s
  - executescript  → execução instrução por instrução
  - INTEGER 0/1    → BOOLEAN nativo
  - UPSERT: ON CONFLICT ... DO UPDATE (compatível com ambos a partir do SQLite 3.24)
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Generator


# ═══════════════════════════════════════════════════════════════════════════════
# RESOLUÇÃO DA URL DO BANCO
# ═══════════════════════════════════════════════════════════════════════════════

def _resolver_url_banco() -> str:
    # 1. Variável de ambiente (Railway, Render, Docker...)
    url_env = os.getenv("DATABASE_URL")
    if url_env:
        # Render/Heroku entregam "postgres://" — psycopg2 exige "postgresql://"
        return url_env.replace("postgres://", "postgresql://", 1)

    # 2. st.secrets (Streamlit Cloud ou secrets.toml local)
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            url = st.secrets["DATABASE_URL"]
            return url.replace("postgres://", "postgresql://", 1)
    except Exception:
        pass

    # 3. Fallback: SQLite local para desenvolvimento
    return "sqlite:///diario_classe.db"


DATABASE_URL  = _resolver_url_banco()
_USANDO_SQLITE = DATABASE_URL.startswith("sqlite")


# ═══════════════════════════════════════════════════════════════════════════════
# CONEXÃO
# ═══════════════════════════════════════════════════════════════════════════════

def _conectar_sqlite() -> sqlite3.Connection:
    caminho = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(caminho, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def obter_conexao() -> Generator:
    """
    Context manager universal: SQLite em dev, PostgreSQL em prod.
    Commit automático no sucesso, rollback em exceção.
    """
    if _USANDO_SQLITE:
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
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# DDL — CRIAÇÃO DAS TABELAS
# ═══════════════════════════════════════════════════════════════════════════════

_DDL_SQLITE = [
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        login    TEXT    NOT NULL UNIQUE,
        hash_senha TEXT  NOT NULL,
        perfil   TEXT    NOT NULL DEFAULT 'professor',
        nome     TEXT    NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS alunos (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        nome      TEXT    NOT NULL,
        matricula TEXT    NOT NULL UNIQUE,
        turma     TEXT    NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS competencias (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_competencia TEXT    NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS avaliacoes (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id       INTEGER NOT NULL REFERENCES alunos(id)       ON DELETE CASCADE,
        competencia_id INTEGER NOT NULL REFERENCES competencias(id) ON DELETE CASCADE,
        nota           REAL,
        data_avaliacao TEXT    NOT NULL,
        UNIQUE (aluno_id, competencia_id, data_avaliacao)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS presenca (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id        INTEGER NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
        data_aula       TEXT    NOT NULL,
        status_presente INTEGER NOT NULL DEFAULT 1,
        UNIQUE (aluno_id, data_aula)
    )
    """,
]

_DDL_POSTGRES = [
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id         SERIAL PRIMARY KEY,
        login      TEXT   NOT NULL UNIQUE,
        hash_senha TEXT   NOT NULL,
        perfil     TEXT   NOT NULL DEFAULT 'professor',
        nome       TEXT   NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS alunos (
        id        SERIAL PRIMARY KEY,
        nome      TEXT   NOT NULL,
        matricula TEXT   NOT NULL UNIQUE,
        turma     TEXT   NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS competencias (
        id               SERIAL PRIMARY KEY,
        nome_competencia TEXT   NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS avaliacoes (
        id             SERIAL PRIMARY KEY,
        aluno_id       INTEGER NOT NULL REFERENCES alunos(id)       ON DELETE CASCADE,
        competencia_id INTEGER NOT NULL REFERENCES competencias(id) ON DELETE CASCADE,
        nota           REAL,
        data_avaliacao DATE    NOT NULL,
        UNIQUE (aluno_id, competencia_id, data_avaliacao)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS presenca (
        id              SERIAL PRIMARY KEY,
        aluno_id        INTEGER NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
        data_aula       DATE    NOT NULL,
        status_presente BOOLEAN NOT NULL DEFAULT TRUE,
        UNIQUE (aluno_id, data_aula)
    )
    """,
]


def inicializar_banco() -> None:
    """Cria todas as tabelas e insere o usuário admin padrão se necessário."""
    instrucoes = _DDL_SQLITE if _USANDO_SQLITE else _DDL_POSTGRES

    with obter_conexao() as conn:
        if _USANDO_SQLITE:
            for ddl in instrucoes:
                conn.execute(ddl)
            conn.commit()
        else:
            cur = conn.cursor()
            for ddl in instrucoes:
                cur.execute(ddl)

    # Garante que o admin padrão exista
    _seed_usuario_admin()


def _seed_usuario_admin() -> None:
    """
    Insere o usuário admin padrão se a tabela estiver vazia.
    Senha padrão: admin123 (oriente o usuário a trocar em produção).
    """
    import hashlib
    hash_admin = hashlib.sha256("admin123".encode()).hexdigest()
    hash_prof  = hashlib.sha256("prof123".encode()).hexdigest()

    if _USANDO_SQLITE:
        sql = "INSERT OR IGNORE INTO usuarios (login, hash_senha, perfil, nome) VALUES (?,?,?,?)"
    else:
        sql = """
            INSERT INTO usuarios (login, hash_senha, perfil, nome)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (login) DO NOTHING
        """

    executar(sql, ("admin",     hash_admin, "admin",     "Administrador"))
    executar(sql, ("professor", hash_prof,  "professor", "Professor(a)"))


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS DE QUERY — adaptam automaticamente o placeholder (? vs %s)
# ═══════════════════════════════════════════════════════════════════════════════

def _adaptar_sql(sql: str) -> str:
    """Converte placeholders ? para %s quando usar PostgreSQL."""
    if _USANDO_SQLITE:
        return sql
    return sql.replace("?", "%s")


def buscar_todos(sql: str, params: tuple = ()) -> list[dict]:
    """SELECT → lista de dicionários."""
    sql = _adaptar_sql(sql)
    with obter_conexao() as conn:
        cursor = conn.execute(sql, params)
        if _USANDO_SQLITE:
            colunas = [d[0] for d in cursor.description]
            return [dict(zip(colunas, row)) for row in cursor.fetchall()]
        else:
            return [dict(row) for row in cursor.fetchall()]


def executar(sql: str, params: tuple = ()) -> None:
    """INSERT / UPDATE / DELETE."""
    sql = _adaptar_sql(sql)
    with obter_conexao() as conn:
        conn.execute(sql, params)


def executar_em_lote(sql: str, lista_params: list[tuple]) -> None:
    """executemany — ideal para salvar o diário em lote."""
    sql = _adaptar_sql(sql)
    with obter_conexao() as conn:
        conn.executemany(sql, lista_params)
