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
                background: rgba(0, 0, 0, 0.3);
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
                color: #ffffff;
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
                color: #ffffff;
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
        
        # Aplicar estilo global (Imagem de fundo)
        bg_path = os.path.join(os.path.dirname(__file__), "fotos", "Cópia de TELA DE TEMPO.png")
        # Normalizar path para formato que o Qt aceita (forward slashes)
        bg_path = bg_path.replace("\\", "/")
        
        self.setStyleSheet(f"""
            QMainWindow {{
                border-image: url("{bg_path}") 0 0 0 0 stretch stretch;
            }}
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
    
    def __init__(self):
        super().__init__()
        
        self.current_vereador = None
        self.remaining_seconds = 0
        self.is_running = False
        self.timer_started = False
        
        # Blink state
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.blink_update)
        self.blink_state = True # Visible
        
        # Carregar configuração da sessão
        from session_config import SessionConfig
        self.session_config = SessionConfig()
        
        self.init_ui()
        self.move_to_second_monitor()
        
        # Mostrar logo e sessão inicialmente
        self.show_session_info()

    # ... (init_ui and others remain same, skipping to update_timer)

    @Slot(int)
    def update_timer(self, seconds, is_aparte=False):
        """Atualizar cronômetro"""
        self.remaining_seconds = seconds
        minutes = seconds // 60
        secs = seconds % 60
        self.timer_label.setText(f"{minutes:02d}:{secs:02d}")
        
        # Modo Aparte
        if is_aparte:
             self.blink_timer.stop()
             self.timer_label.setVisible(True) # Garantir visibilidade
             
             self.timer_label.setStyleSheet("""
                QLabel {
                    font-size: 180px;
                    font-weight: bold;
                    color: #fceabb;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(248, 181, 0, 0.2),
                        stop:1 rgba(252, 234, 187, 0.2));
                    border-radius: 25px;
                    padding: 40px;
                    border: 3px solid #f8b500;
                    margin: 20px;
                }
            """)
             # Opcional: Adicionar label de "EM APARTE" em algum lugar ou mudar o status
             self.status_label.setText("🗣️ EM APARTE")
             self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 36px;
                    font-weight: bold;
                    color: #ffffff;
                    background: #f8b500;
                    border-radius: 20px;
                    padding: 15px 30px;
                }
            """)
             return

        # Modo Normal - Verificar Tempo
        if seconds <= 60 and seconds > 0:
            # Danger Zone - Vermelho e Piscando
            
            # Definir velocidade do pisca
            if seconds <= 10:
                interval = 200 # Muito rápido
            elif seconds <= 30:
                interval = 500 # Médio
            else:
                interval = 1000 # Lento
                
            if not self.blink_timer.isActive() or self.blink_timer.interval() != interval:
                self.blink_timer.start(interval)
            
            # Estilos para o Pisca (Apenas texto muda)
            base_style = """
                QLabel {
                    font-size: 180px;
                    font-weight: bold;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(255, 0, 0, 0.1),
                        stop:1 rgba(100, 0, 0, 0.1));
                    border-radius: 25px;
                    padding: 40px;
                    margin: 20px;
                    border: 2px solid #ff0000;
            """
            
            self.style_blink_on = base_style + "color: #ff0000; }"
            self.style_blink_off = base_style + "color: rgba(255, 0, 0, 0.1); }" # Texto quase invisível
            
            # Se o timer acabou de começar, aplica estilo imediatamente
            if self.blink_state:
                 self.timer_label.setStyleSheet(self.style_blink_on)
            
        else:
            # Normal ou Zerado
            self.blink_timer.stop()
            self.timer_label.setVisible(True)
            self.blink_state = True
            
            self.timer_label.setStyleSheet("""
                QLabel {
                    font-size: 180px;
                    font-weight: bold;
                    color: #ffffff;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(102, 126, 234, 0.2),
                        stop:1 rgba(118, 75, 162, 0.2));
                    border-radius: 25px;
                    padding: 40px;
                    margin: 20px;
                }
            """)

    def blink_update(self):
        """Atualizar animação de piscar"""
        self.blink_state = not self.blink_state
        
        if self.blink_state:
             self.timer_label.setStyleSheet(self.style_blink_on)
        else:
             self.timer_label.setStyleSheet(self.style_blink_off)
    
    @Slot(bool)
    def update_status(self, is_running):
        """Atualizar status"""
        self.is_running = is_running
        
        if is_running and not self.timer_started:
            # Primeira vez que inicia - mostrar informações do vereador
            self.timer_started = True
            self.show_vereador_info()
        
        if is_running:
            self.status_label.setText("▶️ Em Execução")
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 36px;
                    font-weight: bold;
                    color: #ffffff;
                    background: rgba(0, 242, 254, 0.2);
                    border-radius: 20px;
                    padding: 15px 30px;
                }
            """)
        else:
            if not self.timer_started:
                # Se ainda não iniciou, manter logo/sessão
                self.show_session_info()
            
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
    
    def show_session_info(self):
        """Mostrar logo e número da sessão"""
        # Carregar logo se existir
        logo_path = self.session_config.get_logo()
        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
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
            self.foto_label.setText("🏛️")
            self.foto_label.setStyleSheet("""
                QLabel {
                    border: 5px solid rgba(102, 126, 234, 0.5);
                    border-radius: 20px;
                    background: rgba(255, 255, 255, 0.05);
                    font-size: 200px;
                    color: rgba(255, 255, 255, 0.3);
                }
            """)
        
        # Mostrar número da sessão
        session_number = self.session_config.get_session_number()
        if session_number:
            self.nome_label.setText(session_number)
            self.partido_label.setText("CÂMARA MUNICIPAL")
        else:
            # Sem número de sessão - mostrar apenas texto padrão
            self.nome_label.setText("CÂMARA MUNICIPAL")
            self.partido_label.setText("")
        
        # Esconder timer e status
        self.timer_label.setVisible(False)
        self.status_label.setVisible(False)
    
    def show_vereador_info(self):
        """Mostrar informações do vereador"""
        # Mostrar timer e status
        self.timer_label.setVisible(True)
        self.status_label.setVisible(True)
        
        # Atualizar com vereador atual se existir
        if self.current_vereador:
            self.update_vereador(self.current_vereador)
        else:
            self.nome_label.setText("")
            self.partido_label.setText("")
            self.set_placeholder_photo()
    
    def keyPressEvent(self, event):
        """Permitir fechar com ESC"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
