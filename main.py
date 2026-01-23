"""
Sistema de Controle de Tribuna Parlamentar
Interface Desktop Principal - Painel do Presidente
Desenvolvido com PyQt6
"""

import sys
import json
import os
from typing import Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QLineEdit,
    QSpinBox, QGroupBox, QGridLayout, QMessageBox, QComboBox,
    QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QFont, QIcon, QPalette, QColor, QPixmap

from arduino_controller import ArduinoController
from admin_vereadores import VereadoresAdminDialog
from tela_plenario import TelaPlenario
import urllib.request
import urllib.error
import threading
import server
import multiprocessing

def api_post(endpoint, data):
    """Envia comando HTTP POST para o servidor Flask em background"""
    def run():
        try:
            url = f"http://127.0.0.1:5000/api/action/{endpoint}"
            req = urllib.request.Request(url)
            req.add_header('Content-Type', 'application/json')
            jsondata = json.dumps(data).encode('utf-8')
            req.add_header('Content-Length', len(jsondata))
            with urllib.request.urlopen(req, jsondata, timeout=1) as response:
                pass # Sucesso
        except Exception as e:
            # Silencioso em caso de erro de conexão (server offline)
            # print(f"Erro API ({endpoint}): {e}")
            pass
    
    threading.Thread(target=run, daemon=True).start()



class ArduinoConnectionThread(QThread):
    """Thread para conectar ao Arduino sem travar a GUI"""
    finished = Signal(bool)
    
    def __init__(self, arduino_controller):
        super().__init__()
        self.arduino = arduino_controller
        
    def run(self):
        connected = self.arduino.connect()
        self.finished.emit(connected)

class PainelPresidente(QMainWindow):
    """Janela principal do Painel do Presidente"""
    
    def __init__(self):
        super().__init__()
        
        # Estado do sistema
        self.vereadores = []
        self.selected_vereador = None
        self.total_seconds = 0
        self.remaining_seconds = 0
        self.staged_seconds = 0 # Tempo preparado para o próximo ato (aparte)
        self.saved_main_seconds = 0 # Tempo salvo de quem sofreu aparte
        self.aparte_initial_seconds = 0 # Tempo inicial do aparte (para calculo de uso)
        self.is_running = False
        self.is_paused = False
        
        # Estado Aparte
        self.is_active_aparte = False
        self.live_vereador = None  # Quem está realmente falando (na tela)
        self.main_speaker = None   # Orador principal (se houver aparte)
        self.aparte_speaker = None # Quem pediu aparte
        
        # Controladores
        self.arduino = ArduinoController()
        self.arduino.on_connection_change = self.on_arduino_connection_change
        
        self.websocket_thread = None
        
        # Tela do Plenário (Monitor 2)
        self.tela_plenario = None
        
        # Dialog de administração
        self.admin_dialog = None
        
        # Timer Qt
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        
        # Configurar UI primeiro
        self.init_ui()
        

    
    # Agendar inicialização pesada para depois que a janela aparecer
        print("DEBUG: Agendando inicialização...")
        QTimer.singleShot(100, self.delayed_init)
    
    def delayed_init(self):
        """Inicialização atrasada para evitar travamento da UI"""
        print("DEBUG: Executando delayed_init...")
        
        # Carregar dados
        self.load_vereadores()
        
        # Iniciar conexão com Arduino em Thread separada
        print("DEBUG: Iniciando thread de conexão Arduino...")
        self.arduino_worker = ArduinoConnectionThread(self.arduino)
        self.arduino_worker.finished.connect(self.on_arduino_connection_finished)
        self.arduino_worker.start()
        
        # Iniciar servidor WebSocket (apenas atualização de status visual)
        self.start_websocket()

        # Abrir Tela do Plenário automaticamente (agora, em paralelo)
        print("DEBUG: Abrindo tela do plenário...")
        self.open_tela_plenario()
        print("DEBUG: Inicialização completa!")

    def on_arduino_connection_finished(self, connected):
        """Chamado quando a thread de conexão do Arduino termina"""
        print(f"DEBUG: Conexão Arduino finalizada. Conectado: {connected}")




    
    def init_ui(self):
        """Inicializar interface do usuário"""
        self.setWindowTitle("Painel do Presidente - Controle de Tribuna")
        self.setMinimumSize(1400, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Coluna esquerda - Cronômetro e Controles
        left_column = self.create_timer_section()
        main_layout.addWidget(left_column, 2)
        
        # Coluna direita - Vereadores
        right_column = self.create_vereadores_section()
        main_layout.addWidget(right_column, 3)
        
        # Aplicar estilo
        self.apply_styles()
        
        # Abrir em fullscreen
        self.showFullScreen()
    
    def create_timer_section(self):
        """Criar seção do cronômetro"""
        group = QGroupBox("Cronômetro")
        group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ocupar todo espaço
        layout = QVBoxLayout()
        layout.setSpacing(20) # Mais espaçamento
        
        # Display do timer
        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("""
            QLabel {
                font-size: 120px;
                font-weight: bold;
                color: #4facfe;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(102, 126, 234, 0.1),
                    stop:1 rgba(118, 75, 162, 0.1));
                border-radius: 15px;
                padding: 20px;
            }
        """)
        layout.addWidget(self.timer_label, 2) # Peso 2 para crescer
        
        # Status
        self.status_label = QLabel("⏸️ Aguardando")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #ffffff;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Controles Principais (Gigantes)
        controls_layout = QVBoxLayout() # Mudado para vertical para botões grandes empilhados ou Grid
        controls_layout.setSpacing(15)
        
        # INICIAR
        self.play_btn = QPushButton("▶️ INICIAR")
        self.play_btn.clicked.connect(self.start_timer)
        self.play_btn.setMinimumHeight(80)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #11998e, stop:1 #38ef7d);
                color: white;
                font-size: 24px;
                font-weight: 900;
                border: none;
                border-radius: 15px;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0f877d, stop:1 #32d670);
                margin-top: 2px;
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.1);
                color: #555;
            }
        """)
        controls_layout.addWidget(self.play_btn)
        
        # AJUSTE DE TEMPO (Adicionar/Remover usando o tempo selecionado)
        adjust_time_layout = QHBoxLayout()
        
        # Botão (-)
        self.btn_sub_time = QPushButton("-")
        self.btn_sub_time.setMinimumHeight(60)
        self.btn_sub_time.clicked.connect(self.sub_time)
        self.btn_sub_time.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sub_time.setStyleSheet("""
            QPushButton {
                background: #c0392b;
                color: white;
                font-size: 32px;
                font-weight: bold;
                border-radius: 12px;
            }
            QPushButton:hover { background: #e74c3c; }
        """)
        adjust_time_layout.addWidget(self.btn_sub_time)

        # Botão (+)
        self.btn_add_time = QPushButton("+")
        self.btn_add_time.setMinimumHeight(60)
        self.btn_add_time.clicked.connect(self.add_time)
        self.btn_add_time.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_time.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                font-size: 32px;
                font-weight: bold;
                border-radius: 12px;
            }
            QPushButton:hover { background: #2ecc71; }
        """)
        adjust_time_layout.addWidget(self.btn_add_time)
        
        controls_layout.addLayout(adjust_time_layout)
        
        # Botões Pausar e Parar lado a lado
        sub_controls = QHBoxLayout()
        sub_controls.setSpacing(15)
        
        # PAUSAR
        self.pause_btn = QPushButton("⏸️ PAUSAR")
        self.pause_btn.clicked.connect(self.pause_timer)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setMinimumHeight(70)
        self.pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f2994a, stop:1 #f2c94c);
                color: white;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e08e43, stop:1 #e0ba45);
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.1);
                color: #555;
            }
        """)
        sub_controls.addWidget(self.pause_btn)
        
        # PARAR
        self.stop_btn = QPushButton("⏹️ PARAR")
        self.stop_btn.clicked.connect(self.stop_timer)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(70)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #cb2d3e, stop:1 #ef473a);
                color: white;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #b52837, stop:1 #d64034);
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.1);
                color: #555;
            }
        """)
        sub_controls.addWidget(self.stop_btn)
        
        controls_layout.addLayout(sub_controls)
        
        # Botão de Aparte (Movido para cá)
        self.btn_aparte = QPushButton("🗣️ CONCEDER APARTE")
        self.btn_aparte.clicked.connect(self.toggle_aparte)
        self.btn_aparte.setMinimumHeight(60)
        self.btn_aparte.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e67e22, stop:1 #f39c12);
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 8px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d35400, stop:1 #e67e22);
            }
            QPushButton:checked {
                 background: #c0392b;
                 border: 2px solid #e74c3c;
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.05);
                color: #666;
            }
        """)
        self.btn_aparte.setCheckable(True)
        self.btn_aparte.setEnabled(False) # Habilitado apenas ao selecionar orador
        controls_layout.addWidget(self.btn_aparte)
        
        layout.addLayout(controls_layout)
        
        layout.addSpacing(20)
        
        # Tempos pré-definidos (Grid menor)
        presets_group = QGroupBox("Definir Tempo")
        presets_layout = QGridLayout()
        presets_layout.setSpacing(10)
        
        presets = [
            ("1 min", 60), ("3 min", 180), ("5 min", 300),
            ("10 min", 600), ("15 min", 900), ("20 min", 1200)
        ]
        
        for i, (label, seconds) in enumerate(presets):
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, s=seconds: self.set_time(s))
            btn.setMinimumHeight(50)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    font-size: 16px;
                }
                QPushButton:hover {
                    background: rgba(102, 126, 234, 0.3);
                    border-color: #667eea;
                }
            """)
            presets_layout.addWidget(btn, i // 3, i % 3)
            
        presets_group.setLayout(presets_layout)
        layout.addWidget(presets_group)
        
        # Botão Admin no final
        layout.addStretch()
        self.btn_admin = QPushButton("⚙️ ADMINISTRAR VEREADORES")
        self.btn_admin.clicked.connect(self.open_admin)
        self.btn_admin.setMinimumHeight(60)
        self.btn_admin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_admin.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #764ba2, stop:1 #667eea);
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
            }
        """)
        layout.addWidget(self.btn_admin)
        
        layout.addStretch()
        group.setLayout(layout)
        return group
    
    def create_vereadores_section(self):
        """Criar seção de vereadores"""
        group = QGroupBox("👥 Vereadores")
        layout = QVBoxLayout()
        
        # Busca
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 Buscar:")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nome ou partido...")
        self.search_input.textChanged.connect(self.filter_vereadores)
        self.search_input.setMinimumHeight(35)
        search_layout.addWidget(self.search_input)
        
        layout.addLayout(search_layout)
        
        # Lista de vereadores (Visualização em Cards)
        self.vereadores_list = QListWidget()
        self.vereadores_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.vereadores_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.vereadores_list.setMovement(QListWidget.Movement.Static)
        self.vereadores_list.setSpacing(15)
        self.vereadores_list.setIconSize(QPixmap(100, 100).size())
        self.vereadores_list.itemClicked.connect(self.select_vereador)
        
        # Estilo específico para Cards
        self.vereadores_list.setStyleSheet("""
            QListWidget {
                background: rgba(255, 255, 255, 0.05);
                border: none;
                outline: none;
            }
            QListWidget::item {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 10px;
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QListWidget::item:hover {
                background: rgba(102, 126, 234, 0.3);
                border-color: #667eea;
                transform: scale(1.05);
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border: 2px solid #00f2fe;
            }
        """)
        layout.addWidget(self.vereadores_list)
        
        # Orador atual
        current_group = QGroupBox("🎤 Orador Atual")
        current_layout = QVBoxLayout()
        
        # Foto do orador atual
        self.current_speaker_photo = QLabel()
        self.current_speaker_photo.setFixedSize(120, 120)
        self.current_speaker_photo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_speaker_photo.setStyleSheet("""
            QLabel {
                border: 3px solid rgba(102, 126, 234, 0.5);
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        self.current_speaker_photo.setText("👤")
        current_layout.addWidget(self.current_speaker_photo, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.current_speaker_label = QLabel("Nenhum vereador selecionado")
        self.current_speaker_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_speaker_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(102, 126, 234, 0.2),
                    stop:1 rgba(118, 75, 162, 0.2));
                border-radius: 10px;
                padding: 20px;
                margin: 10px;
            }
        """)
        current_layout.addWidget(self.current_speaker_label)
        
        current_group.setLayout(current_layout)
        layout.addWidget(current_group)
        
        group.setLayout(layout)
        return group
    
    def apply_styles(self):
        """Aplicar estilos globais"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f0f23, stop:1 #1a1a2e);
            }
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                background: rgba(255, 255, 255, 0.05);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(102, 126, 234, 0.3);
                border-color: #667eea;
            }
            QPushButton:pressed {
                background: rgba(102, 126, 234, 0.5);
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.05);
                color: #666;
            }
            QLineEdit, QSpinBox {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border-color: #667eea;
            }
            QListWidget {
                background: rgba(255, 255, 255, 0.05);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 6px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background: rgba(102, 126, 234, 0.2);
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
            }
        """)
    
    def load_vereadores(self):
        """Carregar vereadores do JSON"""
        try:
            # Carregar configuração da sessão para saber qual lista usar
            from session_config import SessionConfig
            session_config = SessionConfig()
            active_list = session_config.get_active_list()
            
            json_path = os.path.join(os.path.dirname(__file__), active_list)
            
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    self.vereadores = json.load(f)
            else:
                self.vereadores = []
            
            self.populate_vereadores_list()
        except Exception as e:
            print(f"Erro ao carregar vereadores: {e}")
            self.vereadores = []
            self.populate_vereadores_list()
    
    def populate_vereadores_list(self, filter_text=''):
        """Preencher lista de vereadores"""
        self.vereadores_list.clear()
        
        for vereador in self.vereadores:
            nome = vereador['nome']
            partido = vereador['partido']
            
            if filter_text.lower() in nome.lower() or filter_text.lower() in partido.lower():
                # Texto formatado para o card
                item_text = f"{nome}\n{partido}"
                item = QListWidgetItem(item_text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setData(Qt.ItemDataRole.UserRole, vereador)
                
                # Adicionar foto como ícone
                if vereador.get('foto'):
                    foto_path = os.path.join(os.path.dirname(__file__), vereador['foto'])
                    if os.path.exists(foto_path):
                        pixmap = QPixmap(foto_path)
                        # Escalar imagem mantendo aspecto e cobrindo quadrado
                        scaled = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                        
                        # Recortar quadrado central
                        rect = scaled.rect()
                        size = min(rect.width(), rect.height())
                        cropped = scaled.copy(
                            (rect.width() - size) // 2,
                            (rect.height() - size) // 2,
                            size, size
                        )
                        
                        icon = QIcon(cropped)
                        item.setIcon(icon)
                    else:
                        item.setIcon(QIcon()) # Ícone vazio se arquivo não existir
                else:
                    item.setIcon(QIcon()) # Sem foto
                
                # Definir tamanho do card
                item.setSizeHint(QPixmap(140, 160).size())
                
                self.vereadores_list.addItem(item)
    
    def filter_vereadores(self):
        """Filtrar vereadores"""
        filter_text = self.search_input.text()
        self.populate_vereadores_list(filter_text)
    
    def select_vereador(self, item):
        """Selecionar vereador"""
        self.selected_vereador = item.data(Qt.ItemDataRole.UserRole)
        nome = self.selected_vereador['nome']
        partido = self.selected_vereador['partido']
        
        self.current_speaker_label.setText(f"{nome}\n{partido}")
        
        # Carregar foto do vereador
        if self.selected_vereador.get('foto'):
            foto_path = os.path.join(os.path.dirname(__file__), self.selected_vereador['foto'])
            if os.path.exists(foto_path):
                pixmap = QPixmap(foto_path)
                self.current_speaker_photo.setPixmap(
                    pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                )
                self.current_speaker_photo.setStyleSheet("""
                    QLabel {
                        border: 3px solid rgba(102, 126, 234, 0.5);
                        border-radius: 10px;
                    }
                """)
            else:
                self.current_speaker_photo.setText("👤")
        else:
            self.current_speaker_photo.setText("👤")
            
        # Habilitar botão de aparte apenas quando iniciar a fala
        self.btn_aparte.setEnabled(False)
        
        # Enviar para Servidor (API)
        api_post('speaker', {'speaker': self.selected_vereador})
        
        # Sincronizar com tela do plenário APENAS SE NÃO ESTIVER RODANDO
        # Se estiver rodando, a troca visual só acontece no START ou APARTE
        if not self.is_running:
             self.live_vereador = self.selected_vereador
             self.sync_tela_plenario()
    
    def set_time(self, seconds):
        """Definir tempo"""
        if self.is_running:
            # Se estiver rodando, apenas prepara o tempo para usar depois (Aparte)
            self.staged_seconds = seconds
            self.status_label.setText(f"⏱️ Tempo {seconds//60}min preparado")
            # Não para o timer!
        else:
            self.total_seconds = seconds
            self.remaining_seconds = seconds
            self.staged_seconds = seconds # Sincroniza
            self.update_display()
    
    def set_custom_time(self):
        """Definir tempo customizado"""
        minutes = self.custom_minutes.value()
        self.set_time(minutes * 60)
        
    def add_time(self):
        """Adicionar tempo ao cronômetro"""
        minutes = self.adjust_minutes.value()
        seconds_to_add = minutes * 60
        
        self.remaining_seconds += seconds_to_add
        self.update_display()
        
        # Se não estiver rodando, também atualiza o total para consistência visual
        if not self.is_running:
            self.total_seconds = self.remaining_seconds
            
        self.sync_tela_plenario()
        
        # Feedback visual rápido
        self.status_label.setText(f"+ {minutes} min")
        QTimer.singleShot(2000, lambda: self.status_label.setText("▶️ Em Execução" if self.is_running else "⏸️ Aguardando"))

    def sub_time(self):
        """Remover tempo do cronômetro"""
        minutes = self.adjust_minutes.value()
        seconds_to_sub = minutes * 60
        
        self.remaining_seconds -= seconds_to_sub
        if self.remaining_seconds < 0:
            self.remaining_seconds = 0
            
        self.update_display()
        
        # Se não estiver rodando, também atualiza o total
        if not self.is_running:
             self.total_seconds = self.remaining_seconds
        
        self.sync_tela_plenario()
        
        # Feedback visual rápido
        self.status_label.setText(f"- {minutes} min")
        QTimer.singleShot(2000, lambda: self.status_label.setText("▶️ Em Execução" if self.is_running else "⏸️ Aguardando"))
    
    def _run_arduino_async(self, func):
        """Executar comando Arduino em thread separada"""
        threading.Thread(target=func, daemon=True).start()
    
    def start_timer(self):
        """Iniciar cronômetro"""
        print("DEBUG: start_timer chamado")
        if self.remaining_seconds == 0:
            self.show_warning("Aviso", "Defina um tempo antes de iniciar!")
            return
        
        if not self.selected_vereador:
            reply = QMessageBox.question(
                self, "Confirmação",
                "Nenhum vereador selecionado. Deseja continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Definir Orador Vivo
        self.live_vereador = self.selected_vereador
        
        self.is_running = True
        self.is_paused = False
        self.timer.start(1000)
        
        # Abrir áudio (Async)
        print("DEBUG: Abrindo áudio...")
        self._run_arduino_async(self.arduino.open_audio)
        
        # Atualizar UI
        self.status_label.setText("▶️ Em Execução")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #00f2fe;
                background: rgba(0, 242, 254, 0.2);
                border-radius: 20px;
                padding: 10px 20px;
                margin: 5px;
            }
        """)
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.btn_aparte.setEnabled(True)
        
        # Enviar para Servidor (API)
        api_post('timer', {'action': 'start', 'remaining': self.remaining_seconds, 'total': self.total_seconds})
        
        # Sincronizar com tela do plenário
        self.sync_tela_plenario()
        print("DEBUG: start_timer finalizado")
    
    def show_warning(self, title, message):
        """Mostrar aviso customizado com estilo"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(QMessageBox.Icon.Warning)
        
        # Estilo customizado
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1a1a2e; /* Fundo escuro */
            }
            QLabel {
                color: #ffffff;
                font-size: 20px; /* Fonte maior */
                font-weight: bold;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #067b42, stop:1 #ff5e62);
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff5e62, stop:1 #067b42);
            }
        """)
        msg.exec()
    
    def pause_timer(self):
        """Pausar cronômetro"""
        self.is_running = False
        self.is_paused = True
        self.timer.stop()
        
        # Cortar áudio (Async)
        self._run_arduino_async(self.arduino.cut_audio)
        
        # Atualizar UI
        self.status_label.setText("⏸️ Pausado")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #fee140;
                background: rgba(254, 225, 64, 0.2);
                border-radius: 20px;
                padding: 10px 20px;
                margin: 5px;
            }
        """)
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        
        # Enviar para Servidor (API)
        api_post('timer', {'action': 'pause', 'remaining': self.remaining_seconds})
        
        # Sincronizar com tela do plenário
        self.sync_tela_plenario()
    
    def stop_timer(self):
        """Parar cronômetro"""
        self.is_running = False
        self.is_paused = False
        self.timer.stop()
        
        # Cortar áudio (Async)
        self._run_arduino_async(self.arduino.cut_audio)
        
        # Resetar tempo
        self.remaining_seconds = self.total_seconds
        self.update_display()
        
        # Atualizar UI
        self.status_label.setText("⏸️ Aguardando")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 10px 20px;
                margin: 5px;
            }
        """)
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.btn_aparte.setEnabled(False)
        
        # Enviar para Servidor (API)
        api_post('timer', {'action': 'stop', 'total': self.total_seconds})
        
        # Sincronizar com tela do plenário e RESETAR para logo
        self.sync_tela_plenario()
        if self.tela_plenario:
            self.tela_plenario.timer_started = False  # Resetar flag
            self.tela_plenario.show_session_info()  # Voltar para logo
    
    def update_timer(self):
        """Atualizar cronômetro"""
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update_display()
            
            # Enviar para Servidor (API)
            api_post('timer', {'action': 'update', 'remaining': self.remaining_seconds})
            
            # Sincronizar com tela do plenário
            self.sync_tela_plenario()
            
            # Verificar se chegou a zero
            if self.remaining_seconds == 0:
                self.on_time_up()
    
    def on_time_up(self):
        """Tempo esgotado"""
        self.stop_timer()
        QMessageBox.information(self, "Tempo Esgotado", "⏰ O tempo do orador terminou!")
    
    def update_display(self):
        """Atualizar display do timer"""
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
    
    def connect_arduino(self):
        """Conectar ao Arduino"""
        if self.arduino.connect():
            self.arduino_status.setText("✅ Arduino: Conectado")
            self.arduino_status.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #ffffff;
                    background-color: rgba(0, 242, 254, 0.4);
                    border: 1px solid #00f2fe;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
            
            # Enviar status para Servidor (API)
            api_post('arduino', {'connected': True})
        else:
            self.arduino_status.setText("❌ Arduino: Desconectado")
            self.arduino_status.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #ffffff;
                    background-color: rgba(250, 112, 154, 0.4);
                    border: 1px solid #fa709a;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
    
    def on_arduino_connection_change(self, connected):
        """Callback de mudança de conexão Arduino"""
        # Status movido para Admin
        # Enviar status para Servidor (API)
        api_post('arduino', {'connected': connected})
    
    def start_websocket(self):
        """Iniciar thread WebSocket (Desativado - Controle Direto)"""
        # Status movido para Admin
        pass
    
    def on_websocket_connection_change(self, connected):
        """Callback de mudança de conexão WebSocket"""
        # Status movido para Admin
        pass
    

    def open_admin(self):
        """Abrir painel administrativo"""
        # Sempre criar nova instância para evitar problemas de estado/referência
        if self.admin_dialog:
            self.admin_dialog.close()
            
        self.admin_dialog = VereadoresAdminDialog(self)
        self.admin_dialog.vereadores_updated.connect(self.on_vereadores_updated)
        self.admin_dialog.session_updated.connect(self.on_session_updated)
        
        self.admin_dialog.show()
        self.admin_dialog.raise_()
        self.admin_dialog.activateWindow()
    
    def on_vereadores_updated(self):
        """Callback quando vereadores são atualizados"""
        self.load_vereadores()
        print("✅ Lista de vereadores atualizada")
    
    def on_session_updated(self):
        """Callback quando sessão é atualizada"""
        if self.tela_plenario:
            # Recarregar configuração da sessão
            self.tela_plenario.session_config.load_config()
            # Se ainda não iniciou, atualizar tela
            if not self.tela_plenario.timer_started:
                self.tela_plenario.show_session_info()
            print("✅ Configuração da sessão atualizada na tela do plenário")
        
        # Avisar clientes web (Lower Third)
        api_post('config_update', {})
    
    def open_tela_plenario(self):
        """Abrir tela do plenário (Monitor 2)"""
        if not self.tela_plenario:
            self.tela_plenario = TelaPlenario()
            self.tela_plenario.show()
            print("✅ Tela do Plenário aberta")
    
    def toggle_aparte(self):
        """Alternar modo Aparte (Com troca de contexto e cálculo de uso)"""
        if self.btn_aparte.isChecked():
            # INICIAR APARTE
            
            # Validar se temos tempo "staged" (preparado)
            if self.staged_seconds > 0:
                novo_tempo = self.staged_seconds
            else:
                # Se não selecionou tempo, usa 1 min padrão ou pergunta?
                novo_tempo = 60
            
            # Salvar estado do orador principal (SEM SUBTRAIR AINDA)
            self.saved_main_seconds = self.remaining_seconds
            self.aparte_initial_seconds = novo_tempo # Guardar total concedido
            
            self.main_speaker = self.live_vereador # Quem estava falando antes
            
            # Definir novo orador como o Selecionado na lista
            self.aparte_speaker = self.selected_vereador
            self.live_vereador = self.aparte_speaker # Agora ele é o vivo
            
            # Aplicar novo tempo
            self.remaining_seconds = novo_tempo
            self.is_active_aparte = True
            self.update_display()
            
            # Atualizar UI Botão
            self.btn_aparte.setText("🛑 ENCERRAR APARTE")
            self.btn_aparte.setStyleSheet("""
                QPushButton {
                    background: #c0392b;
                    color: white;
                    font-weight: bold;
                    font-size: 16px;
                    border-radius: 8px;
                    margin-top: 10px;
                } 
                QPushButton:hover { background: #e74c3c; }
            """)
            
            # Timer Amarelo
            self.timer_label.setStyleSheet("""
                QLabel {
                    font-size: 120px;
                    font-weight: bold;
                    color: #fceabb;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(248, 181, 0, 0.2),
                        stop:1 rgba(252, 234, 187, 0.2));
                    border-radius: 15px;
                    padding: 20px;
                    border: 2px solid #f8b500;
                }
            """)
            
            self.sync_tela_plenario()
            
            # Garantir start se não estiver rodando
            if not self.is_running:
                 self.start_timer()
            
        else:
            # ENCERRAR APARTE (Restaurar)
            self.is_active_aparte = False
            self.aparte_speaker = None
            
            # Calcular tempo efetivamente usado no aparte
            tempo_usado = self.aparte_initial_seconds - self.remaining_seconds
            if tempo_usado < 0: tempo_usado = 0
            
            # Restaurar Orador Principal
            if self.main_speaker:
                self.live_vereador = self.main_speaker
                
                # Restaurar tempo subtraindo APENAS O QUE FOI USADO
                self.remaining_seconds = self.saved_main_seconds - tempo_usado
                if self.remaining_seconds < 0: self.remaining_seconds = 0
                
            self.update_display()
            
            # Restaurar UI Botão
            self.btn_aparte.setText("🗣️ CONCEDER APARTE")
            self.btn_aparte.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #e67e22, stop:1 #f39c12);
                    color: white;
                    font-weight: bold;
                    font-size: 16px;
                    border-radius: 8px;
                    margin-top: 10px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #d35400, stop:1 #e67e22);
                }
            """)
            
            # Timer Azul
            self.timer_label.setStyleSheet("""
                QLabel {
                    font-size: 120px;
                    font-weight: bold;
                    color: #4facfe;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(102, 126, 234, 0.1),
                        stop:1 rgba(118, 75, 162, 0.1));
                    border-radius: 15px;
                    padding: 20px;
                }
            """)
            
            self.sync_tela_plenario()

    def sync_tela_plenario(self):
        """Sincronizar dados com tela do plenário"""
        if self.tela_plenario:
            # Atualizar vereador (Usa o live_vereador que é a verdade atual)
            if self.live_vereador:
                self.tela_plenario.update_vereador(self.live_vereador)
            elif self.selected_vereador and not self.is_running:
                 # Fallback para preview se parado
                 self.tela_plenario.update_vereador(self.selected_vereador)
            
            # Atualizar timer (Passar flag de aparte)
            self.tela_plenario.update_timer(self.remaining_seconds, self.is_active_aparte)
            
            # Atualizar status
            self.tela_plenario.update_status(self.is_running)

    def update_timer(self):
        """Atualizar cronômetro"""
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update_display()
            
            # Enviar para Servidor (API)
            api_post('timer', {'action': 'update', 'remaining': self.remaining_seconds})
            
            # Sincronizar com tela do plenário
            self.sync_tela_plenario()
            
            # Verificar se chegou a zero
            if self.remaining_seconds == 0:
                self.on_time_up()
                if self.is_active_aparte:
                      self.btn_aparte.setChecked(False) # Forçar estado checked=False
                      self.toggle_aparte() # Chamar toggle para resetar visual
                
                self.btn_aparte.setEnabled(False)
            else:
                 self.btn_aparte.setEnabled(True)
    
    def on_time_up(self):
        """Tempo esgotado"""
        self.stop_timer()
        
        # Exibir mensagem no display (5 segundos)
        self.timer_label.setText("TEMPO\nESGOTADO")
        self.timer_label.setStyleSheet("""
            QLabel {
                font-size: 60px;
                font-weight: bold;
                color: #ffffff;
                background: #c0392b;
                border-radius: 15px;
                padding: 10px;
                border: 2px solid #e74c3c;
            }
        """)
        
        # Restaurar display após 5 segundos
        QTimer.singleShot(5000, self.reset_timer_display)

    def reset_timer_display(self):
        """Restaurar display do timer para o normal"""
        self.timer_label.setText("00:00")
        self.timer_label.setStyleSheet("""
            QLabel {
                font-size: 120px;
                font-weight: bold;
                color: #4facfe;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(102, 126, 234, 0.1),
                    stop:1 rgba(118, 75, 162, 0.1));
                border-radius: 15px;
                padding: 20px;
            }
        """)
    
    def closeEvent(self, event):
        """Evento de fechamento da janela"""
        # Parar timer
        if self.is_running:
            self.stop_timer()
        
        # Desconectar Arduino
        self.arduino.disconnect()
        
        # Fechar tela do plenário
        if self.tela_plenario:
            self.tela_plenario.close()
        
        # Servidor roda em thread daemon, será encerrado automaticamente
        event.accept()


def main():
    """Função principal"""
    
    # Verificar se servidor já está rodando
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 5000))
    sock.close()

    if result == 0:
        print("✅ Servidor já está rodando (detectado na porta 5000)")
    else:
        # Iniciar servidor Flask em processo separado
        print("🚀 Iniciando servidor Flask-SocketIO em background...")
        server_process = multiprocessing.Process(target=server.run_server, daemon=True)
        server_process.start()
        
        # Aguardar servidor iniciar
        import time
        time.sleep(2)
        print("✅ Servidor iniciado!\n")
    
    app = QApplication(sys.argv)
    
    # Configurar fonte padrão
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Criar e mostrar janela
    window = PainelPresidente()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
