from database.connection import DATABASE_URL, get_db_connection

def obter_resumo_cards(mes=None, ano=None):
    """
    Calcula os indicadores principais da tela inicial filtrados por Mês/Ano:
    1. Total de receitas (ganhos do mês)
    2. Total gasto em despesas gerais (mês)
    3. Quantidade de cartões cadastrados (global)
    4. Valor total das faturas (compras em cartão do mês)
    5. Total de saídas (Despesas + Faturas do mês)
    6. Saldo disponível/líquido (Receitas - Saídas)
    7. Dados consolidados de metas financeiras (patrimônio acumulado)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    mes_str = f"{mes:02d}" if mes else None
    ano_str = str(ano) if ano else None
    ph = "%s" if DATABASE_URL else "?"

    if mes and ano:
        if DATABASE_URL:
            cursor.execute(f"""
                SELECT COALESCE(SUM(valor), 0) FROM receitas 
                WHERE EXTRACT(MONTH FROM data_receita) = {ph} AND EXTRACT(YEAR FROM data_receita) = {ph}
            """, (int(mes_str), int(ano_str)))
            total_receitas = cursor.fetchone()[0]

            cursor.execute(f"""
                SELECT COALESCE(SUM(valor), 0) FROM despesas 
                WHERE EXTRACT(MONTH FROM data_despesa) = {ph} AND EXTRACT(YEAR FROM data_despesa) = {ph}
            """, (int(mes_str), int(ano_str)))
            total_despesas = cursor.fetchone()[0]

            cursor.execute(f"""
                SELECT COALESCE(SUM(valor), 0) FROM comprascartao 
                WHERE EXTRACT(MONTH FROM data_compra) = {ph} AND EXTRACT(YEAR FROM data_compra) = {ph}
            """, (int(mes_str), int(ano_str)))
            total_faturas = cursor.fetchone()[0]
        else:
            cursor.execute(f"""
                SELECT COALESCE(SUM(valor), 0) FROM receitas 
                WHERE strftime('%m', data_receita) = {ph} AND strftime('%Y', data_receita) = {ph}
            """, (mes_str, ano_str))
            total_receitas = cursor.fetchone()[0]

            cursor.execute(f"""
                SELECT COALESCE(SUM(valor), 0) FROM despesas 
                WHERE strftime('%m', data_despesa) = {ph} AND strftime('%Y', data_despesa) = {ph}
            """, (mes_str, ano_str))
            total_despesas = cursor.fetchone()[0]

            cursor.execute(f"""
                SELECT COALESCE(SUM(valor), 0) FROM comprascartao 
                WHERE strftime('%m', data_compra) = {ph} AND strftime('%Y', data_compra) = {ph}
            """, (mes_str, ano_str))
            total_faturas = cursor.fetchone()[0]
    else:
        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM receitas")
        total_receitas = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM despesas")
        total_despesas = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM comprascartao")
        total_faturas = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM cartoes")
    total_cartoes = cursor.fetchone()[0]

    cursor.execute("""
        SELECT 
            COUNT(*), 
            COALESCE(SUM(valor_atual), 0),
            COALESCE(SUM(valor_alvo), 0) 
        FROM metas
    """)
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

def obter_despesas_por_categoria(mes=None, ano=None):
    """
    Retorna os dados agrupados por categoria para o Gráfico de Rosca/Pizza
    filtrados pelo mês/ano selecionados.
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
                WHERE EXTRACT(MONTH FROM data_despesa) = {ph} AND EXTRACT(YEAR FROM data_despesa) = {ph}
                GROUP BY categoria
                ORDER BY total DESC
            ''', (int(mes_str), int(ano_str)))
        else:
            cursor.execute(f'''
                SELECT categoria, SUM(valor) as total
                FROM despesas
                WHERE strftime('%m', data_despesa) = {ph} AND strftime('%Y', data_despesa) = {ph}
                GROUP BY categoria
                ORDER BY total DESC
            ''', (mes_str, ano_str))
    else:
        cursor.execute('''
            SELECT categoria, SUM(valor) as total
            FROM despesas
            GROUP BY categoria
            ORDER BY total DESC
        ''')
    
    dados = cursor.fetchall()
    cursor.close()
    conn.close()

    labels = [row['categoria'] for row in dados]
    valores = [row['total'] for row in dados]

    return {"labels": labels, "valores": valores}

def obter_despesas_por_mes(mes=None, ano=None):
    """
    Retorna o total gasto mês a mês para o Gráfico de Barras.
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
                WHERE EXTRACT(YEAR FROM data_despesa) <= {ph}
                GROUP BY mes
                ORDER BY mes ASC
                LIMIT 12
            ''', (int(ano),))
        else:
            cursor.execute(f'''
                SELECT strftime('%Y-%m', data_despesa) as mes, SUM(valor) as total
                FROM despesas
                WHERE strftime('%Y', data_despesa) <= {ph}
                GROUP BY mes
                ORDER BY mes ASC
                LIMIT 12
            ''', (str(ano),))
    else:
        if DATABASE_URL:
            cursor.execute('''
                SELECT TO_CHAR(data_despesa, 'YYYY-MM') as mes, SUM(valor) as total
                FROM despesas
                GROUP BY mes
                ORDER BY mes ASC
                LIMIT 12
            ''')
        else:
            cursor.execute('''
                SELECT strftime('%Y-%m', data_despesa) as mes, SUM(valor) as total
                FROM despesas
                GROUP BY mes
                ORDER BY mes ASC
                LIMIT 12
            ''')

    dados = cursor.fetchall()
    cursor.close()
    conn.close()

    labels = [row['mes'] for row in dados]
    valores = [row['total'] for row in dados]

    return {"labels": labels, "valores": valores}

def obter_ultimas_despesas(limit=5, mes=None, ano=None):
    """
    Retorna as despesas lançadas dentro do período filtrado.
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
                WHERE EXTRACT(MONTH FROM data_despesa) = {ph} AND EXTRACT(YEAR FROM data_despesa) = {ph}
                ORDER BY data_despesa DESC, id DESC
                LIMIT {ph}
            ''', (int(mes_str), int(ano_str), limit))
        else:
            cursor.execute(f'''
                SELECT * FROM despesas
                WHERE strftime('%m', data_despesa) = {ph} AND strftime('%Y', data_despesa) = {ph}
                ORDER BY data_despesa DESC, id DESC
                LIMIT {ph}
            ''', (mes_str, ano_str, limit))
    else:
        cursor.execute(f'''
            SELECT * FROM despesas
            ORDER BY data_despesa DESC, id DESC
            LIMIT {ph}
        ''', (limit,))

    despesas = cursor.fetchall()
    cursor.close()
    conn.close()

    return despesas