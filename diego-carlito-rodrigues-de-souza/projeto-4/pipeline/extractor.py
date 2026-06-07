import os
import sqlite3
import instructor
from groq import Groq
from pydantic import BaseModel, Field
from typing import Optional, List
from dotenv import load_dotenv
from db import connect

# Definicao do Contrato Semantico
class DadosTrimestre(BaseModel):
    empresa: str = Field(description="Nome da construtora (ex: MRV, Tenda, Cury, Plano & Plano, Direcional, Pacaembu).")
    ano: int = Field(description="Ano de referência do relatório.")
    trimestre: int = Field(description="Trimestre de referência (1, 2, 3 ou 4).")
    lancamentos_valor_absoluto: Optional[float] = Field(
        description="Valor financeiro numérico bruto. Extraia APENAS se o número estiver clara e inequivocamente associado a Lançamentos. Se a tabela mostrar apenas porcentagens ou se houver dúvida, retorne null."
    )
    lancamentos_unidade: Optional[str] = Field(
        description="A unidade de grandeza (ex: 'milhões', 'bilhões'). Retorne null se não houver."
    )
    vendas_valor_absoluto: Optional[float] = Field(
        description="Valor financeiro numérico bruto. Extraia APENAS se o número estiver clara e inequivocamente associado a Vendas. Se a tabela mostrar apenas porcentagens ou se houver dúvida, retorne null."
    )
    vendas_unidade: Optional[str] = Field(
        description="A unidade de grandeza (ex: 'milhões', 'bilhões'). Retorne null se não houver."
    )

class ResultadoExtracao(BaseModel):
    resultados: List[DadosTrimestre]

# Inicializacao do Cliente LLM
load_dotenv()
client = instructor.from_groq(Groq(api_key=os.environ.get("GROQ_API_KEY")))

def buscar_paginas_relevantes(conn: sqlite3.Connection, documento_id: int) -> str:
    """Filtra o PDF via SQL contornando a limitação de acentos do SQLite."""
    cur = conn.execute("""
        SELECT texto FROM pagina 
        WHERE documento_id = ? 
          AND (
              texto LIKE '%lan_amento%' OR texto LIKE '%LAN_AMENTO%' OR 
              texto LIKE '%venda%' OR texto LIKE '%VENDA%' OR 
              texto LIKE '%trimestre%' OR texto LIKE '%TRIMESTRE%'
          )
        ORDER BY num_pagina
    """, (documento_id,))
    
    linhas = cur.fetchall()
    return "\n\n---\n\n".join([linha["texto"] for linha in linhas])

def extrair_dados_llm(texto_contexto: str) -> ResultadoExtracao:
    """Envia as páginas relevantes ao LLM e força o retorno estruturado."""
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        response_model=ResultadoExtracao,
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é um analista financeiro sênior extraindo dados operacionais rigorosos. "
                    "REGRA 1: Retorne APENAS UM registro por construtora listada. "
                    "REGRA 2: Procure os valores financeiros ABSOLUTOS (em milhões ou bilhões). "
                    "REGRA 3: Ignore completamente variações percentuais de marketing (+17%, -5%). "
                    "REGRA 4: TOLERÂNCIA ZERO PARA ALUCINAÇÃO. Nunca tente deduzir ou 'adivinhar' um valor. Se um número não estiver clara e diretamente associado à métrica solicitada, você DEVE retornar null. A integridade do dado é mais importante que o preenchimento do campo."
                )
            },
            {
                "role": "user",
                "content": f"Extraia os dados estruturados do seguinte trecho de relatório:\n\n{texto_contexto}"
            }
        ]
    )

def processar_extracao(conn: sqlite3.Connection, documento_id: int):
    texto_relevante = buscar_paginas_relevantes(conn, documento_id)
    if not texto_relevante.strip():
        print(f"Documento ID {documento_id}: Nenhuma página com termos relevantes encontrada.")
        return

    print("Enviando páginas filtradas para o LLM via Groq...")
    extracao = extrair_dados_llm(texto_relevante)
    
    # Persistir os dados limpos no banco
    sucessos = 0
    for item in extracao.resultados:
        try:
            conn.execute("""
                INSERT INTO dados_operacionais_trimestre 
                (documento_id, empresa, ano, trimestre, lancamentos_valor_absoluto, lancamentos_unidade, vendas_valor_absoluto, vendas_unidade)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                documento_id, item.empresa, item.ano, item.trimestre, 
                item.lancamentos_valor_absoluto, item.lancamentos_unidade, item.vendas_valor_absoluto, item.vendas_unidade
            ))
            sucessos += 1
        except sqlite3.IntegrityError:
            print(f"Aviso: Dados da empresa {item.empresa} já existem para este documento. Ignorando.")
            
    conn.commit()
    print(f"Extração concluída: {sucessos} empresas processadas e salvas.")
    return extracao

if __name__ == "__main__":
    conn = connect()
    
    # Busca todos os PDFs ingeridos
    docs = conn.execute("SELECT id, url_origem FROM documento_origem ORDER BY id ASC").fetchall()
    
    if docs:
        print(f"Encontrados {len(docs)} documentos para processar.")
        for doc in docs:
            print(f"\nProcessando Documento ID: {doc['id']} | Origem: {doc['url_origem']}")
            processar_extracao(conn, doc["id"])
    else:
        print("Nenhum documento encontrado. Rode o ingest.py primeiro.")
