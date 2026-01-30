"""
Script de Testes - Validação Completa do Sistema
Testa scraper, API e integração
"""

import requests
import json
import time
from datetime import datetime
import sys
import io

# Configurar encoding UTF-8 para stdout (necessário no Windows)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

class TestadorSistema:
    def __init__(self, api_url='http://localhost:5000'):
        self.api_url = api_url
        self.resultados = []
    
    def print_header(self, titulo):
        """Imprime cabeçalho bonito"""
        print("\n" + "="*60)
        print(f"🧪 {titulo}")
        print("="*60)
    
    def print_resultado(self, teste, sucesso, detalhes=""):
        """Imprime resultado do teste"""
        status = "✅ PASSOU" if sucesso else "❌ FALHOU"
        print(f"{status} - {teste}")
        if detalhes:
            print(f"   → {detalhes}")
        
        self.resultados.append({
            'teste': teste,
            'sucesso': sucesso,
            'detalhes': detalhes,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def teste_1_arquivo_estoque_existe(self):
        """Teste 1: Verificar se arquivo de estoque existe"""
        self.print_header("Teste 1: Arquivo de Estoque")
        
        import os
        arquivo_existe = os.path.exists('estoque_camoes.json')
        
        self.print_resultado(
            "Arquivo estoque_camoes.json existe",
            arquivo_existe,
            "Arquivo encontrado" if arquivo_existe else "Execute o scraper primeiro"
        )
        
        if arquivo_existe:
            with open('estoque_camoes.json', 'r', encoding='utf-8') as f:
                dados = json.load(f)
                total = dados.get('total_veiculos', 0)
                self.print_resultado(
                    "Arquivo contém dados válidos",
                    total > 0,
                    f"{total} veículos no estoque"
                )
        
        return arquivo_existe
    
    def teste_2_api_online(self):
        """Teste 2: Verificar se API está online"""
        self.print_header("Teste 2: Status da API")
        
        try:
            response = requests.get(f"{self.api_url}/api/status", timeout=5)
            online = response.status_code == 200
            
            if online:
                dados = response.json()
                self.print_resultado(
                    "API está online",
                    True,
                    f"Status: {dados.get('status')} | Atualização: {dados.get('ultima_atualizacao')}"
                )
            else:
                self.print_resultado("API está online", False, f"Status code: {response.status_code}")
            
            return online
            
        except requests.exceptions.ConnectionError:
            self.print_resultado("API está online", False, "Não foi possível conectar. Inicie a API com: python api_estoque.py")
            return False
        except Exception as e:
            self.print_resultado("API está online", False, str(e))
            return False
    
    def teste_3_endpoint_estoque(self):
        """Teste 3: Endpoint GET /api/estoque"""
        self.print_header("Teste 3: Endpoint Estoque Completo")
        
        try:
            response = requests.get(f"{self.api_url}/api/estoque", timeout=5)
            sucesso = response.status_code == 200
            
            if sucesso:
                dados = response.json()
                total = dados.get('total_veiculos', 0)
                self.print_resultado(
                    "GET /api/estoque",
                    True,
                    f"{total} veículos retornados"
                )
            else:
                self.print_resultado("GET /api/estoque", False, f"Status: {response.status_code}")
            
            return sucesso
            
        except Exception as e:
            self.print_resultado("GET /api/estoque", False, str(e))
            return False
    
    def teste_4_endpoint_buscar(self):
        """Teste 4: Endpoint GET /api/estoque/buscar"""
        self.print_header("Teste 4: Busca por Modelo")
        
        # Primeiro, obter um modelo do estoque
        try:
            response = requests.get(f"{self.api_url}/api/estoque", timeout=5)
            estoque = response.json()
            
            if estoque['total_veiculos'] == 0:
                self.print_resultado("GET /api/estoque/buscar", False, "Estoque vazio")
                return False
            
            # Pegar o modelo do primeiro veículo
            modelo_teste = estoque['veiculos'][0].get('modelo', 'teste')
            palavra_busca = modelo_teste.split()[0].lower()  # Primeira palavra do modelo
            
            # Fazer busca
            response = requests.get(
                f"{self.api_url}/api/estoque/buscar",
                params={'modelo': palavra_busca},
                timeout=5
            )
            
            sucesso = response.status_code == 200
            
            if sucesso:
                dados = response.json()
                total = dados.get('total_encontrados', 0)
                self.print_resultado(
                    f"GET /api/estoque/buscar?modelo={palavra_busca}",
                    True,
                    f"{total} veículos encontrados"
                )
            else:
                self.print_resultado("GET /api/estoque/buscar", False, f"Status: {response.status_code}")
            
            return sucesso
            
        except Exception as e:
            self.print_resultado("GET /api/estoque/buscar", False, str(e))
            return False
    
    def teste_5_endpoint_codigo(self):
        """Teste 5: Endpoint GET /api/estoque/codigo/{codigo}"""
        self.print_header("Teste 5: Busca por Código")
        
        try:
            # Obter primeiro código do estoque
            response = requests.get(f"{self.api_url}/api/estoque", timeout=5)
            estoque = response.json()
            
            if estoque['total_veiculos'] == 0:
                self.print_resultado("GET /api/estoque/codigo", False, "Estoque vazio")
                return False
            
            codigo_teste = estoque['veiculos'][0].get('codigo', '001')
            
            # Buscar por código
            response = requests.get(
                f"{self.api_url}/api/estoque/codigo/{codigo_teste}",
                timeout=5
            )
            
            sucesso = response.status_code == 200
            
            if sucesso:
                dados = response.json()
                self.print_resultado(
                    f"GET /api/estoque/codigo/{codigo_teste}",
                    True,
                    f"Veículo: {dados.get('modelo', 'N/A')}"
                )
            else:
                self.print_resultado(f"GET /api/estoque/codigo/{codigo_teste}", False, f"Status: {response.status_code}")
            
            return sucesso
            
        except Exception as e:
            self.print_resultado("GET /api/estoque/codigo", False, str(e))
            return False
    
    def teste_6_endpoint_webhook_n8n(self):
        """Teste 6: Endpoint POST /api/webhook/n8n"""
        self.print_header("Teste 6: Webhook N8N")
        
        try:
            # Obter modelo para teste
            response = requests.get(f"{self.api_url}/api/estoque", timeout=5)
            estoque = response.json()
            
            if estoque['total_veiculos'] == 0:
                self.print_resultado("POST /api/webhook/n8n", False, "Estoque vazio")
                return False
            
            modelo_teste = estoque['veiculos'][0].get('modelo', 'teste').split()[0]
            
            # Fazer requisição ao webhook
            response = requests.post(
                f"{self.api_url}/api/webhook/n8n",
                json={
                    'acao': 'buscar',
                    'modelo': modelo_teste
                },
                timeout=5
            )
            
            sucesso = response.status_code == 200
            
            if sucesso:
                dados = response.json()
                total = dados.get('total', 0)
                
                # Verificar se retorna campos formatados para N8N
                campos_ok = False
                if total > 0:
                    primeiro = dados['veiculos'][0]
                    campos_ok = all(k in primeiro for k in ['codigo', 'titulo', 'mensagem_whatsapp'])
                
                self.print_resultado(
                    f"POST /api/webhook/n8n (modelo={modelo_teste})",
                    campos_ok,
                    f"{total} veículos com campos formatados" if campos_ok else "Campos faltando"
                )
                
                return campos_ok
            else:
                self.print_resultado("POST /api/webhook/n8n", False, f"Status: {response.status_code}")
                return False
            
        except Exception as e:
            self.print_resultado("POST /api/webhook/n8n", False, str(e))
            return False
    
    def teste_7_performance(self):
        """Teste 7: Performance da API"""
        self.print_header("Teste 7: Performance")
        
        try:
            # Fazer 10 requisições e medir tempo médio
            tempos = []
            
            for i in range(10):
                inicio = time.time()
                requests.get(f"{self.api_url}/api/estoque", timeout=5)
                fim = time.time()
                tempos.append(fim - inicio)
            
            tempo_medio = sum(tempos) / len(tempos)
            tempo_ok = tempo_medio < 1.0  # Menos de 1 segundo
            
            self.print_resultado(
                "Tempo de resposta médio < 1s",
                tempo_ok,
                f"{tempo_medio:.3f}s (10 requisições)"
            )
            
            return tempo_ok
            
        except Exception as e:
            self.print_resultado("Performance", False, str(e))
            return False
    
    def gerar_relatorio(self):
        """Gera relatório final dos testes"""
        self.print_header("RELATÓRIO FINAL")
        
        total_testes = len(self.resultados)
        testes_ok = sum(1 for r in self.resultados if r['sucesso'])
        testes_falha = total_testes - testes_ok
        
        print(f"\n📊 Resumo:")
        print(f"   Total de testes: {total_testes}")
        print(f"   ✅ Sucessos: {testes_ok}")
        print(f"   ❌ Falhas: {testes_falha}")
        
        if testes_ok == total_testes:
            print(f"\n🎉 PARABÉNS! Todos os testes passaram!")
        else:
            print(f"\n⚠️  Alguns testes falharam. Revise os erros acima.")
        
        # Salvar relatório em JSON
        with open('relatorio_testes.json', 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'resumo': {
                    'total': total_testes,
                    'sucessos': testes_ok,
                    'falhas': testes_falha
                },
                'testes': self.resultados
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Relatório salvo em: relatorio_testes.json\n")


def main():
    """Executa todos os testes"""
    print("\n🚀 INICIANDO BATERIA DE TESTES DO SISTEMA CAMÕES")
    print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    testador = TestadorSistema()
    
    # Executar testes sequencialmente
    testador.teste_1_arquivo_estoque_existe()
    
    # Se API não estiver online, avisar e parar
    if not testador.teste_2_api_online():
        print("\n⚠️  API não está online. Inicie com: python api_estoque.py")
        print("   Alguns testes não podem ser executados.\n")
        testador.gerar_relatorio()
        return
    
    testador.teste_3_endpoint_estoque()
    testador.teste_4_endpoint_buscar()
    testador.teste_5_endpoint_codigo()
    testador.teste_6_endpoint_webhook_n8n()
    testador.teste_7_performance()
    
    # Gerar relatório final
    testador.gerar_relatorio()


if __name__ == "__main__":
    main()
