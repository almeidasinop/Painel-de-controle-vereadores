import logging
import os
import sys
from datetime import datetime

class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass

def setup_logger(process_name="app"):
    """
    Configura o sistema de log para salvar em arquivo na pasta `logs`.
    Redireciona stdout e stderr para o log.
    """
    # 1. Criar diretório de logs no AppData (Escrita permitida)
    app_data = os.getenv('LOCALAPPDATA')
    if not app_data:
        app_data = os.path.expanduser('~')
        
    logs_dir = os.path.join(app_data, 'PainelControleTribuna', 'logs')
    
    if not os.path.exists(logs_dir):
        try:
            os.makedirs(logs_dir, exist_ok=True)
        except OSError as e:
            print(f"Erro ao criar diretório de logs: {e}")
            return

    # 1.5 Limpar logs antigos (Manter apenas ultimas 20 sessões ~ 40 arquivos)
    try:
        files = [os.path.join(logs_dir, f) for f in os.listdir(logs_dir) if f.startswith('log_') and f.endswith('.txt')]
        if len(files) > 40:
            # Ordenar por data de modificação (mais antigo primeiro)
            files.sort(key=os.path.getmtime)
            
            # Deletar excedentes
            files_to_delete = files[:-40]
            for f in files_to_delete:
                try:
                    os.remove(f)
                    # logging ainda não está configurado, usar print
                    # print(f"Log antigo removido: {f}") 
                except OSError:
                    pass
    except Exception:
        pass

    # 2. Definir nome do arquivo: log_YYYY-MM-DD_HH-MM-SS_nome.log
    # Tenta usar ID compartilhado da sessão (passado pelo run.bat)
    session_id = os.environ.get('PAINEL_SESSION_ID')
    if not session_id:
        session_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
    log_filename = f"log_{session_id}_{process_name}.txt"
    log_path = os.path.join(logs_dir, log_filename)

    # 3. Configurar Formato
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 4. Configurar Handler de Arquivo
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG) # Capturar tudo no arquivo

    # 5. Configurar Handler de Console (para continuar vendo no terminal)
    # Importante: Usamos sys.__stdout__ para garantir que vamos para o terminal real
    # e não para o nosso redirecionador (evitando loop infinito)
    console_handler = logging.StreamHandler(sys.__stdout__)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO) # No console, apenas Info pra cima

    # 6. Configurar Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # 7. Redirecionar print (stdout) e erros (stderr) para o Logger
    # Isso garante que 'print()' e crashs apareçam no arquivo de log
    sys.stdout = StreamToLogger(logging.getLogger('STDOUT'), logging.INFO)
    sys.stderr = StreamToLogger(logging.getLogger('STDERR'), logging.ERROR)
    
    # 8. Hook para Exceções Não Tratadas (Crashes)
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logging.critical("CRITICAL ERROR: Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Tentar escrever no arquivo diretamente em caso de falha grave do logging
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"\nCRITICAL CRASH: {exc_value}\n")
        except:
            pass

    sys.excepthook = handle_exception

    logging.info(f"=== Logger Iniciado: {process_name} ===")
    logging.info(f"Arquivo de Log: {log_path}")
    
    return log_path
