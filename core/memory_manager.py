import sqlite3
import os
import re

class MemoryManager:
    def __init__(self, data_dir, db_name="cromak_v3.db"): # Banco V3 para suportar fixação
        # Utiliza o diretório persistente repassado pelo main.py
        db_folder = os.path.join(data_dir, "banco_de_dados")
        os.makedirs(db_folder, exist_ok=True)
        self.db_path = os.path.join(db_folder, db_name)
        self._criar_tabelas()

    def _criar_tabelas(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    is_pinned INTEGER DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            ''')
            conn.commit()

    def criar_sessao(self, title="Nova Conversa"):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO sessions (title) VALUES (?)', (title,))
            conn.commit()
            return cursor.lastrowid

    def listar_sessoes(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Ordena os fixados primeiro (1), depois os mais recentes
            cursor.execute('SELECT id, title, is_pinned FROM sessions ORDER BY is_pinned DESC, id DESC')
            return cursor.fetchall()

    def renomear_sessao(self, session_id, novo_titulo):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE sessions SET title = ? WHERE id = ?', (novo_titulo, session_id))
            conn.commit()

    def fixar_sessao(self, session_id, status):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE sessions SET is_pinned = ? WHERE id = ?', (status, session_id))
            conn.commit()

    def excluir_sessao(self, session_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Apaga as mensagens primeiro, depois a sessão para não deixar dados órfãos
            cursor.execute('DELETE FROM chat_history WHERE session_id = ?', (session_id,))
            cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
            conn.commit()

    def salvar_mensagem(self, session_id, role, content):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)', (session_id, role, content))
            conn.commit()

    def carregar_historico_api(self, session_id, limite=40):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT role, content FROM (
                    SELECT role, content, id FROM chat_history WHERE session_id = ? ORDER BY id DESC LIMIT ?
                ) ORDER BY id ASC
            ''', (session_id, limite))
            
            historico = []
            for r, c in cursor.fetchall():
                # Remove o bloco da imagem em base64 para não explodir os tokens do Gemini
                c_clean = re.sub(r'!\[.*?\]\(data:image.*?\)', '[Imagem Anexada pelo Usuário]', c)
                historico.append({"role": r, "parts": [c_clean]})
            return historico

    def carregar_historico_ui(self, session_id, limite=40):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT role, content FROM (
                    SELECT role, content, id FROM chat_history WHERE session_id = ? ORDER BY id DESC LIMIT ?
                ) ORDER BY id ASC
            ''', (session_id, limite))
            return cursor.fetchall()