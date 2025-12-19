"""
Sistema de Controle de Tribuna Parlamentar
Servidor Flask-SocketIO para comunicação com Lower Third Web
"""

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import os
from datetime import datetime

# Configuração do Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'tribuna-parlamentar-2024'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Estado global do sistema
system_state = {
    'timer': {
        'total_seconds': 0,
        'remaining_seconds': 0,
        'is_running': False,
        'is_paused': False
    },
    'speaker': None,
    'audio_muted': True,  # Áudio fechado por padrão
    'delay_seconds': 10,  # Delay para Lower Third
    'connections': {
        'arduino': False,
        'clients': 0
    }
}

def load_vereadores():
    """Carrega lista de vereadores do JSON"""
    json_path = os.path.join(os.path.dirname(__file__), 'vereadores.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

@app.route('/')
def index():
    """Página principal - Lower Third"""
    return render_template('lower_third.html')

@app.route('/api/vereadores')
def get_vereadores():
    """API para obter lista de vereadores"""
    return jsonify(load_vereadores())

@app.route('/api/state')
def get_state():
    """API para obter estado atual do sistema"""
    return jsonify(system_state)

@app.route('/api/config')
def get_config():
    """API para obter configurações"""
    return jsonify({
        'delay_seconds': system_state['delay_seconds']
    })

# ===================================
# WebSocket Events
# ===================================

@socketio.on('connect')
def handle_connect():
    """Cliente conectado"""
    system_state['connections']['clients'] += 1
    print(f"✅ Cliente conectado. Total: {system_state['connections']['clients']}")
    emit('state_update', system_state)

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado"""
    system_state['connections']['clients'] -= 1
    print(f"❌ Cliente desconectado. Total: {system_state['connections']['clients']}")

@socketio.on('timer_start')
def handle_timer_start(data):
    """Iniciar cronômetro"""
    system_state['timer']['is_running'] = True
    system_state['timer']['is_paused'] = False
    system_state['timer']['remaining_seconds'] = data.get('remaining_seconds', 0)
    system_state['timer']['total_seconds'] = data.get('total_seconds', 0)
    
    print(f"⏱️ Timer iniciado: {data.get('remaining_seconds')}s")
    emit('timer_start', system_state['timer'], broadcast=True)

@socketio.on('timer_pause')
def handle_timer_pause(data):
    """Pausar cronômetro"""
    system_state['timer']['is_running'] = False
    system_state['timer']['is_paused'] = True
    system_state['timer']['remaining_seconds'] = data.get('remaining_seconds', 0)
    
    print(f"⏸️ Timer pausado: {data.get('remaining_seconds')}s")
    emit('timer_pause', system_state['timer'], broadcast=True)

@socketio.on('timer_stop')
def handle_timer_stop():
    """Parar cronômetro"""
    system_state['timer']['is_running'] = False
    system_state['timer']['is_paused'] = False
    system_state['timer']['remaining_seconds'] = system_state['timer']['total_seconds']
    
    print("⏹️ Timer parado")
    emit('timer_stop', system_state['timer'], broadcast=True)

@socketio.on('timer_update')
def handle_timer_update(data):
    """Atualizar tempo restante"""
    system_state['timer']['remaining_seconds'] = data.get('remaining_seconds', 0)
    emit('timer_update', system_state['timer'], broadcast=True)

@socketio.on('speaker_selected')
def handle_speaker_selected(data):
    """Vereador selecionado"""
    system_state['speaker'] = data.get('speaker')
    
    print(f"🎤 Orador selecionado: {data.get('speaker', {}).get('nome', 'N/A')}")
    emit('speaker_selected', system_state['speaker'], broadcast=True)

@socketio.on('speaker_cleared')
def handle_speaker_cleared():
    """Limpar orador"""
    system_state['speaker'] = None
    
    print("🔇 Orador removido")
    emit('speaker_cleared', broadcast=True)

@socketio.on('audio_toggle')
def handle_audio_toggle(data):
    """Toggle de áudio"""
    system_state['audio_muted'] = data.get('muted', True)
    
    status = "cortado" if system_state['audio_muted'] else "ativo"
    print(f"🔊 Áudio {status}")
    emit('audio_toggle', {'muted': system_state['audio_muted']}, broadcast=True)

@socketio.on('arduino_status')
def handle_arduino_status(data):
    """Status da conexão Arduino"""
    system_state['connections']['arduino'] = data.get('connected', False)
    
    status = "conectado" if system_state['connections']['arduino'] else "desconectado"
    print(f"🔌 Arduino {status}")
    emit('arduino_status', {'connected': system_state['connections']['arduino']}, broadcast=True)

@socketio.on('request_state')
def handle_request_state():
    """Cliente solicitando estado atual"""
    emit('state_update', system_state)

def run_server(host='127.0.0.1', port=5000, debug=False):
    """Iniciar servidor Flask-SocketIO"""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🏛️  Sistema de Controle de Tribuna Parlamentar             ║
║                                                              ║
║  Servidor Flask-SocketIO iniciado                           ║
║  URL: http://{host}:{port}                            ║
║  Lower Third: http://{host}:{port}/                   ║
║                                                              ║
║  Pressione Ctrl+C para encerrar                             ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    run_server(debug=True)
