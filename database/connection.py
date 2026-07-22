import sqlite3
import os

# Caminho absoluto para o banco de dados na raiz do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')

def get_db_connection():
    """
    Estabelece e retorna a conexão com o banco de dados SQLite.
    Configura o row_factory para acessar colunas pelo nome (como dicionários).
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    # Ativa o suporte a chaves estrangeiras no SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """
    Cria as tabelas do sistema automaticamente caso não existam
    e aplica migrações de colunas novas.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Tabela de Despesas Gerais
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            categoria TEXT NOT NULL,
            data_despesa DATE NOT NULL,
            forma_pagamento TEXT NOT NULL,
            observacoes TEXT
        )
    ''')

    # 2. Tabela de Receitas / Ganhos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Receitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            fonte TEXT NOT NULL,
            data_receita DATE NOT NULL,
            observacoes TEXT
        )
    ''')

    # 3. Tabela de Cartões de Crédito
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Cartoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            banco TEXT NOT NULL,
            bandeira TEXT NOT NULL,
            limite REAL NOT NULL,
            dia_fechamento INTEGER NOT NULL,
            dia_vencimento INTEGER NOT NULL
        )
    ''')

    # 4. Tabela de Compras do Cartão (com categoria_id)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ComprasCartao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cartao_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            data_compra DATE NOT NULL,
            parcelas INTEGER NOT NULL DEFAULT 1,
            parcela_atual INTEGER NOT NULL DEFAULT 1,
            categoria_id INTEGER,
            FOREIGN KEY (cartao_id) REFERENCES Cartoes (id) ON DELETE CASCADE
        )
    ''')

    # 5. Tabela de Metas Financeiras
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Metas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            valor_alvo REAL NOT NULL DEFAULT 0,
            valor_atual REAL NOT NULL DEFAULT 0,
            data_limite DATE,
            observacoes TEXT
        )
    ''')

    # 6. Tabela de Transações Recorrentes / Fixas (NOVA)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS TransacoesRecorrentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            tipo TEXT NOT NULL, -- 'Despesa' ou 'Receita'
            categoria TEXT,
            forma_pagamento TEXT,
            dia_vencimento INTEGER NOT NULL,
            ativo INTEGER DEFAULT 1,
            ultimo_processamento TEXT -- Formato 'YYYY-MM' para controle de duplicidade
        )
    ''')

    # Migração automática: Adiciona a coluna categoria_id caso o banco já existisse
    try:
        cursor.execute("ALTER TABLE ComprasCartao ADD COLUMN categoria_id INTEGER;")
    except sqlite3.OperationalError:
        # A coluna já existe no banco local, ignora o erro
        pass

    conn.commit()
    conn.close()