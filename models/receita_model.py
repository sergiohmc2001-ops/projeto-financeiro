from database.connection import DATABASE_URL, get_db_connection

def listar_receitas(fonte=None, busca=None, data_inicio=None, data_fim=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    ph = "%s" if DATABASE_URL else "?"
    query = "SELECT * FROM Receitas WHERE 1=1"
    params = []

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
    conn.close()
    return receitas

def criar_receita(descricao, valor, fonte, data_receita, observacoes=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    cursor.execute(f'''
        INSERT INTO Receitas (descricao, valor, fonte, data_receita, observacoes)
        VALUES ({ph}, {ph}, {ph}, {ph}, {ph})
    ''', (descricao, valor, fonte, data_receita, observacoes))
    conn.commit()
    conn.close()

def obter_receita_por_id(receita_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    cursor.execute(f"SELECT * FROM Receitas WHERE id = {ph}", (receita_id,))
    receita = cursor.fetchone()
    conn.close()
    return receita

def atualizar_receita(receita_id, descricao, valor, fonte, data_receita, observacoes=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    cursor.execute(f'''
        UPDATE Receitas 
        SET descricao = {ph}, valor = {ph}, fonte = {ph}, data_receita = {ph}, observacoes = {ph}
        WHERE id = {ph}
    ''', (descricao, valor, fonte, data_receita, observacoes, receita_id))
    conn.commit()
    conn.close()

def deletar_receita(receita_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    cursor.execute(f"DELETE FROM Receitas WHERE id = {ph}", (receita_id,))
    conn.commit()
    conn.close()

def calcular_total_receitas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(valor) as total FROM Receitas")
    resultado = cursor.fetchone()
    conn.close()
    return resultado['total'] if resultado and resultado['total'] else 0.0