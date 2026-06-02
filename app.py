from flask import Flask, render_template, request, jsonify
import os
import subprocess
from rembg import remove

app = Flask(__name__)

# Konfigurasi Folder
UPLOAD_FOLDER = 'static/uploads'
RESULT_FOLDER = 'static/results'

# Pastikan folder ada
for folder in [UPLOAD_FOLDER, RESULT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# ---> TAMBAHAN 1: Buat route untuk menampilkan file HTML <---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_image():
    file = request.files.get('image')
    selected_filter = request.form.get('filter', 'normal') 
    selected_bg = request.form.get('background', 'original') # Default ke original

    input_path = os.path.join(UPLOAD_FOLDER, 'raw.png')
    no_bg_path = os.path.join(UPLOAD_FOLDER, 'no_bg.png')
    final_path = os.path.join(RESULT_FOLDER, 'final_output.jpg')
    
    file.save(input_path)

    # --- JIKA USER MEMILIH BACKGROUND ORIGINAL (TIDAK DIHAPUS) ---
    if selected_bg == 'original':
        # Tentukan efek filter untuk satu gambar saja (-vf)
        vf_filter = "null" # Default normal
        
        if selected_filter == 'sepia':
            vf_filter = "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131"
        elif selected_filter == 'bw':
            vf_filter = "format=gray"
        elif selected_filter == 'bright':
            vf_filter = "eq=brightness=0.05:contrast=1.2:saturation=1.2"
        elif selected_filter == 'warm':
            vf_filter = "curves=r='0/0 0.5/0.6 1/1':b='0/0 0.5/0.4 1/1'"

        command = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-vf', vf_filter,
            final_path
        ]
        subprocess.run(command)

    # --- JIKA USER MEMILIH GANTI BACKGROUND ---
    # --- JIKA USER MEMILIH GANTI BACKGROUND ---
    else:
        # 1. Jalankan AI Rembg
        with open(input_path, 'rb') as i:
            input_data = i.read()
            output_data = remove(input_data)
            with open(no_bg_path, 'wb') as o:
                o.write(output_data)

        bg_path = os.path.join('static/backgrounds', selected_bg)

        # 2. Tentukan efek filter untuk layer foreground [1:v]
        filter_chain = "[1:v]null[filtered]"
        
        if selected_filter == 'sepia':
            filter_chain = "[1:v]colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131[filtered]"
        elif selected_filter == 'bw':
            filter_chain = "[1:v]format=gray[filtered]"
        elif selected_filter == 'bright':
            filter_chain = "[1:v]eq=brightness=0.05:contrast=1.2:saturation=1.2[filtered]"
        elif selected_filter == 'warm':
            filter_chain = "[1:v]curves=r='0/0 0.5/0.6 1/1':b='0/0 0.5/0.4 1/1'[filtered]"

        # 3. Gabungkan: scale2ref memaksa background [0:v] mengikuti ukuran foreground [filtered]
        # Kemudian digabung dengan overlay=0:0 karena ukurannya sudah sama persis
        ffmpeg_filters = f"{filter_chain};[0:v][filtered]scale2ref[bg][fg];[bg][fg]overlay=0:0"

        command = [
            'ffmpeg', '-y',
            '-i', bg_path,
            '-i', no_bg_path,
            '-filter_complex', ffmpeg_filters,
            final_path
        ]
        subprocess.run(command)

    return jsonify({"result_url": final_path})
    
    subprocess.run(command)

    return jsonify({"result_url": final_path})

# ---> TAMBAHAN 2: Perintah untuk menyalakan server <---
if __name__ == '__main__':
    # debug=True membuat server otomatis restart kalau ada perubahan kode
    app.run(debug=True, port=5000)