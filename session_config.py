"""
Configuração de Sessão - Logo e Número da Sessão
"""

import json
import os

class SessionConfig:
    """Gerenciador de configuração da sessão"""
    
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), 'session_config.json')
        self.load_config()
    
    def load_config(self):
        """Carregar configuração"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.logo_path = data.get('logo_path', None)
                # Migração: Tenta ler session_name, senão session_number
                self.session_name = data.get('session_name', data.get('session_number', ''))
                self.active_list = data.get('active_list', 'presets/padrao.json')
                
                # Cores
                self.colors = data.get('colors', {
                    'primary': '#1e4586',
                    'secondary': '#067b42',
                    'background': '#000000'
                })
                
        except FileNotFoundError:
            self.logo_path = None
            self.session_name = ''
            self.active_list = 'presets/padrao.json'
            self.colors = {
                'primary': '#1e4586',
                'secondary': '#067b42',
                'background': '#000000'
            }
            self.save_config()
    
    def save_config(self):
        """Salvar configuração"""
        data = {
            'logo_path': self.logo_path,
            'session_name': self.session_name, # Salva como name
            'active_list': self.active_list,
            'colors': self.colors
        }
        print(f"DEBUG: Gravando JSON session_name='{self.session_name}'")
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    def set_colors(self, primary, secondary, background=None):
        """Definir cores do tema"""
        self.colors['primary'] = primary
        self.colors['secondary'] = secondary
        if background:
            self.colors['background'] = background
        self.save_config()
        
    def get_colors(self):
        """Obter cores"""
        return self.colors
    
    def set_logo(self, logo_path):
        """Definir logo"""
        self.logo_path = logo_path
        self.save_config()
    
    def set_session_name(self, name):
        """Definir nome da sessão"""
        self.session_name = name
        self.save_config()
        
    def get_session_name(self):
        """Obter nome da sessão"""
        return self.session_name
    
    # Aliases de compatibilidade
    def set_session_number(self, number):
        self.set_session_name(number)
        
    def get_session_number(self):
        return self.get_session_name()
    
    def set_active_list(self, list_path):
        """Definir lista de vereadores ativa"""
        self.active_list = list_path
        self.save_config()
        
    def get_logo(self):
        """Obter logo"""
        return self.logo_path
        
    def get_active_list(self):
        """Obter caminho da lista ativa"""
        if not self.active_list:
            return 'presets/padrao.json'
        return self.active_list
