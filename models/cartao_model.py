from datetime import datetime
from dateutil.relativedelta import relativedelta
from database.connection import DATABASE_URL, get_db_connection

def listar_cartoes(user_id, busca=None):
    """
    Retorna todos os cartões cadastrados do usuário calculando automaticamente:
    - valor_utilizado
    - limite_disponivel
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    query = f'''
        SELECT 
            c.*,
            COALESCE(SUM(cc.valor), 0) AS valor_utilizado
        FROM Cartoes c
        LEFT JOIN ComprasCartao cc ON c.id = cc.cartao_id AND cc.user_id = {ph}
        WHERE c.user_id = {ph}
    '''
    params = [user_id, user_id]

    if busca:
        query += f" AND (c.nome LIKE {ph} OR c.banco LIKE {ph})"
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

def obter_cartao_por_id(cartao_id, user_id):
    """
    Retorna os detalhes de um cartão específico do usuário com seus totais calculados.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"

    query = f'''
        SELECT 
            c.*,
            COALESCE(SUM(cc.valor), 0) AS valor_utilizado
        FROM Cartoes c
        LEFT JOIN ComprasCartao cc ON c.id = cc.cartao_id AND cc.user_id = {ph}
        WHERE c.id = {ph} AND c.user_id = {ph}
        GROUP BY c.id
    '''
    try:
        cursor.execute(query, (user_id, cartao_id, user_id))
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

def criar_cartao(user_id, nome, banco, bandeira, limite, dia_fechamento, dia_vencimento, cor="#1f2937"):
    """
    Cadastra um novo cartão de crédito vinculado ao usuário com suporte a cor personalizada.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"

    try:
        cursor.execute(f'''
            INSERT INTO Cartoes (user_id, nome, banco, bandeira, limite, dia_fechamento, dia_vencimento, cor)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
        ''', (user_id, nome, banco, bandeira, limite, dia_fechamento, dia_vencimento, cor))
        conn.commit()
    except Exception:
        if DATABASE_URL:
            conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def atualizar_cartao(cartao_id, user_id, nome, banco, bandeira, limite, dia_fechamento, dia_vencimento, cor="#1f2937"):
    """
    Atualiza os dados cadastrais do cartão do usuário incluindo a cor.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"

    try:
        cursor.execute(f'''
            UPDATE Cartoes
            SET nome = {ph}, banco = {ph}, bandeira = {ph}, limite = {ph}, dia_fechamento = {ph}, dia_vencimento = {ph}, cor = {ph}
            WHERE id = {ph} AND user_id = {ph}
        ''', (nome, banco, bandeira, limite, dia_fechamento, dia_vencimento, cor, cartao_id, user_id))
        conn.commit()
    except Exception:
        if DATABASE_URL:
            conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def excluir_cartao(cartao_id, user_id):
    """
    Remove um cartão do usuário e, via ON DELETE CASCADE, todas as suas compras associadas.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"

    try:
        cursor.execute(f"DELETE FROM Cartoes WHERE id = {ph} AND user_id = {ph}", (cartao_id, user_id))
        conn.commit()
    except Exception:
        if DATABASE_URL:
            conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

# --- Gerenciamento de Compras do Cartão ---

def listar_compras_cartao(cartao_id, user_id, busca=None, mes=None, ano=None):
    """
    Lista as compras lançadas em um determinado cartão do usuário, permitindo filtrar por termo
    e/ou por mês e ano de referência da fatura.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"

    params = [cartao_id, user_id]
    
    filtro_data = ""
    if mes and ano:
        mes_int = int(mes)
        ano_int = int(ano)
        data_inicio = f"{ano_int:04d}-{mes_int:02d}-01"
        if mes_int == 12:
            data_fim = f"{ano_int + 1:04d}-01-01"
        else:
            data_fim = f"{ano_int:04d}-{mes_int + 1:02d}-01"

        filtro_data = f" AND cc.data_compra >= {ph} AND cc.data_compra < {ph}"
        params.extend([data_inicio, data_fim])

    filtro_busca = ""
    if busca:
        filtro_busca = f" AND cc.descricao LIKE {ph}"
        params.append(f"%{busca}%")

    query = f'''
        SELECT cc.*, cat.nome AS categoria 
        FROM ComprasCartao cc
        LEFT JOIN Categorias cat ON cc.categoria_id = cat.id
        WHERE cc.cartao_id = {ph} AND cc.user_id = {ph}
        {filtro_data}
        {filtro_busca}
        ORDER BY cc.data_compra DESC, cc.id DESC
    '''

    try:
        cursor.execute(query, params)
        compras = cursor.fetchall()
    except Exception:
        if DATABASE_URL:
            conn.rollback()
            
        query_fallback = f'''
            SELECT cc.*, NULL as categoria 
            FROM ComprasCartao cc
            WHERE cc.cartao_id = {ph} AND cc.user_id = {ph}
            {filtro_data.replace("cc.", "")}
            {filtro_busca.replace("cc.", "")}
            ORDER BY data_compra DESC, id DESC
        '''
        try:
            cursor.execute(query_fallback, params)
            compras = cursor.fetchall()
        except Exception:
            if DATABASE_URL:
                conn.rollback()
            raise
    finally:
        cursor.close()
        conn.close()
        
    return compras

def criar_compra_cartao(cartao_id, user_id, descricao, valor_total, data_compra, parcelas=1, categoria_id=None, fixa=0):
    """
    Registra uma compra no cartão vinculada ao usuário. Se o número de parcelas for maior que 1,
    divide o valor total e gera automaticamente N registros nos meses subsequentes. Suporta marcação de despesa fixa.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"

    parcelas = int(parcelas) if int(parcelas) > 0 else 1
    valor_total = float(valor_total)
    fixa = int(fixa) if fixa else 0

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
                    INSERT INTO ComprasCartao (user_id, cartao_id, descricao, valor, data_compra, parcelas, parcela_atual, categoria_id, fixa)
                    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                ''', (user_id, cartao_id, desc_final, valor_atual, data_str, parcelas, i, categoria_id, fixa))
            except Exception:
                if DATABASE_URL:
                    conn.rollback()
                try:
                    cursor.execute(f'''
                        INSERT INTO ComprasCartao (user_id, cartao_id, descricao, valor, data_compra, parcelas, parcela_atual, fixa)
                        VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                    ''', (user_id, cartao_id, desc_final, valor_atual, data_str, parcelas, i, fixa))
                except Exception:
                    if DATABASE_URL:
                        conn.rollback()
                    cursor.execute(f'''
                        INSERT INTO ComprasCartao (user_id, cartao_id, descricao, valor, data_compra, parcelas, parcela_atual)
                        VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                    ''', (user_id, cartao_id, desc_final, valor_atual, data_str, parcelas, i))

        conn.commit()
    except Exception:
        if DATABASE_URL:
            conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def obter_compra_por_id(compra_id, user_id):
    """
    Retorna os detalhes de uma compra específica do usuário.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"

    try:
        cursor.execute(f"SELECT * FROM ComprasCartao WHERE id = {ph} AND user_id = {ph}", (compra_id, user_id))
        compra = cursor.fetchone()
    except Exception:
        if DATABASE_URL:
            conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
    return compra

def atualizar_compra_cartao(compra_id, user_id, descricao, valor, data_compra, parcelas, parcela_atual, categoria_id=None, fixa=0):
    """
    Atualiza os dados de uma compra específica do cartão pertencente ao usuário, incluindo a marcação de fixa.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"
    
    if categoria_id and str(categoria_id).strip():
        categoria_id = int(categoria_id)
    else:
        categoria_id = None

    fixa = int(fixa) if fixa else 0

    try:
        try:
            cursor.execute(f'''
                UPDATE ComprasCartao
                SET descricao = {ph}, valor = {ph}, data_compra = {ph}, parcelas = {ph}, parcela_atual = {ph}, categoria_id = {ph}, fixa = {ph}
                WHERE id = {ph} AND user_id = {ph}
            ''', (descricao, valor, data_compra, parcelas, parcela_atual, categoria_id, fixa, compra_id, user_id))
        except Exception:
            if DATABASE_URL:
                conn.rollback()
            try:
                cursor.execute(f'''
                    UPDATE ComprasCartao
                    SET descricao = {ph}, valor = {ph}, data_compra = {ph}, parcelas = {ph}, parcela_atual = {ph}, fixa = {ph}
                    WHERE id = {ph} AND user_id = {ph}
                ''', (descricao, valor, data_compra, parcelas, parcela_atual, fixa, compra_id, user_id))
            except Exception:
                if DATABASE_URL:
                    conn.rollback()
                cursor.execute(f'''
                    UPDATE ComprasCartao
                    SET descricao = {ph}, valor = {ph}, data_compra = {ph}, parcelas = {ph}, parcela_atual = {ph}
                    WHERE id = {ph} AND user_id = {ph}
                ''', (descricao, valor, data_compra, parcelas, parcela_atual, compra_id, user_id))

        conn.commit()
    except Exception:
        if DATABASE_URL:
            conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def excluir_compra_cartao(compra_id, user_id):
    """
    Remove uma compra específica do cartão do usuário.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = "%s" if DATABASE_URL else "?"

    try:
        cursor.execute(f"DELETE FROM ComprasCartao WHERE id = {ph} AND user_id = {ph}", (compra_id, user_id))
        conn.commit()
    except Exception:
        if DATABASE_URL:
            conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()