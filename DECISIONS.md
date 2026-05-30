# Documento de Decisões Arquiteturais (DECISIONS.md) - Fase 1

Esta seção documenta as principais decisões de design, ferramentas e estratégias adotadas na primeira fase do projeto, incluindo ingestão de dados, processamento de PDFs, estruturação do banco de dados e rotas da API.

---

# 1. Frameworks e Tecnologias Base

## API Web: FastAPI

Adotamos o **FastAPI** como framework principal da API.

### Por que utilizamos?

* Alta performance;
* Suporte nativo a tipagem com Pydantic;
* Facilidade para criação de rotas;
* Geração automática de documentação da API.

---

## ORM e Banco de Dados: SQLAlchemy

Utilizamos o **SQLAlchemy** para o mapeamento objeto-relacional (ORM).

### Por que utilizamos?

* Facilita a comunicação com o banco de dados;
* Reduz a necessidade de escrever SQL manualmente;
* Melhor organização e manutenção do código;
* Controle seguro de conexões com o banco.

---

# 2. Processamento e Ingestão de Dados (CSVs)

## Uso do Pandas

Optamos pelo **pandas** para leitura e tratamento dos arquivos CSV.

### Por que utilizamos?

* Processamento rápido de grandes volumes de dados;
* Facilidade para limpeza e transformação das informações;
* Manipulação eficiente de tabelas e planilhas.

---

## Higienização de Nulos (`limpar_dado`)

Criamos a função `limpar_dado` para padronizar valores nulos.

### Por que utilizamos?

* Evita erros de tipagem no banco;
* Garante maior consistência dos dados;
* Facilita a importação de arquivos com dados incompletos.

---

## Desduplicação e Idempotência

Aplicamos validações antes da inserção dos registros.

### Por que utilizamos?

* Evita registros duplicados;
* Permite executar o script várias vezes com segurança;
* Mantém a integridade dos dados.

---

# 3. Extração e Estruturação de PDFs

## Extração de Texto: `pdfplumber`

Utilizamos a biblioteca **pdfplumber** para leitura dos PDFs.

### Por que utilizamos?

* Boa precisão na extração de texto;
* Melhor leitura de documentos jurídicos complexos;
* Facilidade para trabalhar página por página.

---

## Separação de Responsabilidades (Pipeline)

Criamos a função genérica `processar_lote_pdfs`.

### Por que utilizamos?

* Melhor organização do processamento;
* Código mais reutilizável;
* Facilidade para adicionar novos tipos de documentos futuramente.

---

## Armazenamento Intermediário (JSON)

Os dados extraídos são salvos em arquivos `.json` antes da inserção no banco.

### Por que utilizamos?

* Cria uma camada de backup;
* Facilita auditoria e depuração;
* Evita reprocessamento dos PDFs em caso de falha.

---

# 4. Modelo de Dados Unificado (Movimentações)

## Tabela Híbrida

A tabela `movimentacoes` reúne dados vindos de PDFs e planilhas CSV.

### Por que utilizamos?

* Simplifica consultas;
* Reduz a complexidade do banco;
* Facilita o consumo dos dados pelo front-end.

---

# 5. Busca Semântica e Banco de Dados Vetorial

## Extensão `pgvector`

Utilizamos o **pgvector** integrado ao PostgreSQL.

### Por que utilizamos?

* Mantém dados relacionais e vetoriais no mesmo banco;
* Reduz complexidade de infraestrutura;
* Facilita buscas semânticas combinadas com filtros tradicionais.

---

## Embeddings: `gemini-embedding-001`

Utilizamos o modelo `gemini-embedding-001` para gerar embeddings.

### Por que utilizamos?

* Bom suporte ao português;
* Fácil integração;
* Boa relação entre desempenho e custo.

---

## Controle de Migração (`extend_existing=True`)

Adotamos a configuração:

```python id="z18k44"
__table_args__ = {'extend_existing': True}
```

### Por que utilizamos?

* Evita conflitos durante alterações no schema;
* Facilita testes e ajustes no ambiente de desenvolvimento.
