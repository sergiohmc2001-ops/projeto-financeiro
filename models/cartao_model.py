from datetime import datetime
from dateutil.relativedelta import relativedelta
from database.connection import get_db_connection

def listar_cartoes(busca=None):
    """
    Retorna todos os cartões cadastrados calculando automaticamente:
    - valor_utilizado
    - limite_disponivel
    """
    conn = get_db_connection()
    
    query = '''
        SELECT 
            c.*,
            COALESCE(SUM(cc.valor), 0) AS valor_utilizado
        FROM Cartoes c
        LEFT JOIN ComprasCartao cc ON c.id = cc.cartao_id
    '''
    params = []

    if busca:
        query += " WHERE c.nome LIKE ? OR c.banco LIKE ?"
        params.extend([f"%{busca}%", f"%{busca}%"])

    query += " GROUP BY c.id ORDER BY c.nome ASC"

    cartoes_raw = conn.execute(query, params).fetchall()
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
    query = '''
        SELECT 
            c.*,
            COALESCE(SUM(cc.valor), 0) AS valor_utilizado
        FROM Cartoes c
        LEFT JOIN ComprasCartao cc ON c.id = cc.cartao_id
        WHERE c.id = ?
        GROUP BY c.id
    '''
    cartao_raw = conn.execute(query, (cartao_id,)).fetchone()
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
    conn.execute('''
        INSERT INTO Cartoes (nome, banco, bandeira, limite, dia_fechamento, dia_vencimento)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nome, banco, bandeira, limite, dia_fechamento, dia_vencimento))
    conn.commit()
    conn.close()

def atualizar_cartao(cartao_id, nome, banco, bandeira, limite, dia_fechamento, dia_vencimento):
    """
    Atualiza os dados cadastrais do cartão.
    """
    conn = get_db_connection()
    conn.execute('''
        UPDATE Cartoes
        SET nome = ?, banco = ?, bandeira = ?, limite = ?, dia_fechamento = ?, dia_vencimento = ?
        WHERE id = ?
    ''', (nome, banco, bandeira, limite, dia_fechamento, dia_vencimento, cartao_id))
    conn.commit()
    conn.close()

def excluir_cartao(cartao_id):
    """
    Remove um cartão e, via ON DELETE CASCADE, todas as suas compras associadas.
    """
    conn = get_db_connection()
    conn.execute("DELETE FROM Cartoes WHERE id = ?", (cartao_id,))
    conn.commit()
    conn.close()

# --- Gerenciamento de Compras do Cartão ---

def listar_compras_cartao(cartao_id, busca=None, mes=None, ano=None):
    """
    Lista as compras lançadas em um determinado cartão, permitindo filtrar por termo
    e/ou por mês e ano de referência da fatura. Tenta incluir o nome da Categoria.
    """
    conn = get_db_connection()
    
    # Tenta fazer JOIN com Categorias se a tabela existir
    try:
        query = '''
            SELECT cc.*, cat.nome AS categoria 
            FROM ComprasCartao cc
            LEFT JOIN Categorias cat ON cc.categoria_id = cat.id
            WHERE cc.cartao_id = ?
        '''
        params = [cartao_id]

        if mes and ano:
            mes_str = f"{int(mes):02d}"
            ano_str = str(ano)
            query += " AND strftime('%m', cc.data_compra) = ? AND strftime('%Y', cc.data_compra) = ?"
            params.extend([mes_str, ano_str])

        if busca:
            query += " AND cc.descricao LIKE ?"
            params.append(f"%{busca}%")

        query += " ORDER BY cc.data_compra DESC, cc.id DESC"
        compras = conn.execute(query, params).fetchall()

    except Exception:
        # Fallback caso a tabela Categorias ainda não esteja estruturada no banco
        query = "SELECT *, NULL as categoria FROM ComprasCartao WHERE cartao_id = ?"
        params = [cartao_id]

        if mes and ano:
            mes_str = f"{int(mes):02d}"
            ano_str = str(ano)
            query += " AND strftime('%m', data_compra) = ? AND strftime('%Y', data_compra) = ?"
            params.extend([mes_str, ano_str])

        if busca:
            query += " AND descricao LIKE ?"
            params.append(f"%{busca}%")

        query += " ORDER BY data_compra DESC, id DESC"
        compras = conn.execute(query, params).fetchall()

    conn.close()
    return compras

def criar_compra_cartao(cartao_id, descricao, valor_total, data_compra, parcelas=1, categoria_id=None):
    """
    Registra uma compra no cartão. Se o número de parcelas for maior que 1,
    divide o valor total e gera automaticamente N registros nos meses subsequentes.
    """
    conn = get_db_connection()
    parcelas = int(parcelas) if int(parcelas) > 0 else 1
    valor_total = float(valor_total)

    # Converte string de data para objeto datetime
    if isinstance(data_compra, str):
        data_base = datetime.strptime(data_compra, '%Y-%m-%d')
    else:
        data_base = data_compra

    # Cálculo do valor das parcelas e ajuste de centavos
    valor_parcela = round(valor_total / parcelas, 2)
    diferenca_centavos = round(valor_total - (valor_parcela * parcelas), 2)

    # Converte categoria_id vazia/string para None/int
    if categoria_id and str(categoria_id).strip():
        categoria_id = int(categoria_id)
    else:
        categoria_id = None

    for i in range(1, parcelas + 1):
        # A primeira parcela absorve os centavos de arredondamento
        valor_atual = valor_parcela + diferenca_centavos if i == 1 else valor_parcela
        
        # Calcula a data para os meses subsequentes
        data_parcela = data_base + relativedelta(months=i-1)
        data_str = data_parcela.strftime('%Y-%m-%d')

        # Mantém a descrição original limpa ou formatada se desejar
        desc_final = descricao

        try:
            conn.execute('''
                INSERT INTO ComprasCartao (cartao_id, descricao, valor, data_compra, parcelas, parcela_atual, categoria_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (cartao_id, desc_final, valor_atual, data_str, parcelas, i, categoria_id))
        except Exception:
            # Fallback caso o banco ainda não possua categoria_id
            conn.execute('''
                INSERT INTO ComprasCartao (cartao_id, descricao, valor, data_compra, parcelas, parcela_atual)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (cartao_id, desc_final, valor_atual, data_str, parcelas, i))

    conn.commit()
    conn.close()

def obter_compra_por_id(compra_id):
    """
    Retorna os detalhes de uma compra específica.
    """
    conn = get_db_connection()
    compra = conn.execute("SELECT * FROM ComprasCartao WHERE id = ?", (compra_id,)).fetchone()
    conn.close()
    return compra

def atualizar_compra_cartao(compra_id, descricao, valor, data_compra, parcelas, parcela_atual, categoria_id=None):
    """
    Atualiza os dados de uma compra específica do cartão.
    """
    conn = get_db_connection()
    
    if categoria_id and str(categoria_id).strip():
        categoria_id = int(categoria_id)
    else:
        categoria_id = None

    try:
        conn.execute('''
            UPDATE ComprasCartao
            SET descricao = ?, valor = ?, data_compra = ?, parcelas = ?, parcela_atual = ?, categoria_id = ?
            WHERE id = ?
        ''', (descricao, valor, data_compra, parcelas, parcela_atual, categoria_id, compra_id))
    except Exception:
        conn.execute('''
            UPDATE ComprasCartao
            SET descricao = ?, valor = ?, data_compra = ?, parcelas = ?, parcela_atual = ?
            WHERE id = ?
        ''', (descricao, valor, data_compra, parcelas, parcela_atual, compra_id))

    conn.commit()
    conn.close()

def excluir_compra_cartao(compra_id):
    """
    Remove uma compra específica do cartão.
    """
    conn = get_db_connection()
    conn.execute("DELETE FROM ComprasCartao WHERE id = ?", (compra_id,))
    conn.commit()
    conn.close()