from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from database.connection import DATABASE_URL, get_db_connection
import sqlite3

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Usa a variável DATABASE_URL para definir o placeholder correto (? ou %s)
        ph = "%s" if DATABASE_URL else "?"
        
        try:
            cursor.execute(f"SELECT * FROM usuarios WHERE email = {ph}", (email,))
            user = cursor.fetchone()
        except Exception:
            user = None
        finally:
            cursor.close()
            conn.close()

        if user and user["senha"] == senha:  # O ideal depois é usar hash de senha
            session["user_id"] = user["id"]
            session["user_email"] = user["email"]
            return redirect(url_for("dashboard.index"))
        else:
            flash("E-mail ou senha incorretos!", "danger")

    return render_template("login.html")


@auth_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        conn = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if DATABASE_URL else "?"

        try:
            cursor.execute(f"INSERT INTO usuarios (email, senha) VALUES ({ph}, {ph})", (email, senha))
            conn.commit()
            flash("Conta criada com sucesso! Faça o login.", "success")
            return redirect(url_for("auth.login"))
        except Exception:
            # Captura erro de chave duplicada tanto no SQLite quanto no PostgreSQL/Supabase
            conn.rollback()
            flash("Este e-mail já está cadastrado!", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template("cadastro.html")


@auth_bp.route("/recuperar", methods=["GET", "POST"])
def recuperar():
    if request.method == "POST":
        email = request.form.get("email")
        nova_senha = request.form.get("nova_senha")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        ph = "%s" if DATABASE_URL else "?"

        try:
            cursor.execute(f"SELECT * FROM usuarios WHERE email = {ph}", (email,))
            user = cursor.fetchone()

            if user:
                cursor.execute(f"UPDATE usuarios SET senha = {ph} WHERE email = {ph}", (nova_senha, email))
                conn.commit()
                flash("Senha alterada com sucesso! Faça o login com a nova senha.", "success")
                return redirect(url_for("auth.login"))
            else:
                flash("E-mail não encontrado no sistema.", "danger")
                return redirect(url_for("auth.recuperar"))
        finally:
            cursor.close()
            conn.close()

    return render_template("recuperar.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))