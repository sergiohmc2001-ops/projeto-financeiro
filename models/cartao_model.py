from datetime import datetime
from dateutil.relativedelta import relativedelta
from database.connection import DATABASE_URL, get_db_connection

def listar_cartoes(busca=None):
    """
    Retorna todos os cartões cadastrados calculando automaticamente:
    - valor_utilizado
    - limite_disponivel
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    query = '''
        SELECT 
            c.*,
            COALESCE(SUM(cc.valor), 0) AS valor_utilizado
        FROM Cartoes c
        LEFT JOIN ComprasCartao cc ON c.id = cc.cartao_id
    '''
    params = []

    if busca:
        query += f" WHERE c.nome LIKE {ph} OR c.banco LIKE {ph}"
        params.extend([f"%{busca}%", f"%{busca}%"])

    query += " GROUP BY c.id ORDER BY c.nome ASC"

    try:
        cursor.execute(query, params)
        cartoes_raw = cursor.fetchall()
    except Exception:
        if DATABASE_URL:
            conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    cartoes = []
    for c in cartoes_raw:
        cartao_dict = dict(c)
        limite = cartao_dict['limite']
        utilizado = cartao_dict['valor_utilizado']
        cartao_dict['limite_disponivel'] = limite - utilizado
        cartoes.append(cartao_dict)

    return cartoes

def obter_cartao_por_id(cartao_id):
    """
    Retorna os detalhes de um cartão específico com seus totais calculados.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"

    query = f'''
        SELECT 
            c.*,
            COALESCE(SUM(cc.valor), 0) AS valor_utilizado
        FROM Cartoes c
        LEFT JOIN ComprasCartao cc ON c.id = cc.cartao_id
        WHERE c.id = {ph}
        GROUP BY c.id
    '''
    try:
        cursor.execute(query, (cartao_id,))
        cartao_raw = cursor.fetchone()
    except Exception:
        if DATABASE_URL:
            conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

    if cartao_raw:
        cartao_dict = dict(cartao_raw)
        cartao_dict['limite_disponivel'] = cartao_dict['limite'] - cartao_dict['valor_utilizado']
        return cartao_dict
    return None

def criar_cartao(nome, banco, bandeira, limite, dia_fechamento, dia_vencimento):
    """
    Cadastra um novo cartão de crédito.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"

    try:
        cursor.execute(f'''
            INSERT INTO Cartoes (nome, banco, bandeira, limite, dia_fechamento, dia_vencimento)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})
        ''', (nome, banco, bandeira, limite, dia_fechamento, dia_vencimento))
        conn.commit()
    except Exception:
        if DATABASE_URL:
            conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def atualizar_cartao(cartao_id, nome, banco, bandeira, limite, dia_fechamento, dia_vencimento):
    """
    Atualiza os dados cadastrais do cartão.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"

    try:
        cursor.execute(f'''
            UPDATE Cartoes
            SET nome = {ph}, banco = {ph}, bandeira = {ph}, limite = {ph}, dia_fechamento = {ph}, dia_vencimento = {ph}
            WHERE id = {ph}
        ''', (nome, banco, bandeira, limite, dia_fechamento, dia_vencimento, cartao_id))
        conn.commit()
    except Exception:
        if DATABASE_URL:
            conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def excluir_cartao(cartao_id):
    """
    Remove um cartão e, via ON DELETE CASCADE, todas as suas compras associadas.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"

    try:
        cursor.execute(f"DELETE FROM Cartoes WHERE id = {ph}", (cartao_id,))
        conn.commit()
    except Exception:
        if DATABASE_URL:
            conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

# --- Gerenciamento de Compras do Cartão ---

def listar_compras_cartao(cartao_id, busca=None, mes=None, ano=None):
    """
    Lista as compras lançadas em um determinado cartão, permitindo filtrar por termo
    e/ou por mês e ano de referência da fatura. Tenta incluir o nome da Categoria.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    mes_str = f"{int(mes):02d}" if mes else None
    ano_str = str(ano) if ano else None

    try:
        query = f'''
            SELECT cc.*, cat.nome AS categoria 
            FROM ComprasCartao cc
            LEFT JOIN Categorias cat ON cc.categoria_id = cat.id
            WHERE cc.cartao_id = {ph}
        '''
        params = [cartao_id]

        if mes and ano:
            if DATABASE_URL:
                query += f" AND EXTRACT(MONTH FROM cc.data_compra) = {ph} AND EXTRACT(YEAR FROM cc.data_compra) = {ph}"
                params.extend([int(mes_str), int(ano_str)])
            else:
                query += f" AND strftime('%m', cc.data_compra) = {ph} AND strftime('%Y', cc.data_compra) = {ph}"
                params.extend([mes_str, ano_str])

        if busca:
            query += f" AND cc.descricao LIKE {ph}"
            params.append(f"%{busca}%")

        query += " ORDER BY cc.data_compra DESC, cc.id DESC"
        cursor.execute(query, params)
        compras = cursor.fetchall()

    except Exception:
        # Importante: limpa o erro de transação abortada do postgres antes de executar o fallback
        if DATABASE_URL:
            conn.rollback()

        # Fallback caso a tabela Categorias ainda não esteja estruturada no banco
        query = f"SELECT *, NULL as categoria FROM ComprasCartao WHERE cartao_id = {ph}"
        params = [cartao_id]

        if mes and ano:
            if DATABASE_URL:
                query += f" AND EXTRACT(MONTH FROM data_compra) = {ph} AND EXTRACT(YEAR FROM data_compra) = {ph}"
                params.extend([int(mes_str), int(ano_str)])
            else:
                query += f" AND strftime('%m', data_compra) = {ph} AND strftime('%Y', data_compra) = {ph}"
                params.extend([mes_str, ano_str])

        if busca:
            query += f" AND descricao LIKE {ph}"
            params.append(f"%{busca}%")

        query += " ORDER BY data_compra DESC, id DESC"
        try:
            cursor.execute(query, params)
            compras = cursor.fetchall()
        except Exception:
            if DATABASE_URL:
                conn.rollback()
            raise

    finally:
        cursor.close()
        conn.close()
        
    return compras

def criar_compra_cartao(cartao_id, descricao, valor_total, data_compra, parcelas=1, categoria_id=None):
    """
    Registra uma compra no cartão. Se o número de parcelas for maior que 1,
    divide o valor total e gera automaticamente N registros nos meses subsequentes.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"

    parcelas = int(parcelas) if int(parcelas) > 0 else 1
    valor_total = float(valor_total)

    if isinstance(data_compra, str):
        data_base = datetime.strptime(data_compra, '%Y-%m-%d')
    else:
        data_base = data_compra

    valor_parcela = round(valor_total / parcelas, 2)
    diferenca_centavos = round(valor_total - (valor_parcela * parcelas), 2)

    if categoria_id and str(categoria_id).strip():
        categoria_id = int(categoria_id)
    else:
        categoria_id = None

    try:
        for i in range(1, parcelas + 1):
            valor_atual = valor_parcela + diferenca_centavos if i == 1 else valor_parcela
            data_parcela = data_base + relativedelta(months=i-1)
            data_str = data_parcela.strftime('%Y-%m-%d')
            desc_final = descricao

            try:
                cursor.execute(f'''
                    INSERT INTO ComprasCartao (cartao_id, descricao, valor, data_compra, parcelas, parcela_atual, categoria_id)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                ''', (cartao_id, desc_final, valor_atual, data_str, parcelas, i, categoria_id))
            except Exception:
                if DATABASE_URL:
                    conn.rollback()
                cursor.execute(f'''
                    INSERT INTO ComprasCartao (cartao_id, descricao, valor, data_compra, parcelas, parcela_atual)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                ''', (cartao_id, desc_final, valor_atual, data_str, parcelas, i))

        conn.commit()
    except Exception:
        if DATABASE_URL:
            conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def obter_compra_por_id(compra_id):
    """
    Retorna os detalhes de uma compra específica.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"

    try:
        cursor.execute(f"SELECT * FROM ComprasCartao WHERE id = {ph}", (compra_id,))
        compra = cursor.fetchone()
    except Exception:
        if DATABASE_URL:
            conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
    return compra

def atualizar_compra_cartao(compra_id, descricao, valor, data_compra, parcelas, parcela_atual, categoria_id=None):
    """
    Atualiza os dados de uma compra específica do cartão.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    if categoria_id and str(categoria_id).strip():
        categoria_id = int(categoria_id)
    else:
        categoria_id = None

    try:
        try:
            cursor.execute(f'''
                UPDATE ComprasCartao
                SET descricao = {ph}, valor = {ph}, data_compra = {ph}, parcelas = {ph}, parcela_atual = {ph}, categoria_id = {ph}
                WHERE id = {ph}
            ''', (descricao, valor, data_compra, parcelas, parcela_atual, categoria_id, compra_id))
        except Exception:
            if DATABASE_URL:
                conn.rollback()
            cursor.execute(f'''
                UPDATE ComprasCartao
                SET descricao = {ph}, valor = {ph}, data_compra = {ph}, parcelas = {ph}, parcela_atual = {ph}
                WHERE id = {ph}
            ''', (descricao, valor, data_compra, parcelas, parcela_atual, compra_id))

        conn.commit()
    except Exception:
        if DATABASE_URL:
            conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def excluir_compra_cartao(compra_id):
    """
    Remove uma compra específica do cartão.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"

    try:
        cursor.execute(f"DELETE FROM ComprasCartao WHERE id = {ph}", (compra_id,))
        conn.commit()
    except Exception:
        if DATABASE_URL:
            conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()