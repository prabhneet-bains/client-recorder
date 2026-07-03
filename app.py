import os
from flask import Flask, request, Response
import requests

PUBLIC_SERVER_URL = os.getenv('BACKEND_URL', 'https://impulse-perfume-afterlife.ngrok-free.dev')
API_KEY = os.getenv('API_KEY', 'jskjdbcskdcs987345873468')
HEADERS = {'X-API-KEY': API_KEY}

app = Flask(__name__, static_folder='static', static_url_path='/static')

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/append_chunk', methods=['POST'])
def append_chunk():
    if 'file' not in request.files or 'session_id' not in request.form:
        return Response('Missing file or session_id', status=400)

    file_storage = request.files['file']
    session_id = request.form['session_id']

    with file_storage.stream as file_stream:
        files = {'file': (file_storage.filename, file_stream, file_storage.content_type)}
        try:
            backend = requests.post(
                f'{PUBLIC_SERVER_URL}/append_chunk',
                files=files,
                data={'session_id': session_id},
                headers=HEADERS,
                timeout=60,
            )
            return Response(backend.content, status=backend.status_code, content_type=backend.headers.get('Content-Type', 'application/json'))
        except requests.RequestException as exc:
            return Response(f'Backend request failed: {exc}', status=502)

@app.route('/finalize_session', methods=['POST'])
def finalize_session():
    session_id = request.form.get('session_id')
    if not session_id:
        return Response('Missing session_id', status=400)

    try:
        backend = requests.post(
            f'{PUBLIC_SERVER_URL}/finalize_session',
            data={'session_id': session_id},
            headers=HEADERS,
            timeout=120,
        )
        return Response(backend.content, status=backend.status_code, content_type=backend.headers.get('Content-Type', 'application/json'))
    except requests.RequestException as exc:
        return Response(f'Backend request failed: {exc}', status=502)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
