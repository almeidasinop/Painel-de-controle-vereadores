"""
Painel Administrativo - Gerenciamento de Vereadores
Interface para cadastro, edição e exclusão de vereadores
"""

import sys
import json
import os
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QFileDialog, QGroupBox, QFormLayout, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QIcon

class VereadoresAdminDialog(QDialog):
    """Dialog para administração de vereadores"""
    
    vereadores_updated = Signal()  # Sinal emitido quando vereadores são atualizados
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vereadores = []
        self.current_vereador = None
        self.json_path = os.path.join(os.path.dirname(__file__), 'vereadores.json')
        self.fotos_dir = os.path.join(os.path.dirname(__file__), 'fotos')
        
        # Criar diretório de fotos se não existir
        if not os.path.exists(self.fotos_dir):
            os.makedirs(self.fotos_dir)
        
        self.init_ui()
        self.load_vereadores()
    
    def init_ui(self):
        """Inicializar interface"""
        self.setWindowTitle("Administração de Vereadores")
        self.setMinimumSize(900, 600)
        
        layout = QHBoxLayout()
        
        # Coluna esquerda - Lista
        left_column = self.create_list_section()
        layout.addWidget(left_column, 1)
        
        # Coluna direita - Formulário
        right_column = self.create_form_section()
        layout.addWidget(right_column, 2)
        
        self.setLayout(layout)
        self.apply_styles()
    
    def create_list_section(self):
        """Criar seção da lista"""
        group = QGroupBox("Vereadores Cadastrados")
        layout = QVBoxLayout()
        
        # Lista
        self.vereadores_list = QListWidget()
        self.vereadores_list.itemClicked.connect(self.select_vereador)
        layout.addWidget(self.vereadores_list)
        
        # Botões
        btn_layout = QVBoxLayout()
        
        self.btn_novo = QPushButton("➕ Novo")
        self.btn_novo.clicked.connect(self.novo_vereador)
        btn_layout.addWidget(self.btn_novo)
        
        self.btn_excluir = QPushButton("🗑️ Excluir")
        self.btn_excluir.clicked.connect(self.excluir_vereador)
        self.btn_excluir.setEnabled(False)
        btn_layout.addWidget(self.btn_excluir)
        
        layout.addLayout(btn_layout)
        
        group.setLayout(layout)
        return group
    
    def create_form_section(self):
        """Criar seção do formulário"""
        group = QGroupBox("Dados do Vereador")
        layout = QVBoxLayout()
        
        # Foto
        foto_layout = QHBoxLayout()
        
        self.foto_label = QLabel()
        self.foto_label.setFixedSize(150, 150)
        self.foto_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.foto_label.setStyleSheet("""
            QLabel {
                border: 2px solid rgba(102, 126, 234, 0.5);
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        self.set_placeholder_photo()
        foto_layout.addWidget(self.foto_label)
        
        foto_btn_layout = QVBoxLayout()
        self.btn_selecionar_foto = QPushButton("📷 Selecionar Foto")
        self.btn_selecionar_foto.clicked.connect(self.selecionar_foto)
        foto_btn_layout.addWidget(self.btn_selecionar_foto)
        
        self.btn_remover_foto = QPushButton("❌ Remover Foto")
        self.btn_remover_foto.clicked.connect(self.remover_foto)
        foto_btn_layout.addWidget(self.btn_remover_foto)
        foto_btn_layout.addStretch()
        
        foto_layout.addLayout(foto_btn_layout)
        layout.addLayout(foto_layout)
        
        # Formulário
        form_layout = QFormLayout()
        
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Nome completo do vereador")
        form_layout.addRow("Nome:", self.input_nome)
        
        self.input_partido = QLineEdit()
        self.input_partido.setPlaceholderText("Sigla do partido (ex: PSDB)")
        form_layout.addRow("Partido:", self.input_partido)
        
        layout.addLayout(form_layout)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        
        self.btn_salvar = QPushButton("💾 Salvar")
        self.btn_salvar.clicked.connect(self.salvar_vereador)
        self.btn_salvar.setEnabled(False)
        btn_layout.addWidget(self.btn_salvar)
        
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.clicked.connect(self.cancelar_edicao)
        self.btn_cancelar.setEnabled(False)
        btn_layout.addWidget(self.btn_cancelar)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def apply_styles(self):
        """Aplicar estilos"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f0f23, stop:1 #1a1a2e);
            }
            QGroupBox {
                font-size: 14px;
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
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
                min-height: 35px;
            }
            QPushButton:hover {
                background: rgba(102, 126, 234, 0.3);
                border-color: #667eea;
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.05);
                color: #666;
            }
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
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
            }
            QLabel {
                color: white;
                font-size: 13px;
            }
        """)
    
    def load_vereadores(self):
        """Carregar vereadores do JSON"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.vereadores = json.load(f)
            self.populate_list()
        except FileNotFoundError:
            self.vereadores = []
    
    def save_vereadores(self):
        """Salvar vereadores no JSON"""
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(self.vereadores, f, ensure_ascii=False, indent=4)
        self.vereadores_updated.emit()
    
    def populate_list(self):
        """Preencher lista de vereadores"""
        self.vereadores_list.clear()
        for vereador in self.vereadores:
            item = QListWidgetItem(f"{vereador['nome']} ({vereador['partido']})")
            item.setData(Qt.ItemDataRole.UserRole, vereador)
            self.vereadores_list.addItem(item)
    
    def select_vereador(self, item):
        """Selecionar vereador para edição"""
        self.current_vereador = item.data(Qt.ItemDataRole.UserRole)
        
        self.input_nome.setText(self.current_vereador['nome'])
        self.input_partido.setText(self.current_vereador['partido'])
        
        # Carregar foto
        if self.current_vereador.get('foto'):
            foto_path = os.path.join(os.path.dirname(__file__), self.current_vereador['foto'])
            if os.path.exists(foto_path):
                pixmap = QPixmap(foto_path)
                self.foto_label.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                self.set_placeholder_photo()
        else:
            self.set_placeholder_photo()
        
        self.btn_salvar.setEnabled(True)
        self.btn_cancelar.setEnabled(True)
        self.btn_excluir.setEnabled(True)
    
    def novo_vereador(self):
        """Criar novo vereador"""
        self.current_vereador = None
        self.input_nome.clear()
        self.input_partido.clear()
        self.set_placeholder_photo()
        
        self.btn_salvar.setEnabled(True)
        self.btn_cancelar.setEnabled(True)
        self.btn_excluir.setEnabled(False)
        
        self.input_nome.setFocus()
    
    def salvar_vereador(self):
        """Salvar vereador"""
        nome = self.input_nome.text().strip()
        partido = self.input_partido.text().strip().upper()
        
        if not nome or not partido:
            QMessageBox.warning(self, "Aviso", "Preencha nome e partido!")
            return
        
        # Obter foto atual
        foto = None
        if hasattr(self, 'selected_foto_path'):
            foto = self.selected_foto_path
        elif self.current_vereador and self.current_vereador.get('foto'):
            foto = self.current_vereador['foto']
        
        if self.current_vereador:
            # Editar existente
            self.current_vereador['nome'] = nome
            self.current_vereador['partido'] = partido
            self.current_vereador['foto'] = foto
        else:
            # Criar novo
            novo_id = max([v['id'] for v in self.vereadores], default=0) + 1
            novo_vereador = {
                'id': novo_id,
                'nome': nome,
                'partido': partido,
                'foto': foto
            }
            self.vereadores.append(novo_vereador)
        
        self.save_vereadores()
        self.populate_list()
        self.cancelar_edicao()
        
        QMessageBox.information(self, "Sucesso", "Vereador salvo com sucesso!")
    
    def excluir_vereador(self):
        """Excluir vereador"""
        if not self.current_vereador:
            return
        
        reply = QMessageBox.question(
            self, "Confirmação",
            f"Deseja realmente excluir {self.current_vereador['nome']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.vereadores = [v for v in self.vereadores if v['id'] != self.current_vereador['id']]
            self.save_vereadores()
            self.populate_list()
            self.cancelar_edicao()
            
            QMessageBox.information(self, "Sucesso", "Vereador excluído com sucesso!")
    
    def cancelar_edicao(self):
        """Cancelar edição"""
        self.current_vereador = None
        self.input_nome.clear()
        self.input_partido.clear()
        self.set_placeholder_photo()
        
        self.btn_salvar.setEnabled(False)
        self.btn_cancelar.setEnabled(False)
        self.btn_excluir.setEnabled(False)
        
        if hasattr(self, 'selected_foto_path'):
            delattr(self, 'selected_foto_path')
    
    def selecionar_foto(self):
        """Selecionar foto do vereador"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Foto",
            "",
            "Imagens (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            # Copiar foto para diretório de fotos
            import shutil
            filename = os.path.basename(file_path)
            dest_path = os.path.join(self.fotos_dir, filename)
            
            shutil.copy2(file_path, dest_path)
            
            # Salvar caminho relativo
            self.selected_foto_path = f"fotos/{filename}"
            
            # Exibir foto
            pixmap = QPixmap(dest_path)
            self.foto_label.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    
    def remover_foto(self):
        """Remover foto do vereador"""
        self.set_placeholder_photo()
        if hasattr(self, 'selected_foto_path'):
            delattr(self, 'selected_foto_path')
    
    def set_placeholder_photo(self):
        """Definir foto placeholder"""
        self.foto_label.setText("👤\nSem Foto")
        self.foto_label.setStyleSheet("""
            QLabel {
                border: 2px solid rgba(102, 126, 234, 0.5);
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.05);
                font-size: 48px;
                color: rgba(255, 255, 255, 0.3);
            }
        """)
