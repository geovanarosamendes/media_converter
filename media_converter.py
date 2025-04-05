from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask import send_file
import os
import uuid
import tempfile
import yt_dlp


app = Flask("APIConverter")
CORS(app, resources={r"/*": {"origins": "*"}})


DOWNLOAD_DIR = tempfile.gettempdir()
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/')
def home():
    return "A API de conversão de Youtube para mp3/mp4 está no ar!"


def progresso(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0%')
        speed = d.get('speed_str', 'Calculando...')
        eta = d.get('_eta_str', '...')
        print(f"Em progresso: {percent} - Velocidade: {speed} - Tempo restante: {eta}")
    elif d['status'] == 'finished':
        print("Ge: Prontinho! Agora vamos converter...")

@app.route('/download', methods=['POST'])
def download_video():
    dados = request.get_json()
    url = dados.get('url')
    formato = dados.get('format')

    if not url or not formato:
        return jsonify({'erro': 'A URL e o formato (mp3 ou mp4) são obrigatórios.'}), 400

    if formato not in ['mp3', 'mp4']:
        return jsonify({'erro': 'Formato inválido! Use apenas mp3 ou mp4.'}), 400

    playlist = 'list=' in url

    if playlist and formato != 'mp3':
        return jsonify({'erro': 'Só é permitido baixar playlist no formato MP3.'}), 400

    try:
        arquivos_baixados = []

        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            infos = ydl.extract_info(url, download=False)

        titulo = infos['title'].strip().replace('/', '_')
        nome_arquivo = f"{titulo}_{uuid.uuid4().hex[:8]}.{formato}"
        caminho_arquivo = os.path.join(DOWNLOAD_DIR, nome_arquivo)


        ydl_opts = {
            'outtmpl': caminho_arquivo,
            'ignoreerrors': True,
            'no_warnings': True,
            'progress_hooks': [progresso]
        }

        if formato == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192'
                }]
            })
        elif formato == 'mp4':
            ydl_opts.update({'format': 'best'})


        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            infos = ydl.extract_info(url, download=True)


        arquivos_baixados.append(nome_arquivo)

        return jsonify({
            'mensagem': f"Olá! O arquivo foi convertido com sucesso ✨",
            'arquivo': nome_arquivo,
            'download_url': f"/download-file/{nome_arquivo}"
        })

    except Exception as erro:
        return jsonify({'erro': str(erro)}), 500


@app.route('/download-file/<nome_arquivo>')
def baixar_arquivo(nome_arquivo):
    file_path = os.path.join(DOWNLOAD_DIR, nome_arquivo)

    if os.path.exists(file_path):
        return jsonify({'erro': 'Arquivo não encontrado.'}), 404

    response = send_file(file_path, as_attachment=True)

    @response.call_on_close
    def apagar():
        if os.path.exists(file_path):
            os.remove(file_path)

    return response

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
