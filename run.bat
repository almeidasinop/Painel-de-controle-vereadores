@echo off
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  🏛️  Sistema de Controle de Tribuna Parlamentar             ║
echo ║                                                              ║
echo ║  Iniciando Sistema...                                       ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Verificar se ambiente virtual existe
if not exist venv (
    echo ❌ Ambiente virtual não encontrado!
    echo.
    echo Execute primeiro: install.bat
    pause
    exit /b 1
)

REM Ativar ambiente virtual
echo 🔧 Ativando ambiente virtual...
call venv\Scripts\activate.bat
echo.

REM Verificar se servidor já está rodando
echo 🔍 Verificando se servidor já está ativo...
netstat -an | findstr ":5000" >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  Servidor já está rodando na porta 5000
    echo.
    echo Escolha uma opção:
    echo 1. Continuar (pode causar erro)
    echo 2. Cancelar
    echo.
    choice /c 12 /n /m "Opção: "
    if errorlevel 2 exit /b 0
)

REM Iniciar servidor em background
echo 🚀 Iniciando servidor Flask-SocketIO...
start /b python server.py
timeout /t 3 /nobreak >nul
echo ✅ Servidor iniciado
echo.

REM Iniciar interface desktop
echo 🖥️  Iniciando Painel do Presidente...
python main.py

REM Ao fechar a interface, perguntar se deseja manter servidor rodando
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  Interface fechada                                          ║
echo ║                                                              ║
echo ║  Deseja manter o servidor rodando?                          ║
echo ║  (Útil se estiver usando Lower Third no OBS)                ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
choice /c SN /n /m "Manter servidor? (S/N): "
if errorlevel 2 (
    echo 🛑 Encerrando servidor...
    taskkill /f /im python.exe >nul 2>&1
    echo ✅ Servidor encerrado
)

echo.
echo ✅ Sistema finalizado
pause
