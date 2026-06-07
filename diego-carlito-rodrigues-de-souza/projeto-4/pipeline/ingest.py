import hashlib
import sqlite3
import requests
import time
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
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/pdf"
    }
    
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    conteudo_pdf = resp.content
    
    sha = calcular_hash_conteudo(conteudo_pdf)
    
    if ja_ingerido(conn, sha):
        return {"status": "pulado", "motivo": "Hash já existe no banco (Idempotência garantida)"}
        
    doc = fitz.open(stream=conteudo_pdf, filetype="pdf")
    num_paginas = doc.page_count
    
    # Salvar metadados da origem
    cur = conn.execute(
        "INSERT INTO documento_origem (url_origem, sha256, num_paginas, ingerido_em) VALUES (?, ?, ?, ?)",
        (url, sha, num_paginas, datetime.now().isoformat())
    )
    doc_id = cur.lastrowid
    
    # Extrair texto pagina a pagina
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
    conn = connect()
    
    urls_para_monitorar = [
        "https://raw.githubusercontent.com/unb-Sistemas-de-Machine-learning/Projetos-Individuais-2026-1/main/projeto-individual-4/exemplo_Boletim_Conjuntura_2025_3T.pdf",
        
        "https://api.mziq.com/mzfilemanager/v2/d/4b56353d-d5d9-435f-bf63-dcbf0a6c25d5/2c084655-23f7-7c55-5ac7-f4b2ed930448?origin=2",

        "https://vipfiles.valor.com.br/BDEmpresas/75b44eb0-d958-4cf6-9cb2-3e37d8fe4490.pdf"
    ]
    
    print("Iniciando rotina de Polling (varredura) nas centrais de RI...")
    
    # Loop de varredura
    for url in urls_para_monitorar:
        try:
            resultado = baixar_e_ingerir(conn, url)
            print(f"Resultado: {resultado}")
        except Exception as e:
            print(f"Erro ao tentar baixar a URL {url}: {e}")
            
        time.sleep(2)
