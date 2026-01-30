# 🚗 Sistema de Scraping Camões Automóveis - VERSÃO FINAL

Sistema completo e otimizado para captura automática do estoque de veículos.

---

## ✨ NOVIDADES DESTA VERSÃO

✅ **Seletores já configurados** para a estrutura real do site  
✅ **Múltiplos métodos de extração** (tenta vários seletores até funcionar)  
✅ **Tratamento robusto de erros** (não para se um campo estiver faltando)  
✅ **2 versões disponíveis**: Selenium (completo) e BeautifulSoup (rápido)  
✅ **Debug automático** (salva HTML e screenshots em caso de erro)  

---

## 📦 ARQUIVOS PRINCIPAIS

### 🎯 Para Uso em Produção:

1. **`scraper_camoes_selenium.py`** ⭐ RECOMENDADO
   - Versão Selenium (funciona com JavaScript)
   - Extrai **Galeria completa** (todas as fotos)
   - Extrai **Cor do veículo** (página interna)
   - Mais robusto e completo

2. **`scraper_camoes_beautifulsoup_FINAL.py`**
   - Versão BeautifulSoup (mais rápida)
   - Use se o site NÃO carrega dados via JS
   - Consome menos recursos

3. **`agendador_scraper.py`**
   - Automatiza execução diária
   - Configurado para rodar às 02:00

4. **`api_estoque.py`**
   - API REST para integração com N8N
   - 6 endpoints prontos

### 📚 Arquivos de Apoio:

- `teste_seletores.py` - Script para testar seletores
- `test_sistema.py` - Testes automatizados
- `GUIA_*.md` - Documentação completa

---

## 🚀 INSTALAÇÃO RÁPIDA

### 1. Instalar dependências:

```bash
pip install -r requirements.txt
```

### 2. Instalar Chrome Driver (para Selenium):

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install chromium-chromedriver
```

**macOS:**
```bash
brew install chromedriver
```

**Windows:**
- Baixe de: https://chromedriver.chromium.org/
- Adicione ao PATH

---

## ▶️ EXECUTAR

### Opção 1: Scraping Manual (uma vez)

```bash
# Versão Selenium (recomendado)
python scraper_camoes_selenium.py

# OU versão BeautifulSoup (mais rápida, simples)
python scraper_camoes.py
```

### Opção 2: Scraping Automático Diário

```bash
# Executar agendador (roda às 02:00 todo dia)
python agendador_scraper.py
```

### Opção 3: Com API para N8N

```bash
# Terminal 1: Iniciar API
python api_estoque.py

# Terminal 2: Rodar agendador
python agendador_scraper.py
```

---

## 📊 RESULTADO

Após executar, você terá:

```
projeto/
├── estoque_camoes.json    ← Dados em JSON
├── estoque_camoes.csv     ← Dados em CSV
└── (arquivos de debug)
```

### Exemplo de `estoque_camoes.json`:

```json
{
  "ultima_atualizacao": "2024-01-29 15:30:00",
  "total_veiculos": 24,
  "veiculos": [
    {
      "codigo": "12345",
      "marca": "FIAT",
      "modelo": "FIAT STRADA ENDURANCE 1.3 Flex 8V CS",
      "versao": "ENDURANCE 1.3 Flex 8V CS",
      "ano": "2023/2024",
      "preco": "R$ 89.900",
      "km": "12.000 km",
      "cambio": "Manual",
      "combustivel": "Flex",
      "cor": "Branco",
      "foto_principal": "https://s3.carro57.com.br/FC/6561/6861249_4_M_f857eaa52e.jpeg",
      "link": "https://camoesmultimarcas.com.br/veiculo/12345",
      "data_scraping": "2024-01-29 15:30:00"
    }
  ]
}
```

---

## 🔧 COMO FUNCIONAM OS SELETORES

Os scrapers já vêm com **múltiplos seletores configurados** e tentam automaticamente:

```python
# Exemplo: para encontrar o preço, tenta na ordem:
preco = (
    elemento.find('.price') OU           # class="price"
    elemento.find('.vehicle-price') OU   # class="vehicle-price"
    elemento.find('[data-price]') OU     # data-price="..."
    elemento.find('.value')              # class="value"
)
```

**Você NÃO precisa ajustar nada!** Os scrapers já testam vários seletores.

---

## 🎯 SELETORES JÁ CONFIGURADOS

Baseados na estrutura real do site:

| Campo | Seletores Testados |
|-------|-------------------|
| **Card** | `.vehicle-item`, `.item`, `[data-vehicle-id]`, `article.vehicle-card` |
| **Imagem** | `img[data-src]`, `img.img-responsive`, `img.lazy` |
| **Título** | `h2`, `h3`, `.vehicle-title`, `.car-name` |
| **Preço** | `.price`, `.vehicle-price`, `[data-price]` |
| **Ano** | `.year`, `[data-year]`, `.model-year` |
| **KM** | `.mileage`, `.km`, `[data-mileage]`, `.odometer` |

---

## 🔍 TESTAR SE ESTÁ FUNCIONANDO

### Teste Rápido:

```bash
python scraper_camoes_selenium.py
```

Deve mostrar:

```
🔍 Iniciando scraping...
🌐 Acessando: https://camoesmultimarcas.com.br/multipla
✅ Encontrados 24 veículos
📋 Processando...
  ✓ [1/24] FIAT STRADA - R$ 89.900
  ✓ [2/24] TOYOTA COROLLA - R$ 125.000
  ...
✅ Scraping concluído! 24 veículos extraídos
💾 Dados salvos em estoque_camoes.json
```

### Se der erro:

1. **Nenhum veículo encontrado**
   - Verifique `debug_page.html` gerado
   - O site pode ter mudado a estrutura

2. **Erro de Chrome Driver**
   ```bash
   # Instalar/atualizar Chrome Driver
   sudo apt-get install chromium-chromedriver
   ```

3. **Timeout**
   - Aumente o tempo de espera no código (linha `time.sleep(5)`)

---

## 🔌 INTEGRAÇÃO COM N8N

### 1. Iniciar a API:

```bash
python api_estoque.py
```

A API estará em: `http://localhost:5000`

### 2. Endpoints disponíveis:

```
GET  /api/estoque                    - Estoque completo
GET  /api/estoque/buscar?modelo=X    - Buscar por modelo
GET  /api/estoque/codigo/123         - Buscar por código
POST /api/webhook/n8n                - Webhook para N8N ⭐
GET  /api/status                     - Status do sistema
```

### 3. Exemplo de uso no N8N:

**HTTP Request Node:**
```
Method: POST
URL: http://seu-servidor:5000/api/webhook/n8n
Body:
{
  "acao": "buscar",
  "modelo": "{{ $json.modelo }}"
}
```

**Resposta:**
```json
{
  "sucesso": true,
  "total": 2,
  "veiculos": [
    {
      "codigo": "001",
      "titulo": "FIAT STRADA ENDURANCE",
      "mensagem_whatsapp": "🚘 *FIAT STRADA*\n📅 2023/2024\n💰 R$ 89.900..."
    }
  ]
}
```

Veja mais detalhes em: **`GUIA_INTEGRACAO_N8N.md`**

---

## ⏰ AGENDAMENTO AUTOMÁTICO

### Configurar horário:

Edite `agendador_scraper.py`:

```python
# Executar todo dia às 02:00 (padrão)
schedule.every().day.at("02:00").do(job_atualizar_estoque)

# Outras opções:
# schedule.every().day.at("08:00").do(...)  # 08:00
# schedule.every(12).hours.do(...)          # A cada 12h
# schedule.every().monday.at("09:00").do(...)  # Segundas às 09:00
```

### Rodar em produção (mantém rodando):

**Opção 1: Screen**
```bash
screen -S scraper
python agendador_scraper.py
# Ctrl+A, D (desanexar)
# Reconectar: screen -r scraper
```

**Opção 2: Systemd**
```bash
# Criar serviço (ver README.md antigo para detalhes)
sudo systemctl enable scraper-camoes
sudo systemctl start scraper-camoes
```

---

## 📊 MONITORAMENTO

### Ver logs em tempo real:

```bash
tail -f /var/log/scraper.log
```

### Verificar última atualização:

```bash
python -c "import json; data=json.load(open('estoque_camoes.json')); print(f\"Última atualização: {data['ultima_atualizacao']}\nTotal: {data['total_veiculos']} veículos\")"
```

---

## 🆘 SOLUÇÃO DE PROBLEMAS

### Problema: "No module named 'selenium'"
```bash
pip install selenium
```

### Problema: "ChromeDriver not found"
```bash
# Ubuntu
sudo apt-get install chromium-chromedriver

# Mac
brew install chromedriver
```

### Problema: Site retorna bloqueio/captcha
- Adicione delay maior: `time.sleep(10)`
- Use User-Agent diferente
- Rode em horários de menor tráfego

### Problema: Dados não aparecem
- O site carrega via JavaScript → Use versão Selenium
- Verifique `debug_page.html` gerado

---

## 🎓 PRÓXIMOS PASSOS

Depois que estiver funcionando:

1. ✅ Testar o scraper manualmente
2. ✅ Configurar agendamento diário
3. ✅ Integrar com N8N (se necessário)
4. ✅ Configurar monitoramento
5. ✅ Implementar backup dos dados

---

## 📞 SUPORTE

Em caso de dúvidas:

1. Veja os arquivos de debug gerados:
   - `debug_page.html`
   - `erro_debug.png`
   - `relatorio_testes.json`

2. Execute os testes:
   ```bash
   python test_sistema.py
   ```

3. Consulte os guias:
   - `GUIA_AJUSTAR_SELETORES.md`
   - `GUIA_VISUAL_SELETORES.md`
   - `GUIA_INTEGRACAO_N8N.md`

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Chrome Driver instalado
- [ ] Scraper testado e funcionando
- [ ] Arquivos JSON/CSV sendo gerados
- [ ] Agendador configurado (se necessário)
- [ ] API rodando (se necessário)
- [ ] Integração N8N configurada (se necessário)
- [ ] Monitoramento ativo

---

**Desenvolvido para Camões Automóveis** 🚗  
**Versão:** 2.0 Final - Otimizada e Pronta para Produção
