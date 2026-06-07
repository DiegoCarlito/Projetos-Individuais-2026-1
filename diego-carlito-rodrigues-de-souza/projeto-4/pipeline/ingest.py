import hashlib
import sqlite3
import requests
from datetime import datetime
import fitz
from scrapers import varrer_portal_ri_playwright

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
        return {"status": "pulado", "motivo": "Hash já existe no banco"}
        
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
    
    # Portais iniciais das empresas
    portais_das_construtoras = [
        "https://ri.mrv.com.br/informacoes-financeiras/central-de-resultados/",
        "https://ri.tenda.com/informacoes-financeiras/central-de-resultados/",
        "https://ri.planoeplano.com.br/informacoes-financeiras/central-de-resultados/",
        "https://ri.cury.net/informacoes-aos-investidores/central-de-resultados/",
        "https://ri.direcional.com.br/informacoes-financeiras/central-de-resultados/"
    ]
    
    fila_de_pdfs = []
    
    # Scraping Ativo com Playwright
    for portal in portais_das_construtoras:
        links_coletados = varrer_portal_ri_playwright(portal)
        fila_de_pdfs.extend(links_coletados)
        
    fila_de_pdfs = list(set(fila_de_pdfs)) # Remove qualquer duplicacao de captura
    
    print(f"\n🚀 Fila final de ingestão montada com {len(fila_de_pdfs)} PDFs encontrados nas centrais.")
    
    # Download e Idempotencia Hash
    if fila_de_pdfs:
        for url in fila_de_pdfs:
            try:
                # O motor baixa o arquivo e verifica o HASH no banco para nao duplicar
                resultado = baixar_e_ingerir(conn, url)
                print(f"Resultado: {resultado}")
            except Exception as e:
                print(f"Erro na ingestão de {url}: {e}")
    else:
        print("Nenhum link de PDF novo encontrado nas varreduras.")
