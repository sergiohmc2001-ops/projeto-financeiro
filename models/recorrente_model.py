from datetime import datetime
from database.connection import DATABASE_URL, get_db_connection

def listar_recorrentes():
    """
    Lista todas as contas fixas/recorrentes cadastradas.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM TransacoesRecorrentes WHERE ativo = 1 ORDER BY dia_vencimento ASC"
    )
    recorrentes = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return recorrentes

def criar_recorrente(descricao, valor, tipo, dia_vencimento, categoria=None, forma_pagamento='Dinheiro/Pix'):
    """
    Cadastra uma nova receita ou despesa fixa mensal.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = "%s" if DATABASE_URL else "?"
    query = f'''
        INSERT INTO TransacoesRecorrentes (descricao, valor, tipo, categoria, forma_pagamento, dia_vencimento)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
    '''
    
    cursor.execute(query, (descricao, float(valor), tipo, categoria, forma_pagamento, int(dia_vencimento)))
    conn.commit()
    
    cursor.close()
    conn.close()

def obter_recorrente_por_id(recorrente_id):
    """
    Retorna os detalhes de uma transação recorrente específica.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = "%s" if DATABASE_URL else "?"
    cursor.execute(f"SELECT * FROM TransacoesRecorrentes WHERE id = {placeholder}", (recorrente_id,))
    recorrente = cursor.fetchone()
    
    cursor.close()
    conn.close()
    return recorrente

def excluir_recorrente(recorrente_id):
    """
    Remove um lançamento recorrente.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = "%s" if DATABASE_URL else "?"
    cursor.execute(f"DELETE FROM TransacoesRecorrentes WHERE id = {placeholder}", (recorrente_id,))
    conn.commit()
    
    cursor.close()
    conn.close()

def processar_recorrencias_do_mes():
    """
    Verifica todas as contas fixas ativas. Se alguma ainda não tiver sido
    gerada no mês/ano atual, insere automaticamente na tabela Despesas ou Receitas.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hoje = datetime.now()
    mes_ano_atual = hoje.strftime('%Y-%m') # Exemplo: '2026-07'

    cursor.execute("SELECT * FROM TransacoesRecorrentes WHERE ativo = 1")
    recorrentes = cursor.fetchall()

    placeholder = "%s" if DATABASE_URL else "?"

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

        if item['tipo'] == 'Despesa':
            cursor.execute(f'''
                INSERT INTO Despesas (descricao, valor, categoria, data_despesa, forma_pagamento, observacoes)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
                item['descricao'],
                item['valor'],
                item['categoria'] or 'Fixa',
                data_lancamento,
                item['forma_pagamento'] or 'Outros',
                'Gerado automaticamente por Transação Fixa'
            ))

        elif item['tipo'] == 'Receita':
            cursor.execute(f'''
                INSERT INTO Receitas (descricao, valor, fonte, data_receita, observacoes)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (
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