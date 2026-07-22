import os
import shutil
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from database.connection import DATABASE_PATH

configuracoes_bp = Blueprint('configuracoes', __name__)

@configuracoes_bp.route('/configuracoes')
def index():
    return render_template('configuracoes.html')

@configuracoes_bp.route('/configuracoes/backup/download')
def fazer_backup():
    if os.path.exists(DATABASE_PATH):
        # Garante que a pasta de backup exista
        backup_folder = current_app.config.get('BACKUP_FOLDER', 'backups')
        os.makedirs(backup_folder, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"balancs_backup_{timestamp}.db"
        backup_path = os.path.join(backup_folder, backup_filename)
        
        shutil.copy2(DATABASE_PATH, backup_path)
        
        return send_file(backup_path, as_attachment=True, download_name=backup_filename)
    else:
        flash('Banco de dados não encontrado para realizar backup!', 'danger')
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

    if file and file.filename.endswith('.db'):
        file.save(DATABASE_PATH)
        flash('Banco de dados restaurado com sucesso!', 'success')
    else:
        flash('Por favor, envie um arquivo de banco de dados válido (.db).', 'danger')

    return redirect(url_for('configuracoes.index'))