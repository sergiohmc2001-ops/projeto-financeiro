from database.connection import DATABASE_URL, get_db_connection

def listar_metas(user_id, categoria=None, busca=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    ph = "%s" if DATABASE_URL else "?"
    query = f"SELECT * FROM metas WHERE user_id = {ph}"
    params = [user_id]

    if categoria:
        query += f" AND categoria = {ph}"
        params.append(categoria)
    
    if busca:
        query += f" AND nome LIKE {ph}"
        params.append(f"%{busca}%")

    cursor.execute(query, params)
    metas = cursor.fetchall()
    conn.close()
    return [dict(m) for m in metas]

def obter_meta_por_id(id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    cursor.execute(f"SELECT * FROM metas WHERE id = {ph} AND user_id = {ph}", (id, user_id))
    meta = cursor.fetchone()
    conn.close()
    return dict(meta) if meta else None

def criar_meta(user_id, nome, categoria, valor_alvo, valor_atual, data_limite, observacoes):
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    cursor.execute(f"""
        INSERT INTO metas (user_id, nome, categoria, valor_alvo, valor_atual, data_limite, observacoes)
        VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
    """, (user_id, nome, categoria, valor_alvo, valor_atual, data_limite, observacoes))
    conn.commit()
    conn.close()

def atualizar_meta(id, user_id, nome, categoria, valor_alvo, valor_atual, data_limite, observacoes):
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    cursor.execute(f"""
        UPDATE metas
        SET nome = {ph}, categoria = {ph}, valor_alvo = {ph}, valor_atual = {ph}, data_limite = {ph}, observacoes = {ph}
        WHERE id = {ph} AND user_id = {ph}
    """, (nome, categoria, valor_alvo, valor_atual, data_limite, observacoes, id, user_id))
    conn.commit()
    conn.close()

def excluir_meta(id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    cursor.execute(f"DELETE FROM metas WHERE id = {ph} AND user_id = {ph}", (id, user_id))
    conn.commit()
    conn.close()