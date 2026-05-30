# Projeto PTA Dados

## 📌 Visão Geral
O projeto **PTA Dados** é uma arquitetura de engenharia de dados e inteligência artificial desenvolvida para automação, extração e armazenamento de dados jurídicos (Petições, Citações, Intimações, Acordos e Contratos). 

O projeto está dividido em fases, sendo a **Fase 1** focada na extração de dados não estruturados (PDFs convertidos em JSON) e no armazenamento estruturado em um Banco de Dados Relacional.

## 🛠 Tecnologias Utilizadas
* **Linguagem:** Python 3.x
* **Banco de Dados:** PostgreSQL (com suporte nativo a `pgvector` via Docker)
* **ORM:** SQLAlchemy
* **API:** FastAPI e Uvicorn
* **Extração de Texto:** Expressões Regulares (`re`) nativas do Python
* **Gerenciamento de Ambiente:** Docker Compose e `python-dotenv`

## 📂 Estrutura de Diretórios
A arquitetura do projeto está modularizada da seguinte forma:

```text
PTA-DADOS-26/
├── data/                           # Armazenamento local de arquivos
│   ├── Bases_Tratadas/             # Dados limpos e prontos para banco
│   ├── pdfs_brutos/                # Documentos originais do escritório
│   ├── Planilhas_sem_tratamento/   # Arquivos de apoio em formato tabular
│   └── Texto_json/                 # Dados extraídos categorizados
├── fase1_engenharia/               # Core da Engenharia de Dados
│   ├── api/                        # Endpoints do FastAPI (Rotas de consulta)
│   ├── BD/                         # Modelagem e conexão com Banco de Dados
│   │   ├── Ingestão/               # Scripts de carga (ETL/Upsert)
│   │   │   └── insert_clientes.py  # Script de inserção inteligente de clientes
│   │   ├── criar_banco.py          # Script de materialização (DDL)
│   │   ├── database_model.py       # Motor de conexão via SQLAlchemy
│   │   └── model_Cliente.py        # Modelo relacional da tabela Clientes
│   ├── extração/                   # Lógica de processamento de PDFs
│   │   ├── extracao.py             # Motor principal de leitura de documentos
│   │   └── regras_extracao.py      # Dicionários de Expressões Regulares (Regex)
│   └── limpeza/                    # Tratamento e normalização de dados
│       ├── Tratamento_Cliente.py
│       ├── Tratamento_Honorarios.py
│       ├── tratamento_movimentacao.py
│       └── Tratamento_processos.py
├── fase2_agente/                   # [Em Desenvolvimento] IA e RAG
├── fase3_interface/                # [Em Desenvolvimento] Front-end
├── .env                            # Variáveis de ambiente (Credenciais ocultas)
├── .env.example                    # Template de variáveis para novos desenvolvedores
├── .gitignore                      # Regras de exclusão de arquivos para o repositório Git
├── DECISIONS.md                    # Registro de decisões arquiteturais da equipe
├── docker-compose.yml              # Orquestração do banco de dados PostgreSQL
├── README.md                       # Documentação principal do projeto
└── requirements.txt                # Lista de dependências e bibliotecas Python

## Pré-requisitos

- Python 3.11+
- Docker e Docker Compose

## Configuração

### 1. Clone o repositório e crie o ambiente virtual

```bash
git clone https://github.com/CITi-UFPE/pta-dados-2026.git
cd pta-dados-2026
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 2. Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite o .env com suas credenciais
```

### 3. Suba o banco local

```bash
docker-compose up -d
```

### 4. Como verificar que está funcionando

```bash
# Banco
docker-compose ps  # postgres deve estar Up

# API
curl -H "X-API-Key: sua_api_key" http://localhost:8000/health
```
