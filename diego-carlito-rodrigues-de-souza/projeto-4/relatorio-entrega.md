# Relatório de Entrega — Projeto Individual 4

> **Aluno(a):** Diego Carlito Rodrigues de Souza
> **Data de entrega:** 08/06/2026

---

## 1. Resumo do Projeto

O projeto consiste na implementação de um Pipeline de Análise de Dados Não Estruturados (UDA - Unstructured Data Analysis) para o setor habitacional. O sistema automatiza a coleta de relatórios operacionais (Prévias e Boletins) em PDF de portais de Relações com Investidores (RI). Diferente de scrapers tradicionais, a solução utiliza **Playwright** para contornar renderizações dinâmicas (JavaScript) dos portais corporativos. O processamento realiza a extração de métricas financeiras utilizando a API da Groq (Llama-3.3-70b-versatile) sob um contrato semântico rigoroso (com tolerância zero a alucinações), disponibilizando esses dados consolidados através de uma API RESTful para alimentar o Relatório de Conjuntura do Setor Habitacional do Ministério das Cidades.

---

## 2. Escopo Técnico

| Componente | Implementação |
|------------|---------------|
| **Gatilho de Ingestão** | Polling Autônomo com Web Scraping Headless (Playwright) para renderização de JavaScript e SPAs (ex: MZ Group). |
| **Idempotência** | Verificação de Hash SHA-256 do arquivo em memória/banco de dados para evitar reprocessamento e duplicidade. |
| **Segmentação de PDF** | Parsing via PyMuPDF aliado a Chunking Semântico para mitigar estouro de tokens da LLM. |
| **Motor de Extração** | Llama-3.3-70b-versatile (via Groq API) orquestrado com biblioteca `Instructor` e Pydantic para validação. |
| **Camada de Serviço** | API FastAPI entregando métricas com linhagem de dados (Data Lineage) via `url_origem`. |

---

## 3. Modelagem do Pipeline

### 3.1 Fluxo de Dados (Pipeline)

```text
Playwright Scraper (Portais RI) → Idempotência (Hash SHA-256) → SQLite (Ingestão) → PyMuPDF (Chunking Semântico) → LLM Llama-3.3-70b (Pydantic/Instructor) → SQLite (Métricas) → FastAPI (Service Layer)

```

### 3.2 Contrato Semântico e Modelagem de Metadados

A extração é blindada por esquemas rigorosos do Pydantic, forçando o LLM a retornar JSONs estruturados.
**Diferencial Arquitetural:** Para evitar "números mágicos" e cálculos frágeis na normalização, o Contrato Semântico foi desenhado para extrair o valor absoluto separadamente de seu metadado de grandeza (ex: `vendas_valor_absoluto: 1.2`, `vendas_unidade: "Bilhões"`), tratando valores ausentes ou ambíguos de marketing corporativo estritamente como `NULL`.

---

## 4. Implementação

### 4.1 Tecnologias utilizadas

| Tecnologia | Finalidade |
| --- | --- |
| Python 3.12+ | Linguagem principal do pipeline |
| Groq API (Llama 3.3 70B) | Motor de extração semântica e raciocínio (LLM) |
| FastAPI / Uvicorn | Camada de Serviço e documentação interativa (Swagger) |
| Playwright | Web scraping avançado (Bypass de páginas dinâmicas/React) |
| PyMuPDF (fitz) | Leitura, parsing e conversão de PDF |
| Pydantic & Instructor | Contrato Semântico, Structured Output e Validação de Tipos |
| SQLite | Armazenamento do Catálogo de Documentos e Métricas UDA |

### 4.2 Estrutura do código

```text
projeto-4/
├── pipeline/
│   ├── scrapers.py       # Robôs adaptativos de varredura web (Playwright)
│   ├── ingest.py         # Orquestrador de downloads e Idempotência
│   ├── extractor.py      # Motor UDA (Chunking e Interação com LLM)
│   ├── db.py             # Configurações de esquema e queries
│   └── api.py            # Camada de serviço (Endpoints RESTful)
├── data/
│   └── conjuntura.sqlite # Banco de Dados (Gerado automaticamente)
└── requirements.txt      # Dependências do projeto
```

### 4.3 Como executar

```bash
# 1. Instalar dependências da aplicação
pip install -r requirements.txt

# 2. Instalar os binários do navegador headless para o web scraper
playwright install chromium

# 3. Configurar a chave da API
# Renomeie .env.example para .env e adicione sua chave:
# GROQ_API_KEY=sua_chave_aqui

# 4. Iniciar o Motor de Ingestão (Busca e salva PDFs novos)
python pipeline/ingest.py

# 5. Iniciar o Motor de Extração (Lê os PDFs e processa na LLM)
python pipeline/extractor.py

# 6. Servir os Dados (API)
python -m uvicorn pipeline.api:app --reload
# Acesse: http://127.0.0.1:8000/docs
```

---

## 5. Checklist de entrega

* [x] Documento de engenharia preenchido
* [x] Código funcional no repositório com arquitetura isolada
* [x] Relatório de entrega preenchido
* [x] Pull Request aberto
