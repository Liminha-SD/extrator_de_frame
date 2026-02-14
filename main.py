# -*- coding: utf-8 -*- 

import os
import sys

try:
    import PySide6
    pyside6_path = PySide6.__path__[0]
    plugins_path = os.path.join(pyside6_path, "Qt", "plugins")
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugins_path
except ImportError:
    print("PySide6 is not installed. Please install it using: pip install PySide6")

try:
    import tensorflow as tf
    from tensorflow.keras.preprocessing import image
    import numpy as np
except ImportError:
    print("TensorFlow is not installed. Please install it using: pip install tensorflow")

import threading
import json
import subprocess
import random
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QMessageBox,
    QSlider, QListWidget, QListWidgetItem, QGridLayout, QStyle, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtSvg import QSvgRenderer

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    else:
        # Get the directory where the main.py file is located
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

# ==============================================================================
# --- Lógica de Extração de Frames (do extrator_frame.py) ---
# ==============================================================================

# Para esconder a janela do console no Windows
if os.name == 'nt':
    _CREATE_NO_WINDOW = 0x08000000
    _startupinfo = subprocess.STARTUPINFO()
    try:
        _startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        _startupinfo.wShowWindow = subprocess.SW_HIDE
    except Exception:
        _startupinfo = None
else:
    _startupinfo = None


def run_process(cmd, **kwargs):
    """Wrapper para subprocess.run que aplica startupinfo e creationflags no Windows.
    Usa o `_startupinfo` já configurado; quando necessário adiciona CREATE_NO_WINDOW como creationflags.
    """
    creationflags = kwargs.pop('creationflags', None)
    if os.name == 'nt':
        # se não foi passado creationflags explicitamente, use CREATE_NO_WINDOW
        if creationflags is None:
            try:
                creationflags = subprocess.CREATE_NO_WINDOW
            except Exception:
                creationflags = 0
    else:
        creationflags = 0

    # passe startupinfo padrão se não fornecido
    if 'startupinfo' not in kwargs and _startupinfo is not None:
        kwargs['startupinfo'] = _startupinfo

    if creationflags:
        kwargs['creationflags'] = creationflags

    return subprocess.run(cmd, **kwargs)

CONFIG_FILE = "config.json"

def salvar_caminho_ffmpeg(path):
    """Salva o caminho da pasta 'bin' do FFmpeg no arquivo de configuração."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"ffmpeg_bin_path": path}, f)
        return True
    except IOError as e:
        print(f"Erro ao salvar o arquivo de configuração: {e}")
        return False

def carregar_caminho_ffmpeg():
    """Carrega o caminho da pasta 'bin' do FFmpeg do arquivo de configuração."""
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config.get("ffmpeg_bin_path")
    except (IOError, json.JSONDecodeError) as e:
        print(f"Erro ao carregar ou decodificar o arquivo de configuração: {e}")
        return None

def encontrar_ffmpeg_tools(caminho_custom=None):
    """Verifica se ffmpeg e ffprobe estão disponíveis e retorna os caminhos absolutos."""
    ferramentas = {"ffmpeg": None, "ffprobe": None}
    nomes = ["ffmpeg", "ffprobe"]
    error_log = []

    # 1. Tenta o caminho customizado (ex: ffmpeg/bin no diretório do projeto)
    if caminho_custom:
        encontrou_todos = True
        for nome in nomes:
            exec_name = f"{nome}.exe" if os.name == 'nt' else nome
            full_path = os.path.join(caminho_custom, exec_name)
            if os.path.exists(full_path):
                ferramentas[nome] = os.path.abspath(full_path)
            else:
                encontrou_todos = False
                error_log.append(f"'{exec_name}' não encontrado em '{caminho_custom}'.")
        
        if encontrou_todos:
            return ferramentas, ""

    # 2. Tenta o caminho salvo no config.json (se não for o mesmo já tentado)
    caminho_config = carregar_caminho_ffmpeg()
    if caminho_config and caminho_config != caminho_custom:
        encontrou_todos = True
        temp_ferramentas = {}
        for nome in nomes:
            exec_name = f"{nome}.exe" if os.name == 'nt' else nome
            full_path = os.path.join(caminho_config, exec_name)
            if os.path.exists(full_path):
                temp_ferramentas[nome] = os.path.abspath(full_path)
            else:
                encontrou_todos = False
        
        if encontrou_todos:
            return temp_ferramentas, ""

    # 3. Tenta no PATH do sistema
    ferramentas_path = {"ffmpeg": None, "ffprobe": None}
    encontrou_no_path = True
    for nome in nomes:
        try:
            # Verifica se responde no PATH
            run_process([nome, '-version'], check=True, capture_output=True)
            ferramentas_path[nome] = nome
        except Exception:
            encontrou_no_path = False
    
    if encontrou_no_path:
        return ferramentas_path, ""

    return ferramentas, "FFmpeg/FFprobe não encontrados."

def get_video_duration(video_path, ffprobe_path='ffprobe', logger_callback=print):
    """Obtém a duração de um vídeo em segundos usando ffprobe."""
    command = [
        ffprobe_path,
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    try:
        result = run_process(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
        return float(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        logger_callback(f"Erro ao obter duração do vídeo com ffprobe: {e.stderr}")
        return None
    except ValueError:
        logger_callback(f"Não foi possível converter a duração para número: {result.stdout.strip()}")
        return None
    except Exception as e:
        logger_callback(f"Erro inesperado ao obter duração do vídeo: {e}")
        return None

def is_frame_good(model, frame_path, logger_callback):
    """Classifica um frame como 'good' ou 'bad' usando um modelo Keras e retorna a confiança."""
    try:
        # Usar tf.keras.utils para garantir consistência com o treinamento
        img = tf.keras.utils.load_img(
            frame_path, target_size=(128, 128)
        )
        img_array = tf.keras.utils.img_to_array(img)
        img_array = tf.expand_dims(img_array, 0) # Cria um lote (batch)

        prediction = model.predict(img_array, verbose=0) # verbose=0 para não poluir o log
        score = prediction[0][0]

        if score > 0.5:
            logger_callback(f"Predição para {os.path.basename(frame_path)}: GOOD ({score:.2f})")
            return True
        else:
            logger_callback(f"Predição para {os.path.basename(frame_path)}: BAD ({score:.2f})")
            return False
            
    except Exception as e:
        logger_callback(f"Erro ao classificar o frame '{os.path.basename(frame_path)}': {e}")
        return False

def extrair_frames_aleatorios(video_path, output_dir, num_frames=1, ffmpeg_path='ffmpeg', ffprobe_path='ffprobe', keras_model_path=None, logger_callback=print, stop_event=None):
    """
    Extrai um número especificado de frames de um vídeo usando uma lógica de passes
    para garantir que todos os frames salvos sejam validados como 'GOOD' por um modelo Keras.
    """
    if not os.path.exists(video_path):
        logger_callback(f"Erro: O arquivo de vídeo '{video_path}' não foi encontrado.")
        return

    # --- Carregamento do Modelo ---
    model = None
    if keras_model_path and os.path.exists(keras_model_path):
        try:
            logger_callback(f"Carregando modelo Keras de: {keras_model_path}")
            model = tf.keras.models.load_model(keras_model_path)
            logger_callback("Modelo Keras carregado com sucesso.")
        except Exception as e:
            logger_callback(f"Erro ao carregar o modelo Keras: {e}")
            logger_callback("A extração não pode continuar sem um modelo válido.")
            return
    elif keras_model_path:
        logger_callback(f"Erro: O arquivo do modelo Keras não foi encontrado em '{keras_model_path}'.")
        return

    # --- Configuração dos Diretórios e Nomes ---
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    new_output_dir = os.path.join(output_dir, video_name)

    if not os.path.exists(new_output_dir):
        logger_callback(f"Criando diretório de saída: {new_output_dir}")
        os.makedirs(new_output_dir)

    video_digits = ''.join(re.findall(r'\d', video_name))[-3:]
    if not video_digits or len(video_digits) < 3:
        logger_callback("Aviso: Não foi possível extrair 3 dígitos do nome do vídeo. Usando '000' como padrão.")
        video_digits = "000"

    # --- Obtenção da Duração do Vídeo ---
    duration = get_video_duration(video_path, ffprobe_path, logger_callback)
    if duration is None:
        logger_callback("Não foi possível determinar a duração do vídeo. Abortando extração.")
        return

    logger_callback(f"Duração do vídeo: {duration:.2f} segundos.")
    logger_callback(f"Iniciando processo para obter {num_frames} frames validados...")

    # --- Loop Principal de Extração e Validação ---
    good_frames_count = 0
    total_attempts = 0
    max_total_attempts = 10000  # Limite de segurança para evitar loops infinitos
    used_timestamps = set()
    extraction_batch_size = 500  # Extrair em lotes de 500

    while good_frames_count < num_frames:
        if stop_event and stop_event.is_set():
            logger_callback("Extração interrompida pelo usuário.")
            break

        if total_attempts >= max_total_attempts:
            logger_callback(f"Atingido o limite máximo de {max_total_attempts} tentativas. Interrompendo.")
            break

        frames_needed = num_frames - good_frames_count
        logger_callback(f"--- Passando: Faltam {frames_needed} frames. Tentando extrair um lote de {extraction_batch_size} ---")

        # --- 1. Extrair Novos Frames ---
        extracted_this_pass = []
        for _ in range(extraction_batch_size):
            if total_attempts >= max_total_attempts:
                break
            
            total_attempts += 1
            random_timestamp = random.uniform(0, duration)
            # Evitar extrair o mesmo frame repetidamente
            while random_timestamp in used_timestamps:
                random_timestamp = random.uniform(0, duration)
            used_timestamps.add(random_timestamp)

            temp_filename = f"temp_{total_attempts}.jpg"
            temp_filepath = os.path.join(new_output_dir, temp_filename)

            command_extraction = [
                ffmpeg_path, '-ss', str(random_timestamp), '-i', video_path,
                '-vframes', '1', '-q:v', '2', '-y', temp_filepath
            ]

            try:
                run_process(command_extraction, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                extracted_this_pass.append(temp_filepath)
            except subprocess.CalledProcessError as e:
                logger_callback(f"Erro ao extrair frame em {random_timestamp:.2f}s. Detalhes: {e.stderr}")
            except Exception as e:
                logger_callback(f"Erro inesperado ao extrair frame: {e}")

        # --- 2. Validar Frames Extraídos Neste Passe ---
        if not extracted_this_pass:
            logger_callback("Nenhum frame foi extraído neste passe. Tentando novamente.")
            continue

        logger_callback(f"Validando {len(extracted_this_pass)} frames extraídos...")
        good_frames_in_pass = []
        for frame_path in extracted_this_pass:
            if model:
                is_good = is_frame_good(model, frame_path, logger_callback)
                if is_good:
                    good_frames_in_pass.append(frame_path)
                else:
                    logger_callback(f"Frame '{os.path.basename(frame_path)}' validado como 'BAD'. Deletando.")
                    try:
                        os.remove(frame_path)
                    except OSError as e:
                        logger_callback(f"Erro ao deletar frame ruim: {e}")
            else:
                # Se não houver modelo, todos os frames são considerados bons
                good_frames_in_pass.append(frame_path)

        # --- 3. Renomear Frames Bons e Atualizar Contagem ---
        logger_callback(f"{len(good_frames_in_pass)} frames validados como 'GOOD' neste passe.")
        for good_frame_path in good_frames_in_pass:
            if good_frames_count < num_frames:
                good_frames_count += 1
                new_filename = f"{video_digits}-{good_frames_count}.jpg"
                final_filepath = os.path.join(new_output_dir, new_filename)
                try:
                    os.rename(good_frame_path, final_filepath)
                    logger_callback(f"Frame salvo como: {new_filename}")
                except OSError as e:
                    logger_callback(f"Erro ao renomear frame bom: {e}")
                    good_frames_count -= 1  # Desfaz o incremento se a renomeação falhar
            else:
                # Meta atingida, deletar os frames bons restantes deste lote
                logger_callback(f"Meta de {num_frames} frames atingida. Descartando frame bom extra: {os.path.basename(good_frame_path)}")
                try:
                    os.remove(good_frame_path)
                except OSError as e:
                    logger_callback(f"Erro ao deletar frame extra: {e}")

    logger_callback(f"""
Processo de extração concluído.
Total de frames bons salvos: {good_frames_count} de {num_frames}.
Salvos em: {os.path.abspath(new_output_dir)}
""")

# ==============================================================================
# --- Interface Gráfica (do gui_pyside.py) ---
# ==============================================================================

DARK_STYLESHEET = """
    QWidget {
        background-color: rgb(46, 46, 46);
        color: rgb(255, 255, 255);
    }
    QLineEdit {
        background-color: rgb(62, 62, 62);
        border: 1px solid rgb(62, 62, 62);
        padding: 5;
        border-radius: 8px;
    }
    QLineEdit:hover {
        border: 1px solid rgb(194, 54, 54);
    }
    QPushButton {
        background-color: rgb(85, 85, 85);
        border: none;
        padding: 5;
        border-radius: 8px;
    }
    QPushButton:hover {
        background-color: rgb(194, 54, 54);
    }
    QPushButton:pressed {
        background-color: rgb(224, 64, 64);
    }
    QTextEdit {
        background-color: rgb(30, 30, 30);
        border: 2px solid transparent;
        border-radius: 8px;
    }
    QTextEdit:hover {
        border: 2px solid rgb(194, 54, 54);
    }
    QLabel {
        background-color: rgb(46, 46, 46);
    }
    QSlider::groove:horizontal {
        border: none;
        background: rgb(255, 255, 255);
        height: 10;
        border-radius: 4;
    }
    QSlider::handle:horizontal {
        background: rgb(194, 54, 54);
        border: none;
        width: 18;
        margin: -2 0;
        border-radius: 4;
    }
    QListWidget {
        background-color: rgb(62, 62, 62);
        border: 2px solid transparent;
        border-radius: 8px;
    }
    QListWidget:hover {
        border: 2px solid rgb(194, 54, 54);
    }
    QScrollBar:vertical {
        border: none;
        background: rgb(46, 46, 46);
        width: 12px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:vertical {
        background: rgb(85, 85, 85);
        min-height: 20px;
        border-radius: 6px;
    }
    QScrollBar::handle:vertical:hover {
        background: rgb(194, 54, 54);
    }
    QScrollBar::handle:vertical:pressed {
        background: rgb(224, 64, 64);
    }
    QScrollBar:horizontal {
        border: none;
        background: rgb(46, 46, 46);
        height: 12px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:horizontal {
        background: rgb(85, 85, 85);
        min-width: 20px;
        border-radius: 6px;
    }
    QScrollBar::handle:horizontal:hover {
        background: rgb(194, 54, 54);
    }
    QScrollBar::handle:horizontal:pressed {
        background: rgb(224, 64, 64);
    }
    QScrollBar::add-line, QScrollBar::sub-line {
        background: none;
        border: none;
    }
    QScrollBar::add-page, QScrollBar::sub-page {
        background: none;
    }
    QPushButton#start_stop_button {
        font-weight: bold;
        color: white;
    }
    QPushButton#start_stop_button[state="start"] {
        background-color: rgb(40, 167, 69);
    }
    QPushButton#start_stop_button[state="start"]:hover {
        background-color: rgb(45, 180, 75);
    }
    QPushButton#start_stop_button[state="stop"] {
        background-color: rgb(220, 53, 69);
    }
    QPushButton#start_stop_button[state="stop"]:hover {
        background-color: rgb(235, 60, 75);
    }

    QCheckBox {
        spacing: 10px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 2px solid rgb(85, 85, 85);
        background-color: transparent;
    }
    QCheckBox::indicator:hover {
        border-color: rgb(194, 54, 54);
    }
    QCheckBox::indicator:checked {
        background-color: rgb(194, 54, 54);
        border-color: rgb(194, 54, 54);
    }
    QCheckBox::indicator:checked:hover {
        background-color: rgb(224, 64, 64);
        border-color: rgb(224, 64, 64);
    }
"""

class Worker(QObject):
    log_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, video_path, output_dir, num_frames, ffmpeg_path, ffprobe_path, keras_model_path, stop_event):
        super().__init__()
        self.video_path = video_path
        self.output_dir = output_dir
        self.num_frames = num_frames
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.keras_model_path = keras_model_path
        self.stop_event = stop_event

    def run(self):
        extrair_frames_aleatorios(
            video_path=self.video_path,
            output_dir=self.output_dir,
            num_frames=self.num_frames,
            ffmpeg_path=self.ffmpeg_path,
            ffprobe_path=self.ffprobe_path,
            keras_model_path=self.keras_model_path,
            logger_callback=self.log_signal.emit,
            stop_event=self.stop_event
        )
        self.finished_signal.emit()

class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Extrator de Frames")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet(DARK_STYLESHEET)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.ffmpeg_path = ""
        self.ffprobe_path = ""
        self.keras_file_path = ""
        self.stop_event = None
        self.worker_thread = None
        self.is_extracting = False
        self.currently_processing_path = None

        # Verificação e carregamento dos ícones
        icon_files = {
            'pending': 'assets/pending.svg',
            'completed': 'assets/check_circle.svg'
        }
        
        for icon_name, icon_path in icon_files.items():
            full_path = resource_path(icon_path)
            if not os.path.exists(full_path):
                print(f"Erro: Arquivo de ícone não encontrado: {full_path}")
            else:
                print(f"Carregando ícone: {full_path}")
        
        self.pending_icon = QIcon(resource_path("assets/pending.svg"))
        self.completed_icon = QIcon(resource_path("assets/check_circle.svg"))
        
        # Verificar se os ícones foram carregados corretamente
        if self.pending_icon.isNull():
            print("Erro: Não foi possível carregar o ícone pending.svg")
        if self.completed_icon.isNull():
            print("Erro: Não foi possível carregar o ícone check_circle.svg")

        self.keras_checkbox = QCheckBox("Carregar modelo Keras") 
        self.create_widgets()
        self.load_paths()
        self.check_ffmpeg_tools_on_startup()

    def toggle_keras_input_visibility(self, checked):
        self.keras_file_widget.setVisible(checked)
        self.save_paths()

    def load_paths(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                self.output_dir_input.setText(config.get("output_dir", ""))
                self.keras_file_input.setText(config.get("keras_file_path", ""))
                self.keras_checkbox.setChecked(config.get("load_keras_model", True))
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save_paths(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}

        config["output_dir"] = self.output_dir_input.text()
        config["keras_file_path"] = self.keras_file_input.text()
        config["load_keras_model"] = self.keras_checkbox.isChecked()

        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)

    def toggle_keras_input_visibility(self, checked):
        self.keras_file_widget.setVisible(checked)
        self.save_paths()

    def create_widgets(self):
        # --- Layout Superior (Fila e Log) ---
        top_layout = QHBoxLayout()

        # Painel do Log (agora à esquerda)
        log_panel = QWidget()
        log_layout = QVBoxLayout(log_panel)
        log_layout.addWidget(QLabel("Log da Extração:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        # Painel da Fila (agora à direita)
        queue_panel = QWidget()
        queue_layout = QVBoxLayout(queue_panel)
        queue_layout.setContentsMargins(0, 0, 0, 0)
        queue_layout.setSpacing(0)
        queue_layout.addWidget(QLabel("Fila de Extração:"))

        # Container para a lista e os botões sobrepostos
        list_container = QWidget()
        grid_layout = QGridLayout(list_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        self.video_list_widget = QListWidget()
        grid_layout.addWidget(self.video_list_widget, 0, 0)

        # Container para os botões
        buttons_container = QWidget()
        buttons_container.setAttribute(Qt.WA_TranslucentBackground)
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 5, 5) # Margem para afastar da borda

        # Botões com ícones
        add_icon = QIcon(resource_path("assets/add.svg"))
        add_videos_btn = QPushButton(add_icon, "")
        add_videos_btn.setObjectName("add_button")
        add_videos_btn.setToolTip("Adicionar vídeos à fila")
        add_videos_btn.clicked.connect(self.add_videos)
        add_videos_btn.setFixedSize(30, 30) # Tamanho compacto

        remove_icon = QIcon(resource_path("assets/close.svg"))
        remove_video_btn = QPushButton(remove_icon, "")
        remove_video_btn.setObjectName("remove_button")
        remove_video_btn.setToolTip("Remover item selecionado")
        remove_video_btn.clicked.connect(self.remove_selected_video)
        remove_video_btn.setFixedSize(30, 30)

        clear_icon = QIcon(resource_path("assets/clear_all.svg"))
        clear_queue_btn = QPushButton(clear_icon, "")
        clear_queue_btn.setObjectName("clear_button")
        clear_queue_btn.setToolTip("Limpar toda a fila")
        clear_queue_btn.clicked.connect(self.clear_queue)
        clear_queue_btn.setFixedSize(30, 30)

        buttons_layout.addWidget(add_videos_btn)
        buttons_layout.addWidget(remove_video_btn)
        buttons_layout.addWidget(clear_queue_btn)
        
        grid_layout.addWidget(buttons_container, 0, 0, Qt.AlignBottom | Qt.AlignRight)
        queue_layout.addWidget(list_container)

        top_layout.addWidget(log_panel, 1)    # 50% da largura
        top_layout.addWidget(queue_panel, 1)  # 50% da largura
        self.layout.addLayout(top_layout)

        # --- Caminho do Arquivo Keras ---
        keras_layout = QVBoxLayout()
        self.keras_checkbox = QCheckBox("Carregar modelo Keras")
        self.keras_checkbox.toggled.connect(self.toggle_keras_input_visibility)
        keras_layout.addWidget(self.keras_checkbox)

        self.keras_file_widget = QWidget()
        keras_file_layout = QHBoxLayout(self.keras_file_widget)
        keras_file_layout.setContentsMargins(0,0,0,0)
        keras_file_layout.addWidget(QLabel("Arquivo Keras:"))
        self.keras_file_input = QLineEdit()
        keras_file_layout.addWidget(self.keras_file_input)
        self.browse_keras_btn = QPushButton("Procurar...")
        self.browse_keras_btn.clicked.connect(self.browse_keras_file)
        keras_file_layout.addWidget(self.browse_keras_btn)
        keras_layout.addWidget(self.keras_file_widget)
        self.layout.addLayout(keras_layout)

        # --- Caminho de Saída ---
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(QLabel("Caminho de Saída:"))
        self.output_dir_input = QLineEdit()
        output_dir_layout.addWidget(self.output_dir_input)
        browse_output_btn = QPushButton("Procurar...")
        browse_output_btn.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(browse_output_btn)
        self.layout.addLayout(output_dir_layout)

        # --- Controles Inferiores (Botão Iniciar/Parar e Slider) ---
        bottom_controls_layout = QHBoxLayout()

        # Botão Iniciar/Parar
        self.start_stop_button = QPushButton("Iniciar Extração")
        self.start_stop_button.setObjectName("start_stop_button")
        self.start_stop_button.setProperty("state", "start")
        self.start_stop_button.clicked.connect(self.toggle_extraction)
        bottom_controls_layout.addWidget(self.start_stop_button)

        # Slider de Frames
        frames_layout = QHBoxLayout()
        frames_layout.addWidget(QLabel("Frames a extrair:"))
        self.num_frames_slider = QSlider(Qt.Horizontal)
        self.num_frames_slider.setRange(1, 500)
        self.num_frames_slider.setValue(500)
        frames_layout.addWidget(self.num_frames_slider)
        self.num_frames_input = QLineEdit("500")
        self.num_frames_input.setFixedWidth(40)
        self.num_frames_slider.valueChanged.connect(lambda v: self.num_frames_input.setText(str(v)))
        self.num_frames_input.editingFinished.connect(self.update_slider_from_input)
        frames_layout.addWidget(self.num_frames_input)
        
        bottom_controls_layout.addLayout(frames_layout)
        self.layout.addLayout(bottom_controls_layout)

        self.toggle_keras_input_visibility(self.keras_checkbox.isChecked())


    def add_videos(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Selecione os arquivos de vídeo", "", "Arquivos de Vídeo (*.mp4 *.avi *.mkv *.mov);;Todos os arquivos (*.*)")
        if paths:
            for path in paths:
                item = QListWidgetItem(self.pending_icon, path)
                self.video_list_widget.addItem(item)

    def remove_selected_video(self):
        for item in self.video_list_widget.selectedItems():
            self.video_list_widget.takeItem(self.video_list_widget.row(item))

    def clear_queue(self):
        self.video_list_widget.clear()

    def browse_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Selecione o diretório de saída")
        if path:
            self.output_dir_input.setText(path)
            self.save_paths()

    def browse_keras_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecione o arquivo Keras", "", "Keras Files (*.h5 *.keras);;All Files (*.*)")
        if path:
            self.keras_file_input.setText(path)
            self.save_paths()

    def log(self, message):
        self.log_text.append(message)

    def find_item_by_text(self, text):
        for i in range(self.video_list_widget.count()):
            item = self.video_list_widget.item(i)
            if item.text() == text:
                return item
        return None

    def update_slider_from_input(self):
        try:
            value = int(self.num_frames_input.text())
            # Clamp the value to the slider's range
            value = max(self.num_frames_slider.minimum(), min(value, self.num_frames_slider.maximum()))
            
            self.num_frames_slider.setValue(value)
            self.num_frames_input.setText(str(value))

        except ValueError:
            # If the input is empty or not a number, reset to the slider's current value
            self.num_frames_input.setText(str(self.num_frames_slider.value()))

    def check_ffmpeg_tools_on_startup(self):
        self.log("Verificando ferramentas FFmpeg...")
        
        # Determine the base directory (where the script or exe is)
        if hasattr(sys, '_MEIPASS'):
            # When running as exe, look next to the exe, not inside the _MEIPASS temp folder
            # unless ffmpeg was bundled inside. But usually it's better to keep it external.
            # If the user wants it next to the .exe:
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        project_bin_path = os.path.join(base_dir, 'ffmpeg', 'bin')
        self.log(f"Procurando FFmpeg local em: {project_bin_path}")
        
        tools, error_msg = encontrar_ffmpeg_tools(caminho_custom=project_bin_path)

        if tools.get("ffmpeg") and tools.get("ffprobe"):
            self.ffmpeg_path = tools["ffmpeg"]
            self.ffprobe_path = tools["ffprobe"]
            self.log(f"FFmpeg encontrado com sucesso: {self.ffmpeg_path}")
            self.log(f"FFprobe encontrado com sucesso: {self.ffprobe_path}")
        else:
            # Se não encontrou no local padrão, tenta no PATH do sistema ou caminho salvo
            self.log("FFmpeg não encontrado no diretório local. Verificando alternativas...")
            tools, error_msg_fallback = encontrar_ffmpeg_tools()
            
            if tools.get("ffmpeg") and tools.get("ffprobe"):
                self.ffmpeg_path = tools["ffmpeg"]
                self.ffprobe_path = tools["ffprobe"]
                self.log(f"FFmpeg carregado: {self.ffmpeg_path}")
            else:
                self.log("Aviso: FFmpeg/FFprobe não encontrados.")
                self.prompt_for_ffmpeg_folder()

    def prompt_for_ffmpeg_folder(self):
        reply = QMessageBox.question(self, "Ferramentas não encontradas", "Deseja apontar para a pasta 'bin' do FFmpeg agora?")
        if reply == QMessageBox.Yes:
            path = QFileDialog.getExistingDirectory(self, "Selecione a pasta 'bin' que contém ffmpeg.exe e ffprobe.exe")
            if path:
                self.log(f"Verificando a pasta selecionada: {path}")
                tools, error_msg = encontrar_ffmpeg_tools(path)
                if tools["ffmpeg"] and tools["ffprobe"]:
                    self.ffmpeg_path = tools["ffmpeg"]
                    self.ffprobe_path = tools["ffprobe"]
                    self.log("Sucesso! Ferramentas FFmpeg configuradas e o caminho foi salvo para futuras execuções.")
                else:
                    QMessageBox.critical(self, "Erro", f"A pasta selecionada é inválida ou as ferramentas não puderam ser executadas.\n\nDetalhes: {error_msg}")
                    self.log("Falha ao verificar a pasta selecionada.")

    def toggle_extraction(self):
        if self.is_extracting:
            self.stop_extraction()
        else:
            self.start_extraction()

    def stop_extraction(self):
        if self.stop_event:
            self.log("Sinal de parada enviado...")
            self.stop_event.set()
            self.start_stop_button.setEnabled(False)
            self.start_stop_button.setText("Parando...")

    def start_extraction(self):
        self.video_queue = [self.video_list_widget.item(i).text() for i in range(self.video_list_widget.count())]
        output_dir = self.output_dir_input.text()

        if not self.video_queue:
            QMessageBox.critical(self, "Erro", "A fila de vídeos está vazia.")
            return
        if not output_dir:
            QMessageBox.critical(self, "Erro", "Por favor, especifique o diretório de saída.")
            return

        keras_model_path = self.keras_file_input.text()
        if keras_model_path and not os.path.exists(keras_model_path):
            QMessageBox.critical(self, "Erro", f"O arquivo do modelo Keras não foi encontrado em: {keras_model_path}")
            return

        if not self.ffmpeg_path or not self.ffprobe_path:
            QMessageBox.critical(self, "Erro", "Caminhos para FFmpeg/FFprobe não definidos.")
            self.prompt_for_ffmpeg_folder()
            return

        self.log_text.clear()

        for i in range(self.video_list_widget.count()):
            self.video_list_widget.item(i).setIcon(self.pending_icon)

        self.is_extracting = True
        self.start_stop_button.setText("Parar Extração")
        self.start_stop_button.setProperty("state", "stop")
        self.style().unpolish(self.start_stop_button)
        self.style().polish(self.start_stop_button)
        
        self.process_next_video()

    def process_next_video(self):
        if not self.video_queue:
            self.on_extraction_finished(is_queue_finished=True)
            return

        self.currently_processing_path = self.video_queue.pop(0)
        video_path = self.currently_processing_path
        self.log(f"--- Iniciando extração para: {video_path} ---")

        self.stop_event = threading.Event()
        self.worker = Worker(
            video_path,
            self.output_dir_input.text(),
            self.num_frames_slider.value(),
            self.ffmpeg_path,
            self.ffprobe_path,
            self.keras_file_input.text(),
            self.stop_event
        )
        self.worker_thread = threading.Thread(target=self.worker.run)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_extraction_finished)
        self.worker_thread.start()

    def on_extraction_finished(self, is_queue_finished=False):
        if self.currently_processing_path:
            # Only set as completed if not stopped by the user
            if not (self.stop_event and self.stop_event.is_set()):
                item = self.find_item_by_text(self.currently_processing_path)
                if item:
                    item.setIcon(self.completed_icon)
            self.currently_processing_path = None

        # Se a parada foi solicitada, a fila não está 'concluída'
        if self.stop_event and self.stop_event.is_set():
             self.log("--- Extração interrompida ---")
             is_queue_finished = True # Força a finalização

        if is_queue_finished:
            self.log("--- Fila de extração concluída ---")
            self.is_extracting = False
            self.start_stop_button.setEnabled(True)
            self.start_stop_button.setText("Iniciar Extração")
            self.start_stop_button.setProperty("state", "start")
            self.style().unpolish(self.start_stop_button)
            self.style().polish(self.start_stop_button)
            self.worker_thread = None
        else:
            self.process_next_video()



if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    # Garantir política de arredondamento de scale factor em alto DPI antes de criar QApplication
    try:
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(QGuiApplication.PassThrough)
    except Exception:
        # fallback: algumas versões podem não expor a enum como PassThrough; ignore se não suportado
        pass

    app = QApplication(sys.argv)

    # Adicionar o caminho para os plugins de imagem, incluindo SVG
    try:
        import PySide6
        pyside6_path = PySide6.__path__[0]
        QApplication.addLibraryPath(os.path.join(pyside6_path, "Qt", "plugins", "iconengines"))
        QApplication.addLibraryPath(os.path.join(pyside6_path, "Qt", "plugins", "imageformats"))
    except ImportError:
        pass

    window = App()
    window.show()
    sys.exit(app.exec())