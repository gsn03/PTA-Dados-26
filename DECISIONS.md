# Documento de Decisões Arquiteturais (DECISIONS.md)

Este documento cobre as decisões de design, ferramentas e estratégias adotadas em todas as fases do projeto — engenharia de dados, agente de IA e interface.

---

# 1. Infraestrutura e Base

## `database_model.py` — Configuração do Banco
SQLAlchemy com `create_engine` + `SessionLocal` (fábrica de sessões) + `Base` declarativa. A URL é carregada exclusivamente via `.env` (`DATABASE_URL`), sem fallback hardcoded.

## `docker-compose.yml` — Banco de Dados
Imagem `pgvector/pgvector:pg16` (não o Postgres vanilla) para já ter a extensão vetorial disponível. Volume nomeado `postgres_data` para persistência entre reinicializações. Healthcheck com `pg_isready` para garantir que o banco suba antes de qualquer serviço dependente.

## `criar_banco.py` — Criação de Tabelas
Script enxuto que importa todos os models e dispara `Base.metadata.create_all`. Para adicionar novas tabelas basta importar o model aqui — sem reescrever o script.

---

# 2. Modelos de Dados

## `model_Cliente.py`
Tabela `clientes`. Campos divididos em dois grupos explícitos no código: os vindos da extração JSON (nacionalidade, estado civil, endereço) e os vindos do CSV (contato, email, data_inicio). Contém comentários Alembic para migrações futuras.

## `model_processos.py`
Tabela `processos`. Usa `__table_args__ = {'extend_existing': True}` para evitar conflito de redefinição quando o model é importado em múltiplos contextos (banco vetorial + routes). FK para `clientes.id` com `relationship` para backref. `prazo_proximo` é o único campo `Date` — os demais campos de valor ficam como `String` para não rejeitar formatações heterogêneas dos CSVs.

## `model_honorarios.py`
Tabela `contratos_honorarios`. Separa campos financeiros brutos (vindos do JSON: `valor_total`, `valor_causa`) dos campos financeiros controlados (vindos do CSV: `valor_total_contratado`, `parcelas_pagas`, `valor_em_aberto`). Todos como `String` para tolerar variações de formato monetário.

## `model_movimentacoes.py`
Tabela `movimentacoes` híbrida: campos narrativos do JSON (tipo_movimentacao, resumo_descricao, orgao_julgador) + campos operacionais do CSV (prazo_final, prazo_gerado, concluido). Unifica dados de PDFs e planilhas numa única tabela.

## `banco_vetorial.py` — Modelo Vetorial
Tabela `documentos_vetoriais` com coluna `Vector(3072)` (dimensão do `gemini-embedding-001`). Também usa `extend_existing=True`. A função `buscar_contexto_semantico` usa busca por distância cosseno via operador `.cosine_distance()` do pgvector — não é full-text, é busca semântica.

---

# 3. Tratamento e Ingestão de Dados

## `Tratamento_Cliente.py`
Pipeline pandas para CSV de clientes: desduplicação por CPF, reindexação a partir de 1, `.str.title()` nos nomes, `fillna("Não informado")` para contato/email, e conversão de mês por extenso para número usando mapa manual.

## `Tratamento_Honorarios.py`
Pipeline pandas para CSV de honorários: remoção de linhas totalmente nulas, desduplicação completa, mapa de normalização para `forma_pagamento` (boleto/TED/PIX → variante canônica), conversão de `n_parcelas` para int.

## `tratamento_movimentacao.py`
Pipeline com `dateparser` para parsing de datas multilíngue (em vez de strptime fixo) e função `formatar_cnj` para normalizar números de processo para o padrão CNJ (`NNNNNNN-DD.AAAA.J.TR.OOOO`), preenchendo com zeros à esquerda quando necessário.

## `Tratamento_processos.py`
Lê `.xlsx` via `pd.read_excel`. Mapas de normalização para `tipo` (trabalhista/civil/cível → forma canônica) e `status`. Stripping de espaços nas colunas.

## `insert_*.py` — Scripts de Inserção (Clientes, Honorários, Processos, Movimentações)
Todos seguem o mesmo padrão: leitura com pandas, desduplicação antes da inserção (ignorando coluna ID), verificação de existência no banco antes de cada `db.add()` (idempotência). `insert_honorarios` e `insert_processos` fazem mapeamento de FK via dicionário `{cliente_id_csv: cpf}` para resolver referências entre planilhas.

## `update_*_json.py` — Enriquecimento via JSON (Clientes, Honorários, Processos, Movimentações)
Varrem todos os JSONs extraídos dos PDFs via `rglob("*.json")`, ignoram arquivos de Relatório pelo nome. Fazem upsert: se o registro já existe no banco (identificado por CPF, número de processo ou chave relevante), atualizam os campos; caso contrário, inserem novo registro. `update_honorarios_json` e `update_processos_json` incluem função `limpar_valor_monetario` que normaliza strings monetárias ("R$ 1.200,00") para float string.

---

# 4. Extração de PDFs

## `extracao.py` — Orquestrador de Lote
Função genérica `processar_lote_pdfs(diretorio, saida_json, funcao_extracao)` que itera PDFs, extrai texto com `pdfplumber` página por página e salva JSON intermediário. A função de extração é injetada como argumento — padrão strategy que facilita adicionar novos tipos de documento.

## `regras_extracao.py` — Extratores por Tipo
Uma função por tipo de documento: `extrair_intimacao`, `extrair_citacao`, `extrair_peticao`, `extrair_contrato_honorarios`, `extrair_acordos`. Todas usam `re` com padrões específicos por tipo: padrão CNJ para número de processo, regex CNPJ, detecção de TRT/Trabalho para classificar tipo de processo, extração de partes por "movida por X em face de Y", OAB por "Dr./Dra. X, OAB nº Y". Retornam sempre um dict com chaves padronizadas.

## `ingestor_pdf.py` — Ingestão Vetorial
Usa `PyPDFLoader` + `RecursiveCharacterTextSplitter` (chunk_size=1000, overlap=150). Dropa e recria a tabela vetorial a cada execução (ingestão destrutiva). Difere do `gerador_rag.py` que usa `PyPDFDirectoryLoader` e overlap maior (200) — são dois scripts com estratégias ligeiramente distintas para o mesmo objetivo.

## `gerador_rag.py` — Ingestão RAG Alternativa
Usa `PyPDFDirectoryLoader` para carregar toda a pasta de uma vez. Salva diretamente no PostgreSQL via `SessionLocal`. Usa `chunk_overlap=200`. Não dropa a tabela antes — complementar ao `ingestor_pdf.py`.

---

# 5. API FastAPI

## `main_routes.py` — Entry Point da API
Instancia `FastAPI` e registra os 5 routers: clientes, honorários, movimentações, processos e ia. Para adicionar um novo domínio, basta criar o router e incluí-lo aqui.

## `routes_cliente.py` / `routes_honorarios.py` / `routes_movimentacoes.py` / `routes_processo.py`
Padrão uniforme: `APIRouter` com prefix e tag, função `get_db()` como dependency injector, rotas GET `/` (listar tudo) e GET `/{chave}` (buscar por chave primária de negócio — CPF para clientes e honorários, número de processo para processos e movimentações).

## `routes_ia.py` — Rotas de Inteligência
Router `/ia` que expõe os endpoints consumidos pela interface: `/chat` (POST com pergunta + histórico), `/prazos_urgentes`, `/status_vertente`, `/carteira_advogados`, `/inadimplencia`, `/alertas_email`. Toda lógica analítica com SQLAlchemy (`func`, `case`, `desc`, `asc`) está aqui. O endpoint `/chat` converte o histórico recebido do front em `HumanMessage`/`AIMessage` e injeta no grafo LangGraph.

---

# 6. Agente LangGraph

## `estado.py` — Schema do Agente
`EstadoAgente` como `TypedDict` com 4 campos: `messages` (anotado com `add_messages` para acumulação automática), `contexto_recuperado`, `resposta_gerada` e `tentativas` (contador de reprocessamento para o nó de validação).

## `fluxo_inicial.py` — Composição do Grafo
Monta o `StateGraph` conectando os 4 nós em sequência: reformulação → busca → resposta → validação. Cada nó é envolto em um wrapper que extrai a entrada correta do estado global e devolve apenas o delta de atualização. O histórico enviado ao reformulador é limitado às últimas 3 perguntas humanas para economia de tokens.

## `no_reformulacao.py` — Nó de Reformulação
LLM `gemini-2.5-flash` (temperature=0.1) com prompt que instrui a resolver pronomes usando o histórico, preservar nomes/números exatos, e retornar string vazia quando a pergunta for fora do escopo jurídico (proteção de jailbreak). Usa `ChatPromptTemplate` com slots `{historico}` e `{pergunta_original}`.

## `no_busca.py` — Nó de Busca (Roteador de Ferramentas)
LLM com `bind_tools(lista_de_ferramentas)` para deixar o modelo escolher qual ferramenta usar. Mapa `{ferramenta.name: ferramenta}` para execução dinâmica pelo nome escolhido pelo LLM. Temperature=0 para roteamento determinístico.

## `no_resposta.py` — Nó de Resposta
LLM com prompt que define formato de saída diferente por ferramenta: busca semântica exige citação `[Doc: nome.pdf]` ao final; prazos exigem lista cronológica; histórico de processo divide em `📌 STATUS ATUAL` e `⏳ HISTÓRICO`. Injeta `data_atual` no prompt para cálculos temporais relativos.

## `no_validacao.py` — Nó de Validação (Juiz)
LLM temperature=0 (determinístico) que compara contexto recuperado com resposta gerada. Aprova ou reprova com base em 4 critérios: incongruência, alucinação, fonte vazia, e citação ausente (apenas obrigatória quando a ferramenta for busca semântica). Possui regra explícita de flexibilidade temporal para não reprovar traduções de datas absolutas para dias relativos.

## `tools.py` — Ferramentas do Agente
4 ferramentas decoradas com `@tool`: `buscar_jurisprudencia_documentos` (busca vetorial via pgvector), `buscar_historico_processo` (API REST + número + nome do cliente), `verificar_prazos_processuais` (API REST com filtro de dias), e uma quarta para inadimplência. Cada docstring contém instrução explícita ao LLM sobre quando usar a ferramenta — essa docstring é o prompt de roteamento.

---

# 7. Interface Streamlit

## `app.py` — Orquestrador da Interface
Ponto de entrada do Streamlit. Carrega CSS global de `style.css`, inicializa `session_state` (pagina_atual, mostrar_historico, ultima_data_interacao), controla o banner de notificação (gatilho após 8h30, uma vez por dia via comparação de `date`). Sidebar construída com botões estilizados via CSS e submenu de Gráficos derivado do `pagina_atual` — sem variáveis de controle extras.

## `chatbot.py` — Interface do Chat
Histórico de conversas em `session_state.conversas` (dict de `conv_id → {titulo, mensagens, criada_em}`). IDs gerados por timestamp (`conv_{int(time.time() * 1000)}`). Balões de mensagem em HTML/CSS via `unsafe_allow_html` para controle total de estilo (gradiente, bordas assimétricas, avatar `⚖️`). Sidebar direita simulada com `position: fixed` via CSS usando seletor `:has(.right-sidebar-marker)`.

## `prazos_urgentes.py` — View de Prazos por Advogado
Padrão `col_filtro, col_metrica = st.columns([2, 1])` com KPI no topo. Gráfico de barras horizontais (volume por advogado) + timeline vertical, ambos com `plotly.graph_objects`. Slider de dias como filtro principal.

## `status_vertente.py` — View de Status por Vertente
Gráfico de barras agrupadas por vertente e status. Paleta de cinzas escalonados (`PALETA_CINZAS`) + azul petróleo como destaque extra. Dados via `/ia/status_vertente`.

## `view_inadimplencia.py` — View de Inadimplência
`MAPA_CORES` por faixa de atraso: cinza claro (1-30 dias) → cinza escuro (61-90 dias) → vermelho `#6f0d0d` (>90 dias). Escala visual de risco crescente. Dados via `/ia/inadimplencia`.

## `carteira_advogados.py` — View de Carteira por Advogado
Selectbox de advogado + totais de processos + tabela dos 5 prazos mais urgentes da carteira selecionada. Variável `COR_AMARELO` com valor `#084d6e` (azul petróleo) — nome inconsistente com o valor, herdado do template original.

## `notificador_prazos.py` — View de Prazos Críticos
Espelha o relatório de email: duas tabelas separadas, processos com vencimento em 5 dias (zona de perigo) e 15 dias (zona de atenção). Dados via `/ia/alertas_email` com param `dias_exatos`.

## `notificador_email.py` — Envio de Email Matinal
Usa SDK `resend` para envio. Monta HTML com duas tabelas coloridas: fundo `#ffebee` (perigo) e `#fff8e1` (atenção). Destinatário fixo `ptaequipegustavo@gmail.com`. Função `executar_relatorio_matinal()` faz duas chamadas à API (5 e 15 dias) e combina o resultado num único email.

## `style.css` — Estilo Global
CSS injetado via `st.markdown` em `app.py`. Sobrescreve seletores internos do Streamlit (`[data-testid="stSidebar"]`, `[data-testid="stVerticalBlock"]`). Degradê fixo com `background-attachment: fixed` aplicado em `html`, `body` e `.stApp` para resistir a reruns. Paleta: cinza `#44464a` para neutros, azul petróleo `#084d6e` para destaques.