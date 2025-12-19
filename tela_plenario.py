"""
Tela do Plenário - Monitor 2
Exibição fullscreen de foto, nome, partido e cronômetro
"""

import sys
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QFont, QPixmap, QScreen
import os

class TelaPlenario(QMainWindow):
    """Janela fullscreen para exibição no plenário"""
    
    def __init__(self):
        super().__init__()
        
        self.current_vereador = None
        self.remaining_seconds = 0
        self.is_running = False
        
        self.init_ui()
        self.move_to_second_monitor()
    
    def init_ui(self):
        """Inicializar interface"""
        self.setWindowTitle("Tela do Plenário")
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(30)
        
        # Foto do vereador
        self.foto_label = QLabel()
        self.foto_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.foto_label.setFixedSize(400, 400)
        self.foto_label.setStyleSheet("""
            QLabel {
                border: 5px solid rgba(102, 126, 234, 0.5);
                border-radius: 20px;
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        self.set_placeholder_photo()
        main_layout.addWidget(self.foto_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Nome do vereador
        self.nome_label = QLabel("Aguardando...")
        self.nome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nome_label.setStyleSheet("""
            QLabel {
                font-size: 72px;
                font-weight: bold;
                color: #ffffff;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                -webkit-background-clip: text;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        main_layout.addWidget(self.nome_label)
        
        # Partido
        self.partido_label = QLabel("")
        self.partido_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.partido_label.setStyleSheet("""
            QLabel {
                font-size: 48px;
                font-weight: 600;
                color: #4facfe;
                padding: 10px;
            }
        """)
        main_layout.addWidget(self.partido_label)
        
        # Cronômetro
        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("""
            QLabel {
                font-size: 180px;
                font-weight: bold;
                color: #4facfe;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(102, 126, 234, 0.2),
                    stop:1 rgba(118, 75, 162, 0.2));
                border-radius: 25px;
                padding: 40px;
                margin: 20px;
            }
        """)
        main_layout.addWidget(self.timer_label)
        
        # Status
        self.status_label = QLabel("⏸️ Aguardando")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #ffffff;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 15px 30px;
            }
        """)
        main_layout.addWidget(self.status_label)
        
        main_layout.addStretch()
        
        central_widget.setLayout(main_layout)
        
        # Aplicar estilo global
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f0f23, stop:1 #1a1a2e);
            }
        """)
        
        # Fullscreen
        self.showFullScreen()
        
        # Permitir sair com ESC
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
    
    def move_to_second_monitor(self):
        """Mover janela para segundo monitor se disponível"""
        screens = QScreen.virtualSiblings(self.screen())
        
        if len(screens) > 1:
            # Mover para segundo monitor
            second_screen = screens[1]
            self.setGeometry(second_screen.geometry())
            print(f"✅ Tela do Plenário movida para Monitor 2: {second_screen.name()}")
        else:
            print("⚠️ Apenas um monitor detectado. Tela do Plenário no monitor principal.")
    
    def set_placeholder_photo(self):
        """Definir foto placeholder"""
        self.foto_label.setText("👤")
        self.foto_label.setStyleSheet("""
            QLabel {
                border: 5px solid rgba(102, 126, 234, 0.5);
                border-radius: 20px;
                background: rgba(255, 255, 255, 0.05);
                font-size: 200px;
                color: rgba(255, 255, 255, 0.2);
            }
        """)
    
    @Slot(dict)
    def update_vereador(self, vereador):
        """Atualizar vereador exibido"""
        self.current_vereador = vereador
        
        if vereador:
            self.nome_label.setText(vereador['nome'])
            self.partido_label.setText(vereador['partido'])
            
            # Carregar foto
            if vereador.get('foto'):
                foto_path = os.path.join(os.path.dirname(__file__), vereador['foto'])
                if os.path.exists(foto_path):
                    pixmap = QPixmap(foto_path)
                    self.foto_label.setPixmap(
                        pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    )
                    self.foto_label.setStyleSheet("""
                        QLabel {
                            border: 5px solid rgba(102, 126, 234, 0.5);
                            border-radius: 20px;
                        }
                    """)
                else:
                    self.set_placeholder_photo()
            else:
                self.set_placeholder_photo()
        else:
            self.nome_label.setText("Aguardando...")
            self.partido_label.setText("")
            self.set_placeholder_photo()
    
    @Slot(int)
    def update_timer(self, seconds):
        """Atualizar cronômetro"""
        self.remaining_seconds = seconds
        minutes = seconds // 60
        secs = seconds % 60
        self.timer_label.setText(f"{minutes:02d}:{secs:02d}")
        
        # Mudar cor se tempo está acabando
        if seconds <= 30 and seconds > 0:
            self.timer_label.setStyleSheet("""
                QLabel {
                    font-size: 180px;
                    font-weight: bold;
                    color: #fa709a;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(250, 112, 154, 0.2),
                        stop:1 rgba(254, 225, 64, 0.2));
                    border-radius: 25px;
                    padding: 40px;
                    margin: 20px;
                }
            """)
        else:
            self.timer_label.setStyleSheet("""
                QLabel {
                    font-size: 180px;
                    font-weight: bold;
                    color: #4facfe;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(102, 126, 234, 0.2),
                        stop:1 rgba(118, 75, 162, 0.2));
                    border-radius: 25px;
                    padding: 40px;
                    margin: 20px;
                }
            """)
    
    @Slot(bool)
    def update_status(self, is_running):
        """Atualizar status"""
        self.is_running = is_running
        
        if is_running:
            self.status_label.setText("▶️ Em Execução")
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 36px;
                    font-weight: bold;
                    color: #00f2fe;
                    background: rgba(0, 242, 254, 0.2);
                    border-radius: 20px;
                    padding: 15px 30px;
                }
            """)
        else:
            self.status_label.setText("⏸️ Aguardando")
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 36px;
                    font-weight: bold;
                    color: #ffffff;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 20px;
                    padding: 15px 30px;
                }
            """)
    
    def keyPressEvent(self, event):
        """Permitir fechar com ESC"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
