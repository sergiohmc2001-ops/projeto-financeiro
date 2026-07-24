from datetime import date
from database.connection import DATABASE_URL, get_db_connection

def obter_resumo_cards(user_id, mes=None, ano=None):
    """
    Calcula os indicadores principais da tela inicial filtrados por Usuário e Mês/Ano:
    1. Total de receitas (ganhos do mês até a data de hoje)
    2. Total gasto em despesas gerais (mês)
    3. Quantidade de cartões cadastrados (global do usuário)
    4. Valor total das faturas (compras em cartão do mês)
    5. Total de saídas (Despesas + Faturas do mês)
    6. Saldo disponível/líquido (Receitas - Saídas)
    7. Dados consolidados de metas financeiras (patrimônio acumulado do usuário)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    mes_str = f"{mes:02d}" if mes else None
    ano_str = str(ano) if ano else None
    ph = "%s" if DATABASE_URL else "?"
    
    # Data de hoje para travar receitas futuras
    hoje_str = date.today().isoformat() # Formato 'YYYY-MM-DD'

    if mes and ano:
        if DATABASE_URL:
            cursor.execute(f"""
                SELECT COALESCE(SUM(valor), 0) FROM receitas 
                WHERE user_id = {ph} 
                  AND EXTRACT(MONTH FROM data_receita) = {ph} 
                  AND EXTRACT(YEAR FROM data_receita) = {ph}
                  AND data_receita <= {ph}
            """, (user_id, int(mes_str), int(ano_str), hoje_str))
            total_receitas = cursor.fetchone()[0]

            cursor.execute(f"""
                SELECT COALESCE(SUM(valor), 0) FROM despesas 
                WHERE user_id = {ph} AND EXTRACT(MONTH FROM data_despesa) = {ph} AND EXTRACT(YEAR FROM data_despesa) = {ph}
            """, (user_id, int(mes_str), int(ano_str)))
            total_despesas = cursor.fetchone()[0]

            cursor.execute(f"""
                SELECT COALESCE(SUM(valor), 0) FROM comprascartao 
                WHERE user_id = {ph} AND EXTRACT(MONTH FROM data_compra) = {ph} AND EXTRACT(YEAR FROM data_compra) = {ph}
            """, (user_id, int(mes_str), int(ano_str)))
            total_faturas = cursor.fetchone()[0]
        else:
            cursor.execute(f"""
                SELECT COALESCE(SUM(valor), 0) FROM receitas 
                WHERE user_id = {ph} 
                  AND strftime('%m', data_receita) = {ph} 
                  AND strftime('%Y', data_receita) = {ph}
                  AND data_receita <= {ph}
            """, (user_id, mes_str, ano_str, hoje_str))
            total_receitas = cursor.fetchone()[0]

            cursor.execute(f"""
                SELECT COALESCE(SUM(valor), 0) FROM despesas 
                WHERE user_id = {ph} AND strftime('%m', data_despesa) = {ph} AND strftime('%Y', data_despesa) = {ph}
            """, (user_id, mes_str, ano_str))
            total_despesas = cursor.fetchone()[0]

            cursor.execute(f"""
                SELECT COALESCE(SUM(valor), 0) FROM comprascartao 
                WHERE user_id = {ph} AND strftime('%m', data_compra) = {ph} AND strftime('%Y', data_compra) = {ph}
            """, (user_id, mes_str, ano_str))
            total_faturas = cursor.fetchone()[0]
    else:
        cursor.execute(f"SELECT COALESCE(SUM(valor), 0) FROM receitas WHERE user_id = {ph} AND data_receita <= {ph}", (user_id, hoje_str))
        total_receitas = cursor.fetchone()[0]
        cursor.execute(f"SELECT COALESCE(SUM(valor), 0) FROM despesas WHERE user_id = {ph}", (user_id,))
        total_despesas = cursor.fetchone()[0]
        cursor.execute(f"SELECT COALESCE(SUM(valor), 0) FROM comprascartao WHERE user_id = {ph}", (user_id,))
        total_faturas = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM cartoes WHERE user_id = {ph}", (user_id,))
    total_cartoes = cursor.fetchone()[0]

    cursor.execute(f"""
        SELECT 
            COUNT(*), 
            COALESCE(SUM(valor_atual), 0),
            COALESCE(SUM(valor_alvo), 0) 
        FROM metas
        WHERE user_id = {ph}
    """, (user_id,))
    resumo_metas = cursor.fetchone()

    qtd_metas = resumo_metas[0]
    valor_total_guardado = resumo_metas[1]
    valor_total_alvo = resumo_metas[2]

    cursor.close()
    conn.close()

    total_saidas = total_despesas + total_faturas
    saldo_atual = total_receitas - total_saidas

    return {
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "total_cartoes": total_cartoes,
        "total_faturas": total_faturas,
        "total_saidas": total_saidas,
        "saldo_atual": saldo_atual,
        "qtd_metas": qtd_metas,
        "valor_total_guardado": valor_total_guardado,
        "valor_total_alvo": valor_total_alvo,
        "qtd_objetos": qtd_metas,
        "valor_total_objetos": valor_total_guardado
    }

def obter_despesas_por_categoria(user_id, mes=None, ano=None):
    """
    Retorna os dados agrupados por categoria para o Gráfico de Rosca/Pizza
    filtrados pelo usuário e mês/ano selecionados.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    if mes and ano:
        mes_str = f"{mes:02d}"
        ano_str = str(ano)
        if DATABASE_URL:
            cursor.execute(f'''
                SELECT categoria, SUM(valor) as total
                FROM despesas
                WHERE user_id = {ph} AND EXTRACT(MONTH FROM data_despesa) = {ph} AND EXTRACT(YEAR FROM data_despesa) = {ph}
                GROUP BY categoria
                ORDER BY total DESC
            ''', (user_id, int(mes_str), int(ano_str)))
        else:
            cursor.execute(f'''
                SELECT categoria, SUM(valor) as total
                FROM despesas
                WHERE user_id = {ph} AND strftime('%m', data_despesa) = {ph} AND strftime('%Y', data_despesa) = {ph}
                GROUP BY categoria
                ORDER BY total DESC
            ''', (user_id, mes_str, ano_str))
    else:
        cursor.execute(f'''
            SELECT categoria, SUM(valor) as total
            FROM despesas
            WHERE user_id = {ph}
            GROUP BY categoria
            ORDER BY total DESC
        ''', (user_id,))
    
    dados = cursor.fetchall()
    cursor.close()
    conn.close()

    labels = [row['categoria'] for row in dados]
    valores = [row['total'] for row in dados]

    return {"labels": labels, "valores": valores}

def obter_despesas_por_mes(user_id, mes=None, ano=None):
    """
    Retorna o total gasto mês a mês para o Gráfico de Barras do usuário.
    Exibe o histórico até o ano selecionado.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    if ano:
        if DATABASE_URL:
            cursor.execute(f'''
                SELECT TO_CHAR(data_despesa, 'YYYY-MM') as mes, SUM(valor) as total
                FROM despesas
                WHERE user_id = {ph} AND EXTRACT(YEAR FROM data_despesa) <= {ph}
                GROUP BY mes
                ORDER BY mes ASC
                LIMIT 12
            ''', (user_id, int(ano)))
        else:
            cursor.execute(f'''
                SELECT strftime('%Y-%m', data_despesa) as mes, SUM(valor) as total
                FROM despesas
                WHERE user_id = {ph} AND strftime('%Y', data_despesa) <= {ph}
                GROUP BY mes
                ORDER BY mes ASC
                LIMIT 12
            ''', (user_id, str(ano)))
    else:
        if DATABASE_URL:
            cursor.execute(f'''
                SELECT TO_CHAR(data_despesa, 'YYYY-MM') as mes, SUM(valor) as total
                FROM despesas
                WHERE user_id = {ph}
                GROUP BY mes
                ORDER BY mes ASC
                LIMIT 12
            ''', (user_id,))
        else:
            cursor.execute(f'''
                SELECT strftime('%Y-%m', data_despesa) as mes, SUM(valor) as total
                FROM despesas
                WHERE user_id = {ph}
                GROUP BY mes
                ORDER BY mes ASC
                LIMIT 12
            ''', (user_id,))

    dados = cursor.fetchall()
    cursor.close()
    conn.close()

    labels = [row['mes'] for row in dados]
    valores = [row['total'] for row in dados]

    return {"labels": labels, "valores": valores}

def obter_ultimas_despesas(user_id, limit=5, mes=None, ano=None):
    """
    Retorna as despesas lançadas pelo usuário dentro do período filtrado.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    if mes and ano:
        mes_str = f"{mes:02d}"
        ano_str = str(ano)
        if DATABASE_URL:
            cursor.execute(f'''
                SELECT * FROM despesas
                WHERE user_id = {ph} AND EXTRACT(MONTH FROM data_despesa) = {ph} AND EXTRACT(YEAR FROM data_despesa) = {ph}
                ORDER BY data_despesa DESC, id DESC
                LIMIT {ph}
            ''', (user_id, int(mes_str), int(ano_str), limit))
        else:
            cursor.execute(f'''
                SELECT * FROM despesas
                WHERE user_id = {ph} AND strftime('%m', data_despesa) = {ph} AND strftime('%Y', data_despesa) = {ph}
                ORDER BY data_despesa DESC, id DESC
                LIMIT {ph}
            ''', (user_id, mes_str, ano_str, limit))
    else:
        cursor.execute(f'''
            SELECT * FROM despesas
            WHERE user_id = {ph}
            ORDER BY data_despesa DESC, id DESC
            LIMIT {ph}
        ''', (user_id,))

    despesas = cursor.fetchall()
    cursor.close()
    conn.close()

    return despesas