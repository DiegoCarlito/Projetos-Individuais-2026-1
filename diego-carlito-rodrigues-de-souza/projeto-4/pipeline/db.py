import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "conjuntura.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS documento_origem (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_origem TEXT NOT NULL,
    sha256 TEXT NOT NULL UNIQUE,     -- Hash do conteúdo (garante idempotência)
    num_paginas INTEGER NOT NULL,
    ingerido_em TEXT NOT NULL        -- Timestamp ISO 8601
);

CREATE TABLE IF NOT EXISTS pagina (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    documento_id INTEGER NOT NULL REFERENCES documento_origem(id) ON DELETE CASCADE,
    num_pagina INTEGER NOT NULL,     -- Índice físico no PDF
    texto TEXT NOT NULL,
    n_chars INTEGER NOT NULL,        -- Útil para pular páginas apenas com imagens
    UNIQUE (documento_id, num_pagina)
);
CREATE INDEX IF NOT EXISTS idx_pagina_documento ON pagina(documento_id);

CREATE TABLE IF NOT EXISTS dados_operacionais_trimestre (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    documento_id INTEGER NOT NULL UNIQUE REFERENCES documento_origem(id) ON DELETE CASCADE,
    empresa TEXT,
    ano INTEGER,
    trimestre INTEGER,
    lancamentos_valor_absoluto REAL,
    vendas_valor_absoluto REAL
);
"""

def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Abre a conexão, garante o diretório e aplica o esquema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA)
    return conn
