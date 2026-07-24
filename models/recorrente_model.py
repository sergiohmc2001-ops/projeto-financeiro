from datetime import datetime
import calendar
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

def criar_recorrente(user_id, descricao, valor, tipo, dia_vencimento, categoria=None, forma_pagamento='Dinheiro/Pix', mes_especifico=None):
    """
    Cadastra uma nova receita ou despesa fixa mensal (ou de mês específico) vinculada ao usuário.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholder = "%s" if DATABASE_URL else "?"
    
    # Tenta inserir incluindo mes_especifico (caso a coluna exista no banco)
    try:
        query = f'''
            INSERT INTO TransacoesRecorrentes (user_id, descricao, valor, tipo, categoria, forma_pagamento, dia_vencimento, mes_especifico)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        '''
        cursor.execute(query, (user_id, descricao, float(valor), tipo, categoria, forma_pagamento, int(dia_vencimento), mes_especifico))
    except Exception:
        if DATABASE_URL:
            conn.rollback()
        # Fallback caso a tabela ainda não tenha a coluna mes_especifico criada
        query = f'''
            INSERT INTO TransacoesRecorrentes (user_id, descricao, valor, tipo, categoria, forma_pagamento, dia_vencimento)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        '''
        cursor.execute(query, (user_id, descricao, float(valor), tipo, categoria, forma_pagamento, int(dia_vencimento)))
        
    conn.commit()
    cursor.close()
    conn.close()

def registrar_recorrente_via_cartao(user_id, descricao, valor, data_compra, categoria=None):
    """
    Espelha uma compra de cartão marcada como fixa na tabela de Transações Recorrentes,
    evitando duplicidade caso já exista um registro com a mesma descrição e valor.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholder = "%s" if DATABASE_URL else "?"

    if isinstance(data_compra, str):
        data_base = datetime.strptime(data_compra, '%Y-%m-%d')
    else:
        data_base = data_compra

    dia_vencimento = data_base.day
    mes_ano_atual = data_base.strftime('%Y-%m')

    # Verifica se já existe uma recorrente idêntica para evitar duplicidade visual na tela
    cursor.execute(f'''
        SELECT id FROM TransacoesRecorrentes 
        WHERE user_id = {placeholder} AND descricao = {placeholder} AND valor = {placeholder}
    ''', (user_id, descricao, float(valor)))
    existe = cursor.fetchone()

    if not existe:
        cat_final = categoria or 'Cartão de Crédito'
        try:
            cursor.execute(f'''
                INSERT INTO TransacoesRecorrentes (user_id, descricao, valor, tipo, categoria, forma_pagamento, dia_vencimento, ativo, ultimo_processamento)
                VALUES ({placeholder}, {placeholder}, {placeholder}, 'Despesa', {placeholder}, 'Cartão', {placeholder}, 1, {placeholder})
            ''', (user_id, descricao, float(valor), cat_final, dia_vencimento, mes_ano_atual))
        except Exception:
            if DATABASE_URL:
                conn.rollback()
            try:
                # Fallback caso a tabela não tenha todas as colunas opcionais
                cursor.execute(f'''
                    INSERT INTO TransacoesRecorrentes (user_id, descricao, valor, tipo, dia_vencimento)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, 'Despesa', {placeholder})
                ''', (user_id, descricao, float(valor), dia_vencimento))
            except Exception:
                pass
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
    caso contrário, processa para todos os usuários ativos.
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
        if item.get('ultimo_processamento') == mes_ano_atual:
            continue

        # Se a transação tem um mês específico definido (ex: '2026-07') e não é o mês atual, pula
        mes_especifico = item.get('mes_especifico')
        if mes_especifico and mes_especifico.strip() and mes_especifico != mes_ano_atual:
            continue

        # Trata o dia do vencimento caso o mês atual tenha menos dias (ex: dia 31 em fevereiro)
        dia = item['dia_vencimento']
        try:
            data_lancamento = datetime(hoje.year, hoje.month, dia).strftime('%Y-%m-%d')
        except ValueError:
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