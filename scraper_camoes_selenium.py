"""
Web Scraper OTIMIZADO para Estoque Camões Automóveis
VERSÃO FINAL - CORRIGIDA com seletores 100% funcionais
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import json
import csv
from datetime import datetime
import time
import re
import sys
import io

# Configurar encoding UTF-8 para stdout (necessário no Windows)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

class CamoesEstoqueFinal:
    def __init__(self, headless=True):
        """
        Inicializa o scraper com Selenium
        headless=True roda sem abrir janela do navegador
        """
        self.base_url = "https://camoesmultimarcas.com.br/multipla"
        self.estoque = []
        self.driver = self._iniciar_driver(headless)
    
    def _iniciar_driver(self, headless):
        """Configura e inicia o Chrome WebDriver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Desabilitar detecção de automação
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Service para baixar driver automaticamente se necessário
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def buscar_estoque(self):
        """Busca o estoque completo de veículos"""
        try:
            print(f"🔍 Iniciando scraping em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"🌐 Acessando: {self.base_url}")
            
            self.driver.get(self.base_url)
            
            # Aguardar página carregar
            print("⏳ Aguardando carregamento da página...")
            time.sleep(5)
            
            # Scroll para carregar todos os veículos (lazy loading)
            self._scroll_pagina()
            
            # BUSCAR TODOS OS DIVS E FILTRAR POR grid-item
            print("🔎 Procurando cards de veículos...")
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "div"))
                )
                
                # Pegar TODOS os divs
                todos_divs = self.driver.find_elements(By.TAG_NAME, "div")
                print(f"DEBUG: Total de divs na página: {len(todos_divs)}")
                print("\n🔍 DEBUG: Procurando classes de cards...")
                classes_unicas = set()
                for i, div in enumerate(todos_divs[:50]):  # Primeiros 50 divs
                    classes = div.get_attribute('class') or ''
                    if classes:
                        classes_unicas.add(classes)
                print("Classes encontradas nos primeiros 50 divs:")
                for classe in sorted(classes_unicas):
                    if 'item' in classe or 'vehicle' in classe or 'car' in classe or 'grid' in classe:
                        print(f"  → '{classe}'")
                
                # FILTRAR só os que tem grid-item na classe
                veiculos = []
                for div in todos_divs:
                    classes = div.get_attribute('class') or ''
                    if 'carro col-md-12' in classes:
                        veiculos.append(div)
                
                print(f"✅ Encontrados {len(veiculos)} cards com classe 'grid-item'!")
                
                if len(veiculos) == 0:
                    print("⚠️ Nenhum grid-item encontrado. Salvando HTML para debug...")
                    with open('debug_page.html', 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    print("💾 HTML salvo em debug_page.html")
                    return []
                
            except TimeoutException:
                print("⚠️ Timeout ao aguardar elementos")
                return []
            
            print(f"📋 Processando {len(veiculos)} veículos encontrados...")
            
            for idx, veiculo in enumerate(veiculos, 1):
                try:
                    dados_veiculo = self._extrair_dados_veiculo(veiculo, idx)
                    
                    if dados_veiculo:
                        # Extrair detalhes adicionais (fotos e cor) da página interna
                        link_detalhes = dados_veiculo.get('link')
                        if link_detalhes:
                            print(f"   → [{idx}/{len(veiculos)}] Coletando fotos e detalhes...", end='\r')
                            detalhes = self._extrair_detalhes_veiculo(link_detalhes)
                            dados_veiculo['fotos'] = detalhes['fotos']
                            if detalhes['cor']:
                                dados_veiculo['cor'] = detalhes['cor']
                        else:
                            dados_veiculo['fotos'] = []

                        self.estoque.append(dados_veiculo)
                        num_fotos = len(dados_veiculo.get('fotos', []))
                        print(f" ✓ [{idx}/{len(veiculos)}] {dados_veiculo.get('modelo', 'N/A')} - {dados_veiculo.get('preco', 'N/A')} ({num_fotos} fotos)")
                except Exception as e:
                    print(f" ✗ [{idx}/{len(veiculos)}] Erro ao processar: {e}")
                    continue
            
            print(f"\n✅ Scraping concluído! {len(self.estoque)} veículos extraídos com sucesso")
            return self.estoque
            
        except Exception as e:
            print(f"❌ Erro durante scraping: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            pass  # Não fechar aqui, fechar manualmente depois
    
    def _scroll_pagina(self):
        """Faz scroll na página para carregar conteúdo lazy loading"""
        print("📜 Fazendo scroll para carregar todos os veículos...")
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 10
        
        while scroll_attempts < max_attempts:
            # Scroll até o final
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Calcular nova altura
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                break
                
            last_height = new_height
            scroll_attempts += 1
        
        print(f"   Scroll concluído após {scroll_attempts} tentativas")
    
    def _extrair_dados_veiculo(self, elemento, index):
        """Extrai dados de um elemento de veículo - VERSÃO CORRIGIDA COM SELETORES REAIS"""
        dados = {'data_scraping': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        # ==== CÓDIGO/ID ====
        # Extrair do ID do elemento ou do link
        try:
            link_elem = elemento.find_element(By.CSS_SELECTOR, 'div.carro-img a')
            href = link_elem.get_attribute('href') or ''
            # Extrair ID do final da URL (ex: 6861249)
            import re
            match = re.search(r'-(\d+)\.html$', href)
            dados['codigo'] = match.group(1) if match else f'CAMOES_{index}'
        except:
            dados['codigo'] = f'CAMOES_{index}'
        
        # ==== MODELO/TÍTULO ====
        try:
            # O modelo está no h2 > a, junto com o ano em um span
            h2_elem = elemento.find_element(By.CSS_SELECTOR, 'h2 a')
            texto_completo = h2_elem.text.strip()
            
            # Remover o ano do início se estiver lá (formato: "2024 MARCA MODELO...")
            partes = texto_completo.split()
            if partes and partes[0].isdigit() and len(partes[0]) == 4:
                # Primeiro item é o ano, remover
                dados['modelo'] = ' '.join(partes[1:])
            else:
                dados['modelo'] = texto_completo
            
            # Extrair marca (primeira palavra do modelo)
            partes_modelo = dados['modelo'].split()
            dados['marca'] = partes_modelo[0] if partes_modelo else ''
            dados['versao'] = ' '.join(partes_modelo[2:]) if len(partes_modelo) > 2 else ''
        except:
            # Fallback: tentar pegar do alt da imagem
            try:
                img = elemento.find_element(By.CSS_SELECTOR, 'img.lazy, img.img-responsive')
                dados['modelo'] = img.get_attribute('alt') or ''
                partes = dados['modelo'].split()
                dados['marca'] = partes[0] if partes else ''
                dados['versao'] = ''
            except:
                return None  # Sem modelo, pula
        
        # ==== PREÇO ====
        try:
            # Preço está em h3.preco com span#valor_veic
            preco_elem = elemento.find_element(By.CSS_SELECTOR, 'h3.preco')
            preco_texto = preco_elem.text.strip()
            # Garantir formato "R$ XX.XXX,XX"
            dados['preco'] = preco_texto.replace('\n', ' ').replace('  ', ' ')
        except:
            try:
                # Tentar pegar só o valor
                valor_elem = elemento.find_element(By.CSS_SELECTOR, 'span#valor_veic')
                dados['preco'] = f"R$ {valor_elem.text.strip()}"
            except:
                dados['preco'] = ''
        
        # Se não tem modelo OU preço, pula
        if not dados.get('modelo') or not dados.get('preco'):
            return None
        
        # ==== ANO ====
        try:
            # Ano está em span.grey-text.text-darken-2 dentro do h2
            ano_elem = elemento.find_element(By.CSS_SELECTOR, 'h2 span.grey-text.text-darken-2')
            dados['ano'] = ano_elem.text.strip()
        except:
            try:
                # Fallback: primeiro span.resumo.black-tx (na seção de detalhes)
                spans = elemento.find_elements(By.CSS_SELECTOR, 'span.resumo.black-tx')
                if spans:
                    texto = spans[0].text.strip()
                    if texto.isdigit() and len(texto) == 4:
                        dados['ano'] = texto
                    else:
                        dados['ano'] = ''
                else:
                    dados['ano'] = ''
            except:
                dados['ano'] = ''
        
        # ==== QUILOMETRAGEM ====
        try:
            # KM está em span.resumo.km.black-tx
            km_elem = elemento.find_element(By.CSS_SELECTOR, 'span.resumo.km')
            dados['km'] = km_elem.text.strip()
        except:
            dados['km'] = ''
        
        # ==== CÂMBIO ====
        try:
            # Câmbio está em span.resumo.cambio34.black-tx
            cambio_elem = elemento.find_element(By.CSS_SELECTOR, 'span.resumo.cambio34')
            dados['cambio'] = cambio_elem.text.strip()
        except:
            dados['cambio'] = ''
        
        # ==== COMBUSTÍVEL ====
        try:
            # Combustível: buscar nos spans.resumo.black-tx pelo padrão
            spans = elemento.find_elements(By.CSS_SELECTOR, 'span.resumo.black-tx')
            combustiveis = ['FLEX', 'GASOLINA', 'DIESEL', 'ETANOL', 'ELÉTRICO', 'HÍBRIDO']
            dados['combustivel'] = ''
            for span in spans:
                texto = span.text.strip().upper()
                if texto in combustiveis:
                    dados['combustivel'] = texto
                    break
        except:
            dados['combustivel'] = ''
        
        # ==== COR ====
        # A cor não está disponível na listagem principal, apenas na página de detalhes
        dados['cor'] = ''
        
        # ==== FOTO ====
        try:
            # Imagem com classe lazy ou img-responsive, priorizar data-src
            img = elemento.find_element(By.CSS_SELECTOR, 'div.carro-img img')
            foto = img.get_attribute('data-src') or img.get_attribute('src')
            # Ignorar placeholder/lazy.gif
            if foto and 'lazy.gif' not in foto.lower() and 'placeholder' not in foto.lower():
                dados['foto_principal'] = foto
            else:
                dados['foto_principal'] = ''
        except:
            dados['foto_principal'] = ''
        
        # ==== LINK ====
        try:
            link_elem = elemento.find_element(By.CSS_SELECTOR, 'div.carro-img a')
            href = link_elem.get_attribute('href')
            if href and not href.startswith('javascript:'):
                # Garantir URL absoluta
                if not href.startswith('http'):
                    dados['link'] = f"https://camoesmultimarcas.com.br{href}"
                else:
                    dados['link'] = href
            else:
                dados['link'] = ''
        except:
            dados['link'] = ''
        
        return dados
    
    def tirar_screenshot(self, arquivo='screenshot_estoque.png'):
        """Tira screenshot da página (útil para debug)"""
        self.driver.save_screenshot(arquivo)
        print(f"📸 Screenshot salva em {arquivo}")
    
    def salvar_json(self, arquivo='estoque_camoes.json'):
        """Salva o estoque em formato JSON"""
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump({
                'ultima_atualizacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_veiculos': len(self.estoque),
                'veiculos': self.estoque
            }, f, ensure_ascii=False, indent=2)
        print(f"💾 Dados salvos em {arquivo}")
    
    def salvar_csv(self, arquivo='estoque_camoes.csv'):
        """Salva o estoque em formato CSV"""
        if not self.estoque:
            print("⚠️ Nenhum veículo para salvar")
            return
        
        with open(arquivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.estoque[0].keys())
            writer.writeheader()
            writer.writerows(self.estoque)
        print(f"💾 Dados salvos em {arquivo}")
    
    def _extrair_detalhes_veiculo(self, link):
        """Acessa a página de detalhes para extrair todas as fotos e a cor"""
        if not link or not link.startswith('http'):
            return {'fotos': [], 'cor': ''}
            
        try:
            # Abrir link em nova aba para não perder a página principal
            self.driver.execute_script(f"window.open('{link}', '_blank');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # Aguardar elementos da página de detalhes
            try:
                WebDriverWait(self.driver, 7).until(
                    EC.presence_of_element_located((By.ID, "SlideShowThumbs"))
                )
            except:
                # Se não encontrar thumbs, tenta esperar pelo título pelo menos
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "h2"))
                )
            
            detalhes = {'fotos': [], 'cor': ''}
            
            # 1. Extrair todas as fotos da galeria (atributo 'ref' contém o link da imagem grande)
            try:
                thumbs = self.driver.find_elements(By.CSS_SELECTOR, "#SlideShowThumbs img")
                for img in thumbs:
                    url_foto = img.get_attribute('ref') or img.get_attribute('src')
                    if url_foto and 'lazy.gif' not in url_foto:
                        detalhes['fotos'].append(url_foto)
                
                # Fallback se não encontrar no SlideShowThumbs (pegar a principal)
                if not detalhes['fotos']:
                    img_principal = self.driver.find_element(By.CSS_SELECTOR, "#veiculo_foto img")
                    url_p = img_principal.get_attribute('src')
                    if url_p: detalhes['fotos'].append(url_p)
            except:
                pass
            
            # 2. Extrair a Cor do veículo (disponível apenas na página interna)
            try:
                # Estrutura: li > div.det-div88 > strong.tit-det66 (Marca/Modelo/Cor...)
                items = self.driver.find_elements(By.CSS_SELECTOR, "li.rela-det5")
                for item in items:
                    texto_item = item.text
                    if "Cor" in texto_item:
                        # O valor da cor está no segundo strong ou após o br
                        valor_cor = item.find_element(By.CSS_SELECTOR, "strong.font-det03").text.strip()
                        detalhes['cor'] = valor_cor
                        break
            except:
                pass
                
            return detalhes
            
        except Exception as e:
            # Silencioso para não poluir o log, já que é um detalhe
            return {'fotos': [], 'cor': ''}
        finally:
            # Fechar aba e voltar para a principal
            if len(self.driver.window_handles) > 1:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
    def fechar(self):
        """Fecha o navegador"""
        if self.driver:
            self.driver.quit()
            print("\n🔒 Navegador fechado")

def main():
    """Função principal"""
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   🚗 SCRAPER CAMÕES AUTOMÓVEIS - VERSÃO FINAL CORRIGIDA  ║
║                                                            ║
║   ✅ Filtro por grid-item implementado                    ║
║   📸 Extração de detalhes (todas as fotos e cor)          ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")
    
    # headless=False para ver o navegador funcionando (debug)
    # headless=True para rodar em background (produção)
    scraper = CamoesEstoqueFinal(headless=True)
    
    try:
        # Buscar estoque
        estoque = scraper.buscar_estoque()
        
        if estoque:
            # Salvar em JSON e CSV
            scraper.salvar_json('estoque_camoes.json')
            scraper.salvar_csv('estoque_camoes.csv')
            
            print(f"\n{'='*60}")
            print(f"📊 RESUMO FINAL")
            print(f"{'='*60}")
            print(f"  Total de veículos: {len(estoque)}")
            print(f"  Arquivo JSON: estoque_camoes.json")
            print(f"  Arquivo CSV: estoque_camoes.csv")
            print(f"  Última atualização: {estoque[0]['data_scraping'] if estoque else 'N/A'}")
            
            # Mostrar preview dos primeiros 3 veículos
            print(f"\n📋 PREVIEW (primeiros 3 veículos):")
            for i, v in enumerate(estoque[:3], 1):
                print(f"\n  {i}. {v.get('modelo', 'N/A')}")
                print(f"     Preço: {v.get('preco', 'N/A')}")
                print(f"     Ano: {v.get('ano', 'N/A')} | Cor: {v.get('cor', 'N/A')}")
                print(f"     Fotos: {len(v.get('fotos', []))} imagens encontradas")
        else:
            print("\n❌ Nenhum veículo encontrado")
            print("💡 Dica: Verifique o arquivo debug_page.html gerado")
            # Tirar screenshot para debug
            scraper.tirar_screenshot('erro_debug.png')
            print("📸 Screenshot de erro salvo em erro_debug.png")
    
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        scraper.fechar()
    
    print(f"\n✅ Processo finalizado!\n")

if __name__ == "__main__":
    main()
