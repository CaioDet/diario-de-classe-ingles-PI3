"""
aba_dashboard.py — Aba 3: Dashboard Individual e Relatórios.

PASSO 4 — Geração de gráficos analíticos por aluno.

Gráficos incluídos:
  1. Gráfico de Radar (Teia de Aranha) — média por competência.
  2. Gráfico de Barras — histórico temporal de notas.
  3. st.metric — indicadores de frequência e desempenho.

Layout otimizado para impressão via Ctrl+P (CSS media print embutido).
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from repositorios import (
    listar_alunos,
    buscar_notas_por_aluno,
    buscar_media_por_competencia,
    buscar_frequencia_aluno,
    buscar_aluno_por_id,
)

# ─── Paleta de cores consistente ──────────────────────────────────────────────
COR_PRIMARIA  = "#2563EB"   # Azul forte
COR_ACENTO    = "#16A34A"   # Verde sucesso
COR_AVISO     = "#DC2626"   # Vermelho alerta
COR_RADAR     = "rgba(37, 99, 235, 0.3)"
COR_FUNDO     = "rgba(0,0,0,0)"  # Transparente (adapta ao tema Streamlit)

NOTA_MINIMA_APROVACAO = 5.0  # Linha de referência nos gráficos


def renderizar() -> None:
    """Renderiza a aba do Dashboard Individual."""

    st.markdown("## 📊 Dashboard Individual")

    # CSS para melhorar a impressão (Ctrl+P)
    st.markdown(_css_impressao(), unsafe_allow_html=True)

    alunos = listar_alunos()
    if not alunos:
        st.warning("⚠️ Nenhum aluno cadastrado. Vá para a aba **Cadastros** primeiro.")
        return

    # ─── Seleção do Aluno ─────────────────────────────────────────────────────
    opcoes = {f"{a['nome']} ({a['turma']}) — {a['matricula']}": a["id"] for a in alunos}

    col_select, col_btn = st.columns([5, 1])
    with col_select:
        aluno_selecionado_label = st.selectbox(
            "🔍 Selecione o aluno",
            options=list(opcoes.keys()),
            label_visibility="collapsed",
            placeholder="Busque pelo nome, turma ou matrícula...",
        )
    with col_btn:
        st.markdown("&nbsp;")

    if not aluno_selecionado_label:
        return

    aluno_id = opcoes[aluno_selecionado_label]
    aluno    = buscar_aluno_por_id(aluno_id)

    if not aluno:
        st.error("Aluno não encontrado.")
        return

    # ─── Cabeçalho do Boletim (visível na impressão) ──────────────────────────
    st.markdown("---")
    _renderizar_cabecalho_boletim(aluno)
    st.markdown("---")

    # ─── Carregamento de dados ────────────────────────────────────────────────
    medias       = buscar_media_por_competencia(aluno_id)
    historico    = buscar_notas_por_aluno(aluno_id)
    frequencia   = buscar_frequencia_aluno(aluno_id)

    df_medias    = pd.DataFrame(medias)
    df_historico = pd.DataFrame(historico) if historico else pd.DataFrame()

    # ─── Métricas Resumidas ───────────────────────────────────────────────────
    _renderizar_metricas(df_medias, frequencia)

    st.markdown("---")

    # ─── Gráficos lado a lado ─────────────────────────────────────────────────
    col_radar, col_barras = st.columns([1, 1], gap="large")

    with col_radar:
        st.markdown("#### 🕸️ Radar de Competências")
        _renderizar_grafico_radar(df_medias)

    with col_barras:
        st.markdown("#### 📈 Histórico de Notas")
        if df_historico.empty:
            st.info("Nenhum histórico de avaliações encontrado.")
        else:
            _renderizar_grafico_barras(df_historico)

    st.markdown("---")

    # ─── Tabela Detalhada ─────────────────────────────────────────────────────
    st.markdown("#### 📋 Extrato Completo de Avaliações")
    _renderizar_tabela_detalhada(df_medias, df_historico)

    # ─── Rodapé de Impressão ─────────────────────────────────────────────────
    _renderizar_rodape()


# ─── Componentes de Renderização ──────────────────────────────────────────────

def _renderizar_cabecalho_boletim(aluno: dict) -> None:
    """Cabeçalho institucional do boletim — destacado na impressão."""
    st.markdown(
        f"""
        <div class="cabecalho-boletim">
            <h2 style="margin:0; color: {COR_PRIMARIA};">📚 Boletim Individual</h2>
            <table style="width:100%; font-size:1rem; margin-top:0.5rem;">
                <tr>
                    <td><b>Aluno:</b> {aluno['nome']}</td>
                    <td><b>Turma:</b> {aluno['turma']}</td>
                    <td><b>Matrícula:</b> {aluno['matricula']}</td>
                </tr>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _renderizar_metricas(df_medias: pd.DataFrame, frequencia: dict) -> None:
    """
    Exibe os indicadores principais com st.metric.
    Trata corretamente valores nulos (aluno sem nenhuma avaliação).
    """
    # Filtra apenas médias com pelo menos uma avaliação
    df_avaliados = df_medias[df_medias["total_avaliacoes"] > 0]

    media_geral = (
        round(df_avaliados["media_nota"].mean(), 2)
        if not df_avaliados.empty
        else None
    )
    total_competencias  = len(df_medias)
    comp_avaliadas      = len(df_avaliados)
    percentual_freq     = frequencia["percentual"]

    # Define emoji de status
    def _status_nota(nota):
        if nota is None:
            return "—"
        return "✅" if nota >= NOTA_MINIMA_APROVACAO else "⚠️"

    def _status_freq(pct):
        return "✅" if pct >= 75 else "⚠️"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📊 Média Geral",
            value=f"{media_geral:.1f}" if media_geral is not None else "N/A",
            delta=_status_nota(media_geral),
        )
    with col2:
        st.metric(
            label="🎯 Competências Avaliadas",
            value=f"{comp_avaliadas}/{total_competencias}",
        )
    with col3:
        st.metric(
            label="✅ Frequência",
            value=f"{percentual_freq:.1f}%",
            delta=_status_freq(percentual_freq),
            delta_color="normal" if percentual_freq >= 75 else "inverse",
        )
    with col4:
        st.metric(
            label="📅 Aulas Registradas",
            value=frequencia["total_aulas"],
            help=f"Presenças: {frequencia['presencas']} | Faltas: "
                 f"{frequencia['total_aulas'] - frequencia['presencas']}",
        )


def _renderizar_grafico_radar(df_medias: pd.DataFrame) -> None:
    """
    Gráfico de Radar (Teia de Aranha) usando Plotly.
    Competências sem avaliação são exibidas com valor 0.
    """
    if df_medias.empty:
        st.info("Nenhuma competência cadastrada.")
        return

    # Substitui None/NaN por 0 para o radar (aluno não avaliado = 0)
    categorias = df_medias["nome_competencia"].tolist()
    valores    = df_medias["media_nota"].fillna(0).tolist()

    # Fecha o polígono do radar
    categorias_fechadas = categorias + [categorias[0]]
    valores_fechados    = valores    + [valores[0]]

    fig = go.Figure()

    # Área preenchida
    fig.add_trace(go.Scatterpolar(
        r=valores_fechados,
        theta=categorias_fechadas,
        fill="toself",
        fillcolor=COR_RADAR,
        line=dict(color=COR_PRIMARIA, width=2),
        name="Desempenho",
        hovertemplate="<b>%{theta}</b><br>Média: %{r:.1f}<extra></extra>",
    ))

    # Linha de referência (nota mínima)
    valores_ref = [NOTA_MINIMA_APROVACAO] * len(categorias) + [NOTA_MINIMA_APROVACAO]
    fig.add_trace(go.Scatterpolar(
        r=valores_ref,
        theta=categorias_fechadas,
        mode="lines",
        line=dict(color=COR_AVISO, width=1, dash="dash"),
        name=f"Mínimo ({NOTA_MINIMA_APROVACAO})",
        hoverinfo="skip",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickvals=[0, 2, 4, 5, 6, 8, 10],
                tickfont=dict(size=10),
                gridcolor="rgba(128,128,128,0.3)",
            ),
            angularaxis=dict(
                tickfont=dict(size=10),
            ),
            bgcolor=COR_FUNDO,
        ),
        showlegend=True,
        legend=dict(orientation="h", y=-0.15),
        paper_bgcolor=COR_FUNDO,
        plot_bgcolor=COR_FUNDO,
        margin=dict(l=40, r=40, t=40, b=60),
        height=380,
    )

    st.plotly_chart(fig, use_container_width=True)


def _renderizar_grafico_barras(df_historico: pd.DataFrame) -> None:
    """
    Gráfico de barras agrupadas: nota por competência × data de avaliação.
    Notas nulas são omitidas do gráfico.
    """
    # Remove registros sem nota para o gráfico
    df_plot = df_historico.dropna(subset=["nota"]).copy()

    if df_plot.empty:
        st.info("Todas as avaliações estão com nota em branco.")
        return

    # Formata a data para exibição no eixo X
    df_plot["data_fmt"] = pd.to_datetime(df_plot["data_avaliacao"]).dt.strftime("%d/%m/%Y")

    fig = px.bar(
        df_plot,
        x="data_fmt",
        y="nota",
        color="nome_competencia",
        barmode="group",
        text_auto=".1f",
        labels={
            "data_fmt":        "Data",
            "nota":            "Nota",
            "nome_competencia": "Competência",
        },
        color_discrete_sequence=px.colors.qualitative.Set2,
        height=380,
    )

    # Linha de aprovação
    fig.add_hline(
        y=NOTA_MINIMA_APROVACAO,
        line_dash="dash",
        line_color=COR_AVISO,
        annotation_text=f"Mínimo ({NOTA_MINIMA_APROVACAO})",
        annotation_position="top right",
    )

    fig.update_layout(
        paper_bgcolor=COR_FUNDO,
        plot_bgcolor=COR_FUNDO,
        legend=dict(orientation="h", y=-0.25, font=dict(size=10)),
        margin=dict(l=10, r=10, t=20, b=80),
        yaxis=dict(range=[0, 10.5], gridcolor="rgba(128,128,128,0.2)"),
        xaxis=dict(title=""),
    )

    st.plotly_chart(fig, use_container_width=True)


def _renderizar_tabela_detalhada(
    df_medias: pd.DataFrame,
    df_historico: pd.DataFrame,
) -> None:
    """
    Tabela consolidada de médias por competência com indicador visual de status.
    """
    if df_medias.empty:
        st.info("Nenhuma competência cadastrada.")
        return

    def _formatar_nota(val):
        if pd.isna(val) or val is None:
            return "Não avaliado"
        return f"{val:.1f}"

    def _status(val):
        if pd.isna(val) or val is None:
            return "—"
        return "✅ Aprovado" if val >= NOTA_MINIMA_APROVACAO else "⚠️ Atenção"

    df_tabela = df_medias.copy()
    df_tabela["Média"]  = df_tabela["media_nota"].apply(_formatar_nota)
    df_tabela["Status"] = df_tabela["media_nota"].apply(_status)
    df_tabela["Avaliações"] = df_tabela["total_avaliacoes"]

    st.dataframe(
        df_tabela[["nome_competencia", "Média", "Avaliações", "Status"]].rename(
            columns={"nome_competencia": "Competência"}
        ),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Competência": st.column_config.TextColumn(width="large"),
            "Média":       st.column_config.TextColumn(width="small"),
            "Avaliações":  st.column_config.NumberColumn(width="small"),
            "Status":      st.column_config.TextColumn(width="medium"),
        },
    )


def _renderizar_rodape() -> None:
    """Rodapé visível apenas na impressão."""
    st.markdown(
        """
        <div class="rodape-impressao">
            <hr/>
            <p>Documento gerado pelo Sistema de Diário de Classe</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── CSS para impressão ───────────────────────────────────────────────────────

def _css_impressao() -> str:
    """
    CSS injetado via st.markdown para melhorar a impressão via Ctrl+P.
    Esconde elementos de navegação do Streamlit e formata o conteúdo.
    """
    return """
    <style>
    @media print {
        /* Esconde elementos de navegação do Streamlit */
        [data-testid="stSidebar"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stHeader"],
        [data-testid="stStatusWidget"],
        .stSelectbox,
        button,
        .stTabs [data-baseweb="tab-list"] {
            display: none !important;
        }

        /* Garante fundo branco e texto preto na impressão */
        body, .main, .block-container {
            background-color: white !important;
            color: black !important;
        }

        /* Ajusta margens para impressão */
        .block-container {
            padding: 1rem 2rem !important;
            max-width: 100% !important;
        }

        /* Evita quebra de página dentro dos gráficos */
        [data-testid="stPlotlyChart"] {
            page-break-inside: avoid;
        }

        /* Cabeçalho sempre na primeira página */
        .cabecalho-boletim {
            page-break-before: avoid;
        }

        /* Rodapé somente na impressão */
        .rodape-impressao {
            display: block !important;
            margin-top: 2rem;
            font-size: 0.8rem;
            color: #666;
            text-align: center;
        }
    }

    /* Esconde o rodapé durante o uso normal */
    .rodape-impressao {
        display: none;
    }

    /* Estilo do cabeçalho */
    .cabecalho-boletim {
        padding: 1rem;
        border-radius: 0.5rem;
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border-left: 4px solid #2563EB;
    }
    </style>
    """
