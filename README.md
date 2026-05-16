# Diário de Classe: Sistema Digital de Gestão de Notas e Frequência

## Sobre o Projeto
O Diário de Classe é um sistema web de gestão de notas e frequência voltado ao apoio de professores do Ensino Profissionalizante do Estado de São Paulo, vinculados à Secretaria da Educação do Estado de São Paulo (SEDUC-SP). O sistema atua como uma ferramenta complementar à plataforma oficial Sala do Futuro, centralizando o registro e a organização diária das informações acadêmicas de forma estruturada, facilitando a posterior inserção de dados na plataforma do estado.

Este projeto foi desenvolvido como requisito para a disciplina de Projeto Integrador 3 do curso de Engenharia da Computação e Ciência de Dados da Universidade Virtual do Estado de São Paulo (UNIVESP).

## Equipe Desenvolvedora
* Adriano Josias da Silva
* Caio Vinicius Detoni
* Cristiane T. Biazotto
* Mariana da Conceição Mendes
* Mateus Vaz Hipólito
* Mayckon Oliveira Campos

**Tutora:** Isabella Caroline Martins
**Polos:** Hortolândia / Mogi Mirim — SP (2026)

## Tecnologias Utilizadas
A aplicação foi construída com foco em portabilidade e eficiência, utilizando as seguintes tecnologias:
* **Python (3.11+):** Linguagem principal do projeto.
* **Streamlit (1.35+):** Framework web para o desenvolvimento da interface interativa.
* **SQLite:** Banco de dados relacional embarcado para o ambiente de desenvolvimento local.
* **PostgreSQL (Supabase):** Banco de dados relacional em nuvem para o ambiente de produção.
* **Plotly & Pandas:** Bibliotecas utilizadas para manipulação dos dados tabulares e geração de gráficos analíticos (Radar e Barras).

## Arquitetura e Módulos do Sistema
O sistema adota um padrão de arquitetura modular em camadas, separando infraestrutura, acesso a dados e interface de usuário. O projeto está dividido nos seguintes arquivos:

* `app.py`: Ponto de entrada da aplicação, responsável pela configuração, controle de autenticação e navegação entre abas.
* `autenticacao.py`: Gerenciamento de segurança, contemplando login, logout e controle de sessão via hash SHA-256.
* `database.py`: Infraestrutura de conexão com o banco de dados, definição de DDL e adaptação de queries SQL.
* `repositorios.py`: Camada de acesso a dados (Repository Pattern), centralizando as queries SQL do domínio.
* `aba_cadastros.py`: Interface de CRUD para registro e gerenciamento de alunos e competências avaliadas.
* `aba_diario.py`: Módulo central com editor visual em grade (estilo planilha) para inserção em lote de notas e presenças.
* `aba_dashboard.py`: Interface analítica para geração de gráficos de desempenho (radar), histórico e exportação de boletim imprimível.

## Funcionalidades Principais
1. **Controle de Acesso:** Autenticação baseada em perfis de usuário (Administrador e Professor).
2. **Gestão de Turmas:** Cadastro estruturado de alunos (nome, matrícula, turma) e competências.
3. **Diário Interativo:** Grade de edição (Data Editor) para lançamentos em lote com operação UPSERT, evitando duplicidade de registros.
4. **Dashboard Individual:** Geração automática de gráficos de radar e barras por aluno, calculando médias, total de faltas e aulas ministradas.
5. **Impressão de Boletins:** Layout responsivo formatado para impressão (A4) do boletim acadêmico do aluno através do atalho Ctrl+P do navegador.

## Como Executar o Projeto Localmente

1. Clone este repositório para o seu ambiente local.
2. Certifique-se de ter o Python 3.11 ou superior instalado em sua máquina.
3. Crie e ative um ambiente virtual (recomendado).
4. Instale as dependências listadas no projeto:
   ```bash
   pip install -r requirements.txt
