from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.cartao_model import (
    listar_cartoes,
    obter_cartao_por_id,
    criar_cartao,
    atualizar_cartao,
    excluir_cartao,
    listar_compras_cartao,
    criar_compra_cartao,
    atualizar_compra_cartao,
    excluir_compra_cartao
)

# Função temporária até que a tabela/model de categorias seja criada definitivamente
def listar_categorias():
    return []

cartoes_bp = Blueprint('cartoes', __name__)

@cartoes_bp.route('/cartoes')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    busca = request.args.get('busca')
    
    # Captura mês e ano selecionados ou define o mês/ano atual como padrão
    hoje = datetime.now()
    mes = request.args.get('mes', type=int, default=hoje.month)
    ano = request.args.get('ano', type=int, default=hoje.year)

    cartoes = listar_cartoes(user_id=user_id, busca=busca)
    
    cartao_selecionado_id = request.args.get('cartao_id', type=int)
    cartao_detalhe = None
    compras = []

    if cartao_selecionado_id:
        cartao_detalhe = obter_cartao_por_id(cartao_selecionado_id, user_id=user_id)
        if cartao_detalhe:
            compras = listar_compras_cartao(
                cartao_selecionado_id, 
                user_id=user_id,
                busca=busca, 
                mes=mes, 
                ano=ano
            )

    # Carrega as categorias
    categorias = listar_categorias()

    return render_template(
        'cartoes.html',
        cartoes=cartoes,
        cartao_detalhe=cartao_detalhe,
        compras=compras,
        categorias=categorias,
        busca=busca,
        mes_atual=mes,
        ano_atual=ano
    )

@cartoes_bp.route('/cartoes/novo', methods=['POST'])
def novo_cartao():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    nome = request.form.get('nome')
    banco = request.form.get('banco')
    bandeira = request.form.get('bandeira')
    
    # Tratamento seguro para campos numéricos que podem vir vazios
    limite_str = request.form.get('limite')
    limite = float(limite_str) if limite_str else 0.0
    
    dia_fechamento = int(request.form.get('dia_fechamento') or 1)
    dia_vencimento = int(request.form.get('dia_vencimento') or 1)
    cor = request.form.get('cor', '#1f2937')

    criar_cartao(user_id, nome, banco, bandeira, limite, dia_fechamento, dia_vencimento, cor)
    flash('Cartão cadastrado com sucesso!', 'success')
    return redirect(url_for('cartoes.index'))

@cartoes_bp.route('/cartoes/editar/<int:id>', methods=['POST'])
def editar_cartao(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    nome = request.form.get('nome')
    banco = request.form.get('banco')
    bandeira = request.form.get('bandeira')
    
    limite_str = request.form.get('limite')
    limite = float(limite_str) if limite_str else 0.0
    
    dia_fechamento = int(request.form.get('dia_fechamento') or 1)
    dia_vencimento = int(request.form.get('dia_vencimento') or 1)
    cor = request.form.get('cor', '#1f2937')

    atualizar_cartao(id, user_id, nome, banco, bandeira, limite, dia_fechamento, dia_vencimento, cor)
    flash('Cartão atualizado com sucesso!', 'success')
    return redirect(url_for('cartoes.index'))

@cartoes_bp.route('/cartoes/excluir/<int:id>', methods=['POST'])
def excluir_cartao_route(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    excluir_cartao(id, user_id=user_id)
    flash('Cartão e suas compras associadas foram excluídos!', 'success')
    return redirect(url_for('cartoes.index'))

# --- Compras do Cartão ---

@cartoes_bp.route('/cartoes/<int:cartao_id>/compra/nova', methods=['POST'])
def nova_compra(cartao_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    descricao = request.form.get('descricao')
    
    valor_str = request.form.get('valor')
    valor = float(valor_str) if valor_str else 0.0
    
    data_compra = request.form.get('data_compra')
    parcelas = int(request.form.get('parcelas') or 1)
    
    # Captura da Categoria
    categoria_id = request.form.get('categoria_id', type=int)

    mes = request.form.get('mes')
    ano = request.form.get('ano')

    criar_compra_cartao(
        user_id=user_id,
        cartao_id=cartao_id, 
        descricao=descricao, 
        valor_total=valor, 
        data_compra=data_compra, 
        parcelas=parcelas, 
        categoria_id=categoria_id
    )

    flash('Compra lançada no cartão com sucesso!', 'success')
    return redirect(url_for('cartoes.index', cartao_id=cartao_id, mes=mes, ano=ano))

@cartoes_bp.route('/cartoes/compra/editar/<int:id>', methods=['POST'])
def editar_compra(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    cartao_id = request.form.get('cartao_id', type=int)
    descricao = request.form.get('descricao')
    
    valor_str = request.form.get('valor')
    valor = float(valor_str) if valor_str else 0.0
    
    data_compra = request.form.get('data_compra')
    parcelas = int(request.form.get('parcelas') or 1)
    parcela_atual = int(request.form.get('parcela_atual') or 1)
    
    # Captura da Categoria
    categoria_id = request.form.get('categoria_id', type=int)

    mes = request.form.get('mes')
    ano = request.form.get('ano')

    atualizar_compra_cartao(
        compra_id=id, 
        user_id=user_id,
        descricao=descricao, 
        valor=valor, 
        data_compra=data_compra, 
        parcelas=parcelas, 
        parcela_atual=parcela_atual, 
        categoria_id=categoria_id
    )

    flash('Compra atualizada!', 'success')
    return redirect(url_for('cartoes.index', cartao_id=cartao_id, mes=mes, ano=ano))

@cartoes_bp.route('/cartoes/compra/excluir/<int:id>', methods=['POST'])
def excluir_compra(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    # Captura os parâmetros enviados via query string na URL de exclusão
    cartao_id = request.args.get('cartao_id', type=int)
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)

    excluir_compra_cartao(id, user_id=user_id)
    flash('Compra removida!', 'success')
    
    # Redireciona de volta para a fatura do cartão mantendo o mês e ano visualizados
    return redirect(url_for('cartoes.index', cartao_id=cartao_id, mes=mes, ano=ano))