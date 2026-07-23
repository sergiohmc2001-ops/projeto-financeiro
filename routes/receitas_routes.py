from flask import Blueprint, render_template, request, redirect, url_for, flash
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
    fonte_selecionada = request.args.get('fonte', '')
    busca_selecionada = request.args.get('busca', '')
    data_inicio_selecionada = request.args.get('data_inicio', '')
    data_fim_selecionada = request.args.get('data_fim', '')

    # Passando os filtros para a função de listagem
    receitas = listar_receitas(
        fonte=fonte_selecionada or None, 
        busca=busca_selecionada or None,
        data_inicio=data_inicio_selecionada or None,
        data_fim=data_fim_selecionada or None
    )
    
    # Se houver filtro ativo, o ideal é calcular o total filtrado, mas mantemos a chamada padrão caso o model faça o cálculo geral
    total_receitas = calcular_total_receitas(
        fonte=fonte_selecionada or None, 
        busca=busca_selecionada or None,
        data_inicio=data_inicio_selecionada or None,
        data_fim=data_fim_selecionada or None
    ) if hasattr(calcular_total_receitas, '__code__') and 'data_inicio' in calcular_total_receitas.__code__.co_varnames else calcular_total_receitas()

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
    descricao = request.form.get('descricao')
    
    valor_str = request.form.get('valor')
    valor = float(valor_str) if valor_str else 0.0
    
    fonte = request.form.get('fonte')
    data_receita = request.form.get('data_receita')
    observacoes = request.form.get('observacoes')

    criar_receita(descricao, valor, fonte, data_receita, observacoes)
    flash('Ganho/Receita cadastrada com sucesso!', 'success')
    return redirect(url_for('receitas.index'))

@receitas_bp.route('/receitas/editar/<int:id>', methods=['POST'])
def editar(id):
    descricao = request.form.get('descricao')
    
    valor_str = request.form.get('valor')
    valor = float(valor_str) if valor_str else 0.0
    
    fonte = request.form.get('fonte')
    data_receita = request.form.get('data_receita')
    observacoes = request.form.get('observacoes')

    atualizar_receita(id, descricao, valor, fonte, data_receita, observacoes)
    flash('Receita atualizada com sucesso!', 'success')
    return redirect(url_for('receitas.index'))

@receitas_bp.route('/receitas/excluir/<int:id>', methods=['POST'])
def excluir(id):
    deletar_receita(id)
    flash('Receita removida com sucesso!', 'success')
    return redirect(url_for('receitas.index'))