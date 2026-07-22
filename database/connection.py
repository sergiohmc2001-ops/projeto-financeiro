import os
import sqlite3
from urllib.parse import urlparse

# Tenta pegar a URL do Supabase/PostgreSQL configurada nas variáveis de ambiente do Render
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Estabelece e retorna a conexão com o banco de dados.
    Usa PostgreSQL (Supabase) se estiver no Render, ou SQLite se estiver local.
    """
    if DATABASE_URL:
        try:
            import psycopg2  # type: ignore
            import psycopg2.extras  # type: ignore
            # Conexão com o PostgreSQL do Supabase
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            return conn
        except ImportError:
            raise RuntimeError("O pacote psycopg2 não está instalado localmente, mas a DATABASE_URL foi detectada.")
    else:
        # Conexão local com SQLite para testes na sua máquina
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        DATABASE_PATH = os.path.join(BASE_DIR, "database.db")
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

def init_db():
    """Cria as tabelas do sistema automaticamente caso não existam."""
    conn = get_db_connection()
    cursor = conn.cursor()

    is_postgres = bool(DATABASE_URL)

    # Ajuste de sintaxe para SERIAL (PostgreSQL) vs AUTOINCREMENT (SQLite)
    id_pk = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"

    # 0. Tabela de Usuários
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS usuarios (
            id {id_pk},
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)

    # 1. Tabela de Despesas Gerais
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

    # 2. Tabela de Receitas / Ganhos
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

    # 3. Tabela de Cartões de Crédito
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

    # 4. Tabela de Compras do Cartão
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

    # 5. Tabela de Metas Financeiras
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

    # 6. Tabela de Transações Recorrentes / Fixas
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

# Compatibilidade para arquivos antigos que tentam importar DATABASE_PATH
DATABASE_PATH = None