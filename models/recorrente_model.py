from datetime import datetime
from database.connection import get_db_connection

def listar_recorrentes():
    """
    Lista todas as contas fixas/recorrentes cadastradas.
    """
    conn = get_db_connection()
    recorrentes = conn.execute(
        "SELECT * FROM TransacoesRecorrentes WHERE ativo = 1 ORDER BY dia_vencimento ASC"
    ).fetchall()
    conn.close()
    return recorrentes

def criar_recorrente(descricao, valor, tipo, dia_vencimento, categoria=None, forma_pagamento='Dinheiro/Pix'):
    """
    Cadastra uma nova receita ou despesa fixa mensal.
    """
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO TransacoesRecorrentes (descricao, valor, tipo, categoria, forma_pagamento, dia_vencimento)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (descricao, float(valor), tipo, categoria, forma_pagamento, int(dia_vencimento)))
    conn.commit()
    conn.close()

def obter_recorrente_por_id(recorrente_id):
    """
    Retorna os detalhes de uma transação recorrente específica.
    """
    conn = get_db_connection()
    recorrente = conn.execute("SELECT * FROM TransacoesRecorrentes WHERE id = ?", (recorrente_id,)).fetchone()
    conn.close()
    return recorrente

def excluir_recorrente(recorrente_id):
    """
    Remove um lançamento recorrente.
    """
    conn = get_db_connection()
    conn.execute("DELETE FROM TransacoesRecorrentes WHERE id = ?", (recorrente_id,))
    conn.commit()
    conn.close()

def processar_recorrencias_do_mes():
    """
    Verifica todas as contas fixas ativas. Se alguma ainda não tiver sido
    gerada no mês/ano atual, insere automaticamente na tabela Despesas ou Receitas.
    """
    conn = get_db_connection()
    hoje = datetime.now()
    mes_ano_atual = hoje.strftime('%Y-%m') # Exemplo: '2026-07'

    recorrentes = conn.execute("SELECT * FROM TransacoesRecorrentes WHERE ativo = 1").fetchall()

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
            conn.execute('''
                INSERT INTO Despesas (descricao, valor, categoria, data_despesa, forma_pagamento, observacoes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                item['descricao'],
                item['valor'],
                item['categoria'] or 'Fixa',
                data_lancamento,
                item['forma_pagamento'] or 'Outros',
                'Gerado automaticamente por Transação Fixa'
            ))

        elif item['tipo'] == 'Receita':
            conn.execute('''
                INSERT INTO Receitas (descricao, valor, fonte, data_receita, observacoes)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                item['descricao'],
                item['valor'],
                item['categoria'] or 'Fixa',
                data_lancamento,
                'Gerado automaticamente por Transação Fixa'
            ))

        # Atualiza a marcação para indicar que já foi lançada neste mês
        conn.execute('''
            UPDATE TransacoesRecorrentes 
            SET ultimo_processamento = ? 
            WHERE id = ?
        ''', (mes_ano_atual, item['id']))

    conn.commit()
    conn.close()