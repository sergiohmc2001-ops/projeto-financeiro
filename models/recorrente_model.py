from datetime import datetime
from database.connection import DATABASE_URL, get_db_connection

def listar_recorrentes(user_id):
    """
    Lista todas as contas fixas/recorrentes cadastradas para o usuário.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = "%s" if DATABASE_URL else "?"
    cursor.execute(
        f"SELECT * FROM TransacoesRecorrentes WHERE user_id = {placeholder} AND ativo = 1 ORDER BY dia_vencimento ASC",
        (user_id,)
    )
    recorrentes = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return recorrentes

def criar_recorrente(user_id, descricao, valor, tipo, dia_vencimento, categoria=None, forma_pagamento='Dinheiro/Pix'):
    """
    Cadastra uma nova receita ou despesa fixa mensal vinculada ao usuário.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = "%s" if DATABASE_URL else "?"
    query = f'''
        INSERT INTO TransacoesRecorrentes (user_id, descricao, valor, tipo, categoria, forma_pagamento, dia_vencimento)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
    '''
    
    cursor.execute(query, (user_id, descricao, float(valor), tipo, categoria, forma_pagamento, int(dia_vencimento)))
    conn.commit()
    
    cursor.close()
    conn.close()

def obter_recorrente_por_id(recorrente_id, user_id):
    """
    Retorna os detalhes de uma transação recorrente específica do usuário.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = "%s" if DATABASE_URL else "?"
    cursor.execute(f"SELECT * FROM TransacoesRecorrentes WHERE id = {placeholder} AND user_id = {placeholder}", (recorrente_id, user_id))
    recorrente = cursor.fetchone()
    
    cursor.close()
    conn.close()
    return recorrente

def excluir_recorrente(recorrente_id, user_id):
    """
    Remove um lançamento recorrente do usuário.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = "%s" if DATABASE_URL else "?"
    cursor.execute(f"DELETE FROM TransacoesRecorrentes WHERE id = {placeholder} AND user_id = {placeholder}", (recorrente_id, user_id))
    conn.commit()
    
    cursor.close()
    conn.close()

def processar_recorrencias_do_mes(user_id=None):
    """
    Verifica contas fixas ativas. Se user_id for passado, processa apenas para ele; 
    caso contrário, pode ser adaptado ou chamado passando o usuário da sessão.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hoje = datetime.now()
    mes_ano_atual = hoje.strftime('%Y-%m') # Exemplo: '2026-07'
    placeholder = "%s" if DATABASE_URL else "?"

    if user_id:
        cursor.execute(f"SELECT * FROM TransacoesRecorrentes WHERE user_id = {placeholder} AND ativo = 1", (user_id,))
    else:
        cursor.execute("SELECT * FROM TransacoesRecorrentes WHERE ativo = 1")
        
    recorrentes = cursor.fetchall()

    for item in recorrentes:
        # Se já foi processada neste mês, pula para a próxima
        if item['ultimo_processamento'] == mes_ano_atual:
            continue

        # Trata o dia do vencimento caso o mês atual tenha menos dias (ex: dia 31 em fevereiro)
        dia = item['dia_vencimento']
        try:
            data_lancamento = datetime(hoje.year, hoje.month, dia).strftime('%Y-%m-%d')
        except ValueError:
            # Pega o último dia do mês corrente se o dia configurado não existir no mês
            import calendar
            ultimo_dia = calendar.monthrange(hoje.year, hoje.month)[1]
            data_lancamento = datetime(hoje.year, hoje.month, ultimo_dia).strftime('%Y-%m-%d')

        current_user_id = item['user_id']

        if item['tipo'] == 'Despesa':
            cursor.execute(f'''
                INSERT INTO Despesas (user_id, descricao, valor, categoria, data_despesa, forma_pagamento, observacoes)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                current_user_id,
                item['descricao'],
                item['valor'],
                item['categoria'] or 'Fixa',
                data_lancamento,
                item['forma_pagamento'] or 'Outros',
                'Gerado automaticamente por Transação Fixa'
            ))

        elif item['tipo'] == 'Receita':
            cursor.execute(f'''
                INSERT INTO Receitas (user_id, descricao, valor, fonte, data_receita, observacoes)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                current_user_id,
                item['descricao'],
                item['valor'],
                item['categoria'] or 'Fixa',
                data_lancamento,
                'Gerado automaticamente por Transação Fixa'
            ))

        # Atualiza a marcação para indicar que já foi lançada neste mês
        cursor.execute(f'''
            UPDATE TransacoesRecorrentes 
            SET ultimo_processamento = {placeholder} 
            WHERE id = {placeholder}
        ''', (mes_ano_atual, item['id']))

    conn.commit()
    cursor.close()
    conn.close()