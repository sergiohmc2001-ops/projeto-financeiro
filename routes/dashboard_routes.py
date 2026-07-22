from datetime import datetime
from flask import Blueprint, render_template, jsonify, request
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
    # Obtém o mês e ano do parâmetro de URL (se não passados, usa o mês/ano atuais)
    agora = datetime.now()
    mes = request.args.get('mes', type=int, default=agora.month)
    ano = request.args.get('ano', type=int, default=agora.year)

    # Passa o mês e ano para as funções que geram as métricas
    cards = obter_resumo_cards(mes=mes, ano=ano)
    ultimas_despesas = obter_ultimas_despesas(limit=5, mes=mes, ano=ano)
    
    return render_template(
        'dashboard.html', 
        cards=cards, 
        ultimas_despesas=ultimas_despesas,
        mes_atual=mes,
        ano_atual=ano
    )

@dashboard_bp.route('/api/grafico-categorias')
def api_grafico_categorias():
    agora = datetime.now()
    mes = request.args.get('mes', type=int, default=agora.month)
    ano = request.args.get('ano', type=int, default=agora.year)

    dados = obter_despesas_por_categoria(mes=mes, ano=ano)
    return jsonify(dados)

@dashboard_bp.route('/api/grafico-meses')
def api_grafico_meses():
    agora = datetime.now()
    mes = request.args.get('mes', type=int, default=agora.month)
    ano = request.args.get('ano', type=int, default=agora.year)

    dados = obter_despesas_por_mes(mes=mes, ano=ano)
    return jsonify(dados)