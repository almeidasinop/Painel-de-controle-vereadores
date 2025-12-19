# 🔒 Guia de Montagem - Sistema Fail-Safe de Áudio

## ⚠️ IMPORTANTE: Lógica Fail-Safe

Este sistema utiliza **lógica inversa** para garantir que o áudio permaneça **ATIVO** em caso de falha do sistema.

### 🎯 Objetivo da Segurança

**Problema:** Se o sistema travar, desligar ou o cabo USB desconectar durante uma sessão, o áudio NÃO pode ser cortado.

**Solução:** Usar contatos **NC (Normalmente Fechado)** do relé.

---

## 📋 Lista de Materiais (BOM)

| Item | Quantidade | Especificação |
|------|------------|---------------|
| Arduino Uno/Nano | 1 | Microcontrolador |
| Módulo Relé 5V | 1 | **2 Canais** |
| Cabo USB | 1 | Para Arduino |
| Cabos de Áudio | 2 | XLR ou P10 macho |
| Conectores Fêmea | 2 | XLR ou P10 fêmea |
| Caixa Plástica | 1 | Proteção do circuito |
| Cabos Jumper | 3 | Conexão Arduino-Relé |

---

## 🔌 Esquema de Ligação

### 1. Conexão Arduino → Relé

```
Arduino Uno/Nano          Módulo Relé 2 Canais
─────────────────         ────────────────────
    5V        ────────────    VCC
    GND       ────────────    GND
    D7        ────────────    IN1 (Canal 1)
    D8        ────────────    IN2 (Canal 2)
```

### 2. Conexão de Áudio (CRÍTICO - Fail-Safe)

**⚠️ ATENÇÃO:** Use os contatos **NC (Normalmente Fechado)** e **COM (Comum)**

#### Canal 1 (Microfone 1):
```
[Microfone 1] ──┬── Sinal+ ──┐
                │             │
                └── GND ──────┼─────→ [Mesa de Som Canal 1]
                              │
                         ┌────┴────┐
                         │  Relé 1 │
                         │ NC  COM │
                         └─────────┘
                              │
                         [Arduino D7]
```

#### Canal 2 (Microfone 2):
```
[Microfone 2] ──┬── Sinal+ ──┐
                │             │
                └── GND ──────┼─────→ [Mesa de Som Canal 2]
                              │
                         ┌────┴────┐
                         │  Relé 2 │
                         │ NC  COM │
                         └─────────┘
                              │
                         [Arduino D8]
```

### 3. Identificação dos Terminais do Relé

Cada canal do relé tem 3 terminais:

```
┌─────────────────────┐
│  NO   COM   NC      │  ← Canal 1
│  ●     ●    ●       │
│                     │
│  NO   COM   NC      │  ← Canal 2
│  ●     ●    ●       │
└─────────────────────┘

NO  = Normalmente Aberto (NÃO USAR)
COM = Comum (Sinal de entrada)
NC  = Normalmente Fechado (USAR - Fail-Safe)
```

---

## 🔧 Montagem Passo a Passo

### Passo 1: Preparar Cabos de Áudio

Para cada microfone (2 no total):

1. **Corte** um cabo de áudio (XLR ou P10) no meio
2. **Identifique** os fios:
   - Sinal+ (geralmente branco ou vermelho)
   - GND/Shield (geralmente preto ou malha)
3. **Descasque** as pontas (~5mm)
4. **Estanhe** as pontas (opcional, mas recomendado)

### Passo 2: Conectar ao Relé

**Canal 1 (Microfone 1):**
1. Conecte o **Sinal+ do microfone** ao terminal **COM** do Canal 1
2. Conecte o **Sinal+ para mesa** ao terminal **NC** do Canal 1
3. Una os **GND** diretamente (não passa pelo relé)

**Canal 2 (Microfone 2):**
1. Conecte o **Sinal+ do microfone** ao terminal **COM** do Canal 2
2. Conecte o **Sinal+ para mesa** ao terminal **NC** do Canal 2
3. Una os **GND** diretamente (não passa pelo relé)

### Passo 3: Conectar Arduino

1. Conecte **Arduino 5V** → **Relé VCC**
2. Conecte **Arduino GND** → **Relé GND**
3. Conecte **Arduino D7** → **Relé IN1** (Canal 1)
4. Conecte **Arduino D8** → **Relé IN2** (Canal 2)

### Passo 4: Montar na Caixa

1. Fixe o Arduino e o relé na caixa plástica
2. Faça furos para:
   - Cabo USB (Arduino)
   - 2 cabos de entrada (microfones)
   - 2 cabos de saída (mesa de som)
3. Use abraçadeiras para organizar os cabos

---

## ⚡ Lógica de Funcionamento

### Estado 1: Sistema DESLIGADO (Fail-Safe)
```
Arduino: SEM ENERGIA
Relé: DESLIGADO (estado natural)
Contato NC: FECHADO
Resultado: ✅ SOM ATIVO (SEGURO)
```

### Estado 2: Sistema LIGADO - Em Repouso
```
Arduino: ENERGIZADO
Relé: LIGADO (comando do software)
Contato NC: ABERTO
Resultado: 🔇 SOM CORTADO (aguardando)
```

### Estado 3: Vereador Falando
```
Arduino: ENERGIZADO
Relé: DESLIGADO (comando do software)
Contato NC: FECHADO
Resultado: ✅ SOM ATIVO
```

### Estado 4: Falha do Sistema
```
Arduino: PERDE ENERGIA (USB desconectado/travou)
Relé: DESLIGADO (perde energia)
Contato NC: FECHA AUTOMATICAMENTE
Resultado: ✅ SOM ATIVO (FAIL-SAFE ATIVO!)
```

---

## 🧪 Testes de Segurança

### Teste 1: Fail-Safe Básico
1. **Monte o circuito** conforme diagrama
2. **NÃO conecte** o Arduino ao computador
3. **Teste com multímetro**: Deve haver continuidade entre COM e NC
4. **Resultado esperado:** ✅ Circuito fechado = Som passaria

### Teste 2: Sistema Ligado
1. **Conecte** Arduino ao computador
2. **Execute** o software Python
3. **Verifique** LED do Arduino: Deve acender
4. **Teste com multímetro**: NÃO deve haver continuidade entre COM e NC
5. **Resultado esperado:** ✅ Circuito aberto = Som cortado

### Teste 3: Iniciar Fala
1. **Com sistema rodando**, selecione vereador
2. **Clique** em "Iniciar"
3. **Verifique** LED do Arduino: Deve apagar
4. **Teste com multímetro**: Deve haver continuidade entre COM e NC
5. **Resultado esperado:** ✅ Circuito fechado = Som ativo

### Teste 4: Fail-Safe em Ação
1. **Com vereador falando** (som ativo)
2. **Desconecte** cabo USB do Arduino
3. **Teste com multímetro**: Deve MANTER continuidade
4. **Resultado esperado:** ✅ Som continua ativo (FAIL-SAFE!)

### Teste 5: Fechar Sistema
1. **Inicie** uma fala
2. **Feche** o software Python
3. **Aguarde** 1 segundo
4. **Teste com multímetro**: Deve haver continuidade
5. **Resultado esperado:** ✅ Som liberado ao fechar

---

## 🔍 Troubleshooting

### Problema: Som sempre cortado
**Causa:** Usando terminal NO ao invés de NC
**Solução:** Mova o cabo do terminal NO para o NC

### Problema: Som sempre ativo
**Causa:** Relé com lógica invertida ou pinos trocados
**Solução:** 
1. Verifique se IN1 está em D7 e IN2 em D8
2. Teste trocar HIGH por LOW no código (alguns relés são invertidos)

### Problema: Só um canal funciona
**Causa:** Conexão solta ou relé defeituoso
**Solução:**
1. Verifique todas as conexões
2. Teste cada canal separadamente
3. Substitua módulo relé se necessário

### Problema: Relé não aciona
**Causa:** Alimentação insuficiente
**Solução:**
1. Use fonte externa 5V para o relé (não do Arduino)
2. Conecte GND da fonte com GND do Arduino

---

## 📊 Diagrama Completo

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA FAIL-SAFE                        │
└─────────────────────────────────────────────────────────────┘

[Microfone 1] ──────┐                    ┌────→ [Mesa Canal 1]
                    │                    │
                    ├─ GND ──────────────┤
                    │                    │
                    └─ Sinal+ ──┐        │
                                │        │
                           ┌────▼────────▼───┐
                           │  Relé Canal 1   │
                           │  COM ←→ NC      │
                           └────┬────────────┘
                                │
                           [Arduino D7]


[Microfone 2] ──────┐                    ┌────→ [Mesa Canal 2]
                    │                    │
                    ├─ GND ──────────────┤
                    │                    │
                    └─ Sinal+ ──┐        │
                                │        │
                           ┌────▼────────▼───┐
                           │  Relé Canal 2   │
                           │  COM ←→ NC      │
                           └────┬────────────┘
                                │
                           [Arduino D8]


                           ┌─────────────┐
                           │  Arduino    │
                           │  Uno/Nano   │
                           │             │
                           │  D7 ────────┼──→ Relé IN1
                           │  D8 ────────┼──→ Relé IN2
                           │  5V ────────┼──→ Relé VCC
                           │  GND ───────┼──→ Relé GND
                           │             │
                           │  USB ───────┼──→ Computador
                           └─────────────┘
```

---

## ✅ Checklist Final

Antes de usar em produção:

- [ ] Relé de 2 canais instalado
- [ ] Conexões usando terminais NC (Normalmente Fechado)
- [ ] Teste de continuidade COM-NC sem energia: OK
- [ ] Teste com multímetro em todos os estados: OK
- [ ] Teste de Fail-Safe (desconectar USB): Som continua
- [ ] Firmware Arduino carregado
- [ ] Software Python testado
- [ ] Cabos organizados e protegidos
- [ ] Caixa fechada e identificada
- [ ] Documentação anexada à caixa

---

## 🚨 Avisos de Segurança

1. **NUNCA** use os terminais NO (Normalmente Aberto) - isso inverte a lógica de segurança
2. **SEMPRE** teste o Fail-Safe antes de usar em sessão real
3. **IDENTIFIQUE** claramente os cabos (Mic 1, Mic 2, Mesa 1, Mesa 2)
4. **PROTEJA** o circuito em caixa plástica (evitar curtos)
5. **DOCUMENTE** qualquer modificação no sistema

---

## 📞 Suporte

Em caso de dúvidas:
1. Consulte este guia
2. Teste com multímetro
3. Verifique os LEDs do Arduino e Relé
4. Consulte o Serial Monitor (9600 baud)

---

**Sistema desenvolvido com foco em SEGURANÇA e CONFIABILIDADE** 🔒
