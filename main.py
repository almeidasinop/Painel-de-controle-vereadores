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
import socketio
import threading
import server
import multiprocessing

class WebSocketThread(QThread):
    """Thread para gerenciar comunicação WebSocket"""
    
    connection_changed = Signal(bool)
    
    def __init__(self, server_url='http://127.0.0.1:5000'):
        super().__init__()
        self.server_url = server_url
        self.sio = socketio.Client()
        self.is_connected = False
        
        # Configurar eventos
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
    
    def on_connect(self):
        """Callback de conexão"""
        self.is_connected = True
        self.connection_changed.emit(True)
        print("✅ WebSocket conectado")
    
    def on_disconnect(self):
        """Callback de desconexão"""
        self.is_connected = False
        self.connection_changed.emit(False)
        print("❌ WebSocket desconectado")
    
    def run(self):
        """Executar thread"""
        try:
            self.sio.connect(self.server_url)
            self.sio.wait()
        except Exception as e:
            print(f"❌ Erro WebSocket: {e}")
    
    def emit(self, event, data=None):
        """Emitir evento"""
        if self.is_connected:
            self.sio.emit(event, data)
    
    def disconnect(self):
        """Desconectar"""
        if self.is_connected:
            self.sio.disconnect()


class PainelPresidente(QMainWindow):
    """Janela principal do Painel do Presidente"""
    
    def __init__(self):
        super().__init__()
        
        # Estado do sistema
        self.vereadores = []
        self.selected_vereador = None
        self.total_seconds = 0
        self.remaining_seconds = 0
        self.is_running = False
        self.is_paused = False
        
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
        
        # Depois carregar dados
        self.load_vereadores()
        
        # Conectar Arduino
        self.connect_arduino()
        
        # Iniciar servidor WebSocket em thread separada
        self.start_websocket()
        
        # Abrir Tela do Plenário automaticamente
        self.open_tela_plenario()
    
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
    
    def create_timer_section(self):
        """Criar seção do cronômetro"""
        group = QGroupBox("⏱️ Cronômetro")
        layout = QVBoxLayout()
        
        # Display do timer
        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("""
            QLabel {
                font-size: 80px;
                font-weight: bold;
                color: #4facfe;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(102, 126, 234, 0.1),
                    stop:1 rgba(118, 75, 162, 0.1));
                border-radius: 15px;
                padding: 30px;
                margin: 10px;
            }
        """)
        layout.addWidget(self.timer_label)
        
        # Status
        self.status_label = QLabel("⏸️ Aguardando")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        layout.addWidget(self.status_label)
        
        # Tempos pré-definidos
        presets_group = QGroupBox("Tempo Pré-definido")
        presets_layout = QGridLayout()
        
        presets = [
            ("3 min", 180),
            ("5 min", 300),
            ("10 min", 600),
            ("15 min", 900),
            ("20 min", 1200)
        ]
        
        for i, (label, seconds) in enumerate(presets):
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, s=seconds: self.set_time(s))
            btn.setMinimumHeight(40)
            presets_layout.addWidget(btn, i // 3, i % 3)
        
        presets_group.setLayout(presets_layout)
        layout.addWidget(presets_group)
        
        # Tempo customizado
        custom_group = QGroupBox("Tempo Customizado")
        custom_layout = QHBoxLayout()
        
        self.custom_minutes = QSpinBox()
        self.custom_minutes.setMinimum(1)
        self.custom_minutes.setMaximum(99)
        self.custom_minutes.setSuffix(" min")
        self.custom_minutes.setMinimumHeight(40)
        custom_layout.addWidget(self.custom_minutes)
        
        custom_btn = QPushButton("Definir")
        custom_btn.clicked.connect(self.set_custom_time)
        custom_btn.setMinimumHeight(40)
        custom_layout.addWidget(custom_btn)
        
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)
        
        # Controles
        controls_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶️ Iniciar")
        self.play_btn.clicked.connect(self.start_timer)
        self.play_btn.setMinimumHeight(50)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4facfe, stop:1 #00f2fe);
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00f2fe, stop:1 #4facfe);
            }
            QPushButton:disabled {
                background: #555;
                color: #888;
            }
        """)
        controls_layout.addWidget(self.play_btn)
        
        self.pause_btn = QPushButton("⏸️ Pausar")
        self.pause_btn.clicked.connect(self.pause_timer)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setMinimumHeight(50)
        controls_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("⏹️ Parar")
        self.stop_btn.clicked.connect(self.stop_timer)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(50)
        controls_layout.addWidget(self.stop_btn)
        
        layout.addLayout(controls_layout)
        
        # Botão Admin
        self.btn_admin = QPushButton("⚙️ Administrar Vereadores")
        self.btn_admin.clicked.connect(self.open_admin)
        self.btn_admin.setMinimumHeight(45)
        self.btn_admin.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #764ba2, stop:1 #667eea);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
            }
        """)
        layout.addWidget(self.btn_admin)
        
        # Status de conexões
        connections_group = QGroupBox("🔌 Conexões")
        connections_layout = QVBoxLayout()
        
        self.arduino_status = QLabel("❌ Arduino: Desconectado")
        self.arduino_status.setStyleSheet("color: #fa709a; font-weight: bold;")
        connections_layout.addWidget(self.arduino_status)
        
        self.websocket_status = QLabel("❌ WebSocket: Desconectado")
        self.websocket_status.setStyleSheet("color: #fa709a; font-weight: bold;")
        connections_layout.addWidget(self.websocket_status)
        
        connections_group.setLayout(connections_layout)
        layout.addWidget(connections_group)
        
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
        
        # Lista de vereadores
        self.vereadores_list = QListWidget()
        self.vereadores_list.itemClicked.connect(self.select_vereador)
        self.vereadores_list.setIconSize(QPixmap(60, 60).size())  # Tamanho dos ícones
        layout.addWidget(self.vereadores_list)
        
        # Orador atual
        current_group = QGroupBox("🎤 Orador Atual")
        current_layout = QVBoxLayout()
        
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
        json_path = os.path.join(os.path.dirname(__file__), 'vereadores.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.vereadores = json.load(f)
            self.populate_vereadores_list()
        except FileNotFoundError:
            QMessageBox.warning(self, "Aviso", "Arquivo vereadores.json não encontrado!")
    
    def populate_vereadores_list(self, filter_text=''):
        """Preencher lista de vereadores"""
        self.vereadores_list.clear()
        
        for vereador in self.vereadores:
            nome = vereador['nome']
            partido = vereador['partido']
            
            if filter_text.lower() in nome.lower() or filter_text.lower() in partido.lower():
                item = QListWidgetItem(f"{nome} ({partido})")
                item.setData(Qt.ItemDataRole.UserRole, vereador)
                
                # Adicionar foto como ícone
                if vereador.get('foto'):
                    foto_path = os.path.join(os.path.dirname(__file__), vereador['foto'])
                    if os.path.exists(foto_path):
                        pixmap = QPixmap(foto_path)
                        icon = QIcon(pixmap)
                        item.setIcon(icon)
                
                # Aumentar altura do item para exibir foto
                item.setSizeHint(item.sizeHint().expandedTo(QPixmap(50, 50).size()))
                
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
        
        # Enviar para WebSocket
        if self.websocket_thread and self.websocket_thread.is_connected:
            self.websocket_thread.emit('speaker_selected', {'speaker': self.selected_vereador})
        
        # Sincronizar com tela do plenário
        self.sync_tela_plenario()
    
    def set_time(self, seconds):
        """Definir tempo"""
        if self.is_running:
            self.stop_timer()
        
        self.total_seconds = seconds
        self.remaining_seconds = seconds
        self.update_display()
    
    def set_custom_time(self):
        """Definir tempo customizado"""
        minutes = self.custom_minutes.value()
        self.set_time(minutes * 60)
    
    def start_timer(self):
        """Iniciar cronômetro"""
        if self.remaining_seconds == 0:
            QMessageBox.warning(self, "Aviso", "Defina um tempo antes de iniciar!")
            return
        
        if not self.selected_vereador:
            reply = QMessageBox.question(
                self, "Confirmação",
                "Nenhum vereador selecionado. Deseja continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        self.is_running = True
        self.is_paused = False
        self.timer.start(1000)
        
        # Abrir áudio
        self.arduino.open_audio()
        
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
        
        # Enviar para WebSocket
        if self.websocket_thread and self.websocket_thread.is_connected:
            self.websocket_thread.emit('timer_start', {
                'total_seconds': self.total_seconds,
                'remaining_seconds': self.remaining_seconds
            })
        
        # Sincronizar com tela do plenário
        self.sync_tela_plenario()
    
    def pause_timer(self):
        """Pausar cronômetro"""
        self.is_running = False
        self.is_paused = True
        self.timer.stop()
        
        # Cortar áudio
        self.arduino.cut_audio()
        
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
        
        # Enviar para WebSocket
        if self.websocket_thread and self.websocket_thread.is_connected:
            self.websocket_thread.emit('timer_pause', {
                'remaining_seconds': self.remaining_seconds
            })
        
        # Sincronizar com tela do plenário
        self.sync_tela_plenario()
    
    def stop_timer(self):
        """Parar cronômetro"""
        self.is_running = False
        self.is_paused = False
        self.timer.stop()
        
        # Cortar áudio
        self.arduino.cut_audio()
        
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
        
        # Enviar para WebSocket
        if self.websocket_thread and self.websocket_thread.is_connected:
            self.websocket_thread.emit('timer_stop')
        
        # Sincronizar com tela do plenário
        self.sync_tela_plenario()
    
    def update_timer(self):
        """Atualizar cronômetro"""
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update_display()
            
            # Enviar para WebSocket
            if self.websocket_thread and self.websocket_thread.is_connected:
                self.websocket_thread.emit('timer_update', {
                    'remaining_seconds': self.remaining_seconds
                })
            
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
            self.arduino_status.setStyleSheet("color: #00f2fe; font-weight: bold;")
            
            # Enviar status para WebSocket
            if self.websocket_thread and self.websocket_thread.is_connected:
                self.websocket_thread.emit('arduino_status', {'connected': True})
        else:
            self.arduino_status.setText("❌ Arduino: Desconectado")
            self.arduino_status.setStyleSheet("color: #fa709a; font-weight: bold;")
    
    def on_arduino_connection_change(self, connected):
        """Callback de mudança de conexão Arduino"""
        if connected:
            self.arduino_status.setText("✅ Arduino: Conectado")
            self.arduino_status.setStyleSheet("color: #00f2fe; font-weight: bold;")
        else:
            self.arduino_status.setText("❌ Arduino: Desconectado")
            self.arduino_status.setStyleSheet("color: #fa709a; font-weight: bold;")
        
        # Enviar status para WebSocket
        if self.websocket_thread and self.websocket_thread.is_connected:
            self.websocket_thread.emit('arduino_status', {'connected': connected})
    
    def start_websocket(self):
        """Iniciar thread WebSocket"""
        self.websocket_thread = WebSocketThread()
        self.websocket_thread.connection_changed.connect(self.on_websocket_connection_change)
        self.websocket_thread.start()
    
    def on_websocket_connection_change(self, connected):
        """Callback de mudança de conexão WebSocket"""
        if connected:
            self.websocket_status.setText("✅ WebSocket: Conectado")
            self.websocket_status.setStyleSheet("color: #00f2fe; font-weight: bold;")
        else:
            self.websocket_status.setText("❌ WebSocket: Desconectado")
            self.websocket_status.setStyleSheet("color: #fa709a; font-weight: bold;")
    
    def open_admin(self):
        """Abrir painel administrativo"""
        if not self.admin_dialog:
            self.admin_dialog = VereadoresAdminDialog(self)
            self.admin_dialog.vereadores_updated.connect(self.on_vereadores_updated)
        
        self.admin_dialog.show()
        self.admin_dialog.raise_()
        self.admin_dialog.activateWindow()
    
    def on_vereadores_updated(self):
        """Callback quando vereadores são atualizados"""
        self.load_vereadores()
        print("✅ Lista de vereadores atualizada")
    
    def open_tela_plenario(self):
        """Abrir tela do plenário (Monitor 2)"""
        if not self.tela_plenario:
            self.tela_plenario = TelaPlenario()
            self.tela_plenario.show()
            print("✅ Tela do Plenário aberta")
    
    def sync_tela_plenario(self):
        """Sincronizar dados com tela do plenário"""
        if self.tela_plenario:
            # Atualizar vereador
            if self.selected_vereador:
                self.tela_plenario.update_vereador(self.selected_vereador)
            
            # Atualizar timer
            self.tela_plenario.update_timer(self.remaining_seconds)
            
            # Atualizar status
            self.tela_plenario.update_status(self.is_running)
    
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
        
        # Desconectar WebSocket
        if self.websocket_thread:
            self.websocket_thread.disconnect()
            self.websocket_thread.quit()
            self.websocket_thread.wait()
        
        event.accept()


def main():
    """Função principal"""
    
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
