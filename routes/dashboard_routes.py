from datetime import datetime
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from models.dashboard_model import (
    obter_resumo_cards,
    obter_despesas_por_categoria,
    obter_despesas_por_mes,
    obter_ultimas_despesas
)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']

    # Obtém o mês e ano do parâmetro de URL (se não passados, usa o mês/ano atuais)
    agora = datetime.now()
    mes = request.args.get('mes', type=int, default=agora.month)
    ano = request.args.get('ano', type=int, default=agora.year)

    # Passa o user_id, mês e ano para as funções que geram as métricas isoladas
    cards = obter_resumo_cards(user_id=user_id, mes=mes, ano=ano)
    ultimas_despesas = obter_ultimas_despesas(user_id=user_id, limit=5, mes=mes, ano=ano)
    
    return render_template(
        'dashboard.html', 
        cards=cards, 
        ultimas_despesas=ultimas_despesas,
        mes_atual=mes,
        ano_atual=ano
    )

@dashboard_bp.route('/api/grafico-categorias')
def api_grafico_categorias():
    if 'user_id' not in session:
        return jsonify({"erro": "Não autorizado"}), 401
        
    user_id = session['user_id']
    agora = datetime.now()
    mes = request.args.get('mes', type=int, default=agora.month)
    ano = request.args.get('ano', type=int, default=agora.year)

    dados = obter_despesas_por_categoria(user_id=user_id, mes=mes, ano=ano)
    return jsonify(dados)

@dashboard_bp.route('/api/grafico-meses')
def api_grafico_meses():
    if 'user_id' not in session:
        return jsonify({"erro": "Não autorizado"}), 401
        
    user_id = session['user_id']
    agora = datetime.now()
    mes = request.args.get('mes', type=int, default=agora.month)
    ano = request.args.get('ano', type=int, default=agora.year)

    dados = obter_despesas_por_mes(user_id=user_id, mes=mes, ano=ano)
    return jsonify(dados)