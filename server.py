from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import sqlite3
import json
import os

DB_NAME = 'db.sqlite3'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            face_id TEXT UNIQUE NOT NULL,
            first_name TEXT,
            last_name TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            site TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def _send_response(self, code, content, content_type='text/html'):
        self.send_response(code)
        self.send_header('Content-type', content_type)
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        if path == '/':
            path = '/index.html'
        try:
            file_path = f'templates{path}'
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self._send_response(200, content)
        except FileNotFoundError:
            self._send_response(404, 'File not found')

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = parse_qs(post_data)

        if self.path == '/authorise':
            face_id = data.get('face_id', [None])[0]
            if face_id:
                self.handle_authorisation(face_id)
            else:
                self._send_response(400, 'Bad Request')

    def handle_authorisation(self, face_id):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE face_id=?', (face_id,))
        user = cursor.fetchone()

        if user:
            self._send_response(200, 'All good', 'text/plain')
        else:
            cursor.execute('INSERT INTO users (face_id) VALUES (?)', (face_id,))
            conn.commit()
            self._send_response(201, 'New user registered', 'text/plain')

        conn.close()

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    print('Starting server...')
    httpd.serve_forever()

if __name__ == '__main__':
    init_db()
    run()
