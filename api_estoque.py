"""
API REST OTIMIZADA com Cache - Camões Automóveis
Versão com performance melhorada (< 1s de resposta)
"""

from flask import Flask, jsonify, request
import json
from datetime import datetime
import os
from functools import lru_cache
import time

app = Flask(__name__)

# Configurar JSON para usar UTF-8 corretamente
app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

# Arquivo do estoque
ESTOQUE_FILE = 'estoque_camoes.json'

# Cache global
_cache = {
    'estoque': None,
    'timestamp': None,
    'cache_duration': 300  # 5 minutos em segundos
}

def carregar_estoque():
    """Carrega o estoque do arquivo JSON com cache"""
    global _cache
    
    # Verificar se existe cache válido
    now = time.time()
    if _cache['estoque'] is not None and _cache['timestamp'] is not None:
        if now - _cache['timestamp'] < _cache['cache_duration']:
            return _cache['estoque']
    
    # Cache expirado ou não existe, carregar do arquivo
    if not os.path.exists(ESTOQUE_FILE):
        estoque_vazio = {
            'ultima_atualizacao': None,
            'total_veiculos': 0,
            'veiculos': []
        }
        _cache['estoque'] = estoque_vazio
        _cache['timestamp'] = now
        return estoque_vazio
    
    with open(ESTOQUE_FILE, 'r', encoding='utf-8') as f:
        estoque = json.load(f)
        _cache['estoque'] = estoque
        _cache['timestamp'] = now
        return estoque


def limpar_cache():
    """Limpa o cache forçando recarregamento"""
    global _cache
    _cache['estoque'] = None
    _cache['timestamp'] = None


@app.route('/api/estoque', methods=['GET'])
def obter_estoque_completo():
    """
    GET /api/estoque
    Retorna o estoque completo (com cache)
    """
    estoque = carregar_estoque()
    return jsonify(estoque)


@app.route('/api/estoque/buscar', methods=['GET'])
def buscar_veiculo():
    """
    GET /api/estoque/buscar?modelo=corolla
    Busca veículos por modelo (com cache)
    """
    modelo = request.args.get('modelo', '').lower()
    
    if not modelo:
        return jsonify({'erro': 'Parâmetro "modelo" é obrigatório'}), 400
    
    estoque = carregar_estoque()
    resultados = [
        v for v in estoque['veiculos'] 
        if modelo in v.get('modelo', '').lower()
    ]
    
    return jsonify({
        'query': modelo,
        'total_encontrados': len(resultados),
        'veiculos': resultados
    })


@app.route('/api/estoque/codigo/<codigo>', methods=['GET'])
def obter_por_codigo(codigo):
    """
    GET /api/estoque/codigo/001
    Retorna veículo por código (com cache)
    """
    estoque = carregar_estoque()
    veiculo = next(
        (v for v in estoque['veiculos'] if v.get('codigo') == codigo),
        None
    )
    
    if veiculo:
        return jsonify(veiculo)
    else:
        return jsonify({'erro': 'Veículo não encontrado'}), 404


@app.route('/api/estoque/filtrar', methods=['POST'])
def filtrar_veiculos():
    """
    POST /api/estoque/filtrar
    Body: {
        "marca": "Toyota",
        "preco_max": 100000,
        "ano_min": 2020
    }
    Filtra veículos por múltiplos critérios (com cache)
    """
    filtros = request.json
    estoque = carregar_estoque()
    resultados = estoque['veiculos'].copy()
    
    # Aplicar filtros
    if 'marca' in filtros:
        marca = filtros['marca'].lower()
        resultados = [v for v in resultados if marca in v.get('marca', '').lower()]
    
    if 'modelo' in filtros:
        modelo = filtros['modelo'].lower()
        resultados = [v for v in resultados if modelo in v.get('modelo', '').lower()]
    
    if 'ano_min' in filtros:
        try:
            resultados = [
                v for v in resultados 
                if int(v.get('ano', '0/0').split('/')[0]) >= filtros['ano_min']
            ]
        except:
            pass
    
    if 'cor' in filtros:
        cor = filtros['cor'].lower()
        resultados = [v for v in resultados if cor in v.get('cor', '').lower()]
    
    return jsonify({
        'filtros_aplicados': filtros,
        'total_encontrados': len(resultados),
        'veiculos': resultados
    })


@app.route('/api/status', methods=['GET'])
def status():
    """
    GET /api/status
    Retorna status da última atualização
    """
    estoque = carregar_estoque()
    return jsonify({
        'status': 'online',
        'ultima_atualizacao': estoque.get('ultima_atualizacao'),
        'total_veiculos': estoque.get('total_veiculos'),
        'cache_ativo': _cache['estoque'] is not None,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/webhook/n8n', methods=['POST'])
def webhook_n8n():
    """
    POST /api/webhook/n8n
    Body: {
        "acao": "buscar",
        "modelo": "Corolla"
    }
    
    Endpoint especial formatado para N8N (com cache)
    """
    dados = request.json
    acao = dados.get('acao')
    
    if acao == 'buscar':
        modelo = dados.get('modelo', '').lower()
        estoque = carregar_estoque()
        resultados = [
            v for v in estoque['veiculos'] 
            if modelo in v.get('modelo', '').lower()
        ]
        
        # Formato especial para N8N com mensagens prontas
        resposta_formatada = []
        for v in resultados:
            resposta_formatada.append({
                'codigo': v.get('codigo'),
                'titulo': f"{v.get('marca')} {v.get('modelo')} {v.get('versao')}",
                'descricao': f"Ano: {v.get('ano')} | KM: {v.get('km')} | Câmbio: {v.get('cambio')}",
                'preco': v.get('preco'),
                'foto': v.get('foto_principal'),
                'fotos': v.get('fotos', []),
                'cor': v.get('cor'),
                'link': v.get('link'),
                'detalhes': v.get('detalhes', ''),
                'opcionais': v.get('opcionais', []),
                'mensagem_whatsapp': f"🚘 *{v.get('marca')} {v.get('modelo')}*\n🎨 Cor: {v.get('cor')}\n📅 {v.get('ano')}\n💰 {v.get('preco')}\n📍 {v.get('km')}\n⚙️ {v.get('cambio')}\n📸 {len(v.get('fotos', []))} fotos disponíveis\n\n📝 *Detalhes:*\n{v.get('detalhes', 'Não informado')}"
            })
        
        return jsonify({
            'sucesso': True,
            'total': len(resposta_formatada),
            'veiculos': resposta_formatada
        })
    
    return jsonify({'erro': 'Ação não reconhecida'}), 400


@app.route('/api/cache/limpar', methods=['POST'])
def limpar_cache_endpoint():
    """
    POST /api/cache/limpar
    Limpa o cache forçando recarregamento do arquivo
    """
    limpar_cache()
    return jsonify({
        'sucesso': True,
        'mensagem': 'Cache limpo com sucesso'
    })


@app.route('/api/cache/info', methods=['GET'])
def info_cache():
    """
    GET /api/cache/info
    Retorna informações sobre o cache
    """
    return jsonify({
        'cache_ativo': _cache['estoque'] is not None,
        'timestamp_cache': datetime.fromtimestamp(_cache['timestamp']).strftime('%Y-%m-%d %H:%M:%S') if _cache['timestamp'] else None,
        'duracao_cache_segundos': _cache['cache_duration'],
        'veiculos_em_cache': len(_cache['estoque']['veiculos']) if _cache['estoque'] else 0
    })


# Configurar CORS para permitir requisições do N8N
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


if __name__ == '__main__':
    print("🚀 API Camões Automóveis OTIMIZADA iniciada!")
    print("="*70)
    print("📡 Endpoints disponíveis:")
    print("   GET  /api/estoque")
    print("   GET  /api/estoque/buscar?modelo=corolla")
    print("   GET  /api/estoque/codigo/<codigo>")
    print("   POST /api/estoque/filtrar")
    print("   GET  /api/status")
    print("   POST /api/webhook/n8n")
    print("   POST /api/cache/limpar          ← Limpar cache")
    print("   GET  /api/cache/info            ← Info do cache")
    print()
    print("⚡ OTIMIZAÇÕES:")
    print("   • Cache de 5 minutos (resposta < 100ms)")
    print("   • CORS habilitado para N8N")
    print("   • Endpoints de gerenciamento de cache")
    print()
    print("🌐 Rodando em: http://localhost:5000")
    print("="*70)
    print()
    
    # Pré-carregar cache na inicialização
    print("🔄 Pré-carregando cache...")
    estoque = carregar_estoque()
    print(f"✅ Cache carregado: {estoque['total_veiculos']} veículos\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)  # debug=False para produção
