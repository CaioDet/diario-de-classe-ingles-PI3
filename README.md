# Diário de Classe: Sistema Digital de Gestão de Notas e Frequência

## Sobre o Projeto
[cite_start]O Diário de Classe é um sistema web de gestão de notas e frequência voltado ao apoio de professores do Ensino Profissionalizante do Estado de São Paulo, vinculados à Secretaria da Educação do Estado de São Paulo (SEDUC-SP)[cite: 332]. [cite_start]O sistema atua como uma ferramenta complementar à plataforma oficial Sala do Futuro, centralizando o registro e a organização diária das informações acadêmicas de forma estruturada, facilitando a posterior inserção de dados na plataforma do estado[cite: 333, 364].

[cite_start]Este projeto foi desenvolvido como requisito para a disciplina de Projeto Integrador 3 do curso de Engenharia da Computação e Ciência de Dados da Universidade Virtual do Estado de São Paulo (UNIVESP)[cite: 323].

## Equipe Desenvolvedora
* [cite_start]Adriano Josias da Silva [cite: 311]
* [cite_start]Caio Vinicius Detoni [cite: 312]
* [cite_start]Cristiane T. Biazotto [cite: 313]
* [cite_start]Mariana da Conceição Mendes [cite: 314]
* [cite_start]Mateus Vaz Hipólito [cite: 315]
* [cite_start]Mayckon Oliveira Campos [cite: 316]

[cite_start]**Tutora:** Isabella Caroline Martins [cite: 324]
[cite_start]**Polos:** Hortolândia / Mogi Mirim — SP (2026) [cite: 325, 326]

## Tecnologias Utilizadas
A aplicação foi construída com foco em portabilidade e eficiência, utilizando as seguintes tecnologias:
* [cite_start]**Python (3.11+):** Linguagem principal do projeto[cite: 494].
* [cite_start]**Streamlit (1.35+):** Framework web para o desenvolvimento da interface interativa[cite: 494].
* [cite_start]**SQLite:** Banco de dados relacional embarcado para o ambiente de desenvolvimento local[cite: 424, 494].
* [cite_start]**PostgreSQL (Supabase):** Banco de dados relacional em nuvem para o ambiente de produção[cite: 426, 494].
* [cite_start]**Plotly & Pandas:** Bibliotecas utilizadas para manipulação dos dados tabulares e geração de gráficos analíticos (Radar e Barras)[cite: 494].

## Arquitetura e Módulos do Sistema
[cite_start]O sistema adota um padrão de arquitetura modular em camadas, separando infraestrutura, acesso a dados e interface de usuário[cite: 397]. O projeto está dividido nos seguintes arquivos:

* [cite_start]`app.py`: Ponto de entrada da aplicação, responsável pela configuração, controle de autenticação e navegação entre abas[cite: 555].
* [cite_start]`autenticacao.py`: Gerenciamento de segurança, contemplando login, logout e controle de sessão via hash SHA-256[cite: 522, 555].
* [cite_start]`database.py`: Infraestrutura de conexão com o banco de dados, definição de DDL e adaptação de queries SQL[cite: 555].
* [cite_start]`repositorios.py`: Camada de acesso a dados (Repository Pattern), centralizando as queries SQL do domínio[cite: 399, 555].
* [cite_start]`aba_cadastros.py`: Interface de CRUD para registro e gerenciamento de alunos e competências avaliadas[cite: 555].
* [cite_start]`aba_diario.py`: Módulo central com editor visual em grade (estilo planilha) para inserção em lote de notas e presenças[cite: 536, 555].
* [cite_start]`aba_dashboard.py`: Interface analítica para geração de gráficos de desempenho (radar), histórico e exportação de boletim imprimível[cite: 546, 547, 555].

## Funcionalidades Principais
1. [cite_start]**Controle de Acesso:** Autenticação baseada em perfis de usuário (Administrador e Professor)[cite: 523].
2. [cite_start]**Gestão de Turmas:** Cadastro estruturado de alunos (nome, matrícula, turma) e competências[cite: 498].
3. [cite_start]**Diário Interativo:** Grade de edição (Data Editor) para lançamentos em lote com operação UPSERT, evitando duplicidade de registros[cite: 499, 500].
4. [cite_start]**Dashboard Individual:** Geração automática de gráficos de radar e barras por aluno, calculando médias, total de faltas e aulas ministradas[cite: 501].
5. [cite_start]**Impressão de Boletins:** Layout responsivo formatado para impressão (A4) do boletim acadêmico do aluno através do atalho Ctrl+P do navegador[cite: 502, 548].

## Como Executar o Projeto Localmente

1. Clone este repositório para o seu ambiente local.
2. Certifique-se de ter o Python 3.11 ou superior instalado em sua máquina.
3. Crie e ative um ambiente virtual (recomendado).
4. Instale as dependências listadas no projeto:
   ```bash
   pip install -r requirements.txt
