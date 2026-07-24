from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.recorrente_model import listar_recorrentes, criar_recorrente, excluir_recorrente

recorrente_bp = Blueprint('recorrente', __name__)

@recorrente_bp.route('/recorrentes', methods=['GET'])
def gerenciar_recorrentes():
    """
    Exibe a tela de gerenciamento de transações recorrentes/fixas.
    """
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    recorrentes = listar_recorrentes(user_id=user_id)
    return render_template('recorrente.html', recorrentes=recorrentes)

@recorrente_bp.route('/recorrentes/criar', methods=['POST'])
def criar():
    """
    Cadastra uma nova transação recorrente ou com mês específico.
    """
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    descricao = request.form.get('descricao')
    
    valor_str = request.form.get('valor')
    valor = float(valor_str) if valor_str else 0.0
    
    tipo = request.form.get('tipo') # 'Despesa' ou 'Receita'
    categoria = request.form.get('categoria')
    forma_pagamento = request.form.get('forma_pagamento', 'Dinheiro/Pix')
    
    dia_vencimento_str = request.form.get('dia_vencimento')
    dia_vencimento = int(dia_vencimento_str) if dia_vencimento_str else 1

    # Novo campo para definir se é de um mês/ano específico (ex: '2026-07') ou vazio (recorrente mensal)
    mes_especifico = request.form.get('mes_especifico')
    if not mes_especifico or not mes_especifico.strip():
        mes_especifico = None

    if descricao and valor > 0 and tipo and dia_vencimento:
        criar_recorrente(
            user_id=user_id, 
            descricao=descricao, 
            valor=valor, 
            tipo=tipo, 
            dia_vencimento=dia_vencimento, 
            categoria=categoria, 
            forma_pagamento=forma_pagamento, 
            mes_especifico=mes_especifico
        )
        flash('Transação cadastrada com sucesso!', 'success')
    else:
        flash('Preencha todos os campos obrigatórios corretamente.', 'danger')

    return redirect(url_for('recorrente.gerenciar_recorrentes'))

@recorrente_bp.route('/recorrentes/excluir/<int:recorrente_id>', methods=['POST'])
def excluir(recorrente_id):
    """
    Remove uma transação recorrente.
    """
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']
    excluir_recorrente(recorrente_id, user_id=user_id)
    flash('Transação fixa removida com sucesso!', 'success')
    return redirect(url_for('recorrente.gerenciar_recorrentes'))