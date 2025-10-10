# -*- coding: utf-8 -*- 

"""
Este arquivo combina a lógica de extração de frames (originalmente em extrator_frame.py)
com a interface gráfica do usuário (originalmente em gui_pyside.py).
"""

import sys
import threading
import os
import json
import subprocess
import random
import re
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, QMessageBox,
    QSlider, QListWidget, QListWidgetItem, QGridLayout, QStyle
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QGuiApplication, QIcon

# ==============================================================================
# --- Lógica de Extração de Frames (do extrator_frame.py) ---
# ==============================================================================

# Para esconder a janela do console no Windows
if os.name == 'nt':
    _CREATE_NO_WINDOW = 0x08000000
    _startupinfo = subprocess.STARTUPINFO()
    _startupinfo.dwFlags |= _CREATE_NO_WINDOW
else:
    _startupinfo = None

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
    """Verifica se ffmpeg e ffprobe estão disponíveis e retorna o erro se não estiverem."""
    ferramentas = {"ffmpeg": None, "ffprobe": None}
    nomes = ["ffmpeg", "ffprobe"]
    error_log = []

    caminho_a_verificar = caminho_custom

    if not caminho_a_verificar:
        caminho_a_verificar = carregar_caminho_ffmpeg()

    if caminho_a_verificar:
        for nome in nomes:
            try:
                exec_name = f"{nome}.exe" if os.name == 'nt' and not nome.endswith('.exe') else nome
                full_path = os.path.join(caminho_a_verificar, exec_name)
                if os.path.exists(full_path):
                    subprocess.run([full_path, '-version'], check=True, capture_output=True, startupinfo=_startupinfo)
                    ferramentas[nome] = full_path
                else:
                    error_log.append(f"'{exec_name}' não encontrado em '{caminho_a_verificar}'.")
            except (subprocess.CalledProcessError, FileNotFoundError, PermissionError) as e:
                error_log.append(f"Erro ao verificar '{nome}' em '{caminho_a_verificar}': {e}")
        
        if ferramentas["ffmpeg"] and ferramentas["ffprobe"] and caminho_custom:
            salvar_caminho_ffmpeg(caminho_custom)
        
        if ferramentas["ffmpeg"] and ferramentas["ffprobe"]:
            return ferramentas, "".join(error_log)

    if not (ferramentas["ffmpeg"] and ferramentas["ffprobe"]):
        for nome in nomes:
            if not ferramentas[nome]:
                try:
                    subprocess.run([nome, '-version'], check=True, capture_output=True, startupinfo=_startupinfo)
                    ferramentas[nome] = nome
                except (subprocess.CalledProcessError, FileNotFoundError, PermissionError) as e:
                    error_log.append(f"'{nome}' não encontrado ou com erro no PATH do sistema: {e}")

    return ferramentas, "".join(error_log)

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
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', startupinfo=_startupinfo)
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

def extrair_frames_aleatorios(video_path, output_dir, num_frames=1, ffmpeg_path='ffmpeg', ffprobe_path='ffprobe', logger_callback=print, stop_event=None):
    """
    Extrai um número especificado de frames aleatórios de um vídeo.
    """
    if not os.path.exists(video_path):
        logger_callback(f"Erro: O arquivo de vídeo '{video_path}' não foi encontrado.")
        return

    video_name = os.path.splitext(os.path.basename(video_path))[0]
    new_output_dir = os.path.join(output_dir, video_name)

    if not os.path.exists(new_output_dir):
        logger_callback(f"Criando diretório de saída: {new_output_dir}")
        os.makedirs(new_output_dir)

    video_digits = ''.join(re.findall(r'\d', video_name))[-3:]
    if not video_digits or len(video_digits) < 3:
        logger_callback("Aviso: Não foi possível extrair 3 dígitos do nome do vídeo. Usando '000' como padrão.")
        video_digits = "000"

    duration = get_video_duration(video_path, ffprobe_path, logger_callback)
    if duration is None:
        logger_callback("Não foi possível determinar a duração do vídeo. Abortando extração aleatória.")
        return

    logger_callback(f"Duração do vídeo: {duration:.2f} segundos.")
    logger_callback(f"Extraindo {num_frames} frames aleatórios...")

    extracted_count = 0
    for i in range(num_frames):
        if stop_event and stop_event.is_set():
            logger_callback("Extração interrompida pelo usuário.")
            break
        
        random_timestamp = random.uniform(0, duration)
        
        output_filename = f"{video_digits}-{i+1}.jpg"
        output_filepath = os.path.join(new_output_dir, output_filename)

        command_extraction = [
            ffmpeg_path,
            '-ss', str(random_timestamp),
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',
            '-y',
            output_filepath
        ]

        try:
            logger_callback(f"Extraindo frame aleatório em {random_timestamp:.2f}s para '{output_filepath}'")
            subprocess.run(command_extraction, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', startupinfo=_startupinfo)
            extracted_count += 1
        except subprocess.CalledProcessError as e:
            logger_callback(f"""
Ocorreu um erro ao extrair frame em {random_timestamp:.2f}s.""")
            logger_callback(f"Comando: {' '.join(e.cmd)}")
            if e.stdout:
                logger_callback(f"""--- Saída (stdout) ---
{e.stdout}""")
            if e.stderr:
                logger_callback(f"""--- Erro (stderr) ---
{e.stderr}""")
            else:
                logger_callback("Nenhuma saída de erro específica foi capturada (stderr estava vazio).")
        except Exception as e:
            logger_callback(f"Ocorreu um erro inesperado ao extrair frame: {e}")

    logger_callback(f"""
Extração aleatória concluída. {extracted_count} de {num_frames} frames salvos em: {os.path.abspath(new_output_dir)}   """)

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

"""

class Worker(QObject):
    log_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, video_path, output_dir, num_frames, ffmpeg_path, ffprobe_path, stop_event):
        super().__init__()
        self.video_path = video_path
        self.output_dir = output_dir
        self.num_frames = num_frames
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.stop_event = stop_event

    def run(self):
        extrair_frames_aleatorios(
            video_path=self.video_path,
            output_dir=self.output_dir,
            num_frames=self.num_frames,
            ffmpeg_path=self.ffmpeg_path,
            ffprobe_path=self.ffprobe_path,
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
        self.stop_event = None
        self.worker_thread = None
        self.is_extracting = False
        self.currently_processing_path = None

        self.pending_icon = QIcon("pending.svg")
        self.completed_icon = QIcon("check_circle.svg")

        self.create_widgets()
        self.load_paths()
        self.check_ffmpeg_tools_on_startup()

    def load_paths(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                self.output_dir_input.setText(config.get("output_dir", ""))
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save_paths(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}

        config["output_dir"] = self.output_dir_input.text()

        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)

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
        add_icon = QIcon("add.svg")
        add_videos_btn = QPushButton(add_icon, "")
        add_videos_btn.setObjectName("add_button")
        add_videos_btn.setToolTip("Adicionar vídeos à fila")
        add_videos_btn.clicked.connect(self.add_videos)
        add_videos_btn.setFixedSize(30, 30) # Tamanho compacto

        remove_icon = QIcon("close.svg")
        remove_video_btn = QPushButton(remove_icon, "")
        remove_video_btn.setObjectName("remove_button")
        remove_video_btn.setToolTip("Remover item selecionado")
        remove_video_btn.clicked.connect(self.remove_selected_video)
        remove_video_btn.setFixedSize(30, 30)

        clear_icon = QIcon("clear_all.svg")
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
        tools, error_msg = encontrar_ffmpeg_tools()
        if tools["ffmpeg"] and tools["ffprobe"]:
            self.ffmpeg_path = tools["ffmpeg"]
            self.ffprobe_path = tools["ffprobe"]
            ffmpeg_dir = os.path.dirname(tools["ffmpeg"])
            if ffmpeg_dir == "":
                self.log("FFmpeg e FFprobe encontrados no PATH do sistema.")
            else:
                self.log(f"FFmpeg e FFprobe carregados do caminho salvo: {ffmpeg_dir}")
        else:
            self.log("Aviso: FFmpeg/FFprobe não encontrados ou o caminho salvo é inválido.")
            if error_msg:
                self.log(f"Detalhes: {error_msg}")
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
    window = App()
    window.show()
    sys.exit(app.exec())