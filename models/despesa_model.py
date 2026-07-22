from database.connection import get_db_connection

def listar_despesas(mes=None, categoria=None, busca=None, ordem='DESC'):
    """
    Retorna a lista de despesas filtrada e ordenada.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM Despesas WHERE 1=1"
    params = []

    if mes:
        query += " AND strftime('%m', data_despesa) = ?"
        params.append(f"{int(mes):02d}")

    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)

    if busca:
        query += " AND (descricao LIKE ? OR observacoes LIKE ?)"
        params.append(f"%{busca}%")
        params.append(f"%{busca}%")

    query += f" ORDER BY data_despesa {ordem}, id DESC"

    cursor.execute(query, params)
    despesas = cursor.fetchall()
    conn.close()
    return despesas

def obter_despesa_por_id(despesa_id):
    """
    Retorna os detalhes de uma única despesa pelo ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Despesas WHERE id = ?", (despesa_id,))
    despesa = cursor.fetchone()
    conn.close()
    return despesa

def criar_despesa(descricao, valor, categoria, data_despesa, forma_pagamento, observacoes=""):
    """
    Cadastra uma nova despesa no banco de dados.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Despesas (descricao, valor, categoria, data_despesa, forma_pagamento, observacoes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (descricao, valor, categoria, data_despesa, forma_pagamento, observacoes))
    conn.commit()
    conn.close()

def atualizar_despesa(despesa_id, descricao, valor, categoria, data_despesa, forma_pagamento, observacoes=""):
    """
    Atualiza os dados de uma despesa existente.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE Despesas
        SET descricao = ?, valor = ?, categoria = ?, data_despesa = ?, forma_pagamento = ?, observacoes = ?
        WHERE id = ?
    ''', (descricao, valor, categoria, data_despesa, forma_pagamento, observacoes, despesa_id))
    conn.commit()
    conn.close()

def excluir_despesa(despesa_id):
    """
    Remove uma despesa do banco de dados.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Despesas WHERE id = ?", (despesa_id,))
    conn.commit()
    conn.close()

def calcular_total_despesas():
    """
    Retorna o somatório de todas as despesas cadastradas.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(valor) as total FROM Despesas")
    resultado = cursor.fetchone()
    conn.close()
    return resultado['total'] if resultado and resultado['total'] else 0.0