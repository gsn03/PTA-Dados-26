# DECISIONS.md
Documento de decisões técnicas e de arquitetura

# Documento de Decisões Arquiteturais (DECISIONS.md) - Fase 1

Esta seção documenta as principais decisões de estratégias de implementação adotadas na primeira fase do projeto, abrangendo ingestão de dados, processamento de PDFs, estruturação de banco de dados e rotas da API.

---

# 1. Frameworks e Tecnologias Base

## API Web

Adotamos o **FastAPI** devido à sua alta performance, tipagem estática nativa (com Pydantic) e facilidade na criação de rotas modulares usando o `APIRouter`.

## ORM e Banco de Dados

Utilizamos o **SQLAlchemy** para mapeamento objeto-relacional, garantindo flexibilidade para interagir com o banco de dados.

O controle de sessões foi encapsulado na dependência `get_db` usando o recurso `Depends` do FastAPI, assegurando que as conexões sejam abertas e fechadas corretamente em cada requisição.

---

# 2. Processamento e Ingestão de Dados (CSVs)

## Uso do Pandas

Optamos pelo **pandas** para leitura em lote e tratamento inicial dos CSVs.

## Higienização de Nulos

Criamos a função `limpar_dado` para padronizar variações de valores nulos (`NaN`, `NaT`, `""`, `"none"`) transformando-os no tipo genérico `None` do Python, evitando erros de tipagem ao inserir dados no banco relacional.

## Desduplicação e Idempotência

### Em Memória

Aplicamos `drop_duplicates` no `DataFrame` antes do processamento, ignorando o ID original.

### No Banco

Antes de cada inserção, o script verifica se a combinação de `cliente_id` e `numero_processo` já existe na tabela `contrato_honorario`.

Essa abordagem torna o script idempotente, permitindo múltiplas execuções sem duplicar registros.

---

# 3. Extração e Estruturação de PDFs

A conversão de documentos jurídicos não estruturados para dados estruturados foi dividida em etapas.

## Extração de Texto

Escolhemos a biblioteca **pdfplumber** por sua precisão na extração de texto de PDFs pesquisáveis.

## Separação de Responsabilidades (Pipeline)

Em vez de um script monolítico, criamos a função genérica `processar_lote_pdfs`.

Ela recebe:

* o diretório de origem;
* o diretório de destino;
* uma função de extração específica (ex.: `extrair_citacao`, `extrair_acordos`).

## Armazenamento Intermediário (JSON)

Decidimos salvar o resultado da extração em arquivos `.json` locais antes do envio ao banco de dados.

Essa estratégia:

* cria uma camada de backup;
* facilita auditoria;
* simplifica depuração de falhas ou omissões dos extratores.

---

# 4. Modelo de Dados Unificado (Movimentações)

## Tabela Híbrida

A tabela `movimentacoes` foi projetada para consolidar atributos provenientes de duas fontes distintas:

* PDFs extraídos (via JSON);
* planilhas CSV.

Em vez de tabelas separadas, unificamos os dados no mesmo modelo, permitindo que atributos como:

* `tipo_movimentacao` (origem JSON);
* `tipo_ato` e `prazo_gerado` (origem CSV);

coexistam no mesmo registro.

Essa abordagem simplifica consultas futuras e reduz a complexidade da camada de integração para o front-end.

---

# 5. Busca Semântica e Banco de Dados Vetorial

Para permitir buscas avançadas no conteúdo dos documentos:

## Extensão pgvector

Decidimos utilizar o **pgvector** integrado ao SQLAlchemy (`Vector(3072)`).

Essa abordagem permite armazenar embeddings no mesmo banco PostgreSQL que contém os dados relacionais, evitando a necessidade de manter um banco vetorial separado (como Pinecone ou Milvus) nesta fase inicial.

## Embeddings

Utilizamos o modelo `gemini-embedding-001` da Google Generative AI para gerar representações vetoriais dos textos.

A busca semântica utiliza a função `cosine_distance` do pgvector para ranquear os resultados mais semanticamente próximos à pergunta do usuário.

## Controle de Migração

Na declaração da tabela `DocumentoVetorial`, adotamos a configuração:

```python
__table_args__ = {'extend_existing': True}
```

Como o schema vetorial sofre alterações frequentes durante testes de embeddings, essa configuração evita conflitos relacionados à recriação de tabelas já existentes ao reiniciar a aplicação.
