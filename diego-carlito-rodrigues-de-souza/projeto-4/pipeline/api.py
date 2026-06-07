from fastapi import FastAPI, Query, HTTPException
from typing import Optional, List, Dict, Any
import sqlite3
from pipeline.db import connect

app = FastAPI(
    title="API Conjuntura Habitacional - UDA",
    description="API para acesso aos dados operacionais de construtoras com linhagem de dados garantida.",
    version="1.0.0"
)

def get_db():
    conn = connect()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    return conn

@app.get("/api/conjuntura", response_model=List[Dict[str, Any]])
def obter_conjuntura(
    empresa: Optional[str] = Query(None, description="Filtrar por nome da construtora (ex: MRV, Tenda)"),
    ano: Optional[int] = Query(None, description="Filtrar por ano (ex: 2025)"),
    trimestre: Optional[int] = Query(None, description="Filtrar por trimestre (1, 2, 3 ou 4)")
):
    """
    Retorna os dados operacionais estruturados.
    A propriedade 'url_origem' em cada registro garante a rastreabilidade (Data Lineage) do PDF original.
    """
    conn = get_db()
    
    # Consulta base com JOIN para garantir a linhagem
    query = """
        SELECT 
            d.empresa,
            d.ano,
            d.trimestre,
            d.lancamentos_valor_absoluto,
            d.vendas_valor_absoluto,
            o.url_origem
        FROM dados_operacionais_trimestre d
        JOIN documento_origem o ON d.documento_id = o.id
        WHERE 1=1
    """
    parametros = []

    # Adicionando filtros dinamicamente
    if empresa:
        query += " AND d.empresa LIKE ?"
        parametros.append(f"%{empresa}%")
    if ano:
        query += " AND d.ano = ?"
        parametros.append(ano)
    if trimestre:
        query += " AND d.trimestre = ?"
        parametros.append(trimestre)

    query += " ORDER BY d.ano DESC, d.trimestre DESC, d.empresa ASC"

    try:
        cur = conn.execute(query, parametros)
        resultados = cur.fetchall()
        return resultados
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no banco de dados: {str(e)}")
    finally:
        conn.close()
