import sqlite3

DATABASE = 'database.db'

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def listar_metas(categoria=None, busca=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM metas WHERE 1=1"
    params = []

    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    
    if busca:
        query += " AND nome LIKE ?"
        params.append(f"%{busca}%")

    cursor.execute(query, params)
    metas = cursor.fetchall()
    conn.close()
    return [dict(m) for m in metas]

def obter_meta_por_id(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM metas WHERE id = ?", (id,))
    meta = cursor.fetchone()
    conn.close()
    return dict(meta) if meta else None

def criar_meta(nome, categoria, valor_alvo, valor_atual, data_limite, observacoes):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO metas (nome, categoria, valor_alvo, valor_atual, data_limite, observacoes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nome, categoria, valor_alvo, valor_atual, data_limite, observacoes))
    conn.commit()
    conn.close()

def atualizar_meta(id, nome, categoria, valor_alvo, valor_atual, data_limite, observacoes):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE metas
        SET nome = ?, categoria = ?, valor_alvo = ?, valor_atual = ?, data_limite = ?, observacoes = ?
        WHERE id = ?
    """, (nome, categoria, valor_alvo, valor_atual, data_limite, observacoes, id))
    conn.commit()
    conn.close()

def excluir_meta(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM metas WHERE id = ?", (id,))
    conn.commit()
    conn.close()