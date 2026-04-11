# 📚 Diário de Classe — Sistema de Gestão Escolar

Sistema web para gestão de notas, frequência e relatórios individuais de alunos, construído com Python e Streamlit.

## ✨ Funcionalidades

| Aba | Descrição |
|-----|-----------|
| 📋 **Cadastros** | CRUD de alunos e competências avaliadas |
| 📖 **Diário de Classe** | Editor estilo planilha para notas e presenças |
| 📊 **Dashboard** | Gráfico de radar, histórico, métricas e boletim imprimível |

---

## 🚀 Instalação e Execução

### Pré-requisitos
- Python 3.11+
- pip

### 1. Clone o repositório e instale as dependências

```bash
# Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# Instale as dependências
pip install -r requirements.txt
```

### 2. Execute a aplicação

```bash
streamlit run app.py
```

A aplicação abre automaticamente em `http://localhost:8501`.  
O banco de dados SQLite (`diario_classe.db`) é criado automaticamente na primeira execução.

---

## 🗄️ Configuração do Banco de Dados

### Desenvolvimento (padrão) — SQLite

Nenhuma configuração necessária. O arquivo `diario_classe.db` é criado localmente.

### Produção — PostgreSQL

A transição para PostgreSQL exige **apenas uma linha de configuração**.

**Opção A: Variável de ambiente (Docker, Railway, Heroku)**
```bash
export DATABASE_URL="postgresql://usuario:senha@host:5432/diario_db"
streamlit run app.py
```

**Opção B: Streamlit Secrets (Streamlit Cloud)**
1. Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml`
2. Preencha a URL de conexão:
```toml
DATABASE_URL = "postgresql://usuario:senha@host:5432/diario_db"
```

> ⚠️ Lembre-se de instalar o driver: `pip install psycopg2-binary`

---

## 📁 Estrutura do Projeto

```
diario_classe/
│
├── app.py              # Ponto de entrada — layout e abas do Streamlit
├── database.py         # Conexão com o banco, DDL, helpers de query
├── repositorios.py     # Camada de acesso a dados (Repository Pattern)
│
├── aba_cadastros.py    # Aba 1: CRUD de alunos e competências
├── aba_diario.py       # Aba 2: Editor de notas e presenças (data_editor)
├── aba_dashboard.py    # Aba 3: Gráficos, métricas e boletim imprimível
│
├── requirements.txt    # Dependências Python
│
└── .streamlit/
    └── secrets.toml.example   # Template de configuração de credenciais
```

---

## 🏗️ Arquitetura e Decisões Técnicas

### Portabilidade SQLite → PostgreSQL
A função `_resolver_url_banco()` em `database.py` verifica em ordem:
1. Variável de ambiente `DATABASE_URL`
2. `st.secrets["DATABASE_URL"]`
3. Fallback para SQLite local

### st.data_editor (Pivot Table Pattern)
O Diário de Classe usa uma estratégia de **pivot/unpivot**:
- **Banco → Grid**: dados em formato "longo" são pivotados para "largo" (cada competência = coluna)
- **Grid → Banco**: após edição, faz unpivot e persiste via `executemany` com UPSERT

### Tratamento de Nulos
- Notas não registradas são armazenadas como `NULL` no banco
- O gráfico de radar exibe `0` para competências sem avaliação
- O extrato mostra "Não avaliado" em texto

---

## 🖨️ Impressão do Boletim

Na aba **Dashboard & Relatórios**, selecione o aluno e pressione `Ctrl+P`.  
O CSS de impressão esconde os elementos de navegação do Streamlit e formata o conteúdo como um boletim profissional.

---

## 🔮 Roadmap (Próximas Features)

- [ ] Autenticação de professores (Streamlit Authenticator)
- [ ] Export para Excel/PDF via botão dedicado
- [ ] Comparativo de turma (médias agregadas)
- [ ] Alertas automáticos de alunos com baixa frequência
- [ ] Deploy com Docker Compose (app + PostgreSQL)
