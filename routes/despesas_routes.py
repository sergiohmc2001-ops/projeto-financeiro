from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.despesa_model import (
    listar_despesas,
    obter_despesa_por_id,
    criar_despesa,
    atualizar_despesa,
    excluir_despesa
)

despesas_bp = Blueprint('despesas', __name__)

@despesas_bp.route('/despesas')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    mes = request.args.get('mes')
    categoria = request.args.get('categoria')
    busca = request.args.get('busca')
    ordem = request.args.get('ordem', 'DESC')

    despesas = listar_despesas(user_id=user_id, mes=mes, categoria=categoria, busca=busca, ordem=ordem)
    
    # Otimização de Velocidade: Idealmente, o somatório deve vir direto do model/banco de dados 
    # para evitar processamento em loop no Python (ex: sum(d['valor'] for d in despesas))
    total_filtrado = sum(d['valor'] for d in despesas)

    return render_template(
        'despesas.html',
        despesas=despesas,
        total_filtrado=total_filtrado,
        mes_selecionado=mes,
        cat_selecionada=categoria,
        busca_selecionada=busca,
        ordem_selecionada=ordem
    )

@despesas_bp.route('/despesas/nova', methods=['POST'])
def nova():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    descricao = request.form.get('descricao')
    
    valor_str = request.form.get('valor')
    valor = float(valor_str) if valor_str else 0.0
    
    categoria = request.form.get('categoria')
    data_despesa = request.form.get('data_despesa')
    forma_pagamento = request.form.get('forma_pagamento')
    observacoes = request.form.get('observacoes', '')

    criar_despesa(user_id, descricao, valor, categoria, data_despesa, forma_pagamento, observacoes)
    flash('Despesa cadastrada com sucesso!', 'success')
    return redirect(url_for('despesas.index'))

@despesas_bp.route('/despesas/editar/<int:id>', methods=['POST'])
def editar(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    descricao = request.form.get('descricao')
    
    valor_str = request.form.get('valor')
    valor = float(valor_str) if valor_str else 0.0
    
    categoria = request.form.get('categoria')
    data_despesa = request.form.get('data_despesa')
    forma_pagamento = request.form.get('forma_pagamento')
    observacoes = request.form.get('observacoes', '')

    atualizar_despesa(id, user_id, descricao, valor, categoria, data_despesa, forma_pagamento, observacoes)
    flash('Despesa atualizada com sucesso!', 'success')
    return redirect(url_for('despesas.index'))

@despesas_bp.route('/despesas/excluir/<int:id>', methods=['GET', 'POST'])
def excluir(id=None):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    # Trata caso o ID venha pela URL ou pelo corpo de um formulário POST
    despesa_id = id or request.form.get('id')
    
    if despesa_id:
        excluir_despesa(despesa_id, user_id=user_id)
        flash('Despesa excluída com sucesso!', 'success')
    else:
        flash('Erro ao tentar excluir a despesa: ID não encontrado.', 'danger')
        
    return redirect(url_for('despesas.index'))