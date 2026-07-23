from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.meta_model import (
    listar_metas,
    obter_meta_por_id,
    criar_meta,
    atualizar_meta,
    excluir_meta
)

metas_bp = Blueprint('metas', __name__)

@metas_bp.route('/metas')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    categoria = request.args.get('categoria')
    busca = request.args.get('busca')

    metas = listar_metas(user_id=user_id, categoria=categoria, busca=busca)
    
    # Otimização: Idealmente, calcule esses somatórios diretamente no banco (SUM) conforme a tabela crescer.
    valor_alvo_total = sum(m.get('valor_alvo', 0) for m in metas)
    valor_atual_total = sum(m.get('valor_atual', 0) for m in metas)

    return render_template(
        'metas.html',
        metas=metas,
        valor_alvo_total=valor_alvo_total,
        valor_atual_total=valor_atual_total,
        cat_selecionada=categoria,
        busca_selecionada=busca
    )

@metas_bp.route('/metas/nova', methods=['POST'])
def nova():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    nome = request.form.get('nome')
    categoria = request.form.get('categoria')
    
    # Tratamento seguro para conversão de valores numéricos
    valor_alvo_str = request.form.get('valor_alvo')
    valor_alvo = float(valor_alvo_str) if valor_alvo_str else 0.0
    
    valor_atual_str = request.form.get('valor_atual')
    valor_atual = float(valor_atual_str) if valor_atual_str else 0.0
    
    data_limite = request.form.get('data_limite')
    observacoes = request.form.get('observacoes', '')

    criar_meta(user_id, nome, categoria, valor_alvo, valor_atual, data_limite, observacoes)
    flash('Meta cadastrada com sucesso!', 'success')
    return redirect(url_for('metas.index'))

@metas_bp.route('/metas/editar/<int:id>', methods=['POST'])
def editar(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    nome = request.form.get('nome')
    categoria = request.form.get('categoria')
    
    valor_alvo_str = request.form.get('valor_alvo')
    valor_alvo = float(valor_alvo_str) if valor_alvo_str else 0.0
    
    valor_atual_str = request.form.get('valor_atual')
    valor_atual = float(valor_atual_str) if valor_atual_str else 0.0
    
    data_limite = request.form.get('data_limite')
    observacoes = request.form.get('observacoes', '')

    atualizar_meta(id, user_id, nome, categoria, valor_alvo, valor_atual, data_limite, observacoes)
    flash('Meta atualizada com sucesso!', 'success')
    return redirect(url_for('metas.index'))

@metas_bp.route('/metas/excluir/<int:id>', methods=['POST'])
def excluir(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    excluir_meta(id, user_id=user_id)
    flash('Meta removida com sucesso!', 'success')
    return redirect(url_for('metas.index'))