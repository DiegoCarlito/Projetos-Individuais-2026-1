# Projeto 4: Pipeline UDA - Conjuntura do Setor Habitacional

Este projeto apresenta um pipeline resiliente de **Análise de Dados Não Estruturados (UDA)** projetado para automatizar a consolidação de métricas financeiras do setor habitacional. O sistema monitora ativamente portais corporativos de Relações com Investidores (RI), coleta PDFs de Prévias Operacionais e utiliza inteligência artificial para extrair valores brutos com precisão e Data Lineage.

## Solução
A implementação consolidada deste projeto é uma **Arquitetura de Extração em Três Camadas** que resolve o problema da imprevisibilidade de layouts:
1. **Gatilho de Ingestão Dinâmico:** Utiliza web scraping headless (Playwright) para renderizar JavaScript e navegar autonomamente em portais complexos (ex: MZ Group), varrendo abas e menus dropdown em busca de PDFs.
2. **Motor Semântico Idempotente:** Antes de acionar o LLM, o sistema calcula o Hash SHA-256 do arquivo (armazenado em SQLite) para garantir que não haja reprocessamento. A extração utiliza Pydantic para forçar um Contrato Semântico de tolerância zero contra alucinações matemáticas.
3. **Camada de Serviço Auditável:** Uma API RESTful que entrega os dados estruturados com metadados de unidade e rastreabilidade total (retornando a URL do PDF original de onde o dado foi lido).

## Estrutura do Repositório
- `pipeline/`: Código-fonte dos motores do pipeline, contendo:
  - `scrapers.py`: Robôs adaptativos de varredura web (Playwright).
  - `ingest.py`: Orquestrador de downloads e controle de Idempotência.
  - `extractor.py`: Motor UDA e interação com a API da Groq.
  - `db.py`: Configurações de esquema do banco de dados.
  - `api.py`: Camada de serviço (FastAPI).
- `data/`: Diretório de persistência, onde é gerado o banco relacional `conjuntura.sqlite` contendo o Catálogo de Documentos e a Tabela de Métricas.
- `requirements.txt`: Relação de pacotes Python necessários para execução.

## Como Executar
1. Clone este repositório para a sua máquina local.
2. Instale as dependências executando `pip install -r requirements.txt`.
3. Instale os binários do navegador headless executando `playwright install chromium`.
4. Configure sua chave de API criando um arquivo `.env` na raiz do projeto com a variável `GROQ_API_KEY=sua_chave_aqui`.
5. **Gatilho (Varredura e Ingestão):** No terminal, rode `python pipeline/ingest.py` para mapear os sites e enfileirar os PDFs.
6. **Motor UDA (Extração LLM):** Em seguida, rode `python pipeline/extractor.py` para ler os documentos e popular o banco de dados.
7. **Serviço (API):** Suba o servidor com `python -m uvicorn pipeline.api:app --reload` e acesse a documentação interativa em `http://127.0.0.1:8000/docs`.
