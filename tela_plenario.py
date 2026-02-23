"""
Tela do Plenário - Monitor 2
Exibição fullscreen de foto, nome, partido e cronômetro
"""

import sys
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer, Slot, QDate, QLocale
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
        main_layout.setContentsMargins(30, 10, 30, 20)
        main_layout.setSpacing(5)
        
        # --- HEADER (Sessão e Data) ---
        self.header_label = QLabel()
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: rgba(255, 255, 255, 0.9);
                font-weight: 500;
                padding: 8px 20px;
                background: rgba(0, 0, 0, 0.4);
                border-radius: 15px;
            }
        """)
        main_layout.addWidget(self.header_label)
        
        # Spacer
        main_layout.addStretch(1)
        
        # Foto do vereador
        self.foto_label = QLabel()
        self.foto_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.foto_label.setFixedSize(280, 280)
        self.foto_label.setStyleSheet("""
            QLabel {
                border: 4px solid rgba(255, 255, 255, 0.3);
                border-radius: 20px;
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        self.set_placeholder_photo()
        main_layout.addWidget(self.foto_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Nome do vereador
        self.nome_label = QLabel("")
        self.nome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nome_label.setStyleSheet("""
            QLabel {
                font-size: 90px;
                font-weight: bold;
                color: #ffffff;
                background: rgba(0, 40, 80, 0.6);
                border-radius: 10px;
                padding: 0px 0;
                margin: 5px 0;
            }
        """)
        main_layout.addWidget(self.nome_label)
        
        # Partido
        self.partido_label = QLabel("")
        self.partido_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.partido_label.setStyleSheet("""
            QLabel {
                font-size: 48px;
                font-weight: 500;
                color: #dddddd;
                text-transform: uppercase;
                letter-spacing: 2px;
                padding: 5px;
            }
        """)
        main_layout.addWidget(self.partido_label)
        
        # Spacer
        main_layout.addStretch(1)
        
        # --- CONTAINER DO TIMER (Estilo Refined) ---
        self.timer_container = QWidget()
        self.timer_container.setStyleSheet("""
            QWidget {
                background: rgba(30, 144, 255, 0.15);
                border: 2px solid rgba(255, 255, 255, 0.5);
                border-radius: 30px;
            }
        """)
        timer_layout = QVBoxLayout(self.timer_container)
        timer_layout.setContentsMargins(40, 5, 40, 15)
        timer_layout.setSpacing(0)
        
        # Cronômetro Texto
        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("""
            QLabel {
                font-size: 210px;
                font-weight: bold;
                color: #ffffff;
                background: transparent;
                border: none;
                font-family: 'Segoe UI', sans-serif;
                margin-bottom: -10px; /* Ajuste fino */
            }
        """)
        timer_layout.addWidget(self.timer_label)
        
        # Barra de Progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 6px;
                background-color: rgba(0, 0, 0, 0.3);
            }
            QProgressBar::chunk {
                background-color: #00f2fe;
                border-radius: 6px;
            }
        """)
        timer_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(self.timer_container, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Status REMOVIDO conforme soliticação
        # self.status_label = QLabel("") 
        # main_layout.addWidget(self.status_label)
        
        # Spacer
        main_layout.addStretch(1)
        
        central_widget.setLayout(main_layout)
        
        # Aplicar estilo global (Imagem de fundo)
        bg_path = os.path.join(os.path.dirname(__file__), "fotos", "Cópia de TELA DE TEMPO.png")
        bg_path = bg_path.replace("\\", "/")
        
        self.setStyleSheet(f"""
            QMainWindow {{
                border-image: url("{bg_path}") 0 0 0 0 stretch stretch;
            }}
        """)
        
        # Fullscreen
        self.showFullScreen()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # Atualizar header inicial
        self.update_header()

    def update_header(self):
        """Atualizar data e sessão no header"""
        # Data
        locale = QLocale(QLocale.Portuguese, QLocale.Brazil)
        date_str = locale.toString(QDate.currentDate(), "dddd, d 'de' MMMM 'de' yyyy")
        # Capitalizar primeira letra
        date_str = date_str[0].upper() + date_str[1:] if date_str else ""
        
        # Sessão (Pega o nome definido pelo admin)
        session_name = ""
        if hasattr(self, 'session_config'):
             session_name = self.session_config.get_session_name() or "SESSÃO"
        else:
             session_name = "SESSÃO"
        
        self.header_label.setText(f"{session_name}   •   {date_str}")
    
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
        
        # Se o timer container NÃO estiver visível, estamos em MODO SESSÃO
        # Não atualizar visualmente para não quebrar o layout da sessão
        if hasattr(self, 'timer_container') and not self.timer_container.isVisible():
             return

        if vereador:
            self.nome_label.setText(vereador['nome'])
            self.partido_label.setText(vereador['partido'])
            
            # Carregar foto
            if vereador.get('foto'):
                foto_rel = vereador['foto']
                # Tentar primeiro em AppData, depois no Bundle
                foto_path = self.session_config.get_data_path(foto_rel)
                if not os.path.exists(foto_path):
                    foto_path = self.session_config.get_bundle_path(foto_rel)
                
                if os.path.exists(foto_path):
                    pixmap = QPixmap(foto_path)
                    # Escalar para o tamanho do widget (320x320)
                    self.foto_label.setPixmap(
                        pixmap.scaled(280, 280, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    )
                    self.foto_label.setStyleSheet("""
                        QLabel {
                            border: 4px solid rgba(255, 255, 255, 0.3);
                            border-radius: 20px;
                        }
                    """)
                else:
                    self.set_placeholder_photo()
            else:
                self.set_placeholder_photo()
        else:
            self.nome_label.setText("")
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

    @Slot(int, int, bool)
    def update_timer(self, seconds, total_seconds=0, is_aparte=False):
        """Atualizar cronômetro e barra de progresso"""
        try:
            # Compatibilidade com chamada antiga (seconds, is_aparte) -> Onde is_aparte entra no lugar de total_seconds
            if isinstance(total_seconds, bool):
                is_aparte = total_seconds
                total_seconds = 0
        except:
            pass
            

            
        self.remaining_seconds = seconds
        minutes = seconds // 60
        secs = seconds % 60
        self.timer_label.setText(f"{minutes:02d}:{secs:02d}")
        
        # Atualizar Barra de Progresso
        if hasattr(self, 'progress_bar'):
            if total_seconds > 0:
                progress = int((seconds / total_seconds) * 100)
                self.progress_bar.setValue(progress)
                
                # Mudar cor da barra baseada no tempo
                if is_aparte:
                    chunk_color = "#f8b500" # Amarelo
                elif seconds <= 10:
                    chunk_color = "#e74c3c" # Vermelho
                elif seconds <= 30:
                    chunk_color = "#f39c12" # Laranja
                else:
                    chunk_color = "#00f2fe" # Azul
                    
                self.progress_bar.setStyleSheet(f"""
                    QProgressBar {{
                        border: none;
                        border-radius: 4px;
                        background-color: rgba(0, 0, 0, 0.3);
                    }}
                    QProgressBar::chunk {{
                        background-color: {chunk_color};
                        border-radius: 4px;
                    }}
                """)
            else:
                self.progress_bar.setValue(0)

        # Modo Aparte
        if is_aparte:
             self.blink_timer.stop()
             self.timer_label.setVisible(True)
             
             self.timer_label.setStyleSheet("""
                QLabel {
                    font-size: 210px;
                    font-weight: bold;
                    color: #fceabb;
                    background: transparent;
                    border: none;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                }
            """)
             return

        # Modo Normal - Verificar Tempo (Piscar)
        if seconds <= 60 and seconds > 0:
            if seconds <= 10:
                interval = 200
            elif seconds <= 30:
                interval = 500
            else:
                interval = 1000
                
            if not self.blink_timer.isActive() or self.blink_timer.interval() != interval:
                self.blink_timer.start(interval)
            
            # Estilos apenas mudam cor do texto
            self.style_blink_on = "font-size: 210px; font-weight: bold; background: transparent; border: none; color: #ff0000;"
            self.style_blink_off = "font-size: 210px; font-weight: bold; background: transparent; border: none; color: rgba(255, 0, 0, 0.1);"
            
            if self.blink_state:
                 self.timer_label.setStyleSheet(self.style_blink_on)
            
        else:
            self.blink_timer.stop()
            self.timer_label.setVisible(True)
            self.blink_state = True
            
            self.timer_label.setStyleSheet("""
                QLabel {
                    font-size: 210px;
                    font-weight: bold;
                    color: #ffffff;
                    background: transparent;
                    border: none;
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
        
        if is_running:
            # Garantir container visível
            if hasattr(self, 'timer_container') and not self.timer_container.isVisible():
                 self.timer_container.setVisible(True)
                 
            # Verificar se precisamos transicionar da tela de sessão para vereador
            # Se o timer_label está oculto, significa que estamos no modo "Sessão"
            if not self.timer_label.isVisible() or not self.timer_started:
                print("DEBUG: Restaurando Visual Vereador (update_status)")
                self.timer_started = True
                self.show_vereador_info()
        
            # Ocultar mensagem "Em Execução" para limpar a tela
            pass
        else:
            if not self.timer_started:
                # Se ainda não iniciou, manter logo/sessão
                self.show_session_info()
            
            # Status Removido


    def reset_timer_state(self):
        """Resetar estado do timer (Voltar para tela de sessão)"""
        self.timer_started = False
        self.show_session_info()
    
    def show_session_info(self):
        """Mostrar logo e número da sessão (Tela de Espera Limpa)"""
        # Esconder Painel do Timer
        if hasattr(self, 'timer_container'):
             self.timer_container.setVisible(False)
             
        self.timer_label.setVisible(False)
        # self.status_label.setVisible(False) # Removido
        
        # Aumentar Logo e Remover Bordas
        self.foto_label.setFixedSize(450, 450)
        
        # Carregar logo se existir
        logo_path = self.session_config.get_logo()
        if logo_path:
            # Tentar resolver caminho se for relativo
            if not os.path.isabs(logo_path):
                abs_logo = self.session_config.get_data_path(logo_path)
                if not os.path.exists(abs_logo):
                    abs_logo = self.session_config.get_bundle_path(logo_path)
                logo_path = abs_logo
                
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                # Escalar mantendo aspecto, sem cortes
                self.foto_label.setPixmap(
                    pixmap.scaled(450, 450, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                )
                self.foto_label.setStyleSheet("border: none; background: transparent;")
            else:
                self.foto_label.setText("🏛️")
                self.foto_label.setStyleSheet("border: none; background: transparent; font-size: 250px; color: rgba(255, 255, 255, 0.5);")
        else:
            self.foto_label.setText("🏛️")
            self.foto_label.setStyleSheet("border: none; background: transparent; font-size: 250px; color: rgba(255, 255, 255, 0.5);")
        
        # Mostrar número da sessão com DESTAQUE MAIOR
        session_number = self.session_config.get_session_number()
        
        # Estilo de Destaque para Sessão
        self.nome_label.setStyleSheet("""
            QLabel {
                font-size: 70px;
                font-weight: 900;
                color: #ffffff;
                background: transparent;
                padding: 20px 0;
            }
        """)
        
        if session_number:
            self.nome_label.setText(session_number)
            
            city_name = self.session_config.get_city_name()
            partido_text = f"CÂMARA MUNICIPAL DE {city_name}" if city_name else "CÂMARA MUNICIPAL"
            
            self.partido_label.setText(partido_text)
            self.partido_label.setStyleSheet("""
                QLabel {
                    font-size: 40px;
                    font-weight: bold;
                    color: #eeeeee;
                    letter-spacing: 4px;
                    background: transparent;
                }
            """)
        else:
            city_name = self.session_config.get_city_name()
            self.nome_label.setText(f"CÂMARA MUNICIPAL DE {city_name}" if city_name else "CÂMARA MUNICIPAL")
            self.partido_label.setText("")
    
    def show_vereador_info(self):
        """Mostrar informações do vereador (Restaurar Layout Padrão)"""
        # Marcar explicitamente que iniciamos o modo orador
        self.timer_started = True
        
        # Mostrar Painel do Timer
        if hasattr(self, 'timer_container'):
             self.timer_container.setVisible(True)
             
        self.timer_label.setVisible(True)
        # Status depende do is_running, mas deixamos visivel se precisar (ele se auto-gere no update_status)
        
        # Restaurar Tamanho da Foto
        self.foto_label.setFixedSize(280, 280)
        
        # Restaurar Estilos de Texto
        self.nome_label.setStyleSheet("""
            QLabel {
                font-size: 90px;
                font-weight: bold;
                color: #ffffff;
                background: rgba(0, 40, 80, 0.6);
                border-radius: 10px;
                padding: 0px 0;
                margin: 5px 0;
            }
        """)
        
        self.partido_label.setStyleSheet("""
            QLabel {
                font-size: 48px;
                font-weight: 500;
                color: #dddddd;
                text-transform: uppercase;
                letter-spacing: 2px;
                padding: 5px;
            }
        """)
        
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
