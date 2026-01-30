# 🚀 Guia de Deploy em Produção (GitHub + Vercel)

Para rodar este projeto 100% na nuvem (todos os dias e com API), siga estes passos:

---

## 1. No GitHub (Automação do Scraper)

1. **Crie um Repositório:** Suba todos os arquivos para um repositório no seu GitHub.
2. **Ative o Workflow:**
   - Acesse a aba **Actions** no seu repositório.
   - O arquivo `.github/workflows/scraper.yml` já está configurado.
   - Ele rodará automaticamente todo dia às 02:00 AM.
   - Você pode rodar manualmente clicando em "Run workflow".
3. **Permissões:**
   - Vá em **Settings > Actions > General**.
   - Em "Workflow permissions", marque **"Read and write permissions"** (isso permite que o robô salve o JSON no repositório).

---

## 2. Na Vercel (Hospedagem da API)

1. **Importe o Projeto:**
   - No painel da Vercel, clique em "Add New > Project".
   - Importe o repositório que você acabou de criar.
2. **Configuração Automática:**
   - A Vercel detectará o arquivo `vercel.json` e configurará a API Flask automaticamente.
3. **Pronto!**
   - Sua API estará online em algo como `seu-projeto.vercel.app/api/estoque`.

---

## 🔄 Como o Ciclo funciona:

1. **02:00 AM:** O GitHub Actions "acorda", abre o Chrome, faz o scrap dos 29 veículos.
2. **02:05 AM:** O GitHub Actions salva o `estoque_camoes.json` no seu repositório.
3. **Auto-Deploy:** Como o repositório mudou, a **Vercel percebe** e atualiza sua API com os novos dados automaticamente em segundos.
4. **Resultado:** Seu n8n sempre lerá os dados atualizados da URL da Vercel.

---

## 🛠️ Arquivos Modificados para Nuvem:
- `requirements.txt`: Adicionado suporte para ambiente Linux.
- `scraper_camoes_selenium.py`: Agora usa `WebDriverManager` (instala o Chrome sozinho na nuvem).
- `vercel.json`: Arquivo de "receita" para a Vercel.
- `.github/workflows/scraper.yml`: O "agendador" que mora no GitHub.
