# python -m venv venv
# pip install pyinstaller
# pyinstaller --onefile --add-data "app/view/index.html;app/view" --add-data "app/view/App.html;app/view" --add-data "app/view/css/reset.css;app/view/css" --add-data "app/view/css/style.css;app/view/css" --add-data "app/view/css/log_style.css;app/view/css" --add-data "app/view/js/script.js;app/view/js" --add-data "app/Arquivos_Armazenados;app/Arquivos_Armazenados" --add-data "app/model/streamlit_app.py;app/model" --add-data "app/model/Side_Consult.py;app/model" --add-data "app/model/Main_Consult.py;app/model" --add-data "app/model/Users.py;app/model" --hidden-import "pandas._libs.tslibs.timedeltas" --hidden-import "pandas._libs.tslibs.timestamps" --hidden-import "pandas._libs.tslibs.np_datetime" --hidden-import "pandas._libs.tslibs.nattype" --hidden-import "pandas._libs.tslibs.timezones" --hidden-import "streamlit" --hidden-import "pywin32" --workpath build --distpath dist --specpath . app/controller/Main.py

import os
import atexit
import signal
import subprocess
import sys
from flask import Flask, render_template, request, jsonify, redirect, url_for

# Verificar o diretório temporário criado pelo PyInstaller
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    template_folder = os.path.join(base_path, 'app/view')
    static_folder = os.path.join(base_path, 'app/view')
    streamlit_app_path = os.path.join(base_path, 'app/model/streamlit_app.py')
    streamlit_side_path = os.path.join(base_path, 'app/model/Side_Consult.py')
else:
    base_path = os.path.dirname(__file__)
    template_folder = os.path.join(base_path, '../view')
    static_folder = os.path.join(base_path, '../view')
    streamlit_app_path = os.path.abspath(os.path.join(base_path, "../model/streamlit_app.py"))
    streamlit_side_path = os.path.abspath(os.path.join(base_path, "../model/Side_Consult.py"))

if not os.path.exists(template_folder):
    print(f"Template folder not found: {template_folder}")
else:
    print(f"Template folder found: {template_folder}")

if not os.path.exists(os.path.join(template_folder, 'index.html')):
    print("index.html not found in template folder")
else:
    print("index.html found in template folder")

if not os.path.exists(streamlit_app_path):
    print(f"Streamlit app path not found: {streamlit_app_path}")
else:
    print(f"Streamlit app path found: {streamlit_app_path}")

if not os.path.exists(streamlit_side_path):
    print(f"Streamlit side path not found: {streamlit_side_path}")
else:
    print(f"Streamlit side path found: {streamlit_side_path}")

app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '0'  # Deactivate-auto-debug

# Global Vars para armazenar dados dos arquivos e seus nomes
veiculo_data = None
abastecimento_data = None
veiculo_filename = None
abastecimento_filename = None
streamlit_processes = []  # Lista para armazenar processos do Streamlit

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        users = {"Jose Mario": "1234", "Saulo": "5678", "Gesse": "9123"}

        if usuario in users and users[usuario] == senha:
            return redirect(url_for('app_page'))
        else:
            return 'Credenciais inválidas!'
    return render_template('index.html')

@app.route('/app', methods=['GET', 'POST'])
def app_page():
    return render_template('App.html')

@app.route('/process_files', methods=['POST'])
def process_files():
    if 'veiculoFile' not in request.files or 'abastecimentoFile' not in request.files:
        return jsonify({'error': 'Ambos os arquivos são necessários'})
    veiculo_file = request.files['veiculoFile']
    abastecimento_file = request.files['abastecimentoFile']

    global veiculo_data, abastecimento_data, veiculo_filename, abastecimento_filename
    veiculo_data = veiculo_file.read()
    abastecimento_data = abastecimento_file.read()
    veiculo_filename = veiculo_file.filename
    abastecimento_filename = abastecimento_file.filename

    stored_folder = "app/Arquivos_Armazenados"
    os.makedirs(stored_folder, exist_ok=True)

    with open(os.path.join(stored_folder, "veiculo_data.bin"), "wb") as f:
        f.write(veiculo_data)
    with open(os.path.join(stored_folder, "abastecimento_data.bin"), "wb") as f:
        f.write(abastecimento_data)
    return jsonify({'result': 'Arquivos importados com sucesso', 'veiculo_filename': veiculo_filename, 'abastecimento_filename': abastecimento_filename})

@app.route('/main_consult', methods=['GET'])
def main_consult():
    return redirect("http://localhost:8501/main")

@app.route('/side_consult', methods=['GET'])
def side_consult():
    return redirect("http://localhost:8502")

@app.route('/start_streamlit')
def start_streamlit():
    stored_folder = "app/Arquivos_Armazenados"
    streamlit_control_path = os.path.join(stored_folder, "streamlit_control")
    with open(streamlit_control_path, "w") as f:
        f.write("control")

    if request.args.get('consult_type') == 'main':
        process = subprocess.Popen(["streamlit", "run", streamlit_app_path, "--server.port", "8501"])
    else:
        process = subprocess.Popen(["streamlit", "run", streamlit_side_path, "--server.port", "8502"])
    # Adiciona processo à lista de processos
    streamlit_processes.append(process)
    return "Streamlit iniciado. Por favor, acesse a análise na nova aba do navegador."

@app.route('/clean_and_shutdown', methods=['POST'])
def clean_and_shutdown():
    global streamlit_processes
    stored_folder = "app/Arquivos_Armazenados"
    # Limpar os arquivos armazenados
    for filename in os.listdir(stored_folder):
        file_path = os.path.join(stored_folder, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Erro ao deletar {file_path}: {e}")
    # Finalizar todos os processos do Streamlit
    for process in streamlit_processes:
        process.terminate()
    streamlit_processes = []  # Limpar a lista de processos
    shutdown_server()
    return "Aplicação fechada e arquivos limpos."

def shutdown_server():
    os.kill(os.getpid(), signal.SIGINT)
# Registrar função de limpeza no 'atexit'
atexit.register(shutdown_server)

if __name__ == '__main__':
    app.run(debug=False, port=5001)