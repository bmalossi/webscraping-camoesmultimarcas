"""
Agendador para Scraper Camões - Execução Diária Automática
"""

import schedule
import time
from datetime import datetime
from scraper_camoes_selenium import CamoesEstoqueFinal

def job_atualizar_estoque():
    """Job que será executado diariamente"""
    print("\n" + "="*60)
    print(f"🚀 INICIANDO ATUALIZAÇÃO AUTOMÁTICA DO ESTOQUE")
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*60 + "\n")
    
    try:
        scraper = CamoesEstoqueFinal(headless=True)
        estoque = scraper.buscar_estoque()
        
        if estoque:
            scraper.salvar_json('estoque_camoes.json')
            scraper.salvar_csv('estoque_camoes.csv')
            print(f"\n✅ ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!")
            print(f"📊 Total de veículos no estoque: {len(estoque)}")
        else:
            print("\n⚠️ Nenhum veículo encontrado nesta atualização")
        
        scraper.fechar()
            
    except Exception as e:
        print(f"\n❌ ERRO na atualização: {e}")
    
    print("\n" + "="*60 + "\n")


# CONFIGURAÇÕES DE AGENDAMENTO

# Opção 1: Executar todo dia às 02:00 da manhã
schedule.every().day.at("02:00").do(job_atualizar_estoque)

# Opção 2: Executar a cada 24 horas
# schedule.every(24).hours.do(job_atualizar_estoque)

# Opção 3: Executar todo dia às 08:00
# schedule.every().day.at("08:00").do(job_atualizar_estoque)


def main():
    print("🤖 AGENDADOR DE SCRAPING CAMÕES AUTOMÓVEIS")
    print("="*60)
    print("⏰ Configurado para executar diariamente às 02:00")
    print("🔄 Aguardando próxima execução...")
    print("="*60 + "\n")
    
    # Executar uma vez imediatamente ao iniciar
    print("▶️ Executando primeira atualização agora...\n")
    job_atualizar_estoque()
    
    # Loop infinito aguardando os horários agendados
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verifica a cada 60 segundos


if __name__ == "__main__":
    main()
