from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.receita_model import (
    listar_receitas, 
    criar_receita, 
    atualizar_receita, 
    deletar_receita,
    calcular_total_receitas
)

receitas_bp = Blueprint('receitas', __name__)

@receitas_bp.route('/receitas')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    fonte_selecionada = request.args.get('fonte', '')
    busca_selecionada = request.args.get('busca', '')
    data_inicio_selecionada = request.args.get('data_inicio', '')
    data_fim_selecionada = request.args.get('data_fim', '')

    # Passando os filtros e o user_id para a função de listagem
    receitas = listar_receitas(
        user_id=user_id,
        fonte=fonte_selecionada or None, 
        busca=busca_selecionada or None,
        data_inicio=data_inicio_selecionada or None,
        data_fim=data_fim_selecionada or None
    )
    
    # Cálculo do total de receitas filtradas para o usuário logado
    total_receitas = calcular_total_receitas(
        user_id=user_id,
        fonte=fonte_selecionada or None, 
        busca=busca_selecionada or None,
        data_inicio=data_inicio_selecionada or None,
        data_fim=data_fim_selecionada or None
    ) if hasattr(calcular_total_receitas, '__code__') and 'user_id' in calcular_total_receitas.__code__.co_varnames else calcular_total_receitas(user_id=user_id)

    return render_template(
        'receitas.html', 
        receitas=receitas, 
        total_receitas=total_receitas,
        fonte_selecionada=fonte_selecionada,
        busca_selecionada=busca_selecionada,
        data_inicio_selecionada=data_inicio_selecionada,
        data_fim_selecionada=data_fim_selecionada
    )

@receitas_bp.route('/receitas/nova', methods=['POST'])
def nova():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    descricao = request.form.get('descricao')
    
    valor_str = request.form.get('valor')
    valor = float(valor_str) if valor_str else 0.0
    
    fonte = request.form.get('fonte')
    data_receita = request.form.get('data_receita')
    observacoes = request.form.get('observacoes')

    criar_receita(user_id, descricao, valor, fonte, data_receita, observacoes)
    flash('Ganho/Receita cadastrada com sucesso!', 'success')
    return redirect(url_for('receitas.index'))

@receitas_bp.route('/receitas/editar/<int:id>', methods=['POST'])
def editar(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    descricao = request.form.get('descricao')
    
    valor_str = request.form.get('valor')
    valor = float(valor_str) if valor_str else 0.0
    
    fonte = request.form.get('fonte')
    data_receita = request.form.get('data_receita')
    observacoes = request.form.get('observacoes')

    atualizar_receita(id, user_id, descricao, valor, fonte, data_receita, observacoes)
    flash('Receita atualizada com sucesso!', 'success')
    return redirect(url_for('receitas.index'))

@receitas_bp.route('/receitas/excluir/<int:id>', methods=['POST'])
def excluir(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    deletar_receita(id, user_id=user_id)
    flash('Receita removida com sucesso!', 'success')
    return redirect(url_for('receitas.index'))