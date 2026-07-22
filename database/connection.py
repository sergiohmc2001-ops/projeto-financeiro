import os
import sqlite3

# Caminho absoluto para o banco de dados na raiz do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "database.db")


def get_db_connection():
    """Estabelece e retorna a conexão com o banco de dados SQLite.

    Configura o row_factory para acessar colunas pelo nome (como dicionários).
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    # Ativa o suporte a chaves estrangeiras no SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Cria as tabelas do sistema automaticamente caso não existam

    e aplica migrações de colunas novas.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 0. Tabela de Usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)

    # 1. Tabela de Despesas Gerais (Padronizada em minúsculo)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    # 2. Tabela de Receitas / Ganhos (Padronizada em minúsculo)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS receitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            fonte TEXT NOT NULL,
            data_receita DATE NOT NULL,
            observacoes TEXT,
            FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    """)

    # 3. Tabela de Cartões de Crédito (Padronizada em minúsculo)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cartoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    # 4. Tabela de Compras do Cartão (Padronizada em minúsculo)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comprascartao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    # 5. Tabela de Metas Financeiras (Padronizada em minúsculo)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    # 6. Tabela de Transações Recorrentes / Fixas (Padronizada em minúsculo)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoesrecorrentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            tipo TEXT NOT NULL, -- 'Despesa' ou 'Receita'
            categoria TEXT,
            forma_pagamento TEXT,
            dia_vencimento INTEGER NOT NULL,
            ativo INTEGER DEFAULT 1,
            ultimo_processamento TEXT, -- Formato 'YYYY-MM' para controle de duplicidade
            FOREIGN KEY (user_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    """)

    # Migrações automáticas para garantir compatibilidade com bancos antigos/restaurados
    migracoes = [
        ("despesas", "user_id", "INTEGER"),
        ("receitas", "user_id", "INTEGER"),
        ("cartoes", "user_id", "INTEGER"),
        ("metas", "user_id", "INTEGER"),
        ("transacoesrecorrentes", "user_id", "INTEGER"),
        ("comprascartao", "categoria_id", "INTEGER")
    ]

    for tabela, coluna, tipo in migracoes:
        try:
            cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo};")
        except sqlite3.OperationalError:
            # A coluna já existe, ignora o erro
            pass

    conn.commit()
    conn.close()