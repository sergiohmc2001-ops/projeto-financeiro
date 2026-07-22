import os
import sqlite3
import socket
from urllib.parse import urlparse

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if DATABASE_URL:
        import psycopg2  # type: ignore
        import psycopg2.extras  # type: ignore
        
        parsed_url = urlparse(DATABASE_URL)
        hostname = parsed_url.hostname
        port = parsed_url.port or 5432
        
        # Força a resolução estrita para IPv4 (AF_INET) contornando o erro de rede do Render
        try:
            ipv4_address = socket.getaddrinfo(hostname, port, socket.AF_INET)[0][4][0]
            # Substitui o domínio pelo IP IPv4 direto na string de conexão
            safe_url = DATABASE_URL.replace(hostname, ipv4_address)
        except Exception:
            safe_url = DATABASE_URL

        conn = psycopg2.connect(safe_url, sslmode='require')
        return conn
    else:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        DATABASE_PATH = os.path.join(BASE_DIR, "database.db")
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    is_postgres = bool(DATABASE_URL)
    id_pk = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS usuarios (
            id {id_pk},
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS despesas (
            id {id_pk},
            user_id INTEGER,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            categoria TEXT NOT NULL,
            data_despesa DATE NOT NULL,
            forma_pagamento TEXT NOT NULL,
            observacoes TEXT,
            FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS receitas (
            id {id_pk},
            user_id INTEGER,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            fonte TEXT NOT NULL,
            data_receita DATE NOT NULL,
            observacoes TEXT,
            FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS cartoes (
            id {id_pk},
            user_id INTEGER,
            nome TEXT NOT NULL,
            banco TEXT NOT NULL,
            bandeira TEXT NOT NULL,
            limite REAL NOT NULL,
            dia_fechamento INTEGER NOT NULL,
            dia_vencimento INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS comprascartao (
            id {id_pk},
            cartao_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            data_compra DATE NOT NULL,
            parcelas INTEGER NOT NULL DEFAULT 1,
            parcela_atual INTEGER NOT NULL DEFAULT 1,
            categoria_id INTEGER,
            FOREIGN KEY (cartao_id) REFERENCES cartoes (id) ON DELETE CASCADE
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS metas (
            id {id_pk},
            user_id INTEGER,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            valor_alvo REAL NOT NULL DEFAULT 0,
            valor_atual REAL NOT NULL DEFAULT 0,
            data_limite DATE,
            observacoes TEXT,
            FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS transacoesrecorrentes (
            id {id_pk},
            user_id INTEGER,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            tipo TEXT NOT NULL,
            categoria TEXT,
            forma_pagamento TEXT,
            dia_vencimento INTEGER NOT NULL,
            ativo INTEGER DEFAULT 1,
            ultimo_processamento TEXT,
            FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

__all__ = ["get_db_connection", "init_db"]