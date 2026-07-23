from database.connection import DATABASE_URL, get_db_connection

def listar_receitas(user_id, fonte=None, busca=None, data_inicio=None, data_fim=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    ph = "%s" if DATABASE_URL else "?"
    query = f"SELECT * FROM Receitas WHERE user_id = {ph}"
    params = [user_id]

    if fonte:
        query += f" AND fonte = {ph}"
        params.append(fonte)

    if busca:
        query += f" AND descricao LIKE {ph}"
        params.append(f"%{busca}%")

    if data_inicio:
        query += f" AND data_receita >= {ph}"
        params.append(data_inicio)

    if data_fim:
        query += f" AND data_receita <= {ph}"
        params.append(data_fim)

    query += " ORDER BY data_receita DESC"

    cursor.execute(query, params)
    receitas = cursor.fetchall()
    cursor.close()
    conn.close()
    return receitas

def criar_receita(user_id, descricao, valor, fonte, data_receita, observacoes=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    cursor.execute(f'''
        INSERT INTO Receitas (user_id, descricao, valor, fonte, data_receita, observacoes)
        VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})
    ''', (user_id, descricao, valor, fonte, data_receita, observacoes))
    conn.commit()
    cursor.close()
    conn.close()

def obter_receita_por_id(receita_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    cursor.execute(f"SELECT * FROM Receitas WHERE id = {ph} AND user_id = {ph}", (receita_id, user_id))
    receita = cursor.fetchone()
    cursor.close()
    conn.close()
    return receita

def atualizar_receita(receita_id, user_id, descricao, valor, fonte, data_receita, observacoes=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    cursor.execute(f'''
        UPDATE Receitas 
        SET descricao = {ph}, valor = {ph}, fonte = {ph}, data_receita = {ph}, observacoes = {ph}
        WHERE id = {ph} AND user_id = {ph}
    ''', (descricao, valor, fonte, data_receita, observacoes, receita_id, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def deletar_receita(receita_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    cursor.execute(f"DELETE FROM Receitas WHERE id = {ph} AND user_id = {ph}", (receita_id, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def calcular_total_receitas(user_id, fonte=None, busca=None, data_inicio=None, data_fim=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    ph = "%s" if DATABASE_URL else "?"
    query = f"SELECT SUM(valor) as total FROM Receitas WHERE user_id = {ph}"
    params = [user_id]

    if fonte:
        query += f" AND fonte = {ph}"
        params.append(fonte)

    if busca:
        query += f" AND descricao LIKE {ph}"
        params.append(f"%{busca}%")

    if data_inicio:
        query += f" AND data_receita >= {ph}"
        params.append(data_inicio)

    if data_fim:
        query += f" AND data_receita <= {ph}"
        params.append(data_fim)

    cursor.execute(query, params)
    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not resultado:
        return 0.0
    
    # Compatibilidade segura para pegar o valor do dicionário ou tupla
    if isinstance(resultado, dict):
        total = resultado.get('total') or resultado.get('TOTAL')
    else:
        try:
            total = resultado['total']
        except Exception:
            total = resultado[0]
            
    return float(total) if total else 0.0