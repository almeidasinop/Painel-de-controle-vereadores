# 🏛️ Sistema de Controle de Tribuna Parlamentar

Sistema completo para gestão de tempo de fala em sessões parlamentares, com controle de áudio via hardware Arduino e transmissão ao vivo.

## 📋 Índice

- [Características](#características)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração do Hardware](#configuração-do-hardware)
- [Como Usar](#como-usar)
- [Arquitetura do Sistema](#arquitetura-do-sistema)
- [Troubleshooting](#troubleshooting)

## ✨ Características

### 🖥️ Painel do Presidente (Desktop)
- Interface moderna com PyQt6
- Cronômetro regressivo com tempos pré-definidos (3, 5, 10, 15, 20 min)
- Tempo customizado
- Seleção de vereadores com busca
- Controles: Iniciar, Pausar, Parar
- Status de conexões (Arduino e WebSocket)

### 🎬 Lower Third (Web - OBS/vMix)
- Interface HTML transparente para streaming
- Delay configurável de 10 segundos
- Animações suaves de entrada/saída
- Sincronização em tempo real via WebSocket
- Exibição de foto, nome, partido e cronômetro

### 🔊 Controle de Áudio (Arduino)
- Corte físico de áudio via relé
- Áudio fechado por padrão (segurança)
- Abertura automática ao iniciar cronômetro
- Corte automático ao zerar tempo
- Reconexão automática
- Timeout de segurança

## 📦 Requisitos

### Software
- **Python 3.11+**
- **Arduino IDE** (para upload do firmware)
- **OBS Studio** ou **vMix** (para transmissão)

### Hardware
- **Arduino Uno** ou **Nano**
- **Módulo Relé 5V** de 1 canal
- **Cabo USB** para Arduino
- **Cabos de áudio** (XLR ou P10) para confecção do jumper de corte

### Sistema Operacional
- Windows 10/11
- Linux (testado em Ubuntu 20.04+)
- macOS (experimental)

## 🚀 Instalação

### 1. Clone ou baixe o repositório

```bash
cd "c:\Users\caiqu\github\Painel de controle"
```

### 2. Crie um ambiente virtual Python

```bash
python -m venv venv
```

### 3. Ative o ambiente virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### 4. Instale as dependências

```bash
pip install -r requirements.txt
```

### 5. Configure o Arduino

1. Abra o **Arduino IDE**
2. Abra o arquivo `arduino_relay_control.ino`
3. Selecione a placa: **Tools > Board > Arduino Uno** (ou Nano)
4. Selecione a porta COM: **Tools > Port > COM[X]**
5. Clique em **Upload** (ícone de seta)

## 🔧 Configuração do Hardware

### Esquema de Ligação

```
Arduino Uno/Nano          Módulo Relé 5V
─────────────────         ──────────────
    5V        ────────────    VCC
    GND       ────────────    GND
    D7        ────────────    IN
```

### Montagem do Corte de Áudio

1. **Identifique o cabo de sinal** do microfone (geralmente XLR ou P10)
2. **Corte um dos fios** do sinal (não o terra/shield)
3. **Conecte as pontas** aos terminais NO (Normalmente Aberto) e COM do relé
4. **Teste a continuidade** com multímetro

**Lógica:**
- Relé **DESLIGADO** = Circuito **ABERTO** = Áudio **CORTADO** ✅ (Seguro)
- Relé **LIGADO** = Circuito **FECHADO** = Áudio **ATIVO**

## 🎯 Como Usar

### Iniciar o Sistema

#### Opção 1: Executar tudo junto (Recomendado)

```bash
python main.py
```

Isso irá:
1. Iniciar o servidor Flask-SocketIO em background
2. Conectar ao Arduino automaticamente
3. Abrir o Painel do Presidente

#### Opção 2: Executar separadamente

**Terminal 1 - Servidor:**
```bash
python server.py
```

**Terminal 2 - Interface Desktop:**
```bash
python main.py
```

### Configurar OBS/vMix

1. **Adicione uma fonte Browser** no OBS
2. **URL:** `http://127.0.0.1:5000/`
3. **Largura:** 1920
4. **Altura:** 1080
5. **Marque:** "Shutdown source when not visible" (opcional)
6. **CSS Personalizado (opcional):**
   ```css
   body { background-color: rgba(0, 0, 0, 0); }
   ```

### Fluxo de Trabalho

1. **Selecione um vereador** na lista
2. **Defina o tempo** (preset ou customizado)
3. **Clique em "Iniciar"**
   - ✅ Áudio abre automaticamente
   - ✅ Cronômetro inicia
   - ✅ Lower Third aparece após 10 segundos (delay)
4. **Use "Pausar"** se necessário
5. **Ao terminar ou zerar:**
   - ✅ Áudio corta automaticamente
   - ✅ Lower Third desaparece

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    PAINEL DO PRESIDENTE                     │
│                      (PyQt6 Desktop)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Cronômetro  │  │  Vereadores  │  │   Controles  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         │ WebSocket          │ Serial USB         │
         ▼                    ▼                    │
┌──────────────────┐  ┌──────────────────┐        │
│  Flask-SocketIO  │  │     Arduino      │        │
│     Server       │  │   (Relé 5V)      │        │
│  (Port 5000)     │  │                  │        │
└──────────────────┘  └──────────────────┘        │
         │                    │                    │
         │                    │ Corte Físico       │
         ▼                    ▼                    │
┌──────────────────┐  ┌──────────────────┐        │
│   Lower Third    │  │  Sinal de Áudio  │        │
│  (Browser OBS)   │  │   (Microfone)    │        │
└──────────────────┘  └──────────────────┘        │
                                                   │
                            Monitor 2 (Futuro)  ◄──┘
                            Tela do Plenário
```

## 📁 Estrutura de Arquivos

```
Painel de controle/
├── main.py                      # Interface desktop principal
├── server.py                    # Servidor Flask-SocketIO
├── arduino_controller.py        # Módulo de comunicação serial
├── arduino_relay_control.ino    # Firmware Arduino
├── vereadores.json              # Banco de dados de vereadores
├── requirements.txt             # Dependências Python
├── templates/
│   └── lower_third.html         # Interface web para OBS
└── README.md                    # Este arquivo
```

## 🔍 Troubleshooting

### Arduino não conecta

1. **Verifique a porta COM:**
   ```bash
   python arduino_controller.py
   ```
   Isso listará todas as portas disponíveis.

2. **Instale o driver CH340** (se usando Arduino clone)
   - Windows: [Driver CH340](http://www.wch.cn/downloads/CH341SER_EXE.html)

3. **Verifique permissões** (Linux):
   ```bash
   sudo usermod -a -G dialout $USER
   ```
   Faça logout e login novamente.

### WebSocket não conecta

1. **Verifique se o servidor está rodando:**
   ```bash
   netstat -an | findstr 5000
   ```

2. **Firewall:** Permita conexões na porta 5000

3. **Antivírus:** Adicione exceção para Python

### Lower Third não aparece no OBS

1. **Verifique a URL:** `http://127.0.0.1:5000/`
2. **Limpe o cache** do navegador do OBS
3. **Verifique o console** do navegador (F12)
4. **Teste no navegador** normal primeiro

### Áudio não corta

1. **Verifique as conexões** do relé
2. **Teste o relé** manualmente:
   ```bash
   python arduino_controller.py
   ```
3. **Verifique o LED** do Arduino (deve piscar)
4. **Teste continuidade** com multímetro

## 🎨 Personalização

### Alterar delay da Lower Third

Edite `templates/lower_third.html`:
```javascript
const DELAY_SECONDS = 10; // Altere para o valor desejado
```

### Adicionar vereadores

Edite `vereadores.json`:
```json
{
    "id": 9,
    "nome": "Novo Vereador",
    "partido": "PARTIDO",
    "foto": "caminho/para/foto.jpg"
}
```

### Alterar porta do servidor

Edite `server.py`:
```python
run_server(host='127.0.0.1', port=5000)  # Altere a porta
```

## 📝 Licença

Este projeto é de código aberto e está disponível para uso em câmaras municipais e assembleias legislativas.

## 🤝 Suporte

Para dúvidas ou problemas:
1. Verifique a seção [Troubleshooting](#troubleshooting)
2. Consulte os logs do sistema
3. Teste cada componente separadamente

## 🚀 Roadmap Futuro

- [ ] Tela do Plenário (Monitor 2) - Fullscreen
- [ ] Banco de dados SQLite
- [ ] Histórico de sessões
- [ ] Relatórios de tempo de fala
- [ ] Suporte a múltiplos idiomas
- [ ] Temas personalizáveis
- [ ] API REST completa

---

**Desenvolvido para modernizar o controle de sessões parlamentares** 🏛️
