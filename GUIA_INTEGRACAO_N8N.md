# 🔌 Guia de Integração N8N - Camões Automóveis

Este guia mostra como integrar o scraper de estoque com o N8N para automatizar o fluxo de atendimento do WhatsApp.

---

## 📋 ARQUITETURA DA SOLUÇÃO

```
┌─────────────────┐
│  Site Camões    │
│   (estoque)     │
└────────┬────────┘
         │
         │ Web Scraping (diário às 02:00)
         ▼
┌─────────────────┐
│ estoque_camoes  │
│    .json        │
└────────┬────────┘
         │
         │ Leitura
         ▼
┌─────────────────┐        ┌──────────────┐
│   API REST      │◄───────│     N8N      │
│  (Flask)        │        │   Workflow   │
└─────────────────┘        └──────┬───────┘
                                  │
                                  │
                                  ▼
                           ┌──────────────┐
                           │  WhatsApp    │
                           │   Cliente    │
                           └──────────────┘
```

---

## 🚀 CONFIGURAÇÃO INICIAL

### 1. Instalar dependências adicionais

```bash
pip install flask
```

### 2. Estrutura de arquivos

```
projeto/
├── scraper_camoes_selenium.py    # Scraper principal
├── agendador_scraper.py           # Agendador diário
├── api_estoque.py                 # API REST para N8N
├── estoque_camoes.json           # Banco de dados (gerado)
└── requirements.txt
```

---

## ⚙️ EXECUTAR A API

### Em desenvolvimento (local)

```bash
python api_estoque.py
```

A API estará disponível em: `http://localhost:5000`

### Em produção (servidor)

Use Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api_estoque:app
```

---

## 📡 ENDPOINTS DISPONÍVEIS

### 1. **GET** `/api/estoque`
Retorna o estoque completo

**Exemplo de resposta:**
```json
{
  "ultima_atualizacao": "2024-01-29 14:30:00",
  "total_veiculos": 45,
  "veiculos": [...]
}
```

### 2. **GET** `/api/estoque/buscar?modelo=corolla`
Busca veículos por modelo

**Parâmetros:**
- `modelo` (obrigatório): Nome ou parte do modelo

**Exemplo:**
```
GET /api/estoque/buscar?modelo=corolla
```

### 3. **GET** `/api/estoque/codigo/{codigo}`
Retorna veículo específico por código

**Exemplo:**
```
GET /api/estoque/codigo/001
```

### 4. **POST** `/api/estoque/filtrar`
Filtra veículos por múltiplos critérios

**Body:**
```json
{
  "marca": "Toyota",
  "modelo": "Corolla",
  "ano_min": 2020
}
```

### 5. **POST** `/api/webhook/n8n` ⭐ RECOMENDADO
Endpoint especial formatado para N8N

**Body:**
```json
{
  "acao": "buscar",
  "modelo": "Corolla"
}
```

**Resposta formatada:**
```json
{
  "sucesso": true,
  "total": 3,
  "veiculos": [
    {
      "codigo": "001",
      "titulo": "Toyota Corolla XEI",
      "descricao": "Ano: 2023/2024 | KM: 15.000 | Câmbio: Automático",
      "preco": "R$ 125.000",
      "foto": "https://...",
      "link": "https://...",
      "mensagem_whatsapp": "🚘 *Toyota Corolla*\n📅 2023/2024\n💰 R$ 125.000..."
    }
  ]
}
```

---

## 🔄 CONFIGURAÇÃO NO N8N

### Workflow Completo: WhatsApp → API → Resposta

#### **1. Nó: Webhook (Trigger)**

```
Nó: Webhook
- Method: POST
- Path: /webhook/whatsapp
```

Este nó recebe mensagens do WhatsApp (via Evolution API ou similar).

---

#### **2. Nó: Function (Extrair modelo do veículo)**

```javascript
// Extrair o modelo da mensagem do usuário
const mensagem = $input.item.json.body.message.text;
const modelo_solicitado = mensagem.toLowerCase();

return {
  json: {
    telefone: $input.item.json.body.key.remoteJid,
    mensagem_original: mensagem,
    modelo: modelo_solicitado
  }
};
```

---

#### **3. Nó: HTTP Request (Buscar no estoque)**

```
Nó: HTTP Request
- Method: POST
- URL: http://SEU_SERVIDOR:5000/api/webhook/n8n
- Body:
  {
    "acao": "buscar",
    "modelo": "{{ $json.modelo }}"
  }
```

---

#### **4. Nó: IF (Verificar se encontrou veículos)**

```
Nó: IF
- Condition: {{ $json.total }} > 0
```

---

#### **5a. Nó: Function (Formatar mensagem - SE ENCONTROU)**

```javascript
const veiculos = $input.item.json.veiculos;
const total = veiculos.length;

// Limitar a 5 veículos para não sobrecarregar
const veiculos_mostrar = veiculos.slice(0, 5);

let mensagem = `Encontrei ${total} opções de *${$('Function').item.json.modelo}* disponíveis:\n\n`;

veiculos_mostrar.forEach((v, index) => {
  mensagem += `🚘 *Código ${v.codigo}* - ${v.titulo}\n`;
  mensagem += `📅 ${v.descricao}\n`;
  mensagem += `💰 ${v.preco}\n`;
  if (v.foto) {
    mensagem += `📸 Foto: ${v.foto}\n`;
  }
  mensagem += `\n`;
});

mensagem += `Qual dessas opções te interessa mais? Me informe o *código* do veículo! 😊`;

return {
  json: {
    telefone: $('Webhook').item.json.body.key.remoteJid,
    mensagem: mensagem,
    veiculos: veiculos_mostrar
  }
};
```

---

#### **5b. Nó: Set (Mensagem - SE NÃO ENCONTROU)**

```
Nó: Set
- mensagem: "Desculpe, não encontrei esse modelo no momento. 😔\n\nGostaria de ver outras opções disponíveis?"
- telefone: {{ $('Webhook').item.json.body.key.remoteJid }}
```

---

#### **6. Nó: HTTP Request (Enviar mensagem WhatsApp)**

```
Nó: HTTP Request (Evolution API)
- Method: POST
- URL: http://SEU_EVOLUTION_API/message/sendText/INSTANCE
- Headers:
  - apikey: SUA_API_KEY
- Body:
  {
    "number": "{{ $json.telefone }}",
    "text": "{{ $json.mensagem }}"
  }
```

---

## 🎯 WORKFLOW COMPLETO DE EXEMPLO

```
┌───────────┐
│  Webhook  │ (Recebe msg WhatsApp)
└─────┬─────┘
      │
      ▼
┌───────────┐
│ Function  │ (Extrai modelo)
└─────┬─────┘
      │
      ▼
┌───────────┐
│HTTP Request│ (Busca API)
└─────┬─────┘
      │
      ▼
┌───────────┐
│    IF     │ (Encontrou?)
└──┬────┬───┘
   │    │
  SIM  NÃO
   │    │
   ▼    ▼
┌──────┐ ┌──────┐
│Format│ │ Set  │
│Msg   │ │"Não  │
│      │ │Found"│
└───┬──┘ └───┬──┘
    │        │
    └────┬───┘
         ▼
   ┌───────────┐
   │Send WhatsApp│
   └───────────┘
```

---

## 🔧 VARIÁVEIS DE AMBIENTE (PRODUÇÃO)

Crie um arquivo `.env`:

```bash
API_HOST=0.0.0.0
API_PORT=5000
ESTOQUE_FILE=estoque_camoes.json
EVOLUTION_API_URL=http://seu-servidor:8080
EVOLUTION_API_KEY=sua-chave-api
```

---

## 📊 FUNÇÃO PARA BUSCAR VEÍCULO POR CÓDIGO

Adicione este nó após o usuário informar o código:

```javascript
// Function: Buscar veículo por código
const codigo = $input.item.json.body.message.text.trim();

const response = await $http.request({
  method: 'GET',
  url: `http://SEU_SERVIDOR:5000/api/estoque/codigo/${codigo}`
});

const veiculo = response.json;

if (veiculo && !veiculo.erro) {
  // Formatar mensagem completa do veículo
  const mensagem = `
✅ *Você escolheu:*

🚗 *${veiculo.marca} ${veiculo.modelo} ${veiculo.versao}*
📅 Ano: ${veiculo.ano}
💰 Preço: ${veiculo.preco}
📍 KM: ${veiculo.km}
⚙️ Câmbio: ${veiculo.cambio}
⛽ Combustível: ${veiculo.combustivel}
🎨 Cor: ${veiculo.cor}

Como pretende realizar o pagamento?

1️⃣ À vista
2️⃣ Financiamento
3️⃣ Troca (com ou sem troco)
  `.trim();
  
  return {
    json: {
      telefone: $('Webhook').item.json.body.key.remoteJid,
      mensagem: mensagem,
      veiculo_escolhido: veiculo
    }
  };
} else {
  return {
    json: {
      telefone: $('Webhook').item.json.body.key.remoteJid,
      mensagem: "Código não encontrado. Por favor, informe um código válido."
    }
  };
}
```

---

## 🔐 SEGURANÇA

### Adicionar autenticação à API

```python
# No arquivo api_estoque.py
from functools import wraps

API_KEY = "sua-chave-secreta-aqui"

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != API_KEY:
            return jsonify({'erro': 'Acesso negado'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Aplicar em cada rota:
@app.route('/api/estoque', methods=['GET'])
@require_api_key
def obter_estoque_completo():
    ...
```

No N8N, adicione o header:
```
X-API-Key: sua-chave-secreta-aqui
```

---

## 📞 SUPORTE E DEBUG

### Logs da API

```bash
# Ver logs em tempo real
tail -f /var/log/api_estoque.log
```

### Testar endpoints manualmente

```bash
# Buscar estoque
curl http://localhost:5000/api/estoque

# Buscar por modelo
curl "http://localhost:5000/api/estoque/buscar?modelo=corolla"

# Webhook N8N
curl -X POST http://localhost:5000/api/webhook/n8n \
  -H "Content-Type: application/json" \
  -d '{"acao":"buscar","modelo":"corolla"}'
```

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

- [ ] Scraper rodando e salvando estoque em JSON
- [ ] API Flask rodando e respondendo nos endpoints
- [ ] N8N conectado à API
- [ ] Webhook do WhatsApp configurado
- [ ] Workflow testado end-to-end
- [ ] Agendamento diário funcionando
- [ ] Logs e monitoramento configurados

---

## 🎓 PRÓXIMOS PASSOS

1. Configurar cache Redis para melhor performance
2. Adicionar imagens dos veículos nas mensagens
3. Implementar sistema de favoritos
4. Analytics de veículos mais procurados
5. Notificações quando novo veículo entrar no estoque
