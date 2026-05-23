"""
repositorios.py — Camada de acesso a dados (Repository Pattern).

Separa completamente a lógica de negócio das queries SQL.
Cada função representa uma operação bem definida no banco.
"""

from datetime import date
from database import buscar_todos, executar, executar_em_lote


# ═══════════════════════════════════════════════════════════════════════════════
# ALUNOS
# ═══════════════════════════════════════════════════════════════════════════════

def listar_alunos() -> list[dict]:
    """Retorna todos os alunos ordenados por turma e nome."""
    return buscar_todos(
        "SELECT id, nome, matricula, turma FROM alunos ORDER BY turma, nome"
    )


def buscar_aluno_por_id(aluno_id: int) -> dict | None:
    """Retorna um aluno pelo ID ou None se não encontrado."""
    resultado = buscar_todos(
        "SELECT id, nome, matricula, turma FROM alunos WHERE id = ?", (aluno_id,)
    )
    return resultado[0] if resultado else None


def inserir_aluno(nome: str, matricula: str, turma: str) -> None:
    """Cadastra um novo aluno. Lança exceção se matrícula já existir."""
    executar(
        "INSERT INTO alunos (nome, matricula, turma) VALUES (?, ?, ?)",
        (nome.strip(), matricula.strip(), turma.strip()),
    )


def deletar_aluno(aluno_id: int) -> None:
    """Remove um aluno e todos os seus dados (CASCADE)."""
    executar("DELETE FROM alunos WHERE id = ?", (aluno_id,))


# ═══════════════════════════════════════════════════════════════════════════════
# COMPETÊNCIAS
# ═══════════════════════════════════════════════════════════════════════════════

def listar_competencias() -> list[dict]:
    """Retorna todas as competências cadastradas."""
    return buscar_todos(
        "SELECT id, nome_competencia FROM competencias ORDER BY nome_competencia"
    )


def inserir_competencia(nome: str) -> None:
    """Cadastra uma nova competência. Lança exceção se nome já existir."""
    executar(
        "INSERT INTO competencias (nome_competencia) VALUES (?)",
        (nome.strip(),),
    )


def deletar_competencia(competencia_id: int) -> None:
    """Remove uma competência e todas as avaliações associadas."""
    executar("DELETE FROM competencias WHERE id = ?", (competencia_id,))


# ═══════════════════════════════════════════════════════════════════════════════
# AVALIAÇÕES
# ═══════════════════════════════════════════════════════════════════════════════

def salvar_avaliacoes_em_lote(
    registros: list[dict], data_avaliacao: str
) -> None:
    """
    Insere ou atualiza notas em lote usando UPSERT.
    registros: lista de {'aluno_id': int, 'competencia_id': int, 'nota': float|None}
    data_avaliacao: string no formato 'YYYY-MM-DD'
    """
    sql = """
        INSERT INTO avaliacoes (aluno_id, competencia_id, nota, data_avaliacao)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(aluno_id, competencia_id, data_avaliacao)
        DO UPDATE SET nota = excluded.nota
    """
    params = [
        (r["aluno_id"], r["competencia_id"], r.get("nota"), data_avaliacao)
        for r in registros
    ]
    executar_em_lote(sql, params)


def buscar_notas_por_aluno(aluno_id: int) -> list[dict]:
    """
    Retorna todas as notas de um aluno com o nome da competência.
    Notas nulas indicam que o aluno ainda não foi avaliado naquela competência.
    """
    return buscar_todos(
        """
        SELECT
            c.nome_competencia,
            a.nota,
            a.data_avaliacao
        FROM avaliacoes a
        JOIN competencias c ON c.id = a.competencia_id
        WHERE a.aluno_id = ?
        ORDER BY a.data_avaliacao, c.nome_competencia
        """,
        (aluno_id,),
    )


def buscar_media_por_competencia(aluno_id: int) -> list[dict]:
    """
    Retorna a média de notas por competência de um aluno.
    Ignora registros com nota NULL (aluno não avaliado).
    Ideal para o gráfico de radar.
    """
    return buscar_todos(
        """
        SELECT
            c.nome_competencia,
            ROUND(AVG(a.nota), 2) AS media_nota,
            COUNT(a.nota)         AS total_avaliacoes
        FROM competencias c
        LEFT JOIN avaliacoes a
            ON a.competencia_id = c.id AND a.aluno_id = ?
        GROUP BY c.id, c.nome_competencia
        ORDER BY c.nome_competencia
        """,
        (aluno_id,),
    )


def buscar_grid_diario(data_avaliacao: str) -> list[dict]:
    """
    Retorna o grid para o Diário de Classe:
    uma linha por aluno × competência com a nota do dia (ou NULL).
    """
    return buscar_todos(
        """
        SELECT
            al.id       AS aluno_id,
            al.nome     AS aluno_nome,
            al.turma,
            c.id        AS competencia_id,
            c.nome_competencia,
            av.nota
        FROM alunos al
        CROSS JOIN competencias c
        LEFT JOIN avaliacoes av
            ON av.aluno_id = al.id
            AND av.competencia_id = c.id
            AND av.data_avaliacao = ?
        ORDER BY al.turma, al.nome, c.nome_competencia
        """,
        (data_avaliacao,),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PRESENÇA
# ═══════════════════════════════════════════════════════════════════════════════

def salvar_presenca_em_lote(
    registros: list[dict], data_aula: str
) -> None:
    """
    Insere ou atualiza registros de presença em lote.
    registros: lista de {'aluno_id': int, 'presente': bool}
    """
    sql = """
        INSERT INTO presenca (aluno_id, data_aula, status_presente)
        VALUES (?, ?, ?)
        ON CONFLICT(aluno_id, data_aula)
        DO UPDATE SET status_presente = excluded.status_presente
    """
    params = [
        (r["aluno_id"], data_aula, 1 if r.get("presente", True) else 0)
        for r in registros
    ]
    executar_em_lote(sql, params)


def buscar_frequencia_aluno(aluno_id: int) -> dict:
    """
    Calcula o percentual de frequência de um aluno.
    Retorna dict com total_aulas, presencas e percentual.
    """
    resultado = buscar_todos(
        """
        SELECT
            COUNT(*)                                            AS total_aulas,
            SUM(CASE WHEN status_presente THEN 1 ELSE 0 END)   AS presencas,
            ROUND(
                100.0 * SUM(CASE WHEN status_presente THEN 1 ELSE 0 END)
                / NULLIF(COUNT(*), 0),
                1
            )                                                   AS percentual
        FROM presenca
        WHERE aluno_id = ?
        """,
        (aluno_id,),
    )
    if resultado:
        row = resultado[0]
        return {
            "total_aulas": row.get("total_aulas") or 0,
            "presencas": row.get("presencas") or 0,
            "percentual": row.get("percentual") or 0.0,
        }
    return {"total_aulas": 0, "presencas": 0, "percentual": 0.0}


def buscar_presenca_por_data(data_aula: str) -> list[dict]:
    """
    Retorna os registros de presença de todos os alunos em uma data.
    Alunos sem registro são retornados com status_presente=1 (presente por padrão).
    """
    return buscar_todos(
        """
        SELECT
            al.id   AS aluno_id,
            al.nome AS aluno_nome,
            al.turma,
            COALESCE(p.status_presente, TRUE) AS status_presente
        FROM alunos al
        LEFT JOIN presenca p
            ON p.aluno_id = al.id AND p.data_aula = ?
        ORDER BY al.turma, al.nome
        """,
        (data_aula,),
    )
