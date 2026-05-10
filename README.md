# PTA Dados 2026 — Desafio Técnico

Repositório do desafio técnico do Processo Trainee Acelerado da Equipe de Dados — 2026.

## Estrutura

```
pta-dados-2026/
├── fase1_engenharia/
│   ├── ingestao/        # Leitura das planilhas e PDFs
│   ├── limpeza/         # Tratamento e validação dos dados
│   └── api/             # FastAPI — exposição dos dados tratados
├── fase2_agente/
│   ├── rag/             # Arquitetura RAG com LangChain
│   ├── grafo/           # Fluxo do agente com LangGraph
│   └── automacoes/      # Grafos agendados de alertas
├── fase3_interface/     # Interface Streamlit (chat + painel analítico)
├── data/
│   └── pdfs/            # PDFs do cliente (não versionar dados sensíveis)
├── .env.example         # Variáveis de ambiente necessárias
├── docker-compose.yml   # Postgres + pgvector local
├── requirements.txt     # Dependências do projeto
├── DECISIONS.md         # Decisões técnicas e de arquitetura
└── README.md            # Este arquivo
```

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
