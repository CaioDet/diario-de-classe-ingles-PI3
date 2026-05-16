"""
aba_cadastros.py — Aba 1: Cadastro de Alunos e Competências (CRUD básico).

Utiliza st.form para agrupar os campos e evitar reruns desnecessários.
"""

import streamlit as st
from repositorios import (
    listar_alunos,
    inserir_aluno,
    deletar_aluno,
    listar_competencias,
    inserir_competencia,
    deletar_competencia,
)


def renderizar() -> None:
    """Renderiza a aba de cadastros."""

    st.markdown("## 📋 Cadastros")
    st.caption("Gerencie os alunos e as competências avaliadas no período letivo.")

    col_alunos, col_competencias = st.columns(2, gap="large")

    # ─── Coluna Esquerda: Alunos ───────────────────────────────────────────────
    with col_alunos:
        _secao_alunos()

    # ─── Coluna Direita: Competências ─────────────────────────────────────────
    with col_competencias:
        _secao_competencias()


# ─── Seção de Alunos ──────────────────────────────────────────────────────────

def _secao_alunos() -> None:
    st.markdown("### 👤 Alunos")

    # Formulário de cadastro
    with st.form("form_novo_aluno", clear_on_submit=True):
        st.markdown("**Adicionar novo aluno**")
        nome      = st.text_input("Nome completo *", placeholder="Ex: Maria Silva")
        matricula = st.text_input("Matrícula *",     placeholder="Ex: 2024001")
        turma     = st.text_input("Turma *",         placeholder="Ex: 9º Ano A")
        submitted = st.form_submit_button("➕ Cadastrar Aluno", use_container_width=True)

        if submitted:
            if not nome or not matricula or not turma:
                st.error("⚠️ Preencha todos os campos obrigatórios.")
            else:
                try:
                    inserir_aluno(nome, matricula, turma)
                    st.success(f"✅ Aluno **{nome}** cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    # Captura violação de UNIQUE na matrícula
                    if "UNIQUE" in str(e).upper():
                        st.error(f"❌ Matrícula **{matricula}** já cadastrada.")
                    else:
                        st.error(f"❌ Erro ao cadastrar: {e}")

    # Lista de alunos cadastrados
    st.markdown("---")
    st.markdown("**Alunos cadastrados**")
    alunos = listar_alunos()

    if not alunos:
        st.info("Nenhum aluno cadastrado ainda.")
    else:
        for aluno in alunos:
            with st.container():
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(
                        f"**{aluno['nome']}** &nbsp;|&nbsp; "
                        f"`{aluno['matricula']}` &nbsp;|&nbsp; "
                        f"{aluno['turma']}"
                    )
                with c2:
                    # Chave única por aluno para evitar conflito de widgets
                    if st.button("🗑️", key=f"del_aluno_{aluno['id']}",
                                  help=f"Remover {aluno['nome']}"):
                        deletar_aluno(aluno["id"])
                        st.success(f"Aluno **{aluno['nome']}** removido.")
                        st.rerun()
        st.caption(f"Total: {len(alunos)} aluno(s)")


# ─── Seção de Competências ────────────────────────────────────────────────────

def _secao_competencias() -> None:
    st.markdown("### 🎯 Competências")

    with st.form("form_nova_competencia", clear_on_submit=True):
        st.markdown("**Adicionar nova competência**")
        nome_comp = st.text_input(
            "Nome da competência *",
            placeholder="Ex: Leitura e Interpretação"
        )
        submitted = st.form_submit_button("➕ Cadastrar Competência", use_container_width=True)

        if submitted:
            if not nome_comp:
                st.error("⚠️ Informe o nome da competência.")
            else:
                try:
                    inserir_competencia(nome_comp)
                    st.success(f"✅ Competência **{nome_comp}** cadastrada!")
                    st.rerun()
                except Exception as e:
                    if "UNIQUE" in str(e).upper():
                        st.error(f"❌ Competência **{nome_comp}** já existe.")
                    else:
                        st.error(f"❌ Erro ao cadastrar: {e}")

    st.markdown("---")
    st.markdown("**Competências cadastradas**")
    competencias = listar_competencias()

    if not competencias:
        st.info("Nenhuma competência cadastrada ainda.")
    else:
        for comp in competencias:
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"📌 **{comp['nome_competencia']}**")
            with c2:
                if st.button("🗑️", key=f"del_comp_{comp['id']}",
                              help=f"Remover {comp['nome_competencia']}"):
                    deletar_competencia(comp["id"])
                    st.success(f"Competência removida.")
                    st.rerun()
        st.caption(f"Total: {len(competencias)} competência(s)")
