from flask import Flask, request, jsonify, send_from_directory
import os
import yt_dlp

app = Flask("APIConverter")

# Pasta onde os arquivos convertidos serão salvos
DOWNLOAD_DIR = os.path.join(os.getcwd(), 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/')
def home():
    return "🎧 A API de conversão de Youtube para mp3/mp4 está no ar!"


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

    try:
        arquivos_baixados = []

        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            infos = ydl.extract_info(url, download=False)

        titulo = infos['title'].strip().replace('/', '_')
        nome_arquivo = f"{titulo}.{formato}"
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
    try:
        return send_from_directory(DOWNLOAD_DIR, nome_arquivo, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'erro': 'Arquivo não encontrado.'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
