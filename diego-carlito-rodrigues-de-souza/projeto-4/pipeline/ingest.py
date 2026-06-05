import hashlib
import sqlite3
import requests
from datetime import datetime
import fitz

from db import connect

def calcular_hash_conteudo(conteudo_bytes: bytes) -> str:
    return hashlib.sha256(conteudo_bytes).hexdigest()

def ja_ingerido(conn: sqlite3.Connection, sha256: str) -> bool:
    row = conn.execute("SELECT id FROM documento_origem WHERE sha256 = ?", (sha256,)).fetchone()
    return row is not None

def baixar_e_ingerir(conn: sqlite3.Connection, url: str) -> dict:
    print(f"\nBaixando: {url}")
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    conteudo_pdf = resp.content
    
    sha = calcular_hash_conteudo(conteudo_pdf)
    
    if ja_ingerido(conn, sha):
        return {"status": "pulado", "motivo": "Hash já existe no banco (Idempotência garantida)"}
        
    doc = fitz.open(stream=conteudo_pdf, filetype="pdf")
    num_paginas = doc.page_count
    
    # 1. Salvar metadados da origem
    cur = conn.execute(
        "INSERT INTO documento_origem (url_origem, sha256, num_paginas, ingerido_em) VALUES (?, ?, ?, ?)",
        (url, sha, num_paginas, datetime.now().isoformat())
    )
    doc_id = cur.lastrowid
    
    # 2. Extrair texto página a página
    paginas_vazias = 0
    for i, page in enumerate(doc, start=1):
        texto = page.get_text("text")
        n_chars = len(texto.strip())
        if n_chars == 0:
            paginas_vazias += 1
            
        conn.execute(
            "INSERT INTO pagina (documento_id, num_pagina, texto, n_chars) VALUES (?, ?, ?, ?)",
            (doc_id, i, texto, n_chars)
        )
        
    conn.commit()
    return {"status": "ingerido", "paginas": num_paginas, "paginas_vazias": paginas_vazias}

if __name__ == "__main__":
    url_teste = "https://raw.githubusercontent.com/unb-Sistemas-de-Machine-learning/Projetos-Individuais-2026-1/main/projeto-individual-4/exemplo_Boletim_Conjuntura_2025_3T.pdf"
    
    conn = connect()
    
    print("--- 1ª Execução (Deve baixar e extrair) ---")
    resultado1 = baixar_e_ingerir(conn, url_teste)
    print(resultado1)
    
    print("\n--- 2ª Execução (Deve ignorar pelo Hash) ---")
    resultado2 = baixar_e_ingerir(conn, url_teste)
    print(resultado2)
