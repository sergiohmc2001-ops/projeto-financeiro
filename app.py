import sys
import traceback
from flask import Flask, redirect, render_template, request, session, url_for
from database.connection import init_db
from models.recorrente_model import processar_recorrencias_do_mes
from routes.auth_routes import auth_bp
from routes.cartoes_routes import cartoes_bp
from routes.configuracoes_routes import configuracoes_bp
from routes.dashboard_routes import dashboard_bp
from routes.despesas_routes import despesas_bp
from routes.metas_routes import metas_bp
from routes.recorrente_routes import recorrente_bp
from routes.receitas_routes import receitas_bp

app = Flask(__name__)
app.secret_key = "chave_secreta_balancas_app"

# Inicializa as tabelas do banco e processa as transações fixas com tratamento de erro visível
try:
    init_db()
    processar_recorrencias_do_mes()
except Exception as e:
    print("ERRO CRITICO AO INICIAR O BANCO:", str(e), file=sys.stderr)
    traceback.print_exc()
    raise e

# Registra os Blueprints (rotas)
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(despesas_bp)
app.register_blueprint(receitas_bp)
app.register_blueprint(cartoes_bp)
app.register_blueprint(metas_bp)
app.register_blueprint(configuracoes_bp)
app.register_blueprint(recorrente_bp)


# Bloqueador global: protege todas as rotas se o usuário não estiver logado
@app.before_request
def restringir_acesso():
    # Rotas livres que não exigem login (incluindo cadastro e recuperação de senha)
    rotas_liberadas = [
        "auth.login",
        "auth.cadastro",
        "auth.recuperar",
        "static",
    ]

    if "user_id" not in session and request.endpoint not in rotas_liberadas:
        return redirect(url_for("auth.login"))


# Rota raiz redireciona para o login ou dashboard dependendo da sessão
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("auth.login"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)