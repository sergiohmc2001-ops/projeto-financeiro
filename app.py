from flask import Flask
from database.connection import init_db
from models.recorrente_model import processar_recorrencias_do_mes
from routes.dashboard_routes import dashboard_bp
from routes.despesas_routes import despesas_bp
from routes.receitas_routes import receitas_bp
from routes.cartoes_routes import cartoes_bp
from routes.metas_routes import metas_bp
from routes.configuracoes_routes import configuracoes_bp
from routes.recorrente_routes import recorrente_bp

app = Flask(__name__)
app.secret_key = "chave_secreta_balancas_app"

# Inicializa as tabelas do banco SQLite e processa as transações fixas do mês
init_db()
processar_recorrencias_do_mes()

# Registra os Blueprints (rotas)
app.register_blueprint(dashboard_bp)
app.register_blueprint(despesas_bp)
app.register_blueprint(receitas_bp)
app.register_blueprint(cartoes_bp)
app.register_blueprint(metas_bp)
app.register_blueprint(configuracoes_bp)
app.register_blueprint(recorrente_bp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)