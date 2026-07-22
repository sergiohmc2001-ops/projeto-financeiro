from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
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
    busca = request.args.get('busca')
    
    # Captura mês e ano selecionados ou define o mês/ano atual como padrão
    hoje = datetime.now()
    mes = request.args.get('mes', type=int, default=hoje.month)
    ano = request.args.get('ano', type=int, default=hoje.year)

    cartoes = listar_cartoes(busca=busca)
    
    cartao_selecionado_id = request.args.get('cartao_id', type=int)
    cartao_detalhe = None
    compras = []

    if cartao_selecionado_id:
        cartao_detalhe = obter_cartao_por_id(cartao_selecionado_id)
        if cartao_detalhe:
            compras = listar_compras_cartao(
                cartao_selecionado_id, 
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
    nome = request.form.get('nome')
    banco = request.form.get('banco')
    bandeira = request.form.get('bandeira')
    limite = float(request.form.get('limite', 0))
    dia_fechamento = int(request.form.get('dia_fechamento'))
    dia_vencimento = int(request.form.get('dia_vencimento'))

    criar_cartao(nome, banco, bandeira, limite, dia_fechamento, dia_vencimento)
    flash('Cartão cadastrado com sucesso!', 'success')
    return redirect(url_for('cartoes.index'))

@cartoes_bp.route('/cartoes/editar/<int:id>', methods=['POST'])
def editar_cartao(id):
    nome = request.form.get('nome')
    banco = request.form.get('banco')
    bandeira = request.form.get('bandeira')
    limite = float(request.form.get('limite', 0))
    dia_fechamento = int(request.form.get('dia_fechamento'))
    dia_vencimento = int(request.form.get('dia_vencimento'))

    atualizar_cartao(id, nome, banco, bandeira, limite, dia_fechamento, dia_vencimento)
    flash('Cartão atualizado com sucesso!', 'success')
    return redirect(url_for('cartoes.index'))

@cartoes_bp.route('/cartoes/excluir/<int:id>', methods=['POST'])
def excluir_cartao_route(id):
    excluir_cartao(id)
    flash('Cartão e suas compras associadas foram excluídos!', 'success')
    return redirect(url_for('cartoes.index'))

# --- Compras do Cartão ---

@cartoes_bp.route('/cartoes/<int:cartao_id>/compra/nova', methods=['POST'])
def nova_compra(cartao_id):
    descricao = request.form.get('descricao')
    valor = float(request.form.get('valor', 0))
    data_compra = request.form.get('data_compra')
    parcelas = int(request.form.get('parcelas', 1))
    
    # Captura da Categoria
    categoria_id = request.form.get('categoria_id', type=int)

    mes = request.form.get('mes')
    ano = request.form.get('ano')

    # Passa o categoria_id diretamente para o model
    criar_compra_cartao(
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
    cartao_id = request.form.get('cartao_id', type=int)
    descricao = request.form.get('descricao')
    valor = float(request.form.get('valor', 0))
    data_compra = request.form.get('data_compra')
    parcelas = int(request.form.get('parcelas', 1))
    parcela_atual = int(request.form.get('parcela_atual', 1))
    
    # Captura da Categoria
    categoria_id = request.form.get('categoria_id', type=int)

    mes = request.form.get('mes')
    ano = request.form.get('ano')

    atualizar_compra_cartao(
        compra_id=id, 
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
    cartao_id = request.args.get('cartao_id', type=int)
    mes = request.args.get('mes')
    ano = request.args.get('ano')

    excluir_compra_cartao(id)
    flash('Compra removida!', 'success')
    
    return redirect(url_for('cartoes.index', cartao_id=cartao_id, mes=mes, ano=ano))