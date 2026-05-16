"""
aba_diario.py — Aba 2: Diário de Classe (Inserção Rápida).

CORREÇÕES APLICADAS:
  BUG 1 — DataFrame vazio ("empty"):
    pivot_table() com aggfunc="first" descartava linhas quando todos os valores
    de nota eram NULL. Substituído por construção manual linha a linha usando
    um dicionário de lookup {(aluno_id, comp_id): nota}.

  BUG 2 — Células não editáveis:
    disabled=True dentro do column_config trava TODAS as células do editor,
    não só aquela coluna. Corrigido usando o parâmetro disabled=[] do
    próprio st.data_editor, que é a forma correta de marcar colunas como
    somente leitura sem afetar as demais.
"""

import streamlit as st
import pandas as pd
from datetime import date
from repositorios import (
    listar_alunos,
    listar_competencias,
    buscar_grid_diario,
    salvar_avaliacoes_em_lote,
    buscar_presenca_por_data,
    salvar_presenca_em_lote,
)


def renderizar() -> None:
    """Renderiza a aba do Diário de Classe."""

    st.markdown("## 📖 Diário de Classe")
    st.caption(
        "Edite as notas e presenças diretamente nas células. "
        "Clique em **Salvar Tudo** ao finalizar."
    )

    # Verificação inicial
    alunos       = listar_alunos()
    competencias = listar_competencias()

    if not alunos:
        st.warning("⚠️ Nenhum aluno cadastrado. Vá para a aba **Cadastros** primeiro.")
        return

    if not competencias:
        st.warning("⚠️ Nenhuma competência cadastrada. Vá para a aba **Cadastros** primeiro.")
        return

    # ─── Seleção de Data e Turma ──────────────────────────────────────────────
    st.markdown("### 📅 Data da Aula / Avaliação")

    col_data, col_turma, _ = st.columns([2, 2, 3])
    with col_data:
        data_selecionada: date = st.date_input(
            "Data",
            value=date.today(),
            format="DD/MM/YYYY",
            label_visibility="collapsed",
        )
    with col_turma:
        turmas_disponiveis = sorted(set(a["turma"] for a in alunos))
        turma_filtro = st.selectbox(
            "Filtrar por turma",
            options=["Todas"] + turmas_disponiveis,
            label_visibility="collapsed",
        )

    data_str = data_selecionada.strftime("%Y-%m-%d")

    # Aplica filtro de turma
    alunos_filtrados = (
        alunos if turma_filtro == "Todas"
        else [a for a in alunos if a["turma"] == turma_filtro]
    )

    st.divider()

    # ─── Seção de Notas ───────────────────────────────────────────────────────
    st.markdown("### 📝 Notas por Competência (0–10)")
    st.caption("💡 Clique em qualquer célula das colunas de competência para editar a nota.")

    df_notas = _construir_dataframe_notas(alunos_filtrados, competencias, data_str)
    df_notas_editado = _renderizar_editor_notas(df_notas, competencias)

    st.divider()

    # ─── Seção de Presença ────────────────────────────────────────────────────
    st.markdown("### ✅ Registro de Presença")
    st.caption("💡 Desmarque o checkbox para registrar falta.")

    df_presenca = _construir_dataframe_presenca(alunos_filtrados, data_str)
    df_presenca_editado = _renderizar_editor_presenca(df_presenca)

    st.divider()

    # ─── Botão de Salvar ──────────────────────────────────────────────────────
    col_btn, _ = st.columns([2, 5])
    with col_btn:
        salvar = st.button(
            "💾 Salvar Tudo",
            type="primary",
            use_container_width=True,
        )

    if salvar:
        with st.spinner("Salvando no banco de dados..."):
            try:
                _persistir_notas(df_notas_editado, competencias, data_str)
                _persistir_presenca(df_presenca_editado, data_str)
                st.success(
                    f"✅ Dados de **{data_selecionada.strftime('%d/%m/%Y')}** "
                    f"salvos com sucesso para **{len(alunos_filtrados)}** aluno(s)!"
                )
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {e}")


# ─── Helpers: Construção dos DataFrames ───────────────────────────────────────

def _construir_dataframe_notas(
    alunos: list[dict],
    competencias: list[dict],
    data_str: str,
) -> pd.DataFrame:
    """
    Constrói o DataFrame no formato largo (wide-format) manualmente.

    CORREÇÃO do BUG 1:
    A versão anterior usava pivot_table(aggfunc='first'), que descarta linhas
    quando TODOS os valores de nota são NULL — causando o grid vazio ("empty").

    Nova abordagem: monta um dicionário de lookup e constrói cada linha
    diretamente, garantindo que alunos sem nenhuma nota apareçam corretamente.
    """
    # Busca registros existentes no banco para a data
    registros_banco = buscar_grid_diario(data_str)

    # Índice de consulta rápida: (aluno_id, competencia_id) → nota
    # Inclui todos os registros, mesmo os com nota=None
    mapa_notas: dict[tuple, float | None] = {}
    for r in registros_banco:
        chave = (r["aluno_id"], r["competencia_id"])
        mapa_notas[chave] = r["nota"]

    # Constrói o DataFrame linha por linha
    linhas = []
    for aluno in alunos:
        linha: dict = {
            "aluno_id":   aluno["id"],
            "aluno_nome": aluno["nome"],
            "turma":      aluno["turma"],
        }
        for comp in competencias:
            chave = (aluno["id"], comp["id"])
            # get() retorna None se não existe (célula vazia = não avaliado)
            linha[comp["nome_competencia"]] = mapa_notas.get(chave, None)
        linhas.append(linha)

    df = pd.DataFrame(linhas)

    # Converte colunas de notas para float (necessário para NumberColumn)
    for comp in competencias:
        col = comp["nome_competencia"]
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Garante que aluno_id seja int (evita exibição como 1.0, 2.0...)
    df["aluno_id"] = df["aluno_id"].astype(int)

    return df


def _construir_dataframe_presenca(
    alunos: list[dict],
    data_str: str,
) -> pd.DataFrame:
    """
    Constrói o DataFrame de presença.
    Padrão: todos presentes (True) caso ainda não haja registro.
    """
    registros = buscar_presenca_por_data(data_str)
    ids_visiveis = {a["id"] for a in alunos}
    registros = [r for r in registros if r["aluno_id"] in ids_visiveis]

    if registros:
        df = pd.DataFrame(registros)
        df["Presente"] = df["status_presente"].astype(bool)
    else:
        df = pd.DataFrame(
            {
                "aluno_id":   [a["id"]    for a in alunos],
                "aluno_nome": [a["nome"]  for a in alunos],
                "turma":      [a["turma"] for a in alunos],
            }
        )
        df["Presente"] = True

    df["aluno_id"] = df["aluno_id"].astype(int)
    return df[["aluno_id", "aluno_nome", "turma", "Presente"]]


# ─── Helpers: Renderização do st.data_editor ──────────────────────────────────

def _renderizar_editor_notas(
    df: pd.DataFrame,
    competencias: list[dict],
) -> pd.DataFrame:
    """
    Renderiza o data_editor de notas.

    CORREÇÃO do BUG 2:
    A versão anterior usava disabled=True dentro do column_config de cada coluna
    de identificação. Isso causa um bug no Streamlit onde TODAS as células ficam
    travadas, não só as colunas marcadas.

    Correção: usar o parâmetro disabled=["col1", "col2"] diretamente no
    st.data_editor, que é a API correta para somente leitura seletiva.
    """
    nomes_competencias = [c["nome_competencia"] for c in competencias]

    # Configuração visual das colunas (SEM disabled aqui — bug do Streamlit)
    config_colunas = {
        "aluno_id":   st.column_config.NumberColumn("ID",    width="small"),
        "aluno_nome": st.column_config.TextColumn("Aluno",   width="large"),
        "turma":      st.column_config.TextColumn("Turma",   width="small"),
    }

    for nome_comp in nomes_competencias:
        config_colunas[nome_comp] = st.column_config.NumberColumn(
            nome_comp,
            min_value=0.0,
            max_value=10.0,
            step=0.5,
            format="%.1f",
            help=f"Nota de 0 a 10 — deixe vazio se ainda não avaliado.",
        )

    df_editado = st.data_editor(
        df,
        column_config=config_colunas,
        # ✅ FORMA CORRETA: lista de colunas somente leitura no data_editor
        disabled=["aluno_id", "aluno_nome", "turma"],
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="editor_notas",
    )

    return df_editado


def _renderizar_editor_presenca(df: pd.DataFrame) -> pd.DataFrame:
    """Renderiza o data_editor de presença com checkboxes."""
    config_colunas = {
        "aluno_id":   st.column_config.NumberColumn("ID",    width="small"),
        "aluno_nome": st.column_config.TextColumn("Aluno",   width="large"),
        "turma":      st.column_config.TextColumn("Turma",   width="small"),
        "Presente":   st.column_config.CheckboxColumn(
            "Presente",
            help="✅ Marcado = Presente | ☐ Desmarcado = Falta",
            default=True,
        ),
    }

    df_editado = st.data_editor(
        df,
        column_config=config_colunas,
        disabled=["aluno_id", "aluno_nome", "turma"],
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="editor_presenca",
    )

    return df_editado


# ─── Helpers: Persistência ────────────────────────────────────────────────────

def _persistir_notas(
    df: pd.DataFrame,
    competencias: list[dict],
    data_str: str,
) -> None:
    """
    Faz o unpivot do DataFrame editado e salva em lote no banco.
    NaN do pandas → NULL no banco (aluno não avaliado, não zero).
    """
    registros = []
    mapa_comp = {c["nome_competencia"]: c["id"] for c in competencias}

    for _, linha in df.iterrows():
        aluno_id = int(linha["aluno_id"])
        for nome_comp, comp_id in mapa_comp.items():
            valor = linha.get(nome_comp)
            nota = None if pd.isna(valor) else float(valor)
            registros.append({
                "aluno_id":       aluno_id,
                "competencia_id": comp_id,
                "nota":           nota,
            })

    salvar_avaliacoes_em_lote(registros, data_str)


def _persistir_presenca(df: pd.DataFrame, data_str: str) -> None:
    """Converte o DataFrame de presença para lista de dicts e persiste."""
    registros = [
        {
            "aluno_id": int(row["aluno_id"]),
            "presente": bool(row["Presente"]),
        }
        for _, row in df.iterrows()
    ]
    salvar_presenca_em_lote(registros, data_str)