import os
import shutil
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, session
from database.connection import DATABASE_PATH, DATABASE_URL, get_db_connection

configuracoes_bp = Blueprint('configuracoes', __name__)

@configuracoes_bp.route('/configuracoes')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('configuracoes.html')

@configuracoes_bp.route('/configuracoes/backup/download')
def fazer_backup():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    is_postgres = bool(DATABASE_URL if DATABASE_URL else os.getenv("DATABASE_URL"))
    ph = "%s" if is_postgres else "?"

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Descobre quais tabelas existem no banco
        if is_postgres:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tabelas = [row['table_name'] for row in cursor.fetchall()]
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tabelas = [row['name'] for row in cursor.fetchall()]
        
        dados_backup = {}
        for tabela in tabelas:
            # Verifica se a tabela possui a coluna user_id para filtrar os dados do usuário
            cursor.execute(f"PRAGMA table_info({tabela});" if not is_postgres else f"SELECT column_name FROM information_schema.columns WHERE table_name = '{tabela}'")
            col_res = cursor.fetchall()
            colunas_tabela = [col['column_name'] if is_postgres else col[1] for col in col_res]

            if 'user_id' in colunas_tabela:
                cursor.execute(f"SELECT * FROM {tabela} WHERE user_id = {ph}", (user_id,))
            elif tabela == 'usuarios':
                cursor.execute(f"SELECT * FROM usuarios WHERE id = {ph}", (user_id,))
            else:
                continue

            colunas = [desc[0] for desc in cursor.description]
            linhas = cursor.fetchall()
            dados_backup[tabela] = [dict(zip(colunas, linha)) for linha in linhas]
            
        cursor.close()
        conn.close()

        # Salva o JSON do backup isolado do usuário
        backup_folder = current_app.config.get('BACKUP_FOLDER', 'backups')
        os.makedirs(backup_folder, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"balancs_backup_usuario_{user_id}_{timestamp}.json"
        backup_path = os.path.join(backup_folder, backup_filename)
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(dados_backup, f, ensure_ascii=False, indent=4, default=str)
            
        return send_file(backup_path, as_attachment=True, download_name=backup_filename)

    except Exception as e:
        flash(f'Erro ao gerar o backup: {str(e)}', 'danger')
        return redirect(url_for('configuracoes.index'))

@configuracoes_bp.route('/configuracoes/backup/restaurar', methods=['POST'])
def restaurar_backup():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    user_id = session['user_id']

    if 'arquivo_db' not in request.files:
        flash('Nenhum arquivo foi selecionado!', 'danger')
        return redirect(url_for('configuracoes.index'))

    file = request.files['arquivo_db']

    if file.filename == '':
        flash('Nenhum arquivo foi selecionado!', 'danger')
        return redirect(url_for('configuracoes.index'))

    if file.filename.endswith('.db'):
        flash('A restauração por arquivo .db inteiro não é permitida em ambientes compartilhados. Utilize arquivos de backup em JSON.', 'danger')
            
    elif file.filename.endswith('.json'):
        try:
            conteudo_json = json.load(file.stream)
            conn = get_db_connection()
            cursor = conn.cursor()
            is_postgres = bool(DATABASE_URL if DATABASE_URL else os.getenv("DATABASE_URL"))
            ph = "%s" if is_postgres else "?"

            for tabela, registros in conteudo_json.items():
                if tabela == 'usuarios':
                    continue 
                
                for registro in registros:
                    if 'user_id' in registro:
                        registro['user_id'] = user_id

                    registro.pop('id', None)

                    if not registro:
                        continue

                    colunas = list(registro.keys())
                    valores = list(registro.values())
                    
                    cols_sql = ", ".join(colunas)
                    placeholders = ", ".join([ph] * len(valores))
                    
                    sql = f"INSERT INTO {tabela} ({cols_sql}) VALUES ({placeholders})"
                    try:
                        cursor.execute(sql, valores)
                    except Exception:
                        pass 

            conn.commit()
            cursor.close()
            conn.close()
            flash('Dados do backup restaurados com sucesso para a sua conta!', 'success')
        except Exception as e:
            flash(f'Erro ao processar e restaurar o arquivo JSON: {str(e)}', 'danger')
    else:
        flash('Formato de arquivo inválido. Envie um arquivo .json válido.', 'danger')

    return redirect(url_for('configuracoes.index'))