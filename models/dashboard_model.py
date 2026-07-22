from database.connection import get_db_connection

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

    # Formata o mês com 2 dígitos (ex: 7 -> '07') para o SQLite
    mes_str = f"{mes:02d}" if mes else None
    ano_str = str(ano) if ano else None

    if mes and ano:
        # Consultas Filtradas por Período
        total_receitas = conn.execute("""
            SELECT COALESCE(SUM(valor), 0) FROM Receitas 
            WHERE strftime('%m', data_receita) = ? AND strftime('%Y', data_receita) = ?
        """, (mes_str, ano_str)).fetchone()[0]

        total_despesas = conn.execute("""
            SELECT COALESCE(SUM(valor), 0) FROM Despesas 
            WHERE strftime('%m', data_despesa) = ? AND strftime('%Y', data_despesa) = ?
        """, (mes_str, ano_str)).fetchone()[0]

        total_faturas = conn.execute("""
            SELECT COALESCE(SUM(valor), 0) FROM ComprasCartao 
            WHERE strftime('%m', data_compra) = ? AND strftime('%Y', data_compra) = ?
        """, (mes_str, ano_str)).fetchone()[0]
    else:
        # Fallback caso não venha mês/ano
        total_receitas = conn.execute("SELECT COALESCE(SUM(valor), 0) FROM Receitas").fetchone()[0]
        total_despesas = conn.execute("SELECT COALESCE(SUM(valor), 0) FROM Despesas").fetchone()[0]
        total_faturas = conn.execute("SELECT COALESCE(SUM(valor), 0) FROM ComprasCartao").fetchone()[0]

    # Dados Globais (Cartões e Metas)
    total_cartoes = conn.execute("SELECT COUNT(*) FROM Cartoes").fetchone()[0]

    resumo_metas = conn.execute("""
        SELECT 
            COUNT(*), 
            COALESCE(SUM(valor_atual), 0),
            COALESCE(SUM(valor_alvo), 0) 
        FROM Metas
    """).fetchone()

    qtd_metas = resumo_metas[0]
    valor_total_guardado = resumo_metas[1]
    valor_total_alvo = resumo_metas[2]

    conn.close()

    # Cálculos dinâmicos
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
        # Retrocompatibilidade
        "qtd_objetos": qtd_metas,
        "valor_total_objetos": valor_total_guardado
    }

def obter_despesas_por_categoria(mes=None, ano=None):
    """
    Retorna os dados agrupados por categoria para o Gráfico de Rosca/Pizza
    filtrados pelo mês/ano selecionados.
    """
    conn = get_db_connection()
    
    if mes and ano:
        mes_str = f"{mes:02d}"
        ano_str = str(ano)
        dados = conn.execute('''
            SELECT categoria, SUM(valor) as total
            FROM Despesas
            WHERE strftime('%m', data_despesa) = ? AND strftime('%Y', data_despesa) = ?
            GROUP BY categoria
            ORDER BY total DESC
        ''', (mes_str, ano_str)).fetchall()
    else:
        dados = conn.execute('''
            SELECT categoria, SUM(valor) as total
            FROM Despesas
            GROUP BY categoria
            ORDER BY total DESC
        ''').fetchall()

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
    
    if ano:
        dados = conn.execute('''
            SELECT strftime('%Y-%m', data_despesa) as mes, SUM(valor) as total
            FROM Despesas
            WHERE strftime('%Y', data_despesa) <= ?
            GROUP BY mes
            ORDER BY mes ASC
            LIMIT 12
        ''', (str(ano),)).fetchall()
    else:
        dados = conn.execute('''
            SELECT strftime('%Y-%m', data_despesa) as mes, SUM(valor) as total
            FROM Despesas
            GROUP BY mes
            ORDER BY mes ASC
            LIMIT 12
        ''').fetchall()

    conn.close()

    labels = [row['mes'] for row in dados]
    valores = [row['total'] for row in dados]

    return {"labels": labels, "valores": valores}

def obter_ultimas_despesas(limit=5, mes=None, ano=None):
    """
    Retorna as despesas lançadas dentro do período filtrado.
    """
    conn = get_db_connection()
    
    if mes and ano:
        mes_str = f"{mes:02d}"
        ano_str = str(ano)
        despesas = conn.execute('''
            SELECT * FROM Despesas
            WHERE strftime('%m', data_despesa) = ? AND strftime('%Y', data_despesa) = ?
            ORDER BY data_despesa DESC, id DESC
            LIMIT ?
        ''', (mes_str, ano_str, limit)).fetchall()
    else:
        despesas = conn.execute('''
            SELECT * FROM Despesas
            ORDER BY data_despesa DESC, id DESC
            LIMIT ?
        ''', (limit,)).fetchall()

    conn.close()

    return despesas