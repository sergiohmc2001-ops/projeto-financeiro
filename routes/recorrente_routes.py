from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.recorrente_model import listar_recorrentes, criar_recorrente, excluir_recorrente

recorrente_bp = Blueprint('recorrente', __name__)

@recorrente_bp.route('/recorrentes', methods=['GET'])
def gerenciar_recorrentes():
    """
    Exibe a tela de gerenciamento de transações recorrentes/fixas.
    """
    recorrentes = listar_recorrentes()
    return render_template('recorrente.html', recorrentes=recorrentes)

@recorrente_bp.route('/recorrentes/criar', methods=['POST'])
def criar():
    """
    Cadastra uma nova transação recorrente.
    """
    descricao = request.form.get('descricao')
    valor = request.form.get('valor')
    tipo = request.form.get('tipo') # 'Despesa' ou 'Receita'
    categoria = request.form.get('categoria')
    forma_pagamento = request.form.get('forma_pagamento', 'Dinheiro/Pix')
    dia_vencimento = request.form.get('dia_vencimento')

    if descricao and valor and tipo and dia_vencimento:
        criar_recorrente(descricao, valor, tipo, dia_vencimento, categoria, forma_pagamento)
        flash('Transação fixa cadastrada com sucesso!', 'success')
    else:
        flash('Preencha todos os campos obrigatórios.', 'danger')

    return redirect(url_for('recorrente.gerenciar_recorrentes'))

@recorrente_bp.route('/recorrentes/excluir/<int:recorrente_id>', methods=['POST'])
def excluir(recorrente_id):
    """
    Remove uma transação recorrente.
    """
    excluir_recorrente(recorrente_id)
    flash('Transação fixa removida com sucesso!', 'success')
    return redirect(url_for('recorrente.gerenciar_recorrentes'))