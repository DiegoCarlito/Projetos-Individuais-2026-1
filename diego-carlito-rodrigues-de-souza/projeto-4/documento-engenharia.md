# Documento de Engenharia — Projeto Individual 4

## 1. Arquitetura do Sistema

O sistema foi projetado para extração e consolidação de dados não estruturados de portais de Relações com Investidores (RI). A arquitetura é dividida em três camadas de alta resiliência.

### 1.1 Camada de Extração de Dados (Ingestion Layer)

A ingestão opera via **Polling Autônomo** para detecção de novos documentos sem necessidade de intervenção manual:

- **Scraper Adaptativo:** Utiliza o **Playwright** em modo *headless* para renderizar dinamicamente o JavaScript de portais corporativos (SPA/MZ Group). O sistema navega entre abas (Anos) e identifica tabelas de resultados de forma análoga à interação humana.
- **Idempotência Criptográfica:** Implementada através do cálculo de hash `SHA-256` de cada arquivo antes do processamento. O sistema consulta o `conjuntura.sqlite` para ignorar documentos já catalogados, otimizando o uso de rede e evitando duplicidade.
- **Parser de PDF:** Utiliza `PyMuPDF` (fitz) para converter PDFs em estruturas legíveis, mantendo a integridade das tabelas operacionais.

### 1.2 Camada de Processamento (UDA Module)

O motor de processamento utiliza IA Generativa para interpretar documentos com layouts variáveis:

- **LLM Semântico:** Utiliza o modelo `llama-3.3-70b-versatile` (via Groq API) para alta precisão na extração de dados.
- **Contrato Semântico:** Blindagem rigorosa via `Pydantic` e `Instructor`. O prompt do sistema impõe **tolerância zero a alucinações**, forçando a extração apenas de valores absolutos e metadados de unidade, tratando dados inconclusivos de marketing como `NULL`.

### 1.3 Camada de Serviço (API Layer)

Implementada com **FastAPI**, focada em transparência e rastreabilidade:

- **Linhagem de Dados (Data Lineage):** Cada registro no banco de dados vincula a métrica extraída à `url_origem` do documento, permitindo auditoria completa.

---

## 2. Justificativa de Escolhas Tecnológicas

- **Playwright:** Escolhido pela capacidade de renderizar JavaScript, superando a limitação de scrapers estáticos (BeautifulSoup) em sites modernos de RI.
- **Llama 3.3 70B:** Selecionado por seu alto poder de raciocínio lógico, essencial para diferenciar tabelas financeiras de textos de marketing.
- **SQLite:** Banco relacional leve e portátil, ideal para armazenar o Catálogo de Documentos e manter o estado da linhagem.
- **Instructor / Pydantic:** Ferramentas essenciais para garantir que a saída não estruturada do LLM seja convertida em tipos de dados seguros e validados.

---

## 3. Fluxo de Operação

### 3.1 Ingestão (`pipeline/ingest.py`)

- `scrapers.py` (Playwright) navega nos portais de RI → Verificação de Hash no SQLite → Download de novos PDFs.

### 3.2 Extração (`pipeline/extractor.py`)

- `PyMuPDF` converte PDF → Markdown → Prompt para `llama-3.3` (Instructor) → JSON validado.

### 3.3 Persistência

- Dados salvos em `conjuntura.sqlite` com vínculo ao `document_id`.

### 3.4 Serviço (`pipeline/api.py`)

- FastAPI expõe o endpoint `/api/conjuntura` para consulta estruturada.

---

## 4. Considerações de Resiliência

O pipeline é inerentemente resiliente contra "quebras de layout". Ao utilizar a compreensão semântica do LLM em vez de expressões regulares (Regex) ou coordenadas fixas, o sistema é capaz de identificar uma tabela de "Prévia Operacional" independentemente de sua posição no documento.

Além disso, a implementação de tratamento de exceções para `RateLimitError` e `BadRequestError` garante que o pipeline encerre sua execução de forma controlada caso os limites da API sejam atingidos, permitindo retomada posterior sem perda de consistência.

---

## 5. Garantia de Qualidade (QA)

A estabilidade é assegurada por mecanismos de controle de dados:

- **Idempotência:** A verificação via hash SHA-256 garante que um PDF processado nunca seja duplicado, mesmo que a URL seja encontrada em múltiplas varreduras.
- **Contrato Semântico:** A validação Pydantic atua como um filtro de qualidade, garantindo que nenhum valor inventado (alucinado) pela IA seja persistido na camada de banco de dados.
- **Tratamento de Exceções:** Implementado para capturar falhas de timeout em conexões de rede e limites de requisições/tokens da API.