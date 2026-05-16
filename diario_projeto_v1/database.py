"""
database.py — Módulo de configuração e acesso ao banco de dados.

Estratégia de portabilidade:
  - Em desenvolvimento: SQLite local (nenhuma configuração necessária).
  - Em produção: PostgreSQL via st.secrets["DATABASE_URL"] ou
    variável de ambiente DATABASE_URL.

Para migrar para produção, basta definir a variável de ambiente:
    export DATABASE_URL="postgresql://usuario:senha@host:5432/diario_db"
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import Generator

# ─── Resolução da string de conexão ───────────────────────────────────────────
# Prioridade: variável de ambiente > st.secrets > SQLite local (fallback).

def _resolver_url_banco() -> str:
    """
    Retorna a URL de conexão do banco de dados.
    Verifica variáveis de ambiente e st.secrets (Streamlit Cloud).
    Faz fallback para SQLite local em desenvolvimento.
    """
    # 1. Variável de ambiente (Docker, Railway, Heroku, etc.)
    url_env = os.getenv("DATABASE_URL")
    if url_env:
        return url_env

    # 2. st.secrets (Streamlit Cloud / secrets.toml local)
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass  # Streamlit não inicializado ainda — ignora

    # 3. Fallback: SQLite local para desenvolvimento
    return "sqlite:///diario_classe.db"


DATABASE_URL = _resolver_url_banco()

# ─── Detecção do driver ────────────────────────────────────────────────────────

_USANDO_SQLITE = DATABASE_URL.startswith("sqlite")


# ─── Conexão nativa sqlite3 (dev) ─────────────────────────────────────────────

def _conectar_sqlite() -> sqlite3.Connection:
    """Cria e retorna uma conexão SQLite com Row Factory habilitado."""
    caminho = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(caminho, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
    conn.execute("PRAGMA foreign_keys = ON")  # Garante integridade referencial
    return conn


@contextmanager
def obter_conexao() -> Generator:
    """
    Context manager que fornece uma conexão com o banco de dados.
    Faz commit automático em caso de sucesso e rollback em exceções.

    Uso:
        with obter_conexao() as conn:
            conn.execute("SELECT ...")
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
        # PostgreSQL via psycopg2 / psycopg3
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


# ─── DDL: Criação das tabelas ──────────────────────────────────────────────────

_SQL_CRIAR_TABELAS = """
CREATE TABLE IF NOT EXISTS alunos (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT    NOT NULL,
    matricula TEXT    NOT NULL UNIQUE,
    turma     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS competencias (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_competencia TEXT    NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS avaliacoes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id        INTEGER NOT NULL REFERENCES alunos(id)       ON DELETE CASCADE,
    competencia_id  INTEGER NOT NULL REFERENCES competencias(id) ON DELETE CASCADE,
    nota            REAL,                          -- NULL = ainda não avaliado
    data_avaliacao  TEXT    NOT NULL,              -- formato ISO: YYYY-MM-DD
    UNIQUE (aluno_id, competencia_id, data_avaliacao)
);

CREATE TABLE IF NOT EXISTS presenca (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id       INTEGER NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
    data_aula      TEXT    NOT NULL,               -- formato ISO: YYYY-MM-DD
    status_presente INTEGER NOT NULL DEFAULT 1,    -- 1 = presente, 0 = ausente
    UNIQUE (aluno_id, data_aula)
);
"""

# Para PostgreSQL, AUTOINCREMENT → SERIAL e BOOLEAN nativo
_SQL_CRIAR_TABELAS_PG = """
CREATE TABLE IF NOT EXISTS alunos (
    id        SERIAL PRIMARY KEY,
    nome      TEXT   NOT NULL,
    matricula TEXT   NOT NULL UNIQUE,
    turma     TEXT   NOT NULL
);

CREATE TABLE IF NOT EXISTS competencias (
    id               SERIAL PRIMARY KEY,
    nome_competencia TEXT   NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS avaliacoes (
    id              SERIAL PRIMARY KEY,
    aluno_id        INTEGER NOT NULL REFERENCES alunos(id)       ON DELETE CASCADE,
    competencia_id  INTEGER NOT NULL REFERENCES competencias(id) ON DELETE CASCADE,
    nota            REAL,
    data_avaliacao  DATE    NOT NULL,
    UNIQUE (aluno_id, competencia_id, data_avaliacao)
);

CREATE TABLE IF NOT EXISTS presenca (
    id              SERIAL PRIMARY KEY,
    aluno_id        INTEGER NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
    data_aula       DATE    NOT NULL,
    status_presente BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (aluno_id, data_aula)
);
"""


def inicializar_banco() -> None:
    """
    Cria todas as tabelas caso ainda não existam.
    Deve ser chamado uma única vez ao iniciar a aplicação.
    """
    sql = _SQL_CRIAR_TABELAS if _USANDO_SQLITE else _SQL_CRIAR_TABELAS_PG

    with obter_conexao() as conn:
        if _USANDO_SQLITE:
            # executescript não usa o cursor padrão — chamada direta
            conn.executescript(sql)
        else:
            cursor = conn.cursor()
            for instrucao in sql.strip().split(";"):
                instrucao = instrucao.strip()
                if instrucao:
                    cursor.execute(instrucao)


# ─── Funções auxiliares de consulta ───────────────────────────────────────────

def buscar_todos(sql: str, params: tuple = ()) -> list[dict]:
    """Executa uma query SELECT e retorna lista de dicionários."""
    with obter_conexao() as conn:
        cursor = conn.execute(sql, params)
        colunas = [desc[0] for desc in cursor.description]
        return [dict(zip(colunas, row)) for row in cursor.fetchall()]


def executar(sql: str, params: tuple = ()) -> None:
    """Executa uma instrução INSERT/UPDATE/DELETE."""
    with obter_conexao() as conn:
        conn.execute(sql, params)


def executar_em_lote(sql: str, lista_params: list[tuple]) -> None:
    """Executa uma instrução em lote (executemany) — ideal para salvar o diário."""
    with obter_conexao() as conn:
        conn.executemany(sql, lista_params)
