"""
Módulo de Comunicação Serial com Arduino
Controle de Relé para Corte de Áudio
"""

import serial
import serial.tools.list_ports
import threading
import time
from typing import Optional, Callable

class ArduinoController:
    """Controlador de comunicação com Arduino via Serial"""
    
    def __init__(self, baudrate: int = 9600, timeout: float = 1.0):
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_port: Optional[serial.Serial] = None
        self.port_name: Optional[str] = None
        self.is_connected = False
        self.auto_reconnect = True
        self.reconnect_thread: Optional[threading.Thread] = None
        self.on_connection_change: Optional[Callable] = None
        
    def list_available_ports(self):
        """Lista todas as portas COM disponíveis"""
        ports = serial.tools.list_ports.comports()
        available_ports = []
        
        for port in ports:
            available_ports.append({
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid
            })
        
        return available_ports
    
    def connect(self, port_name: str = None) -> bool:
        """
        Conecta ao Arduino
        Se port_name não for especificado, tenta detectar automaticamente
        """
        try:
            if port_name is None:
                # Tentar detectar Arduino automaticamente
                ports = self.list_available_ports()
                for port in ports:
                    if 'Arduino' in port['description'] or 'CH340' in port['description']:
                        port_name = port['device']
                        break
                
                if port_name is None and ports:
                    # Se não encontrou Arduino, usa a primeira porta disponível
                    port_name = ports[0]['device']
            
            if port_name is None:
                print("❌ Nenhuma porta serial disponível")
                return False
            
            # Fechar conexão anterior se existir
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            
            # Abrir nova conexão
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=1.0  # Evitar travamento na escrita
            )
            
            # Aguardar inicialização do Arduino
            time.sleep(2)
            
            self.port_name = port_name
            self.is_connected = True
            
            # Por segurança, cortar áudio ao conectar (sistema em repouso)
            # O áudio só será liberado quando o usuário clicar em "Iniciar"
            self.cut_audio()
            
            print(f"✅ Arduino conectado em {port_name}")
            print("🔒 Áudio cortado (sistema em repouso - Fail-Safe)")
            
            if self.on_connection_change:
                self.on_connection_change(True)
            
            return True
            
        except serial.SerialException as e:
            print(f"❌ Erro ao conectar Arduino: {e}")
            self.is_connected = False
            
            if self.on_connection_change:
                self.on_connection_change(False)
            
            return False
    
    def disconnect(self):
        """Desconecta do Arduino"""
        self.auto_reconnect = False
        
        if self.serial_port and self.serial_port.is_open:
            # FAIL-SAFE: Liberar áudio antes de desconectar
            # Isso garante que ao fechar o sistema, o som fique ativo
            print("🔓 Liberando áudio (Fail-Safe - sistema desligando)...")
            self.open_audio()
            time.sleep(0.2)  # Aguardar comando ser processado
            
            self.serial_port.close()
            self.is_connected = False
            print(f"🔌 Arduino desconectado de {self.port_name}")
            print("✅ Áudio liberado (Fail-Safe ativo)")
            
            if self.on_connection_change:
                self.on_connection_change(False)
    
    def send_command(self, command: str) -> bool:
        """
        Envia comando para o Arduino
        '1' = Abrir áudio
        '0' = Cortar áudio
        """
        if not self.is_connected or not self.serial_port:
            print("⚠️ Arduino não conectado")
            return False
        
        try:
            self.serial_port.write(command.encode())
            self.serial_port.flush()
            return True
            
        except serial.SerialException as e:
            print(f"❌ Erro ao enviar comando: {e}")
            self.is_connected = False
            
            if self.on_connection_change:
                self.on_connection_change(False)
            
            # Tentar reconectar
            if self.auto_reconnect:
                self._start_reconnect_thread()
            
            return False
    
    def open_audio(self) -> bool:
        """Abre o áudio (relé ativo)"""
        success = self.send_command('1')
        if success:
            print("🔊 Áudio ABERTO")
        return success
    
    def cut_audio(self) -> bool:
        """Corta o áudio (relé desativo)"""
        success = self.send_command('0')
        if success:
            print("🔇 Áudio CORTADO")
        return success
    
    def _start_reconnect_thread(self):
        """Inicia thread de reconexão automática"""
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            return
        
        self.reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        self.reconnect_thread.start()
    
    def _reconnect_loop(self):
        """Loop de reconexão automática"""
        print("🔄 Tentando reconectar ao Arduino...")
        
        while self.auto_reconnect and not self.is_connected:
            if self.connect(self.port_name):
                print("✅ Reconexão bem-sucedida!")
                break
            
            time.sleep(3)  # Aguardar 3 segundos antes de tentar novamente
    
    def check_connection(self) -> bool:
        """Verifica se a conexão está ativa"""
        if not self.serial_port or not self.serial_port.is_open:
            self.is_connected = False
            return False
        
        try:
            # Tentar ler status (timeout curto)
            self.serial_port.in_waiting
            return True
            
        except serial.SerialException:
            self.is_connected = False
            
            if self.on_connection_change:
                self.on_connection_change(False)
            
            if self.auto_reconnect:
                self._start_reconnect_thread()
            
            return False
    
    def __del__(self):
        """Destrutor - garante que o áudio seja LIBERADO ao encerrar (Fail-Safe)"""
        if self.serial_port and self.serial_port.is_open:
            self.open_audio()  # FAIL-SAFE: Liberar áudio
            time.sleep(0.1)
            self.serial_port.close()


# Exemplo de uso
if __name__ == '__main__':
    print("=== Teste do Controlador Arduino ===\n")
    
    controller = ArduinoController()
    
    # Listar portas disponíveis
    print("Portas disponíveis:")
    ports = controller.list_available_ports()
    for i, port in enumerate(ports, 1):
        print(f"  {i}. {port['device']} - {port['description']}")
    
    print()
    
    # Conectar
    if controller.connect():
        print("\n✅ Teste de conexão bem-sucedido!")
        
        # Teste de comandos
        print("\n--- Teste de Comandos ---")
        print("Abrindo áudio em 2 segundos...")
        time.sleep(2)
        controller.open_audio()
        
        print("Cortando áudio em 3 segundos...")
        time.sleep(3)
        controller.cut_audio()
        
        print("\n✅ Teste concluído!")
        controller.disconnect()
    else:
        print("\n❌ Falha ao conectar ao Arduino")
        print("Verifique se o Arduino está conectado e o driver está instalado.")
