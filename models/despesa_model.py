from database.connection import DATABASE_URL, get_db_connection

def listar_despesas(user_id, mes=None, categoria=None, busca=None, ordem='DESC'):
    """
    Retorna a lista de despesas do usuário filtrada e ordenada.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    ph = "%s" if DATABASE_URL else "?"
    query = f"SELECT * FROM Despesas WHERE user_id = {ph}"
    params = [user_id]

    if mes:
        mes_formatado = f"{int(mes):02d}"
        if DATABASE_URL:
            # Compatibilidade com PostgreSQL
            query += f" AND EXTRACT(MONTH FROM data_despesa) = {ph}"
            params.append(int(mes_formatado))
        else:
            # Compatibilidade com SQLite
            query += f" AND strftime('%m', data_despesa) = {ph}"
            params.append(mes_formatado)

    if categoria:
        query += f" AND categoria = {ph}"
        params.append(categoria)

    if busca:
        query += f" AND (descricao LIKE {ph} OR observacoes LIKE {ph})"
        params.append(f"%{busca}%")
        params.append(f"%{busca}%")

    query += f" ORDER BY data_despesa {ordem}, id DESC"

    cursor.execute(query, params)
    despesas = cursor.fetchall()
    conn.close()
    return despesas

def obter_despesa_por_id(despesa_id, user_id):
    """
    Retorna os detalhes de uma única despesa pelo ID pertencente ao usuário.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    cursor.execute(f"SELECT * FROM Despesas WHERE id = {ph} AND user_id = {ph}", (despesa_id, user_id))
    despesa = cursor.fetchone()
    conn.close()
    return despesa

def criar_despesa(user_id, descricao, valor, categoria, data_despesa, forma_pagamento, observacoes=""):
    """
    Cadastra uma nova despesa vinculada ao usuário no banco de dados.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    cursor.execute(f'''
        INSERT INTO Despesas (user_id, descricao, valor, categoria, data_despesa, forma_pagamento, observacoes)
        VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
    ''', (user_id, descricao, valor, categoria, data_despesa, forma_pagamento, observacoes))
    conn.commit()
    conn.close()

def atualizar_despesa(despesa_id, user_id, descricao, valor, categoria, data_despesa, forma_pagamento, observacoes=""):
    """
    Atualiza os dados de uma despesa existente do usuário.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    cursor.execute(f'''
        UPDATE Despesas
        SET descricao = {ph}, valor = {ph}, categoria = {ph}, data_despesa = {ph}, forma_pagamento = {ph}, observacoes = {ph}
        WHERE id = {ph} AND user_id = {ph}
    ''', (descricao, valor, categoria, data_despesa, forma_pagamento, observacoes, despesa_id, user_id))
    conn.commit()
    conn.close()

def excluir_despesa(despesa_id, user_id):
    """
    Remove uma despesa do usuário do banco de dados.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    cursor.execute(f"DELETE FROM Despesas WHERE id = {ph} AND user_id = {ph}", (despesa_id, user_id))
    conn.commit()
    conn.close()

def calcular_total_despesas(user_id):
    """
    Retorna o somatório de todas as despesas cadastradas para o usuário.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    cursor.execute(f"SELECT SUM(valor) as total FROM Despesas WHERE user_id = {ph}", (user_id,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado['total'] if resultado and resultado['total'] else 0.0