@echo off
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  🏛️  Sistema de Controle de Tribuna Parlamentar             ║
echo ║                                                              ║
echo ║  Script de Instalação Automática                            ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python não encontrado!
    echo.
    echo Por favor, instale Python 3.11+ de: https://www.python.org/downloads/
    echo Certifique-se de marcar "Add Python to PATH" durante a instalação.
    pause
    exit /b 1
)

echo ✅ Python encontrado
python --version
echo.

REM Criar ambiente virtual
echo 📦 Criando ambiente virtual...
if exist venv (
    echo ⚠️  Ambiente virtual já existe. Removendo...
    rmdir /s /q venv
)

python -m venv venv
if %errorlevel% neq 0 (
    echo ❌ Erro ao criar ambiente virtual
    pause
    exit /b 1
)
echo ✅ Ambiente virtual criado
echo.

REM Ativar ambiente virtual
echo 🔧 Ativando ambiente virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ Erro ao ativar ambiente virtual
    pause
    exit /b 1
)
echo ✅ Ambiente virtual ativado
echo.

REM Atualizar pip
echo 📥 Atualizando pip...
python -m pip install --upgrade pip
echo.

REM Instalar dependências
echo 📥 Instalando dependências...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Erro ao instalar dependências
    pause
    exit /b 1
)
echo ✅ Dependências instaladas
echo.

REM Verificar instalação
echo 🔍 Verificando instalação...
python -c "import PyQt6; import flask; import serial; print('✅ Todas as bibliotecas importadas com sucesso')"
if %errorlevel% neq 0 (
    echo ❌ Erro na verificação das bibliotecas
    pause
    exit /b 1
)
echo.

REM Criar diretório de templates se não existir
if not exist templates mkdir templates
echo ✅ Diretório templates verificado
echo.

echo ╔══════════════════════════════════════════════════════════════╗
echo ║  ✅ Instalação Concluída com Sucesso!                        ║
echo ║                                                              ║
echo ║  Próximos passos:                                           ║
echo ║  1. Configure o Arduino (veja README.md)                    ║
echo ║  2. Execute: run.bat                                        ║
echo ║                                                              ║
echo ║  Para ativar o ambiente virtual manualmente:                ║
echo ║  venv\Scripts\activate                                      ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

pause
