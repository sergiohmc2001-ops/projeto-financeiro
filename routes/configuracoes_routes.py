import os
import shutil
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from database.connection import DATABASE_PATH, get_db_connection

configuracoes_bp = Blueprint('configuracoes', __name__)

@configuracoes_bp.route('/configuracoes')
def index():
    return render_template('configuracoes.html')

@configuracoes_bp.route('/configuracoes/backup/download')
def fazer_backup():
    # 1. Cenário SQLite Local (Arquivo físico existe)
    if DATABASE_PATH and os.path.exists(DATABASE_PATH):
        backup_folder = current_app.config.get('BACKUP_FOLDER', 'backups')
        os.makedirs(backup_folder, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"balancs_backup_{timestamp}.db"
        backup_path = os.path.join(backup_folder, backup_filename)
        
        shutil.copy2(DATABASE_PATH, backup_path)
        
        return send_file(backup_path, as_attachment=True, download_name=backup_filename)
    
    # 2. Cenário Nuvem (PostgreSQL / Supabase) - Gera um backup em JSON inteligente
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Descobre quais tabelas existem no banco remoto
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tabelas = [row['table_name'] for row in cursor.fetchall()] if DATABASE_PATH else [row[0] for row in cursor.fetchall()]
        
        dados_backup = {}
        for tabela in tabelas:
            cursor.execute(f"SELECT * FROM {tabela}")
            colunas = [desc[0] for desc in cursor.description]
            linhas = cursor.fetchall()
            # Converte as linhas para dicionários para serializar em JSON
            dados_backup[tabela] = [dict(zip(colunas, linha)) for linha in linhas]
            
        cursor.close()
        conn.close()

        # Salva o JSON temporariamente para download
        backup_folder = current_app.config.get('BACKUP_FOLDER', 'backups')
        os.makedirs(backup_folder, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"balancs_backup_nuvem_{timestamp}.json"
        backup_path = os.path.join(backup_folder, backup_filename)
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(dados_backup, f, ensure_ascii=False, indent=4, default=str)
            
        return send_file(backup_path, as_attachment=True, download_name=backup_filename)

    except Exception as e:
        flash(f'Erro ao gerar o backup: {str(e)}', 'danger')
        return redirect(url_for('configuracoes.index'))

@configuracoes_bp.route('/configuracoes/backup/restaurar', methods=['POST'])
def restaurar_backup():
    if 'arquivo_db' not in request.files:
        flash('Nenhum arquivo foi selecionado!', 'danger')
        return redirect(url_for('configuracoes.index'))

    file = request.files['arquivo_db']

    if file.filename == '':
        flash('Nenhum arquivo foi selecionado!', 'danger')
        return redirect(url_for('configuracoes.index'))

    # Restauração para arquivo .db (SQLite Local)
    if file.filename.endswith('.db'):
        if DATABASE_PATH and os.path.exists(DATABASE_PATH):
            try:
                file.save(DATABASE_PATH)
                flash('Banco de dados (.db) restaurado com sucesso!', 'success')
            except Exception as e:
                flash(f'Erro ao restaurar o arquivo .db: {str(e)}', 'danger')
        else:
            flash('O sistema está configurado para banco remoto e não pode receber um arquivo .db local.', 'danger')
            
    # Restauração ou leitura para arquivo .json (Nuvem)
    elif file.filename.endswith('.json'):
        try:
            conteudo_json = json.load(file.stream)
            flash('Arquivo JSON processado com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao processar o arquivo JSON: {str(e)}', 'danger')
    else:
        flash('Formato de arquivo inválido. Envie um arquivo .db ou .json válido.', 'danger')

    return redirect(url_for('configuracoes.index'))